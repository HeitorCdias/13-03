# Espelho Touch

Novo projeto de referência para **Raspberry Pi 4 + Arduino Uno R3 + ESP32-CAM AI Thinker / OV2640**, monitor HDMI em pé e touch USB infravermelho instalado à frente do espelho.

## Comece por aqui

- **[Manual ilustrado em PDF](docs/Manual-Espelho-Touch.pdf)** — compra, eletrônica, firmware, moldura, montagem e testes.
- [Manual em texto](docs/GUIA.md).
- **[Peças e links de compra](COMPRAS.md)** e [planilha CSV](hardware/lista-compras.csv).
- [Moldura paramétrica OpenSCAD](hardware/moldura.scad), [DXF frontal](hardware/frente-corte.dxf) e [medidas de exemplo](hardware/medidas-exemplo.json).
- [Tabela completa de ligações](hardware/ligacoes.csv).
- [Resultados e limites da validação](docs/VALIDACAO.md).

## Funcionalidades implementadas

Relógio/data/saudação em português, clima externo Open-Meteo com cache offline, sensores internos DHT22, presença PIR, luminosidade LDR, LED branco 12 V com brilho manual/automático, agenda touch persistente, mensagens rotativas, temporizador visual e captura manual da câmera local. Repouso visual opcional, com toque para acordar. Não corta a alimentação do monitor.

**Antes de comprar:** touch capacitivo atrás de vidro espelhado não é garantido. A referência usa moldura IR na frente do vidro. A OV2640 conecta ao ESP32-CAM, não diretamente ao Uno. O vidro e o corte só podem ser fechados depois de medir monitor e moldura IR reais. Os desenhos são de referência, não projeto estrutural certificado.

## Testar no Windows sem eletrônica

Instale Python 3.10 ou superior. Extraia o ZIP da branch `espelho-touch` e abra o PowerShell na pasta que contém este README:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app/server.py --demo
```

Abra `http://localhost:8000`. A faixa superior identifica **DEMONSTRAÇÃO**. Os sensores e o LED são simulados; a câmera continua exigindo hardware real. Não é necessário ativar o ambiente virtual no PowerShell. Se `py` não existir, use `python` no primeiro comando.

## Raspberry Pi

Use Raspberry Pi OS com desktop. Instale `python3-venv`, `python3-pip`, `chromium`, `git` e `tzdata` via apt. Clone a branch independente:

```bash
git clone --branch espelho-touch --single-branch https://github.com/HeitorCdias/13-03.git ~/espelho-touch
cd ~/espelho-touch
bash scripts/instalar-pi.sh
# Edite .env; identifique o Arduino e o IP reservado do ESP32-CAM.
.venv/bin/python app/server.py
```

Em outro terminal na pasta do projeto, execute `bash scripts/quiosque.sh`. O serviço usa apenas loopback; o monitor local acessa `http://localhost:8000`. Leia o manual antes de instalar o autostart com `bash scripts/ativar-autostart.sh`.

## Firmware

Instale PlatformIO Core/IDE. Na pasta do projeto:

```bash
pio run -d firmware/arduino_uno
pio run -d firmware/arduino_uno -t upload --upload-port SUA_PORTA_UNO
```

Copie `firmware/esp32_cam/include/secrets.example.h` para `secrets.h`, configure Wi-Fi 2,4 GHz e uma chave aleatória de pelo menos 32 caracteres; repita a chave no `.env` do Pi. Para gravar o ESP32-CAM, siga a figura e a sequência de boot do manual:

```bash
pio run -d firmware/esp32_cam
pio run -d firmware/esp32_cam -t upload --upload-port SUA_PORTA_UART
```

## Desenvolvimento e documentação

```bash
python -m unittest discover -s tests -v
node --check app/static/app.js
```

Node serve somente para verificar sintaxe. Para regenerar figuras/PDF, instale `requirements-docs.txt` e execute `python scripts/gerar-ilustracoes.py` e `python scripts/gerar-manual.py`. As fontes DejaVu Sans são necessárias; os scripts usam as fontes do sistema ou `ESPELHO_FONT_DIR`.

Sem senhas em Git, sem gravação contínua, sem reconhecimento facial. Integrações de calendário externo, voz, fechaduras, biometria e vídeo contínuo são extensões futuras, não recursos entregues. O teste físico final depende das peças compradas.
