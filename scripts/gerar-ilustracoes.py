"""Gera os desenhos técnicos originais do manual. Requer Pillow."""
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/imagens'
OUT.mkdir(parents=True, exist_ok=True)
FONT_DIR = Path(os.environ.get('ESPELHO_FONT_DIR', '/usr/share/fonts/truetype/dejavu'))
FONT = str(FONT_DIR / 'DejaVuSans.ttf')
BOLD = str(FONT_DIR / 'DejaVuSans-Bold.ttf')
BG, INK, MUTED, GREEN, BLUE, RED = '#f3f1e9', '#16291f', '#51635a', '#d1e2c3', '#dce8ee', '#f2d9cf'


def canvas(title, subtitle, height=1000):
    image = Image.new('RGB', (1600, height), BG)
    draw = ImageDraw.Draw(image)
    draw.text((60, 38), title, fill=INK, font=ImageFont.truetype(BOLD, 43))
    draw.text((60, 103), subtitle, fill=MUTED, font=ImageFont.truetype(FONT, 24))
    return image, draw


def text(draw, pos, value, size=25, fill=INK, width=50, bold=False):
    font = ImageFont.truetype(BOLD if bold else FONT, size)
    lines=[]
    for line in value.split('\n'):
        lines.extend(textwrap.wrap(line, width) or [''])
    draw.multiline_text(pos, '\n'.join(lines), fill=fill, font=font, spacing=10)


def box(draw, xy, title, detail='', fill=GREEN, title_size=29):
    draw.rounded_rectangle(xy, radius=18, fill=fill, outline=INK, width=2)
    x,y,x2,y2=xy
    text(draw,(x+24,y+22),title,size=title_size,bold=True,width=max(15,int((x2-x-48)/(title_size*.60))))
    if detail:text(draw,(x+24,y+85),detail,size=23,width=max(15,int((x2-x-48)/14)))


def arrow(draw, start, end, label='', color=INK):
    draw.line([start,end],fill=color,width=5)
    import math
    angle=math.atan2(end[1]-start[1],end[0]-start[0])
    points=[end,(end[0]-18*math.cos(angle-.45),end[1]-18*math.sin(angle-.45)),(end[0]-18*math.cos(angle+.45),end[1]-18*math.sin(angle+.45))]
    draw.polygon(points,fill=color)
    if label:text(draw,((start[0]+end[0])/2+12,(start[1]+end[1])/2-34),label,size=22,width=20)


im,d=canvas('01 / Quem faz o quê', 'Três controladores, funções distintas. Não há fio de dados Uno → ESP32.')
box(d,(520,190,1060,385),'Raspberry Pi 4','Interface touch + Python\nAgenda, clima e ponte local')
box(d,(60,520,500,745),'Arduino Uno R3','DHT22 · PIR · LDR\nPWM da iluminação')
box(d,(1100,520,1540,745),'ESP32-CAM','Wi-Fi 2,4 GHz\nOV2640 · foto sob demanda')
box(d,(545,570,1015,790),'Monitor + touch IR','HDMI: imagem\nUSB HID: toque',BLUE)
arrow(d,(610,385),(370,520),'USB / JSON')
arrow(d,(970,385),(1220,520),'HTTP local')
arrow(d,(780,385),(780,570),'HDMI + USB')
text(d,(65,855),'Alimentações externas separadas: Pi 5,1 V / 3 A; câmera 5 V / 1 A; LED 12 V / 2 A; monitor com fonte original.',size=25,width=110)
im.save(OUT/'01-arquitetura.png')

im,d=canvas('02 / Sensores no Arduino', 'Faça primeiro na bancada. Conferir a pinagem serigrafada dos módulos.',1100)
box(d,(70,210,485,865),'UNO R3','USB ← Raspberry Pi\n\n5V / GND\nD2 → DHT22 DATA\nD3 ← PIR OUT\nA0 ← divisor LDR\nD9 → driver LED',BLUE)
box(d,(800,185,1500,355),'DHT22 / AM2302','VCC → 5V · GND → GND\nDATA → D2 · pull-up 10k DATA–5V')
box(d,(800,400,1500,565),'PIR HC-SR501','VCC → 5V · GND → GND · OUT → D3\nLente exposta; aguarde 60 s ao ligar')
box(d,(800,610,1500,815),'LDR + resistor de 10k','5V → LDR → ponto A0 → resistor → GND\nMais luz = leitura maior no A0')
arrow(d,(485,300),(800,270))
arrow(d,(485,500),(800,480))
arrow(d,(485,700),(800,700))
text(d,(75,935),'O DHT22 fica em nicho ventilado fora da câmara quente. A lente PIR não funciona através do espelho. Nunca conecte 12 V em um pino do Uno.',size=28,width=95)
im.save(OUT/'02-sensores.png')

im,d=canvas('03 / LED branco 12 V · até 0,8 A', 'Driver low-side com MOSFET lógico IRLZ44N. Desligue as fontes antes de ligar fios.',1120)
box(d,(70,210,475,380),'Fonte 12 V / 2 A','Saída CC; adaptador fechado',RED)
box(d,(1030,200,1510,400),'Fita LED branca','Até 1 m × 9,6 W/m\n+12V / negativo',GREEN)
arrow(d,(475,260),(1030,260),'fusível ~1,25 A')
box(d,(1000,550,1510,785),'IRLZ44N','Gate (G) · Drain (D) · Source (S)\nConferir datasheet/pinos reais',BLUE)
arrow(d,(1290,400),(1290,550),'LED − → D')
box(d,(70,565,500,805),'Arduino Uno','D9 → 220 Ω → Gate\n10k entre Gate e Source\nGND → Source')
arrow(d,(500,630),(1000,630),'sinal PWM 5 V')
d.line([(260,380),(260,470),(780,470),(780,850),(1330,850),(1330,785)],fill=INK,width=5)
d.line([(260,805),(260,850),(780,850)],fill=INK,width=5)
text(d,(510,890),'GND comum: fonte 12 V (−), source e Arduino.\n+12 V nunca vai para 5V, USB ou pinos de sinal.',size=26,width=65,bold=True)
text(d,(70,1020),'Use conexões soldadas/terminais, isolamento, perfil de alumínio e alívio de tração. Protoboard só no teste de bancada.',size=23,width=115)
im.save(OUT/'03-driver-led.png')

im,d=canvas('04 / Gravar o ESP32-CAM', 'Programador USB-UART com TX/RX de 3,3 V. Alimentação externa regulada de 5 V.',1100)
box(d,(65,225,575,600),'USB-UART 3,3 V','TX → U0R\nRX ← U0T\nGND ↔ GND\nVCC: NÃO conectar',BLUE)
box(d,(975,225,1525,600),'ESP32-CAM AI Thinker','U0R / U0T / GND\nIO0 → GND só para gravar\n5V ← fonte externa\nOV2640 no conector FPC')
arrow(d,(575,320),(975,320),'TX → RX')
arrow(d,(975,410),(575,410),'TX → RX')
d.line([(575,520),(975,520)],fill=INK,width=5)
box(d,(700,760,1510,945),'Fonte 5 V / 1 A + chave','+5V → chave → pino 5V da câmera\n− → GND da câmera e do USB-UART',RED)
arrow(d,(1250,760),(1250,600))
text(d,(65,715),'Sequência de boot',size=28,bold=True)
text(d,(65,775),'1. IO0 no GND.\n2. Reinicie; grave.\n3. Tire IO0 do GND.\n4. Reinicie novamente.\n5. Remova o programador.',size=23,width=37)
text(d,(65,1010),'Não use 5 V nos sinais UART nem no pino 3V3. Não mantenha duas saídas de fonte conectadas ao mesmo +5V.',size=25,width=108)
im.save(OUT/'04-camera-programacao.png')

im,d=canvas('05 / Camadas da montagem', 'Vista lateral esquemática — sem escala. O touch IR fica na frente do vidro.',1100)
layers=[(150,'1','Touch IR','Feixes livres; nada cobrindo os emissores',GREEN),(310,'2','Espelho 4 mm','Calços EPDM + presilhas, sem compressão',BLUE),(470,'3','Monitor HDMI','Fixação VESA própria; não apoiar no vidro',GREEN),(650,'4','Caixa ventilada','Pi, Uno, câmera e driver em suportes',RED),(850,'5','Tampa removível','Passa-cabos e acesso de manutenção',BLUE)]
for x,n,title,detail,color in layers:
 d.polygon([(x,240),(x+95,200),(x+95,770),(x,810)],fill=color,outline=INK,width=3)
 text(d,(x+20,280),n,size=45,bold=True)
 text(d,(x-15,845),title,size=20,width=10,bold=True)
text(d,(1080,220),'Na frente',size=29,bold=True)
text(d,(1080,280),'Lente da câmera com obturador. PIR e LDR em furos próprios, fora do vidro.',size=27,width=25)
text(d,(1080,520),'Atrás',size=29,bold=True)
text(d,(1080,580),'Entradas de ar embaixo e saídas em cima. Fontes de rede elétrica externas à moldura.',size=27,width=25)
text(d,(65,1015),'Tela e vidro são peças independentes. Teste contraste, reflexos e toque com a amostra antes de fabricar.',size=25,width=110)
im.save(OUT/'05-camadas.png')

im,d=canvas('06 / Moldura de exemplo', 'Milímetros. Medidas ilustrativas para monitor em pé; conferir o conjunto comprado.',1350)
scale=1.5; x,y=260,230; w,h=406*scale,626*scale
d.rectangle((x,y,x+w,y+h),fill='#b4a188',outline=INK,width=3)
open_x=x+40*scale;open_y=y+40*scale
d.rectangle((open_x,open_y,x+w-40*scale,y+h-40*scale),fill='#1a2420',outline=INK,width=3)
ax=x+(406-268)/2*scale;ay=y+(626-477)/2*scale
d.rectangle((ax,ay,ax+268*scale,ay+477*scale),fill='#d1e2c3',outline=INK,width=2)
text(d,(ax+35,ay+230),'Área ativa\n268 × 477\n21,5″ / 16:9',size=30,width=17,bold=True)
d.ellipse((x+w/2-7,y+23,x+w/2+7,y+37),fill=INK)
d.ellipse((x+w/2-85,y+h-46,x+w/2-50,y+h-11),fill=INK)
arrow(d,(x,185),(x+w,185));text(d,(x+w/2-50,145),'406',size=26,bold=True)
d.line((x-65,y,x-65,y+h),fill=INK,width=3);text(d,(x-150,y+h/2),'626',size=26,bold=True)
text(d,(980,250),'Frente',size=30,bold=True)
text(d,(980,310),'Abertura: 326 × 546\nVidro: 348 × 568\nBolso: 350 × 570\nSarrafo: 40\nFrente: 18 de espessura',size=25,width=32)
text(d,(980,570),'Profundidade',size=30,bold=True)
text(d,(980,630),'Frente 18 + corpo 92 + tampa 6 = 116 mm\n\nMonitor de exemplo: 310 × 530 × 45\nFolga na abertura: 8 por lado',size=25,width=31)
text(d,(980,935),'Não é escala 1:1.',size=28,bold=True)
text(d,(70,1230),'Furos de câmera/PIR/LDR e posição VESA só são finalizados com os componentes reais em mãos.',size=25,width=110)
im.save(OUT/'06-moldura-medidas.png')

im,d=canvas('07 / Circuito de alimentação', 'Mantenha adaptadores fechados e cabos de rede elétrica fora da caixa.',1030)
for x,title,detail in [(50,'Pi 4','Fonte USB-C 5,1V / 3A'),(440,'Monitor','Fonte original do monitor'),(830,'ESP32-CAM','Fonte 5V / 1A + chave'),(1220,'LED','Fonte 12V / 2A + fusível')]:
 box(d,(x,240,x+330,490),title,detail,BLUE,title_size=26)
 arrow(d,(x+160,490),(x+160,660))
 text(d,(x+20,690),{'Pi 4':'USB → Uno\nUSB → touch\nHDMI → monitor','Monitor':'Não alimentar pelo Pi','ESP32-CAM':'Foto via Wi-Fi\nGND com UART só na gravação','LED':'Retorno via MOSFET\nGND com Uno'}[title],size=23,width=21)
text(d,(70,875),'Não una os positivos das fontes. O único GND adicional permanente é entre o driver LED de 12V e o Uno. A câmera se comunica sem fio.',size=27,width=97)
im.save(OUT/'07-alimentacao.png')
print('Ilustrações geradas em', OUT)
