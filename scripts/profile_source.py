"""Read source references locally without republishing them."""
from pathlib import Path
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
target=root/'tmp'/'reference_extract.txt'; target.parent.mkdir(exist_ok=True)
target.write_text('\n'.join(p.extract_text() for p in PdfReader(root/'EdVyro Internship Task Source Library.pdf').pages),encoding='utf-8')
print(target)
