"""Test 10: rendering (spec section 11). Convert Summary to PDF with LibreOffice and save it to output/phase2/ for
visual review. Not asserted beyond the file being written; Jason reviews the render (Phase 4 acceptance)."""
import os
import shutil

from conftest import PHASE2
from sw import lo


def test_render_summary_pdf(main_wb, lo_profile):
    pdf = lo.render_summary_pdf(main_wb["path"], os.path.join(PHASE2, "render"), profile=lo_profile)
    dst = os.path.join(PHASE2, "Summary_render.pdf")
    shutil.copyfile(pdf, dst)
    assert os.path.getsize(dst) > 10_000
