-- EFA + FAO product schema for Supabase (Postgres 15).
-- Principle: student-level data never enters this database. Only aggregates, model artifacts, and lineage.
-- The Python pipeline writes with the service role; the dashboard reads with the user's JWT under RLS.

create extension if not exists pgcrypto;

create type app_role     as enum ('admin', 'analyst', 'enrollment_team', 'leadership');
create type run_status   as enum ('running', 'succeeded', 'failed');
create type engagement_phase as enum ('scope', 'analysis', 'close');

create table institutions (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  is_synthetic boolean not null default false,
  min_cell_size int not null default 10 check (min_cell_size >= 10),
  created_at timestamptz not null default now()
);

create table memberships (
  user_id uuid not null references auth.users(id) on delete cascade,
  institution_id uuid not null references institutions(id) on delete cascade,
  role app_role not null,
  primary key (user_id, institution_id)
);

create table engagements (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references institutions(id) on delete cascade,
  name text not null,
  phase engagement_phase not null default 'scope',
  scope_of_work_ref text,
  starts_on date, closes_on date
);

-- Lineage: what data (by hash, never content) and what code produced every number on screen.
create table data_batches (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references institutions(id) on delete cascade,
  engagement_id uuid references engagements(id),
  kind text not null,                      -- students | aid_offers | fafsa | price_test | pricing | aid_policy
  sha256 text not null,
  received_at timestamptz not null default now(),
  row_counts jsonb not null default '{}',
  qa jsonb not null default '{}'           -- rules applied and row counts affected
);

create table model_runs (
  id uuid primary key default gen_random_uuid(),
  institution_id uuid not null references institutions(id) on delete cascade,
  engagement_id uuid references engagements(id),
  live_cohort int not null,
  code_version text not null,
  config jsonb not null,
  config_sha256 text not null,
  data_sha256 text not null,
  bootstrap_draws int not null,
  anchor jsonb not null,                   -- experiment, RD, pooled anchor, lambda, kappa
  realization_ratio numeric not null check (realization_ratio between 0 and 1),
  status run_status not null default 'running',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  is_published boolean not null default false,
  published_by uuid references auth.users(id),
  published_at timestamptz
);
create index on model_runs (institution_id, is_published, finished_at desc);

-- Every artifact table carries model_run_id so a published run is an immutable, versioned snapshot.
create table funnel_cells (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  cohort int not null,                     -- 0 = pooled across historical cohorts
  dim1 text not null, val1 text not null, dim2 text, val2 text,
  inquiries int, applications int, admits int, deposits int, enrolled int,
  apply_rate numeric, admit_rate numeric, yield_rate numeric, inquiry_to_enroll numeric,
  suppressed boolean not null default false,
  protected_dimension boolean not null default false,
  check (suppressed = false or (inquiries is null and enrolled is null))      -- disclosure control, enforced in the database
);
create index on funnel_cells (model_run_id, dim1, dim2, cohort);

create table efa_drivers (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  stage text not null, term text not null,
  ame_pp numeric, ci_low_pp numeric, ci_high_pp numeric
);

create table model_coefficients (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  model text not null, term text not null, coef numeric not null, se numeric
);

create table price_response_curves (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  dimension text not null, segment text not null,
  discretionary_award_usd int not null, students int not null check (students >= 10),
  p_enroll numeric not null, p05 numeric, p95 numeric
);
create index on price_response_curves (model_run_id, dimension, segment);

create table scenarios (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  scenario_id text not null, label text not null, objective text,
  budget numeric, min_enrollment numeric,
  expected_enrolled numeric, expected_enrolled_p05 numeric, expected_enrolled_p95 numeric,
  ntr_multi_year numeric, ntr_multi_year_p05 numeric, ntr_multi_year_p95 numeric,
  discretionary_spend numeric, discount_rate numeric,
  ntr_gain_model_pred numeric,             -- raw model estimate; shown as an upper bound
  ntr_gain_planning numeric,               -- after the backtest realization ratio; shown as the planning figure
  prob_ntr_gain_vs_status_quo numeric,
  primary key (model_run_id, scenario_id)
);

create table projection_segments (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  dimension text not null, segment text not null, admits int not null check (admits >= 10),
  expected_enrolled_status_quo numeric, sq_p05 numeric, sq_p95 numeric,
  expected_enrolled_recommended numeric, rec_p05 numeric, rec_p95 numeric,
  avg_discretionary_status_quo numeric, avg_discretionary_recommended numeric,
  yield_status_quo numeric, yield_recommended numeric, avg_price_sensitivity_pp_per_1k numeric
);

create table equity_audit (
  model_run_id uuid not null references model_runs(id) on delete cascade,
  dimension text not null, "group" text not null, allocation text not null,
  admits int not null check (admits >= 10),
  avg_discretionary numeric, expected_yield numeric, expected_discount_rate numeric, share_with_increase numeric
);

create table source_taxonomy (
  institution_id uuid not null references institutions(id) on delete cascade,
  version int not null, category text not null, match_patterns text not null, precedence int not null,
  primary key (institution_id, version, category)
);

-- Synthetic-only validation tables (never populated for real clients).
create table validation_recovery (model_run_id uuid references model_runs(id) on delete cascade, method text, ame_pp_per_1k numeric, ci_low numeric, ci_high numeric, truth_in_ci boolean);
create table validation_backtest (model_run_id uuid references model_runs(id) on delete cascade, strategy text, expected_enrolled numeric, enrolled_vs_status_quo numeric, ntr_multi_year numeric, ntr_vs_status_quo numeric, ntr_vs_status_quo_pct numeric, model_predicted_ntr_vs_status_quo numeric);

create table audit_log (
  id bigint generated always as identity primary key,
  at timestamptz not null default now(),
  user_id uuid, institution_id uuid, action text not null, entity text, entity_id text
);

-- ---------------------------------------------------------------- access control
create or replace function app_role_of(inst uuid) returns app_role
language sql stable security definer set search_path = public as $$
  select role from memberships where user_id = auth.uid() and institution_id = inst
$$;

-- Analysts and admins see every run; enrollment teams and leadership see only published runs.
create or replace function can_read_run(run uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from model_runs r
    join memberships m on m.institution_id = r.institution_id and m.user_id = auth.uid()
    where r.id = run and (m.role in ('admin','analyst') or r.is_published)
  )
$$;

alter table institutions enable row level security;
alter table memberships enable row level security;
alter table engagements enable row level security;
alter table data_batches enable row level security;
alter table model_runs enable row level security;
alter table source_taxonomy enable row level security;
alter table audit_log enable row level security;
create policy inst_read on institutions for select using (app_role_of(id) is not null);
create policy mem_read on memberships for select using (user_id = auth.uid());
create policy eng_read on engagements for select using (app_role_of(institution_id) in ('admin','analyst'));
create policy batch_read on data_batches for select using (app_role_of(institution_id) in ('admin','analyst'));
create policy run_read on model_runs for select using (can_read_run(id));
create policy tax_read on source_taxonomy for select using (app_role_of(institution_id) is not null);
create policy audit_read on audit_log for select using (app_role_of(institution_id) = 'admin');

do $$
declare t text;
begin
  foreach t in array array['funnel_cells','efa_drivers','model_coefficients','price_response_curves','scenarios',
                           'projection_segments','equity_audit','validation_recovery','validation_backtest']
  loop
    execute format('alter table %I enable row level security', t);
    execute format('create policy %I on %I for select using (can_read_run(model_run_id))', t || '_read', t);
  end loop;
end $$;

-- Leadership sees headline scenarios only; the planner and allocation detail are for the enrollment team and analysts.
create view leadership_scenarios with (security_invoker = true) as
  select s.* from scenarios s
  join model_runs r on r.id = s.model_run_id
  where r.is_published and s.scenario_id in ('status_quo','ntr_budget_0.75x','ntr_budget_1x','ntr_budget_1.25x');

-- Publishing is an explicit, logged act by an analyst; the pipeline can never publish on its own.
create or replace function publish_model_run(run uuid) returns void
language plpgsql security definer set search_path = public as $$
declare inst uuid;
begin
  select institution_id into inst from model_runs where id = run and status = 'succeeded';
  if inst is null then raise exception 'run not found or not succeeded'; end if;
  if app_role_of(inst) not in ('admin','analyst') then raise exception 'not permitted'; end if;
  update model_runs set is_published = true, published_by = auth.uid(), published_at = now() where id = run;
  insert into audit_log (user_id, institution_id, action, entity, entity_id) values (auth.uid(), inst, 'publish', 'model_run', run::text);
end $$;
-- No INSERT/UPDATE/DELETE policies exist for authenticated users: only the service role (pipeline) writes.
