#!/usr/bin/env python3
"""Generate the Frankel data request (v3) for one program from the single-source spec.

    python build_request.py --program law --institution "University of Richmond School of Law"
    python build_request.py --program undergraduate --institution "[Institution]"
    python build_request.py --program all

Reads spec/*.csv and spec/request_spec.yaml. Writes to output/ (or --out):
    Data_Request_v3_<program>_<institution>.docx   client-facing request
    Data_Request_v3_<program>_<institution>.md     same content, for diffing in git
    Data_Request_Template_<program>.xlsx           field template, code lists, reference and scoping sheets
    data_dictionary_v3_<program>.csv               field specification for this program

Nothing here touches efa_fao/src or student data. See README.md for how to add a program.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

import yaml
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec"
PROGRAMS = ("law", "undergraduate")
NAVY = "1F3864"
GREY = "F2F2F2"
LINE = "BFBFBF"


# ----------------------------------------------------------------------------
# Spec loading and program resolution
# ----------------------------------------------------------------------------
def read_csv(name):
    with open(SPEC / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_spec():
    with open(SPEC / "request_spec.yaml", encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)
    spec["fields"] = read_csv("fields.csv")
    spec["files"] = read_csv("files.csv")
    spec["components"] = read_csv("components.csv")
    spec["definitions"] = read_csv("definitions.csv")
    spec["reference_items"] = read_csv("reference_items.csv")
    spec["scoping"] = read_csv("scoping.csv")
    return spec


def col(program):
    return "law" if program == "law" else "ug"


def applies(only, program):
    return only in (None, "", "both", "all") or only == program


def pick(value, program):
    """Resolve a text value that may be a {law:, undergraduate:} mapping. None if it has no text for the program."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(program)
    return value


def item_text(item, program):
    """Resolve a bullet/checklist/paragraph item (string, or mapping with text/only)."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        if not applies(item.get("only"), program):
            return None
        return pick(item.get("text"), program)
    return None


def subst(text, ctx):
    if text is None:
        return None
    for k, v in ctx.items():
        text = text.replace("{" + k + "}", v)
    return text


def slug(s):
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s or "Institution"


# ----------------------------------------------------------------------------
# Intermediate representation
# ----------------------------------------------------------------------------
def values_for(fld, program):
    """Values column; a 'Law: ... UG: ...' value is split by program."""
    v = fld["values"]
    if v.startswith("Law:") and " UG: " in v:
        law, ug = v[4:].split(" UG: ", 1)
        return law.strip() if program == "law" else ug.strip()
    return v


def tier_label(t):
    return {"1": "1", "2": "2", "A": "A"}.get(t, t)


def build_ir(spec, program, ctx):
    ir = []
    ir.append(("title", subst(spec["title"], ctx)))
    ir.append(("kv", [[subst(a, ctx), subst(b, ctx)] for a, b in spec["header"]]))
    for n, sec in enumerate(spec["sections"], start=1):
        ir.append(("h1", f"{n}. {sec['title']}"))
        ir.extend(blocks_to_ir(sec["blocks"], spec, program, ctx))
    ir.append(("landscape", None))
    for app in spec["appendices"]:
        ir.append(("h1", app["title"]))
        ir.extend(blocks_to_ir(app["blocks"], spec, program, ctx, landscape=True))
    return ir


def blocks_to_ir(blocks, spec, program, ctx, landscape=False):
    out = []
    for b in blocks:
        if "p" in b:
            t = pick(b["p"], program)
            if t:
                out.append(("p", subst(t, ctx)))
        elif "bullets" in b:
            items = [subst(item_text(i, program), ctx) for i in b["bullets"] if item_text(i, program)]
            if items:
                out.append(("bullets", items))
        elif "checklist" in b:
            items = [subst(item_text(i, program), ctx) for i in b["checklist"] if item_text(i, program)]
            out.append(("checklist", items))
        elif "table" in b:
            tb = b["table"]
            rows = []
            for r in tb["rows"]:
                if isinstance(r, dict):
                    if not applies(r.get("only"), program):
                        continue
                    r = r["cells"]
                rows.append([subst(c, ctx) for c in r])
            out.append(("table", tb["cols"], rows, tb.get("widths")))
        elif "special" in b:
            out.extend(special_to_ir(b["special"], spec, program, ctx))
    return out


def special_to_ir(kind, spec, program, ctx):
    c = col(program)
    if kind == "file_list":
        rows = []
        for f in sorted(spec["files"], key=lambda r: int(r["order"])):
            tier = f["tier_law"] if program == "law" else f["tier_ug"]
            if tier.lower().startswith("not requested"):
                continue
            keys = f["key_fields_law"] if program == "law" else f["key_fields_ug"]
            rows.append([f"`{f['file']}`", f["one_row_per"], keys, tier])
        rows.append(["`Institutional_Reference` (worksheet)", "Measure and cohort", "Totals you already file or publish, for reconciliation (see Institutional reference)", "1"])
        rows.append(["`Scoping_Inputs` (worksheet)", "Input", "Answers for the price-test screen (see Scoping inputs)", "1"])
        return [("table", ["File", "One row per", "Key fields", "Tier"], rows, [1.3, 1.1, 3.2, 0.9])]
    if kind == "definitions_table":
        rows = []
        for d in spec["definitions"]:
            if not applies(d["programs"], program):
                continue
            text = d["definition_law"] if program == "law" else d["definition_ug"]
            src = d["source"] if program == "law" else re.sub(r";?\s*ABA 509", "", d["source"]).strip("; ")
            rows.append([f"**{d['term']}**", text, src])
        return [("table", ["Term", "Definition we use", "Source"], rows, [1.2, 4.3, 1.0])]
    if kind == "components_table":
        rows = []
        for r in spec["components"]:
            flag = r[c]
            if flag == "-":
                continue
            note = r["note"]
            if flag == "C":
                note += " (only if applicable)"
            if flag == "N":
                note += " (if any)"
            rows.append([f"`{r['component']}`", r["category"], note])
        return [("table", ["Component", "Gift or self-help", "Notes"], rows, [1.7, 1.2, 3.6])]
    if kind == "scoping_table":
        rows = [[r["group"], f"**{r['input']}**", r["description"] + (r.get("law_extra", "") if program == "law" else "")] for r in spec["scoping"] if r[c] == "Y"]
        return [("table", ["Who supplies it", "Input", "Description"], rows, [1.5, 1.7, 3.3])]
    if kind == "reference_table":
        rows = [[r["group"], r["item"], r["source_ref"], r["note"]] for r in spec["reference_items"] if r["program"] == program]
        return [("table", ["Group", "Figure, for each cohort year", "Source", "Note"], rows, [1.0, 3.1, 0.9, 1.5])]
    if kind == "events_table":
        rows = []
        for ev in spec["events"]:
            name, desc, ref, who = ev
            if not applies(who, program):
                continue
            rows.append([f"`{name}`", desc, ref])
        return [("table", ["event_type", "What the date is", "Reference"], rows, [2.4, 4.6, 2.0])]
    if kind == "appendix_fields":
        out = []
        order = {f["file"]: int(f["order"]) for f in spec["files"]}
        by_file = {}
        for fld in spec["fields"]:
            if fld[c] == "-":
                continue
            by_file.setdefault(fld["file"], []).append(fld)
        for fname in sorted(by_file, key=lambda k: order[k]):
            out.append(("h2", f"`{fname}`"))
            rows = []
            for fld in by_file[fname]:
                note = fld["law_note"] if program == "law" else fld["ug_note"]
                desc = fld["description"] + (f" {note}" if note else "")
                rows.append([f"`{fld['field']}`", fld["type"], fld[c], tier_label(fld["tier"]), desc, values_for(fld, program)])
            out.append(("table", ["Field", "Type", "Req", "Tier", "Description", "Values or format"], rows, [1.75, 0.6, 0.4, 0.4, 3.85, 2.0]))
        return out
    raise ValueError(f"unknown special block {kind}")


# ----------------------------------------------------------------------------
# Markdown renderer
# ----------------------------------------------------------------------------
def esc_cell(t):
    return t.replace("|", "\\|").replace("\n", " ")


def render_md(ir):
    out = []
    for item in ir:
        k = item[0]
        if k == "title":
            out.append(f"# {item[1]}\n")
        elif k == "kv":
            for a, b in item[1]:
                out.append(f"**{a}:** {b}  ")
            out.append("")
        elif k == "h1":
            out.append(f"\n## {item[1]}\n")
        elif k == "h2":
            out.append(f"\n### {item[1]}\n")
        elif k == "p":
            out.append(item[1] + "\n")
        elif k == "bullets":
            out.extend(f"- {t}" for t in item[1])
            out.append("")
        elif k == "checklist":
            out.extend(f"- [ ] {t}" for t in item[1])
            out.append("")
        elif k == "table":
            cols, rows = item[1], item[2]
            out.append("| " + " | ".join(cols) + " |")
            out.append("|" + "|".join("---" for _ in cols) + "|")
            for r in rows:
                out.append("| " + " | ".join(esc_cell(x) for x in r) + " |")
            out.append("")
    return "\n".join(out)


# ----------------------------------------------------------------------------
# DOCX renderer
# ----------------------------------------------------------------------------
TOKEN = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")


def add_runs(par, text, size=None, bold=False, color=None, italic=False):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = par.add_run(part[2:-2]); r.bold = True
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
            if size:
                r.font.size = Pt(size - 0.5)
            else:
                r.font.size = Pt(9.5)
            if bold:
                r.bold = True
            if color:
                r.font.color.rgb = RGBColor.from_string(color)
            continue
        else:
            r = par.add_run(part)
            if bold:
                r.bold = True
        if italic:
            r.italic = True
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), LINE)
        borders.append(el)
    tblPr.append(borders)
    mar = OxmlElement("w:tblCellMar")
    for edge, w in (("top", 40), ("left", 80), ("bottom", 40), ("right", 80)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(w))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblPr.append(mar)


TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
               "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription"]


def order_tblpr(table):
    """Put tblPr children in schema order (Word is strict about it)."""
    tblPr = table._tbl.tblPr
    kids = list(tblPr)
    for k in kids:
        tblPr.remove(k)
    kids.sort(key=lambda e: TBLPR_ORDER.index(e.tag.split("}")[1]) if e.tag.split("}")[1] in TBLPR_ORDER else 99)
    for k in kids:
        tblPr.append(k)


def fix_layout(table, widths):
    """Fixed layout with explicit grid widths so Word and LibreOffice both honor them."""
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(el)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    for el in tblPr.findall(qn("w:tblW")):
        tblPr.remove(el)
    w = OxmlElement("w:tblW"); w.set(qn("w:w"), str(int(sum(widths) * 1440))); w.set(qn("w:type"), "dxa"); tblPr.append(w)
    for i, wd in enumerate(widths):
        table.columns[i].width = Inches(wd)


def row_flags(row, header=False):
    trPr = row._tr.get_or_add_trPr()
    cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); trPr.append(cs)
    if header:
        h = OxmlElement("w:tblHeader"); h.set(qn("w:val"), "true"); trPr.append(h)


def add_table(doc, cols, rows, widths, avail, font=9):
    total = float(sum(widths)) if widths else float(len(cols))
    widths = [w * avail / total for w in (widths or [1] * len(cols))]
    t = doc.add_table(rows=1, cols=len(cols))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    set_table_borders(t)
    fix_layout(t, widths)
    hdr = t.rows[0]
    row_flags(hdr, header=True)
    for i, c in enumerate(cols):
        cell = hdr.cells[i]
        cell.width = Inches(widths[i])
        shade(cell, NAVY)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        add_runs(p, c, size=font, bold=True, color="FFFFFF")
    for ri, r in enumerate(rows):
        row = t.add_row()
        row_flags(row)
        for i, txt in enumerate(r):
            cell = row.cells[i]
            cell.width = Inches(widths[i])
            if ri % 2 == 1:
                shade(cell, GREY)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            add_runs(p, txt, size=font)
    order_tblpr(t)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_field(par, instr):
    for kind, text in (("begin", None), (None, instr), ("end", None)):
        run = par.add_run()
        run.font.size = Pt(8)
        if kind:
            fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), kind); run._r.append(fc)
        else:
            it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = text; run._r.append(it)


def setup_styles(doc):
    st = doc.styles
    n = st["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(10.5)
    n._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    n.paragraph_format.space_after = Pt(6)
    n.paragraph_format.line_spacing = 1.08
    for name, size, before, after in (("Heading 1", 14, 14, 6), ("Heading 2", 11.5, 10, 4), ("Title", 20, 0, 4)):
        s = st[name]; s.font.name = "Calibri"; s.font.size = Pt(size); s.font.bold = True
        s.font.color.rgb = RGBColor.from_string(NAVY)
        s._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        s._element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); s._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        s.paragraph_format.space_before = Pt(before); s.paragraph_format.space_after = Pt(after)
        s.paragraph_format.keep_with_next = True
    st["List Bullet"].font.name = "Calibri"; st["List Bullet"].font.size = Pt(10.5)
    st["List Bullet"].paragraph_format.space_after = Pt(3)


def footer(section, label):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Frankel  |  {label}  |  Page "); r.font.size = Pt(8)
    add_field(p, "PAGE")
    r = p.add_run(" of "); r.font.size = Pt(8)
    add_field(p, "NUMPAGES")


def render_docx(ir, path, label):
    doc = Document()
    setup_styles(doc)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.top_margin = sec.bottom_margin = Inches(0.9)
    footer(sec, label)
    avail = 6.5
    for item in ir:
        k = item[0]
        if k == "title":
            p = doc.add_paragraph(style="Title"); add_runs(p, item[1])
        elif k == "kv":
            t = doc.add_table(rows=0, cols=2); t.autofit = False
            fix_layout(t, [1.7, 4.8])
            for a, b in item[1]:
                row = t.add_row()
                row.cells[0].width = Inches(1.7); row.cells[1].width = Inches(4.8)
                pa = row.cells[0].paragraphs[0]; pa.paragraph_format.space_after = Pt(1); add_runs(pa, a, bold=True, size=10)
                pb = row.cells[1].paragraphs[0]; pb.paragraph_format.space_after = Pt(1); add_runs(pb, b, size=10)
            order_tblpr(t)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
        elif k == "h1":
            p = doc.add_heading(level=1); add_runs(p, item[1], color=NAVY, bold=True, size=14)
        elif k == "h2":
            p = doc.add_heading(level=2); add_runs(p, item[1].replace("`", ""), color=NAVY, bold=True, size=11.5)
        elif k == "p":
            p = doc.add_paragraph(); add_runs(p, item[1])
        elif k == "bullets":
            for t in item[1]:
                p = doc.add_paragraph(style="List Bullet"); add_runs(p, t)
        elif k == "checklist":
            for t in item[1]:
                p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.3)
                p.paragraph_format.space_after = Pt(2)
                r = p.add_run("\u2610  "); r.font.name = "Segoe UI Symbol"
                add_runs(p, t)
        elif k == "table":
            font = 8.5 if avail > 7 else 9
            add_table(doc, item[1], item[2], item[3], avail, font=font)
        elif k == "landscape":
            new = doc.add_section(WD_SECTION.NEW_PAGE)
            new.orientation = WD_ORIENT.LANDSCAPE
            new.page_width, new.page_height = Inches(11), Inches(8.5)
            new.left_margin = new.right_margin = Inches(0.75)
            new.top_margin = new.bottom_margin = Inches(0.8)
            footer(new, label)
            avail = 9.0
    for z in doc.settings.element.findall(qn("w:zoom")):
        z.set(qn("w:percent"), "100")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


# ----------------------------------------------------------------------------
# Excel template and dictionary
# ----------------------------------------------------------------------------
def render_xlsx(spec, program, ctx, path):
    from openpyxl import Workbook
    from openpyxl.comments import Comment
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    c = col(program)
    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    lines = [
        (f"{ctx['institution']}: data request template (v3), {ctx['program_label']}", True),
        ("", False),
        ("One worksheet per file in the request. Fill in rows from row 8 down. Do not rename the worksheets or the header row.", False),
        ("Row 1 = field name. Row 2 = type. Row 3 = required (Y = send, C = send under the stated condition, N = optional). Row 4 = tier (1, 2, or A = optional add-on).", False),
        ("Row 5 = allowed values or format. Hover over a field name for its description. Rows 6 and 7 are left blank for your notes.", False),
        ("Missing is never zero: leave unknown values blank. Send dates as YYYY-MM-DD. Use the hashed student key in every file.", False),
        ("No names, emails, phone numbers, street addresses, full dates of birth, Social Security numbers or free-text notes. ZIP5 goes only in `zip_key`.", False),
        ("Worksheets Institutional_Reference and Scoping_Inputs are for you to fill in; Codes lists the allowed values; Dictionary is the full field specification.", False),
        ("Send your own data dictionary with every code value you use. We map your values to ours.", False),
    ]
    for i, (t, b) in enumerate(lines, start=1):
        ws.cell(row=i, column=1, value=t.replace("`", "")).font = Font(bold=b, size=13 if b else 11)
    ws.column_dimensions["A"].width = 150

    hdr_fill = {"Y": PatternFill("solid", fgColor=NAVY), "C": PatternFill("solid", fgColor="2E75B6"), "N": PatternFill("solid", fgColor="7F7F7F")}
    codes = []
    order = {f["file"]: int(f["order"]) for f in spec["files"]}
    by_file = {}
    for fld in spec["fields"]:
        if fld[c] == "-":
            continue
        by_file.setdefault(fld["file"], []).append(fld)
    for fname in sorted(by_file, key=lambda k: order[k]):
        sh = wb.create_sheet(fname[:31])
        for j, fld in enumerate(by_file[fname], start=1):
            colL = get_column_letter(j)
            cell = sh.cell(row=1, column=j, value=fld["field"])
            cell.font = Font(bold=True, color="FFFFFF"); cell.fill = hdr_fill.get(fld[c], hdr_fill["N"])
            note = fld["law_note"] if program == "law" else fld["ug_note"]
            cell.comment = Comment((fld["description"] + (" " + note if note else "")).strip(), "Frankel")
            sh.cell(row=2, column=j, value=fld["type"])
            sh.cell(row=3, column=j, value=fld[c])
            sh.cell(row=4, column=j, value=tier_label(fld["tier"]))
            sh.cell(row=5, column=j, value=values_for(fld, program))
            for r in (2, 3, 4, 5):
                sh.cell(row=r, column=j).alignment = Alignment(wrap_text=True, vertical="top")
                sh.cell(row=r, column=j).font = Font(italic=True, color="595959", size=9)
            sh.column_dimensions[colL].width = max(14, min(34, len(fld["field"]) + 4))
            vv = values_for(fld, program)
            if vv:
                codes.append((fname, fld["field"], values_for(fld, program)))
            # permissive validation (warning only) for booleans and short code lists
            opts = None
            if fld["type"] == "bool":
                opts = "true,false"
            elif vv and ":" not in vv and not vv.startswith(("e.g", "Free", "Integer", "JSON", "Whole", "Percent", "Stable", "Blank", "Four", "Never", "Counts", "Do not", "Needed", "Used", "Required", "On or", "Keep", "Default", "Exclude", "Supports", "Reconciles")) and ";" in vv:
                items = [x.strip() for x in vv.split(";")]
                cand = ",".join(items)
                if "," not in "".join(items) and len(cand) < 250:
                    opts = cand
            if opts:
                dv = DataValidation(type="list", formula1=f'"{opts}"', allow_blank=True, showErrorMessage=True, errorStyle="warning")
                sh.add_data_validation(dv)
                dv.add(f"{colL}8:{colL}2000")
        sh.freeze_panes = "A8"
        sh.row_dimensions[5].height = 42

    # Institutional reference
    ref = wb.create_sheet("Institutional_Reference")
    head = ["Group", "Figure", "Source", "Note"] + [f"Cohort year {i}" for i in range(1, 6)]
    for j, h in enumerate(head, start=1):
        cell = ref.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    r = 2
    for it in spec["reference_items"]:
        if it["program"] != program:
            continue
        for j, k in enumerate(("group", "item", "source_ref", "note"), start=1):
            ref.cell(row=r, column=j, value=it[k]).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    for letter, w in zip("ABCDEFGHI", (14, 62, 12, 40, 14, 14, 14, 14, 14)):
        ref.column_dimensions[letter].width = w
    ref.freeze_panes = "C2"

    # Scoping inputs
    sc = wb.create_sheet("Scoping_Inputs")
    for j, h in enumerate(["Who supplies it", "Input", "Description", "Your answer"], start=1):
        cell = sc.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    r = 2
    for it in spec["scoping"]:
        if it[c] != "Y":
            continue
        for j, k in enumerate(("group", "input", "description"), start=1):
            val = it[k] + (it.get("law_extra", "") if (k == "description" and program == "law") else "")
            sc.cell(row=r, column=j, value=val).alignment = Alignment(wrap_text=True, vertical="top")
        r += 1
    for letter, w in zip("ABCD", (30, 34, 80, 40)):
        sc.column_dimensions[letter].width = w

    # Components and events
    cp = wb.create_sheet("Components")
    for j, h in enumerate(["component", "category", "note"], start=1):
        cell = cp.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    r = 2
    for it in spec["components"]:
        if it[c] == "-":
            continue
        cp.cell(row=r, column=1, value=it["component"]); cp.cell(row=r, column=2, value=it["category"]); cp.cell(row=r, column=3, value=it["note"])
        r += 1
    cp.column_dimensions["A"].width = 24; cp.column_dimensions["B"].width = 14; cp.column_dimensions["C"].width = 90
    ev = wb.create_sheet("Event_Types")
    for j, h in enumerate(["event_type", "What the date is", "Reference"], start=1):
        cell = ev.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    r = 2
    for name, desc, rf, who in spec["events"]:
        if applies(who, program):
            ev.cell(row=r, column=1, value=name); ev.cell(row=r, column=2, value=desc); ev.cell(row=r, column=3, value=rf)
            r += 1
    ev.column_dimensions["A"].width = 28; ev.column_dimensions["B"].width = 90; ev.column_dimensions["C"].width = 26

    # Codes and dictionary
    cd = wb.create_sheet("Codes")
    for j, h in enumerate(["file", "field", "allowed values or format"], start=1):
        cell = cd.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    for i, (a, b, v) in enumerate(codes, start=2):
        cd.cell(row=i, column=1, value=a); cd.cell(row=i, column=2, value=b); cd.cell(row=i, column=3, value=v)
    cd.column_dimensions["A"].width = 18; cd.column_dimensions["B"].width = 30; cd.column_dimensions["C"].width = 100
    dc = wb.create_sheet("Dictionary")
    for j, h in enumerate(["file", "field", "type", "required", "tier", "description", "values or format"], start=1):
        cell = dc.cell(row=1, column=j, value=h); cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor=NAVY)
    r = 2
    for fname in sorted(by_file, key=lambda k: order[k]):
        for fld in by_file[fname]:
            note = fld["law_note"] if program == "law" else fld["ug_note"]
            vals = [fname, fld["field"], fld["type"], fld[c], tier_label(fld["tier"]), (fld["description"] + (" " + note if note else "")).strip(), values_for(fld, program)]
            for j, v in enumerate(vals, start=1):
                dc.cell(row=r, column=j, value=v).alignment = Alignment(wrap_text=True, vertical="top")
            r += 1
    for letter, w in zip("ABCDEFG", (18, 30, 9, 9, 6, 90, 50)):
        dc.column_dimensions[letter].width = w
    dc.freeze_panes = "C2"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def render_dictionary(spec, program, path):
    c = col(program)
    order = {f["file"]: int(f["order"]) for f in spec["files"]}
    rows = [f for f in spec["fields"] if f[c] != "-"]
    rows.sort(key=lambda f: order[f["file"]])
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["table", "field", "type", "tier", "required", "description", "allowed_values_or_notes", "ref"])
        for f in rows:
            note = f["law_note"] if program == "law" else f["ug_note"]
            w.writerow([f["file"], f["field"], f["type"], tier_label(f["tier"]), f[c], (f["description"] + (" " + note if note else "")).strip(), values_for(f, program), f["ref"]])


# ----------------------------------------------------------------------------
def build(program, institution, contact, date, due, out):
    spec = load_spec()
    prof = spec["profiles"][program]
    ctx = {
        "institution": institution,
        "program_label": prof["label"],
        "audience": prof["audience"],
        "contact": contact,
        "date": date,
        "due_date": due,
    }
    ir = build_ir(spec, program, ctx)
    base = f"Data_Request_v3_{prof['short']}_{slug(institution)}"
    out.mkdir(parents=True, exist_ok=True)
    render_docx(ir, out / f"{base}.docx", f"{institution} data request v3 ({prof['short']})")
    (out / f"{base}.md").write_text(render_md(ir), encoding="utf-8")
    render_xlsx(spec, program, ctx, out / f"Data_Request_Template_{prof['short']}.xlsx")
    render_dictionary(spec, program, out / f"data_dictionary_v3_{prof['short']}.csv")
    return base


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--program", choices=PROGRAMS + ("all",), default="all")
    ap.add_argument("--institution", default="[Institution]")
    ap.add_argument("--contact", default="[Frankel contact]")
    ap.add_argument("--date", default="[Date]")
    ap.add_argument("--due", default="[Date]")
    ap.add_argument("--out", default=str(HERE / "output"))
    a = ap.parse_args()
    progs = PROGRAMS if a.program == "all" else (a.program,)
    for p in progs:
        base = build(p, a.institution, a.contact, a.date, a.due, Path(a.out))
        print("wrote", base)


if __name__ == "__main__":
    sys.exit(main())
