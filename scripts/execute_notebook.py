"""Execute and save the complete notebook; errors abort without writing broken outputs."""
from pathlib import Path
import asyncio
import sys
if sys.platform=='win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import nbformat
from nbclient import NotebookClient
root=Path(__file__).resolve().parents[1]
path=root/'notebooks/Customer_Segmentation_and_Churn_Risk.ipynb'
nb=nbformat.read(path,as_version=4)
nbformat.validate(nb)
NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
nbformat.write(nb,path)
print(f'Executed {sum(c.cell_type=="code" for c in nb.cells)} code cells successfully: {path.name}')
