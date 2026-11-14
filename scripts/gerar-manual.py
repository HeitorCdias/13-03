"""Transforma o guia e a lista de compras no PDF ilustrado distribuído."""
from pathlib import Path
from html import escape
import json
import os
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle, KeepTogether
from PIL import Image as PILImage

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = Path(os.environ.get('ESPELHO_FONT_DIR', '/usr/share/fonts/truetype/dejavu'))
for name, file in [('Body', 'DejaVuSans.ttf'), ('Bold', 'DejaVuSans-Bold.ttf'), ('Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
INK = colors.HexColor('#1a3023')
GREEN = colors.HexColor('#dbe7cf')
MUTED = colors.HexColor('#59695e')
styles = {
    'cover': ParagraphStyle('cover',fontName='Bold',fontSize=38,leading=46,textColor=INK,spaceAfter=20),
    'h1': ParagraphStyle('h1',fontName='Bold',fontSize=21,leading=27,textColor=INK,spaceAfter=16,keepWithNext=True),
    'body': ParagraphStyle('body',fontName='Body',fontSize=9.5,leading=14.5,textColor=INK,spaceAfter=10),
    'bullet': ParagraphStyle('bullet',fontName='Body',fontSize=9.5,leading=14.5,textColor=INK,leftIndent=13,firstLineIndent=-10,spaceAfter=6),
    'toc': ParagraphStyle('toc',fontName='Body',fontSize=9,leading=12,textColor=MUTED,spaceAfter=7),
    'caption': ParagraphStyle('caption',fontName='Body',fontSize=8.5,leading=12,textColor=MUTED,spaceAfter=15),
    'code': ParagraphStyle('code',fontName='Mono',fontSize=8,leading=12,textColor=INK,backColor=colors.HexColor('#edf0e7'),borderPadding=10,spaceBefore=6,spaceAfter=14,wordWrap='CJK'),
    'table': ParagraphStyle('table',fontName='Body',fontSize=8.5,leading=12,textColor=INK,spaceAfter=3),
}


def inline(value):
    tokens=[]
    def link(match):
        target=match.group(2)
        if not target.startswith(('http://','https://')):
            target='https://github.com/HeitorCdias/13-03/blob/espelho-touch/'+target
        tokens.append(f'<link href="{escape(target,quote=True)}" color="#356d43"><u>{escape(match.group(1))}</u></link>')
        return f'LINKTOKEN{len(tokens)-1}END'
    value=re.sub(r'\[([^]]+)\]\(([^)]+)\)',link,value)
    value=escape(value)
    value=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'`([^`]+)`',r'<font name="Mono" size="8.5">\1</font>',value)
    for i,token in enumerate(tokens):value=value.replace(f'LINKTOKEN{i}END',token)
    return value


def footer(canvas, doc):
    w,h=A4
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#d3d9cc'))
    canvas.line(20*mm,18*mm,w-20*mm,18*mm)
    canvas.setFont('Body',8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20*mm,12*mm,'ESPELHO TOUCH  /  Manual de implementação  /  v1.0')
    canvas.drawRightString(w-20*mm,12*mm,str(doc.page))
    canvas.restoreState()


class ManualDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='h1':
            title=flowable.getPlainText()
            key='section-'+str(self.page)+'-'+str(len(title))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,0)


story=[]
story.append(Spacer(1,5*mm))
story.append(Paragraph('ESPELHO<br/>TOUCH',styles['cover']))
story.append(Paragraph('Do circuito à moldura.<br/>Raspberry Pi 4 · Arduino Uno · ESP32-CAM',styles['h1']))
story.append(Paragraph('Projeto de referência 1.0 · 14 de novembro de 2026',styles['body']))
story.append(Spacer(1,8*mm))
story.append(Image(str(ROOT/'docs/imagens/05-camadas.png'),width=155*mm,height=107*mm))
story.append(Spacer(1,8*mm))
story.append(Paragraph('Códigos, lista de compras com links, ligações ilustradas, modelo paramétrico da moldura e sequência de implementação.',styles['body']))
story.append(Paragraph('As medidas mecânicas são exemplos. A fabricação depende das dimensões dos componentes adquiridos. Hardware físico e firmware em placa ainda exigem validação de bancada.',styles['caption']))
story.append(PageBreak())
story.append(Paragraph('Como usar este manual',styles['h1']))
story.append(Paragraph('Siga as etapas na ordem. Não compre vidro ou libere cortes apenas pela diagonal do monitor. Os marcadores do PDF permitem navegar entre capítulos e o apêndice traz links de busca de cada peça.',styles['body']))
headings=re.findall(r'^## (.+)$',(ROOT/'docs/GUIA.md').read_text(),flags=re.M)
for heading in headings:
    story.append(Paragraph(inline(heading),styles['toc']))
story.append(Paragraph('Apêndice · Lista de compras com links',styles['toc']))
story.append(Paragraph('Status: aplicativo e desenhos verificados em software. Compilação das placas bloqueada pelo registro PlatformIO nesta rede. Não foram executados ensaios com monitor, vidro, eletrônica ou estrutura físicos.',styles['body']))

text=(ROOT/'docs/GUIA.md').read_text('utf-8').splitlines()
index=0
while index<len(text):
    line=text[index].strip()
    index+=1
    if not line:continue
    if line.startswith('# '):
        # A capa e a introdução editorial já foram inseridas acima.
        while index<len(text) and not text[index].startswith('## '):index+=1
        continue
    if line.startswith('## '):
        story.append(PageBreak())
        story.append(Paragraph(inline(line[3:]),styles['h1']))
    elif line.startswith('```'):
        block=[]
        while index<len(text) and not text[index].startswith('```'):
            block.append(text[index]);index+=1
        index+=1
        story.append(Paragraph('<br/>'.join(escape(s).replace(' ','&#160;') for s in block),styles['code']))
    elif line.startswith('!['):
        match=re.match(r'!\[([^]]*)\]\(([^)]+)\)',line)
        path=ROOT/match.group(2)
        with PILImage.open(path) as image:w,h=image.size
        max_w=170*mm
        max_h=(150 if path.name=='painel-demonstracao.png' else 90 if path.name=='05-camadas.png' else 110)*mm
        ratio=min(max_w/w,max_h/h)
        story.append(Image(str(path),width=w*ratio,height=h*ratio))
        story.append(Paragraph(escape(match.group(1)),styles['caption']))
    elif line.startswith('- '):
        story.append(Paragraph('• '+inline(line[2:]),styles['bullet']))
    elif re.match(r'^\d+\. ',line):
        story.append(Paragraph(inline(line),styles['bullet']))
    else:
        paragraph=[line]
        while index<len(text) and text[index].strip() and not text[index].startswith(('#','```','![','- ')) and not re.match(r'^\d+\. ',text[index]):
            paragraph.append(text[index].strip());index+=1
        story.append(Paragraph(inline(' '.join(paragraph)),styles['body']))

items=json.loads((ROOT/'hardware/lista-compras.json').read_text())
for start in range(0,len(items),6):
    story.append(PageBreak())
    story.append(Paragraph(f'Compras · itens {start+1}–{min(start+6,len(items))}',styles['h1']))
    story.append(Paragraph('Buscas no Mercado Livre, sem preço/estoque verificados. Confira especificações, vendedor e compatibilidade antes de pagar.',styles['caption']))
    for number,item in enumerate(items[start:start+6],start+1):
        cells=[]
        cells.append(Paragraph(f"<b>{number:02d} · {item['quantidade']} × {escape(item['item'])}</b>",styles['body']))
        cells.append(Paragraph(escape(item['especificacao']),styles['table']))
        links=f"[Pesquisar para compra]({item['compra']})"
        if item['referencia']:links+=f" · [Referência técnica]({item['referencia']})"
        cells.append(Paragraph(inline(links),styles['body']))
        cells.append(Spacer(1,5*mm))
        story.append(KeepTogether(cells))

output=ROOT/'docs/Manual-Espelho-Touch.pdf'
doc=ManualDoc(str(output),pagesize=A4,rightMargin=20*mm,leftMargin=20*mm,topMargin=22*mm,bottomMargin=25*mm,title='Espelho Touch — Manual de implementação',author='Projeto Espelho Touch',pageCompression=1)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(output)
