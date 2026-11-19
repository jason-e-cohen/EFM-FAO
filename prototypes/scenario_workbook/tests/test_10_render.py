"""Test 10: rendering (spec section 11; Phase 4). Convert Summary to PDF with LibreOffice and save it to
output/phase4/Summary_render.pdf for visual review. Not asserted beyond the file being written; Jason reviews the render
(Phase 4 acceptance). The render carries the two Review_Phase2_Build.md cosmetic fixes: parent names wrap within their
column, and "under 5%" / "over 95%" are right-aligned with the other percentages."""
import os
import shutil

from conftest import ROOT
from sw import lo

PHASE4 = os.path.join(ROOT, "output", "phase4")


def test_render_summary_pdf(main_wb, lo_profile):
    os.makedirs(PHASE4, exist_ok=True)
    pdf = lo.render_summary_pdf(main_wb["path"], os.path.join(PHASE4, "render"), profile=lo_profile)
    dst = os.path.join(PHASE4, "Summary_render.pdf")
    shutil.copyfile(pdf, dst)
    assert os.path.getsize(dst) > 10_000
