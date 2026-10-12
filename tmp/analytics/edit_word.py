from pathlib import Path
from copy import deepcopy
from hashlib import sha256
from lxml import etree
from zipfile import ZipFile
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'tmp/analytics/Investigacion_antes.docx'
OUTPUT = ROOT / 'tmp/analytics/Investigacion_actualizada.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}

CONTENT = [
    ('', 'Data Analytics utilizó únicamente FOOD_INSPECTIONS_CLEAN. Las siete consultas se ejecutaron en Oracle con GRUPO2 y sus resultados fueron verificados.'),
    ('Pregunta de análisis: ', '¿Qué características de las inspecciones están asociadas con una mayor proporción de resultados Fail?'),
    ('Consultas e indicadores: ', 'El script sql/04analytics.sql incluye dos verificaciones y cinco análisis: resultado general, RISK, INSPECTION_TYPE, FACILITY_TYPE y año. Se calcularon total de registros, cantidad de Fail y porcentaje de Fail sobre todos los registros de cada grupo. Para los tipos de inspección y establecimiento se exigió un mínimo de 1.000 registros.'),
    ('Hallazgos: ', '61.038 de 316.961 registros tienen RESULTS = \'Fail\', equivalente al 19,26 % del total de registros. En RISK, Risk 3 (Low) presentó 20,89 % de Fail, Risk 1 (High) 19,14 % y Risk 2 (Medium) 19,05 %.'),
    ('', 'Entre las categorías con al menos 1.000 registros, COMPLAINT presentó la mayor proporción por tipo de inspección (33,23 %), seguida de LICENSE (29,75 %). Por establecimiento destacaron LIQUOR (31,51 %) y MOBILE FOOD PREPARER (25,04 %); RESTAURANT registró 18,64 %.'),
    ('Evolución temporal: ', 'El porcentaje fluctuó entre 24,92 % en 2010 y 15,99 % en 2013; en 2025 fue 17,66 %. En 2026 fue 18,10 %, pero el año solo cubre hasta el 9 de octubre y no debe compararse como si tuviera la misma cobertura que los años completos.'),
    ('Interpretación y limitaciones: ', 'Son asociaciones descriptivas y no demuestran que el riesgo u otra característica cause Fail. Una fila representa una inspección; un establecimiento puede aparecer varias veces. El denominador incluye las siete categorías de RESULTS, no únicamente Pass y Fail. NON-INSPECTION conserva 5.738 registros y 11 Fail; su significado ambiguo impide usarla para conclusiones sobre inspecciones efectivas. RISK conserva 87 All y 87 NULL, grupos pequeños que requieren cautela. No se eliminaron ni reclasificaron registros.'),
]

with ZipFile(SOURCE) as zin:
    original = zin.read('word/document.xml')
    tree = etree.fromstring(original)
    body = tree.find('w:body', NS)
    def text_of(node):
        return ''.join(node.itertext()) if False else ''.join(node.xpath('.//w:t/text()', namespaces=NS))
    start = next(i for i,n in enumerate(body) if text_of(n).strip() == '3.3 Data Analytics')
    end = next(i for i,n in enumerate(body) if text_of(n).strip() == '3.4 Data Science')
    assert end - start - 1 == 5
    before_prefix = [etree.tostring(n, method='c14n') for n in list(body)[:start+1]]
    before_suffix = [etree.tostring(n, method='c14n') for n in list(body)[end:]]
    old_text = [text_of(n) for n in list(body)[start+1:end]]
    template = deepcopy(body[start+1])
    for node in list(body)[start+1:end]:
        body.remove(node)
    for offset,(label,text) in enumerate(CONTENT):
        p = deepcopy(template)
        for node in list(p):
            if node.tag != f'{{{W}}}pPr': p.remove(node)
        if label:
            p.find('w:pPr/w:ind',NS).set(f'{{{W}}}firstLine','0')
        for value,bold in [(label,True),(text,False)]:
            if not value: continue
            r=etree.SubElement(p,f'{{{W}}}r')
            if bold:
                rp=etree.SubElement(r,f'{{{W}}}rPr')
                etree.SubElement(rp,f'{{{W}}}b')
            t=etree.SubElement(r,f'{{{W}}}t')
            t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')
            t.text=value
        body.insert(start+1+offset,p)
    new_end=start+1+len(CONTENT)
    assert before_prefix==[etree.tostring(n,method='c14n') for n in list(body)[:start+1]]
    assert before_suffix==[etree.tostring(n,method='c14n') for n in list(body)[new_end:]]
    updated=etree.tostring(tree,encoding='UTF-8',xml_declaration=True,standalone=True)
    with ZipFile(OUTPUT,'w') as zout:
        for member in zin.infolist():
            zout.writestr(member,updated if member.filename=='word/document.xml' else zin.read(member.filename))

with ZipFile(SOURCE) as a,ZipFile(OUTPUT) as b:
    changed=[name for name in a.namelist() if a.read(name)!=b.read(name)]
    assert changed==['word/document.xml'],changed

report={
    'section':'3.3 Data Analytics',
    'replaced_paragraphs':5,
    'final_paragraphs':7,
    'net_new_paragraphs':2,
    'tables_added':0,
    'tables_modified':0,
    'replaced_content':old_text,
    'new_content':[a+b for a,b in CONTENT],
    'unmodified_outside_section':True,
    'changed_zip_members':changed,
    'source_sha256':sha256(SOURCE.read_bytes()).hexdigest(),
    'words':sum(len((a+b).split()) for a,b in CONTENT),
}
(ROOT/'tmp/analytics/word_change_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['new_content','replaced_content']},ensure_ascii=False))
