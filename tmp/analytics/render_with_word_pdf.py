"""Use the packaged renderer with the PDF exported by Microsoft Word.

The bundled LibreOffice converter is unavailable on this Windows host.
Only the conversion stage is replaced; its PNG rasterization stays intact.
"""
from pathlib import Path
import importlib.util
import tempfile
import sys

docx,pdf,out=sys.argv[1:4]
root=Path(__file__).resolve().parents[2]
temporary=root/'tmp/analytics/render_tmp'
temporary.mkdir(exist_ok=True)
tempfile.tempdir=str(temporary)
source=Path(r'C:/Users/PrestamoIE/.codex/plugins/cache/openai-primary-runtime/documents/26.1011.11113/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('packaged_render_docx',source)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.convert_to_pdf=lambda *args,**kwargs:(str(Path(pdf).resolve()),'PDF exported by Microsoft Word; original DOCX opened read-only.')
sys.argv=[str(source),docx,'--output_dir',out,'--dpi','120']
module.main()
