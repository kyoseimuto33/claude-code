"""Dump a Shoppal monthly EC report PDF (管理画面の月次レポート) as compact text, plus page-1 chart image.

Usage: python3 extract_report_pdf.py <report.pdf> [out_dir]
Prints each page with short lines joined by " | " so tables read as rows. Page 1 is also saved as
<out_dir>/<name>-p1.png: read it to get session / impression / position trends from the charts.
"""
import os, re, sys
import pymupdf

pdf = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(pdf))
doc = pymupdf.open(pdf)
doc[0].get_pixmap(dpi=110).save(os.path.join(out, os.path.splitext(os.path.basename(pdf))[0] + '-p1.png'))
text = '\n'.join(f'--- page {i + 1}\n' + p.get_text() for i, p in enumerate(doc))
print(re.sub(r'\n(?=[^\n]{0,25}\n)', ' | ', text))
