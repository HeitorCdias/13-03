# ESPELHO TOUCH

Manual de implementação · versão de referência 1.0 · 14/11/2026

Um espelho inteligente com interface touch, Arduino, câmera ESP32 e estrutura desmontável. Projeto novo e independente do espelho anterior. Os códigos, desenhos e esta documentação pertencem à branch `espelho-touch`.

## 01 · Entenda o conjunto antes de comprar

O computador do espelho é um Raspberry Pi 4 Model B, com pelo menos 2 GB de memória. Ele executa a interface no Chromium e conversa com os outros dispositivos. Um Arduino Uno R3 lê os sensores e controla o LED. Um ESP32-CAM AI Thinker captura fotos com a OV2640 e atende ao Raspberry pela rede local Wi-Fi de 2,4 GHz.

![Arquitetura dos três controladores](docs/imagens/01-arquitetura.png)

O monitor recebe imagem por HDMI. A moldura touch infravermelha envia os toques por USB, como um dispositivo HID. Essa moldura fica do lado do usuário, na frente do espelho; seus emissores não podem ficar cobertos. É esta combinação que transforma o monitor em uma superfície touch utilizável com o espelho.

Um monitor capacitivo convencional pode perder o toque atrás do vidro ou da camada metálica. Não compre contando com esse funcionamento sem testar a combinação real. A câmera OV2640 também não deve ser comprada avulsa para ligar ao Uno: o processamento e a interface estão no ESP32-CAM.

**Regra de compra:** monitor, touch e amostra de espelho primeiro; corte da estrutura depois. Os desenhos têm medidas de exemplo e não garantem o encaixe de qualquer monitor de 21,5 polegadas.

## 02 · O que o sistema faz

- Relógio, segundos, data e saudação em português no fuso escolhido.
- Clima externo, sensação e umidade via Open-Meteo. Não requer chave de API. A consulta ocorre a cada 15 minutos e depende de internet.
- Temperatura e umidade internas pelo DHT22, instalado em nicho externo ventilado.
- Presença PIR, leitura de luz ambiente e brilho do LED confirmados pela telemetria do Arduino.
- Iluminação branca de 12 V: brilho manual, apagar e modo automático por presença/luminosidade. O modo manual vence após 15 minutos e volta ao automático.
- Agenda manual editável pelo touch, com até 100 eventos salvos e próximos cinco visíveis.
- Mensagens personalizadas, alternadas a cada 30 segundos.
- Temporizador de 1 a 180 minutos, com pausa e aviso visual. É encerrado se a página for recarregada.
- Captura de uma foto por toque, exibida em uma janela local e removida da página ao fechar. Sem gravação em disco pelo aplicativo.
- Repouso visual opcional após 60 segundos sem presença; toque acorda. Não desliga fisicamente o monitor nem constitui economia garantida de energia.

Não estão implementados reconhecimento facial, assistente de voz, calendário Google/Microsoft, streaming contínuo, automação de portas, controle por aplicativo externo ou medição médica. São possibilidades para uma segunda etapa, com requisitos próprios de hardware, autenticação e testes.

## 03 · Como a interface fica

![Captura real da interface executada em demonstração](docs/imagens/painel-demonstracao.png)

A imagem é uma captura do aplicativo em modo de demonstração, em 1080 × 1920. Temperatura interna e umidade nessa captura são simuladas e identificadas na própria tela. O clima externo aparece indisponível quando a rede não permite a consulta.

O painel usa fundo preto e elementos claros. Em um monitor em pé, ocupa toda a área disponível. As cinco ações touch ficam na parte inferior: câmera, iluminação, timer, ajustes e tela cheia. A página se adapta também ao computador para testes; telas menores podem precisar de rolagem quando há muitos compromissos.

## 04 · Planeje as compras

A lista completa, com quantidades e links clicáveis, está no apêndice deste PDF e em `COMPRAS.md` e `hardware/lista-compras.csv`. Os links de compra são buscas no Mercado Livre, não anúncios testados ou ofertas com preço garantido.

Compre o Raspberry Pi 4 com fonte USB-C de 5,1 V / 3 A e microSD original de 32 GB ou mais. O cabo de vídeo para o Pi 4 é **micro-HDMI para HDMI**, não mini-HDMI. A câmera precisa de fonte regulada própria de 5 V / 1 A ou mais e de USB-UART com sinais de 3,3 V para a gravação.

Escolha monitor HDMI com VESA e operação permitida na vertical. Solicite ao fornecedor: dimensões externas sem base, profundidade com conectores, área ativa, padrão VESA, comprimento máximo dos parafusos e posição das entradas. Monitor com fonte externa facilita manter a rede elétrica fora da moldura.

A moldura IR deve combinar área ativa, proporção 16:9, orientação e dimensões externas com esse monitor. Peça confirmação de funcionamento USB HID no Linux/Raspberry Pi OS. O touch só cobre a área ativa da tela; a borda espelhada externa não vira área de interface.

Para o espelho, peça amostra de vidro óptico semitransparente. Teste a legibilidade com iluminação do ambiente e brilho real do monitor. Não existe uma porcentagem universal de transmissão/reflexão que sirva a todos os ambientes. Película de decoração pode produzir reflexos duplos e baixa definição.

## 05 · Alimentação e organização elétrica

![Alimentações independentes](docs/imagens/07-alimentacao.png)

Use fontes externas, fechadas e adequadas para cada carga. Nenhuma ligação de 127/220 V precisa ser montada dentro da moldura. Este projeto cobre apenas as saídas de baixa tensão dos adaptadores. Preserve os aterramentos e a construção original do monitor: não abra sua fonte ou carcaça para adaptar o suporte.

O Pi alimenta o Uno e a moldura touch por USB, desde que a soma das cargas esteja dentro da especificação do Pi. Se o touch exigir mais corrente, use hub alimentado que não realimente o Pi. Confira subtensão no Raspberry com `vcgencmd get_throttled`; eventos históricos permanecem registrados até reiniciar.

LED de exemplo: 1 m × 9,6 W/m = 9,6 W; corrente nominal de 9,6/12 = 0,8 A. A fonte 12 V / 2 A tem margem, mas o fusível deve proteger os fios e os componentes. Um fusível CC de aproximadamente 1,25 A é ponto de partida para essa carga, sujeito à corrente real e à partida. Mais fita exige recalcular corrente, fonte, dissipação e fios.

Não una os positivos das fontes. O driver LED e o Uno compartilham GND para o PWM. A câmera conversa por Wi-Fi e não precisa de GND comum com o Uno em operação normal. Use multímetro para conferir polaridade antes de conectar as placas.

## 06 · Ligue os sensores no Uno

![Ligação dos sensores](docs/imagens/02-sensores.png)

- DHT22: alimentação 5V e GND; DATA em D2. Coloque resistor de 10 kohm entre DATA e 5V se o módulo não trouxer pull-up. No sensor de quatro pinos, confira o datasheet; o pino não usado permanece desconectado.
- PIR HC-SR501: VCC em 5V, GND em GND e OUT em D3. A ordem dos terminais varia entre módulos: siga a serigrafia. O firmware ignora movimento durante os primeiros 60 segundos.
- LDR: ligue 5V → LDR → nó A0 → resistor 10 kohm → GND. A0 lê o ponto entre LDR e resistor. Mais luz produz leitura maior.
- LED: o sinal PWM sai por D9 para o driver da próxima etapa. Nunca ligue a fita de 12 V diretamente ao Uno.

Teste apenas o Uno e os sensores primeiro, sem fita LED. Faça a montagem final em placa perfurada ou PCB, com solda, terminais e isolamento; a protoboard é destinada à bancada. A alimentação normal do Uno vem do USB do Raspberry; não injete também 12 V no pino 5V.

O DHT22 mede o ar junto dele. Deixe-o longe da traseira quente do monitor e das fontes, em nicho ventilado voltado ao ambiente. A lente do PIR deve ficar exposta: vidro bloqueia a radiação infravermelha que ele precisa detectar. Posicione o LDR fora da iluminação direta do LED para evitar oscilação do controle.

## 07 · Monte o driver LED

![Ligação do LED e MOSFET](docs/imagens/03-driver-led.png)

Use MOSFET N lógico **IRLZ44N**, conferindo a procedência e o datasheet do fabricante. Não substitua automaticamente por IRF520, cuja condução pode ser inadequada com o sinal de 5 V. A referência usa PWM no negativo da fita branca, não fita RGB ou endereçável.

- Positivo da fonte 12 V → fusível → positivo da fita LED.
- Negativo da fita → drain do IRLZ44N.
- Source → negativo da fonte 12 V e GND do Uno.
- D9 do Uno → resistor de 220 ohm → gate.
- Resistor de 10 kohm entre gate e source, para manter o MOSFET desligado quando o sinal estiver flutuando.

No encapsulamento TO-220 usual do IRLZ44N, confirme os pinos G/D/S no datasheet antes de soldar. A aba metálica é drain; não deixe encostar na estrutura ou em outra trilha. Isole os terminais. Use perfil de alumínio na fita, evitando concentrar calor na madeira.

Antes do primeiro acionamento, confira ausência de curto entre +12 V e GND com tudo desligado. Comece com brilho baixo, meça corrente e temperatura e teste desligamento pelo aplicativo. Em modo automático, o LED fica apagado sem presença recente e ajusta o brilho entre valores aproximados de 30 e 210 conforme o LDR; os limiares no firmware precisam de calibração no ambiente real.

## 08 · Prepare o Raspberry Pi

Grave Raspberry Pi OS com desktop no microSD usando o [Raspberry Pi Imager oficial](https://www.raspberrypi.com/software/). Defina um usuário e senha próprios e configure a rede. Use rede de 2,4 GHz disponível também para o ESP32-CAM. Conecte monitor e touch, inicialize e atualize o sistema.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip chromium git tzdata
git clone --branch espelho-touch --single-branch https://github.com/HeitorCdias/13-03.git ~/espelho-touch
cd ~/espelho-touch
bash scripts/instalar-pi.sh
.venv/bin/python app/server.py --demo
```

Se sua versão do sistema oferecer `chromium-browser` em vez de `chromium`, instale esse pacote. O script de quiosque aceita ambos. Abra `http://localhost:8000` no navegador do próprio Pi. A faixa superior precisa mostrar DEMONSTRAÇÃO: nenhum sensor físico está sendo validado nessa etapa.

Em Ajustes, configure nome, cidade, latitude, longitude e fuso. Cidade é apenas um rótulo; o clima usa coordenadas. Edite a agenda e as mensagens. Os dados ficam em `data/settings.json`. Faça backup dessa pasta e de `.env` fora do Git, protegendo a chave da câmera.

## 09 · Teste no Windows antes de montar

Instale Python 3.10 ou superior e extraia o ZIP da branch nova. Abra o PowerShell na pasta onde estão `README.md`, `requirements.txt` e `app`.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app/server.py --demo
```

Se `py` não existir, use `python` no primeiro comando. Não é necessário alterar a política de execução do PowerShell: os comandos usam o executável da venv diretamente. O pacote tzdata fornece os fusos usados pelo aplicativo no Windows.

Abra `http://localhost:8000`, teste ajustes, agenda e timer. Para girar o monitor, vá a Configurações → Sistema → Tela, selecione o monitor e escolha Retrato ou Retrato invertido. Pressione F11 no navegador. Só gire o monitor fisicamente se o suporte permitir.

Sem hardware, o modo normal mostra sensores indisponíveis. O modo demo é o único que inventa leituras e sempre informa isso na tela. Para testar o Uno no Windows posteriormente, configure `SERIAL_PORT=COM3` (substitua pela porta real) no `.env` e execute sem `--demo`.

## 10 · Grave o firmware do Uno

Instale PlatformIO Core ou a extensão PlatformIO no VS Code. As duas pastas de firmware já incluem `platformio.ini` com versões de plataforma e bibliotecas definidas. Para instalar o CLI em uma venv de desenvolvimento:

```bash
python -m pip install platformio==6.1.18
pio device list
pio run -d firmware/arduino_uno
pio run -d firmware/arduino_uno -t upload --upload-port SUA_PORTA_UNO
```

Troque SUA_PORTA_UNO por COM3, por exemplo, ou pelo caminho listado no Linux. O alvo é **Uno R3 / ATmega328P**. Uno R4 não é substituto direto para este firmware. Use cabo USB com dados; alguns cabos só alimentam.

O firmware envia uma linha JSON a cada dois segundos. Para inspecionar, use `pio device monitor --baud 115200 --port SUA_PORTA_UNO`. Feche esse monitor antes de iniciar o servidor, porque a porta serial deve ter um único dono. O Uno normalmente reinicia quando a porta é aberta.

```json
{"type":"telemetry","temp_c":24.5,"humidity":58,"presence":true,"light_raw":420,"led":128,"mode":"manual","uptime_ms":70000}
```

Falha no DHT22 aparece como `null`, nunca como uma temperatura inventada. O firmware ignora comandos fora do intervalo de PWM 0–255. Desconecte e reconecte o USB para confirmar a recuperação antes de avançar.

## 11 · Grave o ESP32-CAM e a OV2640

![Programador, alimentação e sequência de boot da câmera](docs/imagens/04-camera-programacao.png)

A pinagem do código é exclusiva do **ESP32-CAM AI Thinker clássico com OV2640**. Não use sem adaptação em ESP32-S3-CAM ou ESP32 comum com câmera de pinagem diferente. Encaixe o cabo FPC com a alimentação desligada, respeitando a orientação do conector e fechando a trava sem forçar.

No USB-UART, use sinais TX/RX de 3,3 V. TX do adaptador vai em U0R, RX vai em U0T, GND vai em GND. Não conecte VCC do adaptador: a câmera é alimentada pela fonte regulada de 5 V no pino 5V. Una o GND dessa fonte ao GND do programador enquanto grava.

## 11B · Configure e grave a câmera

Faça esta etapa depois de conferir as ligações da figura anterior. Crie os arquivos de credenciais localmente e preserve-os fora do Git.

1. Copie `secrets.example.h` para `firmware/esp32_cam/include/secrets.h`.
2. Preencha SSID/senha da rede 2,4 GHz e uma CAMERA_KEY aleatória de 32 ou mais caracteres. Gere uma com `python -c "import secrets; print(secrets.token_hex(32))"` no seu computador e não a publique.
3. Com a alimentação desligada, coloque IO0 em GND. Alimente e reinicie o módulo para entrar no bootloader.
4. Compile e grave pelos comandos abaixo. Se não conectar, pressione RST no momento em que a gravação começar.
5. Desligue, retire a ligação IO0–GND e religue. Se IO0 permanecer no GND, o módulo não inicia normalmente.

```bash
pio run -d firmware/esp32_cam
pio run -d firmware/esp32_cam -t upload --upload-port SUA_PORTA_UART
pio device monitor --baud 115200 --port SUA_PORTA_UART
```

O monitor serial mostra o IP local ao conectar. Reserve esse IP no roteador. Retire o programador para a operação final. O flash fica desligado. O projeto não usa microSD na câmera.

## 12 · Vincule Pi, Arduino e ESP32

No Raspberry, pare a demonstração com Ctrl+C. Conecte o Uno por USB e execute `ls /dev/serial/by-id/`. Use o caminho persistente correspondente em vez de assumir `/dev/ttyACM0`. Se houver erro de permissão, adicione o usuário ao grupo serial da distribuição, normalmente `dialout`, com `sudo usermod -aG dialout "$USER"`, e faça logout/login.

Edite o `.env`, criado pelo instalador, com um editor local. Ele deve conter os dados reais abaixo; não use os valores de exemplo literalmente:

```text
SERIAL_PORT=/dev/serial/by-id/IDENTIFICADOR_DO_SEU_UNO
SERIAL_BAUD=115200
CAMERA_URL=http://IP_RESERVADO_DA_CAMERA
CAMERA_KEY=MESMA_CHAVE_ALEATORIA_DO_SECRETS_H
```

Execute `.venv/bin/python app/server.py` sem `--demo`. A faixa deve mudar para Arduino conectado. Leituras com mais de oito segundos são descartadas da interface. Um comando de LED primeiro é enviado; o valor mostrado no painel vem da próxima telemetria, não de uma suposição de que a fita acendeu.

No botão Câmera, toque em Capturar agora. Uma resposta válida aparece na janela. A imagem fica somente na memória do servidor durante o repasse e em uma URL temporária do navegador. Ao fechar, essa URL é revogada. Use a chave no cabeçalho, não na URL. O HTTP da câmera não é criptografado: use rede privada confiável, não encaminhe portas e não exponha os serviços à internet.

Instale uma chave física no +5 V da câmera e um obturador opaco acessível à frente da lente. Eles permitem bloquear a câmera independentemente de qualquer software. Esta versão não identifica pessoas e não mantém galeria.

## 13 · Touch, retrato e tela cheia

Conecte a moldura touch IR diretamente a uma USB do Pi. Antes de colocar o espelho, toque nos quatro cantos e no centro do monitor. Depois repita com o vidro colocado e a moldura IR à frente dele. O vidro não pode bloquear os feixes entre emissores e receptores.

Nas configurações de tela do Raspberry Pi OS, gire a saída HDMI para a orientação em pé e ajuste para 1080 × 1920 quando o monitor permitir. O método de rotação e associação do touch depende da sessão gráfica e da versão do OS. Use a ferramenta de configuração de telas/dispositivos do sistema; não copie uma matriz de rotação aleatória para outro monitor.

Se a imagem girar e os toques não, a calibração/associação do USB precisa acompanhar a rotação. Em X11, `xinput list` identifica o dispositivo e `xinput list-props ID` mostra as propriedades; em Wayland o ajuste é do compositor/libinput e não do xinput. Consulte o fornecedor da moldura e faça os cinco toques de referência novamente. Não fixe permanentemente o vidro antes desse teste.

No diretório do projeto, com o servidor já rodando, execute `bash scripts/quiosque.sh` em outro terminal da sessão gráfica. O script aguarda a resposta do servidor e abre Chromium em modo quiosque. Alt+F4 fecha o navegador. O botão Tela cheia usa a API do navegador, e F11 pode ser usado durante testes comuns.

## 14 · Desenho mecânico e medidas

![Vista frontal com medidas de exemplo](docs/imagens/06-moldura-medidas.png)

Exemplo: corpo do monitor em pé 310 × 530 × 45 mm; área ativa aproximada 268 × 477 mm. A folga frontal de oito milímetros por lado cria abertura de 326 × 546 mm. Sarrafos frontais de 40 mm levam a uma dimensão externa de **406 × 626 mm**.

O rebaixo sobrepõe o vidro em 12 mm por lado. O bolso tem 350 × 570 mm; com folga de um milímetro por lado, o vidro de exemplo é 348 × 568 × 4 mm. Rebaixo de 6 mm permite vidro e calços; a espessura final precisa ser conferida com o fornecedor. Não force o vidro a entrar.

A frente tem 18 mm, o corpo 92 mm e a tampa 6 mm: profundidade total de referência 116 mm. O modelo mostra a tampa afastada para visualizar o acesso; esse afastamento não entra na dimensão montada. A moldura IR tem dimensões próprias e precisa ser acomodada sem bloquear sua área ativa.

Edite `hardware/moldura.scad` no OpenSCAD conforme as medidas reais. O arquivo JSON documenta o exemplo, mas não alimenta automaticamente o SCAD: mantenha ambos coerentes ao modificar o projeto. O arquivo DXF é apenas o contorno frontal e os furos; não carrega a profundidade de rebaixo. O STL é geometria de referência, não recomendação para imprimir uma estrutura que suporte vidro e monitor.

## 15 · Plano de corte e sustentação

O plano abaixo usa o exemplo de 406 × 626 mm. Ele deve ser aprovado por quem fabricar após medir os componentes. Espessuras e juntas precisam considerar a ferramenta e a fixação escolhidas.

- Frente 18 mm: duas peças com comprimento externo 406 × 40 mm e duas com comprimento externo 626 × 40 mm, cantos a 45°. Alternativa CNC: uma placa 406 × 626 × 18 mm com abertura e rebaixo. Não faça as duas opções ao mesmo tempo.
- Laterais do corpo: duas peças 626 × 92 × 18 mm.
- Travessas superior e inferior do corpo: duas peças 370 × 92 × 18 mm, entre as laterais. Assim o corpo externo permanece 406 × 626 mm.
- Tampa removível: uma peça 406 × 626 × 6 mm, parafusada com ferragens adequadas e sem unir o suporte de carga à tampa fina.
- Rebaixo do vidro: bolso 350 × 570 mm, profundidade de exemplo 6 mm, na traseira da frente.
- Ventilação: aberturas inferiores e superiores no corpo, protegidas por tela. Os cortes no CAD são ilustrativos; confira se não conflitam com cantoneiras ou suporte.

O monitor deve ser sustentado por suporte VESA metálico, conforme o fabricante. O vidro tem apoio por calços EPDM e retenção por presilhas independentes. Não deixe o peso do monitor no vidro ou na moldura IR. Use ferragens de parede dimensionadas para a massa total e o material da parede, verificadas por instalador competente. O desenho não especifica carga admissível nem buchas universais.

Sele madeira e bordas, use espaçadores nas placas, proteja arestas e preveja acesso aos conectores. Mantenha o espelho longe de umidade e respingos: este gabinete não possui classificação IP e não foi projetado para banheiro.

## 16 · Monte na ordem correta

![Montagem em camadas](docs/imagens/05-camadas.png)

1. Teste toda a eletrônica na bancada, com fontes fechadas, antes de cortar a madeira.
2. Faça um gabarito de papelão em tamanho real com monitor, IR, conectores, câmera, PIR e LDR. Meça profundidade considerando a curva dos cabos.
3. Fabrique a frente e o corpo. Faça acabamento e retire todo o pó antes de colocar vidro ou placas.
4. Monte o suporte VESA e confira que a carga vai para a estrutura. Coloque o monitor sem pressão sobre o painel.
5. Aplique máscara preta removível nas regiões que precisam ocultar bordas e eletrônica, atrás do vidro e fora da área ativa. Não cubra ventilação do monitor.
6. Coloque o vidro nos calços e retenha por presilhas. Teste folga e evite parafusos pressionando a borda.
7. Instale a moldura IR à frente do vidro, alinhada à área ativa. Teste toque novamente.
8. Fixe câmera em suporte ajustável, com lente em furo próprio fora da área espelhada, e obturador na frente. Fixe PIR exposto e DHT22 em nicho externo ventilado.
9. Instale Pi, Uno e driver em suportes isolantes. Coloque perfil LED/difusor, fusível e chave da câmera. Separe e identifique cabos de 5 V e de 12 V.
10. Faça alívio de tração e teste acesso de manutenção. Só feche a tampa após o ensaio térmico e de reinicialização.

## 17 · Inicialização automática

O instalador de autostart é destinado ao Pi, executado como o usuário da sessão gráfica. Ele não deve rodar como root e não deve ser configurado no Windows ou no ambiente de nuvem.

```bash
cd ~/espelho-touch
bash scripts/ativar-autostart.sh
systemctl --user status espelho-touch.service
```

O script cria um serviço systemd do usuário para o Python e uma entrada XDG autostart para o Chromium. Não sobrescreve configurações existentes. Ativa o servidor imediatamente; o navegador abre no próximo login gráfico. Configure login automático no desktop pelo `sudo raspi-config` se esse for o comportamento desejado.

Em X11 o quiosque tenta desativar descanso de tela via xset; em Wayland faça o ajuste nas preferências do OS. Não suponha que `xset` funcione no Wayland. O monitor pode ter temporizador próprio de desligamento, que precisa ser conferido.

```bash
journalctl --user -u espelho-touch.service -n 80
systemctl --user restart espelho-touch.service
```

Para remover: desative o serviço, remova `~/.config/systemd/user/espelho-touch.service` e `~/.config/autostart/espelho-touch.desktop` e rode `systemctl --user daemon-reload`. Se usa `XDG_CONFIG_HOME`, adapte os caminhos. Não mova o projeto depois de ativar o serviço sem reinstalar os caminhos. Antes de atualizar o código, faça backup de `.env`, `data/` e `secrets.h`.

## 18 · Protocolo e comportamento em falhas

Uno → Pi: JSON por linha, 115200 baud, a cada dois segundos. Pi → Uno: `{"cmd":"light","mode":"manual","value":128}` ou modo `auto`. O firmware aceita somente um buffer curto de comando, rejeita linhas longas e limita o PWM. O protocolo é privado da conexão USB, não um endpoint de internet.

Pi → ESP32-CAM: GET `/capture`, com cabeçalho `X-Camera-Key`. O ESP32 retorna JPEG VGA ou erro. GET `/health` usa a mesma chave. O servidor Pi limita tamanho e tempo da resposta, bloqueia redirecionamento e só publica o arquivo estático da interface. `.env` e configurações privadas ficam fora dessa pasta pública.

Navegador → Pi: GET `/api/config`, GET `/api/state`, GET `/api/health`; POST `/api/config`, POST `/api/light`, POST `/api/camera`. Gravações exigem Host local e origem local compatível. O serviço escuta somente em 127.0.0.1. Não o exponha em 0.0.0.0 sem um projeto separado de autenticação e transporte seguro.

Se o USB cair, as leituras deixam de ser exibidas e o servidor tenta reconectar. O automático do Uno continua localmente; o manual expira em 15 minutos. Se o ESP32 cair, a janela exibe erro e o restante do painel continua. Clima sem internet usa o último dado de até 24 horas com identificação offline; sem cache, mostra indisponível. O horário precisa do relógio correto do Pi: verifique sincronização NTP ao ligar e depois de falta de energia.

## 19 · Testes antes de fechar a tampa

- Toque: acerte quatro cantos e centro, antes e depois de colocar o vidro; repita após girar a saída HDMI.
- DHT22: confira temperatura/umidade com instrumento de referência após estabilizar. Observe se o monitor aquece o nicho.
- PIR: aguarde 60 segundos, aproxime-se, afaste-se e confira o tempo de retenção. Não coloque vidro na frente da lente.
- LDR/LED: cubra o LDR, ilumine o sensor, teste manual 0/25/50/100%, confira corrente e temperaturas. Verifique se o próprio LED interfere na leitura.
- Câmera: com chave errada, a foto deve falhar; com chave correta, deve aparecer. Fechar a janela remove a exibição. Desligar a chave física deve impedir nova captura.
- Falhas: desconecte USB, desligue câmera e corte internet separadamente. O painel deve continuar e indicar o componente indisponível, sem simular sensores no modo normal.
- Persistência: salve agenda, reinicie Pi e confirme dados. Verifique que não aparece DEMONSTRAÇÃO na operação real.
- Ensaio térmico: acompanhe por pelo menos duas horas na condição de brilho/ambiente prevista, compare temperaturas com os limites dos fabricantes e ajuste ventilação antes de fechar.
- Energia: reinicie três vezes, confira login/quiosque, subtensão do Pi e recuperação da conexão com câmera/Arduino. Não interrompa alimentação durante gravação no microSD.

As verificações físicas acima são critérios de aceitação a executar com as peças compradas. Não foram feitas em hardware nesta entrega. Leia `docs/VALIDACAO.md` para separar o que foi executado em software do que ainda depende de bancada.

## 20 · Resolução de problemas

**Tela vazia:** confirme servidor com `http://localhost:8000/api/health`, feche outro servidor usando a porta 8000 e consulte o terminal. Se o problema surgiu após editar `data/settings.json`, restaure seu backup; o arquivo precisa de JSON válido e campos completos.

**Arduino desconectado:** confira cabo de dados, porta, permissão, monitor serial concorrente e placa correta. Abertura do USB pode reiniciar o Uno; espere alguns segundos. DHT indisponível com USB funcionando indica alimentação, DATA/pull-up ou sensor, não conexão com a câmera.

**Câmera sem foto:** confira Wi-Fi 2,4 GHz, IP reservado, chave idêntica, fonte estável e IO0 solto após gravação. O usuário deve estar na mesma LAN, sem isolamento de clientes impedindo Pi → ESP32. Mau contato no cabo FPC e queda de tensão são causas frequentes. Não desative proteções de brownout para mascarar fonte ruim.

**Touch deslocado:** confira área ativa, alinhamento, associação à saída HDMI e rotação no sistema. Remova obstruções dos emissores IR. Luz solar direta e sujeira na borda podem atrapalhar alguns modelos.

**Reflexo forte/texto fraco:** teste outra iluminação, amostra óptica apropriada e brilho do monitor dentro do limite térmico. O software não compensa um espelho opaco demais. **LED oscilando:** afaste o LDR do LED e calibre os limiares em `firmware/arduino_uno/src/main.cpp`.

**Compilação bloqueada:** o PlatformIO precisa baixar ferramentas e bibliotecas dos servidores oficiais. Não desligue TLS nem verificação para contornar falhas. No ambiente desta entrega, o registro do PlatformIO estava bloqueado pela rede; os binários não foram gerados. Em sua rede, compile os dois alvos e confira placa/porta antes de gravar.

## 21 · Arquivos, referências e próximos passos

- `app/`: aplicação Python e interface touch.
- `firmware/arduino_uno/`: sensores e PWM; plataforma atmelavr 5.1.0, DHT 1.4.6, Unified Sensor 1.1.15.
- `firmware/esp32_cam/`: AI Thinker e OV2640; plataforma espressif32 6.9.0, framework Arduino incluído pela plataforma.
- `hardware/`: compras, medidas, CAD, DXF e geometria de referência.
- `scripts/`: instalação, quiosque, autostart e geração das imagens/PDF.
- `tests/`: validação de API, persistência, modos demo/normal e erros de dispositivos.

Referências oficiais usadas para a arquitetura e conferência de pinagem:

- [Raspberry Pi 4 Model B](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/).
- [Documentação Raspberry Pi](https://www.raspberrypi.com/documentation/).
- [Arduino Uno R3](https://docs.arduino.cc/hardware/uno-rev3/).
- [Exemplo oficial ESP32 CameraWebServer, versão 2.0.17](https://github.com/espressif/arduino-esp32/tree/2.0.17/libraries/ESP32/examples/Camera/CameraWebServer).
- [DHT da Adafruit](https://learn.adafruit.com/dht/overview).
- [PlatformIO](https://docs.platformio.org/).
- [Open-Meteo](https://open-meteo.com/en/docs).
- [IRLZ44N / Infineon](https://www.infineon.com/part/IRLZ44N).

Este é um projeto executável de referência com documentação de montagem, não um produto fisicamente homologado. O próximo marco é selecionar as peças reais, compilar/gravar os controladores, medir o conjunto e completar os testes de bancada antes da fabricação definitiva. A implantação elétrica de rede e a capacidade de carga da parede não são dimensionadas por este manual.
