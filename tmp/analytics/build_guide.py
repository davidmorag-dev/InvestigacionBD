from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics import renderPDF
import json

ROOT=Path(__file__).resolve().parents[2]
DATA=json.loads((ROOT/'tmp/analytics/results.json').read_text(encoding='utf-8'))
OUTPUT=ROOT/'tmp/analytics/Guia_actualizada.pdf'
for name,path in [
    ('Segoe','segoeui.ttf'),('Segoe-Bold','segoeuib.ttf'),
    ('Segoe-Light','segoeuil.ttf'),('Segoe-Italic','segoeuii.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/path)))
pdfmetrics.registerFontFamily('Segoe',normal='Segoe',bold='Segoe-Bold',italic='Segoe-Italic',boldItalic='Segoe-Bold')
W,H=landscape(A4)
M=42
NAVY=HexColor('#203448')
TEXT=HexColor('#26333D')
MUTED=HexColor('#596671')
TEAL=HexColor('#267A7B')
FAIL=HexColor('#B65535')
LINE=HexColor('#D8DFE2')
LIGHT=HexColor('#E9EFF0')
WHITE=HexColor('#FFFFFF')
c=canvas.Canvas(str(OUTPUT),pagesize=(W,H),pageCompression=1)
c.setTitle('Guía visual para la exposición del caso práctico')
c.setAuthor('Grupo 2 · Bases de Datos II')
c.setSubject('Data Engineering y asociaciones descriptivas de Fail en FOOD_INSPECTIONS_CLEAN')
layout=[]

def txt(x,y,text,size=12,font='Segoe',color=TEXT,align='left'):
    c.setFillColor(color);c.setFont(font,size)
    if align=='right':c.drawRightString(x,H-y-size*.82,text)
    elif align=='center':c.drawCentredString(x,H-y-size*.82,text)
    else:c.drawString(x,H-y-size*.82,text)

def para(x,y,text,width,size=12,leading=None,color=TEXT,bold=False):
    style=ParagraphStyle('p',fontName='Segoe-Bold' if bold else 'Segoe',fontSize=size,
                         leading=leading or size*1.35,textColor=color,spaceAfter=0)
    p=Paragraph(text,style)
    _,height=p.wrap(width,1000)
    assert x>=M-1 and x+width<=W-M+1,(x,width)
    assert y+height<=551,(text,y,height)
    p.drawOn(c,x,H-y-height)
    layout.append({'page':page_no,'y':y,'bottom':y+height,'text':text})
    return height

def line(x1,y1,x2,y2,color=LINE,width=.65):
    c.setStrokeColor(color);c.setLineWidth(width);c.line(x1,H-y1,x2,H-y2)

def rect(x,y,w,h,color):
    c.setFillColor(color);c.rect(x,H-y-h,w,h,fill=1,stroke=0)

def num(n):return f'{int(n):,}'.replace(',','.')
def pct(s):return f'{float(str(s).replace(",",".")):.2f}'.replace('.',',')+' %'
def val(s):return float(str(s).replace(',','.'))
def row(key,label):return next(r for r in DATA[key] if r[key]==label)

def header(page,section,title,subtitle):
    global page_no
    page_no=page
    rect(0,0,W,H,WHITE)
    txt(M,23,'CHICAGO FOOD INSPECTIONS  /  BASES DE DATOS II',9.3,'Segoe-Bold',MUTED)
    txt(W-M,23,f'{page:02d} / 04',10.5,'Segoe-Bold',NAVY,'right')
    line(M,45,W-M,45)
    txt(M,64,section.upper(),10.2,'Segoe-Bold',TEAL)
    txt(M,84,title,31,'Segoe-Bold',NAVY)
    para(M,129,subtitle,W-2*M,12.3,16,MUTED)

def footer(source):
    line(M,557,W-M,557)
    txt(M,570,source,8.8,color=MUTED)
    txt(W-M,570,'GUÍA DE EXPOSICIÓN · 11/10/2026',8.8,'Segoe-Bold',MUTED,'right')
    c.showPage()

def metric(x,y,value,label,detail,width=220,color=NAVY,size=35):
    txt(x,y,value,size,'Segoe-Light',color)
    txt(x,y+43,label,12.5,'Segoe-Bold',TEXT)
    para(x,y+64,detail,width,10.8,14,MUTED)

def bars(x,y,width,rows,step=51,max_pct=40):
    for i,(label,r) in enumerate(rows):
        yy=y+i*step
        txt(x,yy,label,11.1,'Segoe-Bold',NAVY)
        txt(x+width,yy,pct(r['PORCENTAJE_FAIL']),15,'Segoe-Bold',FAIL,'right')
        txt(x,yy+18,f"Total {num(r['TOTAL_INSPECCIONES'])}  ·  Fail {num(r['TOTAL_FAIL'])}",10.4,color=MUTED)
        rect(x,yy+35,width,5,LIGHT)
        rect(x,yy+35,width*val(r['PORCENTAJE_FAIL'])/max_pct,5,TEAL)

# 1. Keep the preparation evidence and show the completed analytical handoff.
header(1,'Datos y recorrido','Del CSV a los indicadores',
       'Una fila representa una inspección. Un mismo establecimiento puede aparecer varias veces.')
metric(M,169,'316.961','registros conservados','RAW y CLEAN mantienen el mismo volumen.',225)
metric(308,169,'17','columnas en CLEAN','RESULTS, RISK, tipos y fecha permiten el análisis.',220)
metric(566,169,'7','consultas de Analytics','Dos verificaciones y cinco análisis descriptivos.',233)
positions=[M+6,221,398,575,752]
stages=[('CSV','Conservado'),('RAW','Cargada'),('CLEAN','Verificada'),('Analytics','Ejecutada'),('Science','Pendiente')]
line(positions[0],302,positions[-1],302,LINE,1.3)
for x,(name,status) in zip(positions,stages):
    c.setFillColor(TEAL if name!='Science' else WHITE)
    c.setStrokeColor(TEAL if name!='Science' else MUTED)
    c.setLineWidth(1.3);c.circle(x,H-302,4.2,stroke=1,fill=1)
    txt(x,317,name,13,'Segoe-Bold',NAVY,'center')
    txt(x,337,status,10.7,color=TEAL if name!='Science' else MUTED,align='center')
txt(M,371,'Qué dejó Data Engineering',17,'Segoe-Bold',NAVY)
columns=[(M,223),(308,220),(566,233)]
for x,width in columns:line(x,401,x+width,401)
txt(M,412,'Categorías normalizadas',11.6,'Segoe-Bold',NAVY)
para(M,436,'FACILITY_TYPE: <b>527 → 473</b><br/>INSPECTION_TYPE: <b>110 → 98</b><br/>UPPER(TRIM()) sin eliminar filas.',223,11.1,16)
txt(308,412,'Textos extensos conservados',11.6,'Segoe-Bold',NAVY)
para(308,436,'VIOLATIONS se mantiene como CLOB.<br/><b>12.706</b> caracteres máximos.<br/><b>4.469</b> textos superan 4.000.',220,11.1,16)
txt(566,412,'Coordenadas convertidas',11.6,'Segoe-Bold',NAVY)
para(566,436,'LATITUDE y LONGITUDE: NUMBER.<br/><b>1.061 NULL</b> por columna.<br/><b>0</b> valores fuera de rango.',233,11.1,16)
para(M,514,'RAW permanece intacta. Los 104 grupos candidatos a duplicados se conservaron; no son duplicados exactos confirmados.',W-2*M,10.7,14,MUTED)
footer('Preparación: 03cleaning.sql y evidencias/limpieza/.')

# 2. Overall outcome and risk share a precise denominator.
header(2,'Resultado general y riesgo','Qué proporción tiene resultado Fail',
       'Pregunta: ¿qué características de las inspecciones están asociadas con una mayor proporción de resultados Fail?')
line(405,173,405,525)
txt(M,179,'19,26 %',48,'Segoe-Light',FAIL)
txt(M,239,'61.038 de 316.961 registros',17,'Segoe-Bold',NAVY)
para(M,268,"tienen <b>RESULTS = 'Fail'</b>. El porcentaje se calcula sobre el total de registros.",335,12.3,17)
rect(M,325,335,12,LIGHT);rect(M,325,335*61038/316961,12,FAIL)
txt(M,348,'Fail 19,26 %',11,'Segoe-Bold',FAIL)
txt(M+335,348,'Otros resultados 80,74 %',11,color=MUTED,align='right')
para(M,389,'El resto incluye Pass, Pass w/ Conditions, Out of Business, No Entry, Not Ready y Business Not Located.',335,12,17)
para(M,472,'<b>Denominador:</b> las siete categorías de RESULTS. El indicador no se limita a los registros Pass y Fail.',335,11.5,16,MUTED)
txt(437,179,'Por categoría de RISK',17,'Segoe-Bold',NAVY)
bars(437,219,360,[(name,row('RISK',name)) for name in ['Risk 3 (Low)','Risk 1 (High)','Risk 2 (Medium)']],step=58,max_pct=30)
line(437,408,797,408)
txt(437,423,'También se conservaron',11.3,'Segoe-Bold',NAVY)
for j,name in enumerate(['All','SIN DATO']):
    r=row('RISK',name)
    label='NULL (sin dato)' if name=='SIN DATO' else name
    txt(437,447+j*20,f"{label}: {num(r['TOTAL_INSPECCIONES'])} registros · {num(r['TOTAL_FAIL'])} Fail",10.5,color=MUTED)
    txt(797,447+j*20,pct(r['PORCENTAJE_FAIL']),10.7,'Segoe-Bold',MUTED,'right')
para(437,494,'Grupos pequeños: sus porcentajes requieren cautela. Que Low supere a High no demuestra que el riesgo cause Fail.',360,11.5,15.5)
footer('Fuente: FOOD_INSPECTIONS_CLEAN · Consultas 1, 3 y 4 de 04analytics.sql.')

# 3. Selected comparisons display counts and a common percentage scale.
header(3,'Tipos de inspección y establecimiento','Dónde se observan porcentajes mayores',
       'Ejemplos seleccionados de categorías con al menos 1.000 registros. Las barras usan la misma escala de 0 a 40 %.')
line(420,175,420,497)
txt(M,177,'INSPECTION_TYPE',13,'Segoe-Bold',NAVY)
txt(451,177,'FACILITY_TYPE',13,'Segoe-Bold',NAVY)
type_names=['COMPLAINT','LICENSE','SUSPECTED FOOD POISONING','CANVASS','CANVASS RE-INSPECTION']
facility_names=['LIQUOR','MOBILE FOOD PREPARER','LONG TERM CARE','GROCERY STORE','RESTAURANT']
bars(M,212,348,[(name,row('INSPECTION_TYPE',name)) for name in type_names],step=53)
bars(451,212,348,[(name,row('FACILITY_TYPE',name)) for name in facility_names],step=53)
para(M,501,'<b>Lectura:</b> COMPLAINT (33,23 %) y LIQUOR (31,51 %) encabezan sus respectivas comparaciones entre categorías con al menos 1.000 registros. Son asociaciones descriptivas.',W-2*M,11.5,16)
footer('Fuente: FOOD_INSPECTIONS_CLEAN · Consultas 5 y 6 · Las salidas SQL incluyen todas las categorías que cumplen el mínimo.')

# 4. The time series ends in 2025; partial 2026 remains separate.
header(4,'Evolución temporal e interpretación','La proporción cambia entre años',
       'Serie anual de 2010 a 2025. 2026 se presenta por separado porque su cobertura es incompleta.')
plot_x,plot_y,plot_w,plot_h=M,182,463,215
d=Drawing(plot_w,plot_h)
lp=LinePlot();lp.x=34;lp.y=27;lp.width=plot_w-51;lp.height=plot_h-42
annual=[(int(r['ANO']),val(r['PORCENTAJE_FAIL'])) for r in DATA['ANO'] if int(r['ANO'])<2026]
lp.data=[annual];lp.joinedLines=1
lp.xValueAxis.valueMin=2010;lp.xValueAxis.valueMax=2025
lp.xValueAxis.valueSteps=[2010,2013,2016,2019,2022,2025]
lp.xValueAxis.labels.fontName='Segoe';lp.xValueAxis.labels.fontSize=10
lp.xValueAxis.labels.boxAnchor='n';lp.xValueAxis.labels.dy=-6
lp.xValueAxis.strokeColor=LINE;lp.xValueAxis.tickDown=3
lp.xValueAxis.labelTextFormat=lambda v:str(int(v))
lp.yValueAxis.valueMin=0;lp.yValueAxis.valueMax=30;lp.yValueAxis.valueSteps=[0,10,20,30]
lp.yValueAxis.labels.fontName='Segoe';lp.yValueAxis.labels.fontSize=10
lp.yValueAxis.labelTextFormat=lambda v:f'{int(v)} %'
lp.yValueAxis.strokeColor=LINE;lp.yValueAxis.visibleGrid=1;lp.yValueAxis.gridStrokeColor=LIGHT
lp.lines[0].strokeColor=TEAL;lp.lines[0].strokeWidth=2
lp.lines[0].symbol=makeMarker('FilledCircle');lp.lines[0].symbol.size=4.3
lp.lines[0].symbol.fillColor=TEAL;lp.lines[0].symbol.strokeColor=TEAL
d.add(lp);renderPDF.draw(d,c,plot_x,H-plot_y-plot_h)
txt(M+35,170,'% de registros con Fail',10.6,'Segoe-Bold',MUTED)
for x,year,rate,dy in [(plot_x+34,2010,24.92,-17),(plot_x+34+412*3/15,2013,15.99,13),(plot_x+34+412,2025,17.66,-18)]:
    yy=plot_y+plot_h-27-173*rate/30
    txt(x,yy+dy,pct(rate),10.8,'Segoe-Bold',TEAL,'center')
para(M,412,'El porcentaje fluctuó: <b>24,92 % en 2010</b>, <b>15,99 % en 2013</b> y <b>17,66 % en 2025</b>. No muestra una disminución continua.',463,11.6,16)
line(535,175,535,444)
r=row('ANO','2026')
txt(564,181,'2026 / COBERTURA PARCIAL',11.6,'Segoe-Bold',FAIL)
txt(564,213,pct(r['PORCENTAJE_FAIL']),37,'Segoe-Light',FAIL)
txt(564,263,f"{num(r['TOTAL_INSPECCIONES'])} registros · {num(r['TOTAL_FAIL'])} Fail",12.1,'Segoe-Bold',NAVY)
para(564,298,'Datos hasta el <b>9 de octubre de 2026</b>. No debe compararse como si tuviera la misma cobertura que los años completos.',235,12,17)
para(564,382,'El porcentaje de Fail describe los registros disponibles; no identifica la causa de las diferencias entre años.',235,11.4,16,MUTED)
line(M,458,W-M,458)
txt(M,473,'ALCANCE',10.4,'Segoe-Bold',TEAL)
para(M,493,'Son inspecciones, no establecimientos únicos. Los resultados expresan asociaciones descriptivas, sin afirmar causalidad.',229,10.9,14.5)
txt(309,473,'NON-INSPECTION',10.4,'Segoe-Bold',TEAL)
para(309,493,'5.738 registros y 11 Fail. Se conserva; su significado ambiguo impide usarla para concluir sobre inspecciones efectivas.',229,10.9,14.5)
txt(576,473,'MÍNIMO DE 1.000',10.4,'Segoe-Bold',TEAL)
para(576,493,'Se aplica solo a las salidas por tipo. Omite 3.879 registros por INSPECTION_TYPE y 11.823 por FACILITY_TYPE; CLEAN conserva todo.',223,10.9,14.5)
footer('Fuente: FOOD_INSPECTIONS_CLEAN · Consulta 7 · Resultados completos: evidencias/analytics/analytics_resultados.txt.')
c.save()
(ROOT/'tmp/analytics/guide_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
print('Guía actualizada: 4 páginas; gráficos vectoriales y fuentes integradas.')
