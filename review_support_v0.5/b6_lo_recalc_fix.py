"""Same check, with a LibreOffice profile that sets OOXMLRecalcMode = 0 (always recalculate)."""
import subprocess, sys, os, xlsxwriter, openpyxl
d = sys.argv[1]; prof = sys.argv[2]; src = os.path.join(d, "t2.xlsx"); out = os.path.join(d, "out2")
wb = xlsxwriter.Workbook(src); ws = wb.add_worksheet()
ws.write_formula("A1", "=1+1", None, 5); ws.write_formula("A2", "=NORMSDIST(0)", None, 9); wb.close()
subprocess.run(["soffice", f"-env:UserInstallation=file://{prof}", "--headless", "--convert-to", "xlsx", "--outdir", out, src],
               check=True, capture_output=True, timeout=120)
r = openpyxl.load_workbook(os.path.join(out, "t2.xlsx"), data_only=True).active
print("A1:", r["A1"].value, "| A2:", r["A2"].value)
