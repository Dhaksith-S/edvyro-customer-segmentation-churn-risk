from pathlib import Path
import nbformat

def test_notebook_parses_and_all_cells_executed():
    root=Path(__file__).resolve().parents[1]
    nb=nbformat.read(root/'notebooks/Customer_Segmentation_and_Churn_Risk.ipynb',as_version=4)
    nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    assert len(code)>=14 and all(c.execution_count for c in code)
    assert all(o.output_type!='error' for c in code for o in c.outputs)
    combined='\n'.join(str(o.get('text','')) for c in code for o in c.outputs)
    assert 'Traceback' not in combined and 'Warning:' not in combined
    assert 'Export checks passed for 15 customers' in combined
    assert 'Source: 15 customers, 11 columns' in combined
    assert sum('image/png' in o.get('data',{}) for c in code for o in c.outputs)>=11
