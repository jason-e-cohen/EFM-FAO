"""Does LibreOffice headless recalculate an XlsxWriter file, or pass the cached values through?
Writes =1+1 with a deliberately wrong cached value of 5, converts, reads back."""
import subprocess, sys, os, xlsxwriter, openpyxl
d = sys.argv[1]; src = os.path.join(d, "t.xlsx"); out = os.path.join(d, "out")
wb = xlsxwriter.Workbook(src); ws = wb.add_worksheet()
ws.write_formula("A1", "=1+1", None, 5); ws.write_formula("A2", "=NORMSDIST(0)", None, 9); wb.close()
subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", out, src], check=True, capture_output=True, timeout=120)
r = openpyxl.load_workbook(os.path.join(out, "t.xlsx"), data_only=True).active
print("A1 (=1+1, cached 5):", r["A1"].value, "| A2 (=NORMSDIST(0), cached 9):", r["A2"].value)
