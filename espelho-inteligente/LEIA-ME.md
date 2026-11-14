# Espelho inteligente · Raspberry Pi 3

Painel leve, em português, com fundo preto para um monitor atrás de espelho semitransparente. Python serve arquivos locais; Chromium exibe o painel. Não usa frameworks, banco de dados, fontes externas ou dependências pip/npm.

## Recursos

- Relógio, segundos, data e saudação no fuso configurado.
- Temperatura externa, sensação térmica, umidade e previsão de quatro dias pela Open-Meteo (sem chave de API).
- Agenda manual: próximos cinco compromissos, ocultando os que já passaram.
- Mensagens personalizadas em rotação a cada 30 segundos.
- Página de configuração local, gravação persistente e atômica em `config.json`.
- Clima atualizado a cada 15 minutos; em falha, última consulta identificada como offline por até 24 horas. Sem cache válido, mostra indisponibilidade. Relógio e agenda continuam funcionando.
- Tela cheia e scripts de inicialização para sessão gráfica do Raspberry Pi OS.

## Executar neste ambiente ou no computador

Requer Python 3.9 ou superior com base de fusos IANA (validado aqui com Python 3.12.14).

```bash
cd /workspace/13-03/espelho-inteligente
bash scripts/iniciar.sh
```

No próprio computador que executa o servidor, abra `http://127.0.0.1:8000`. Configure em `http://127.0.0.1:8000/config.html`. O servidor escuta apenas em loopback; não é um serviço de acesso remoto. No ambiente em nuvem, essas URLs servem para verificações internas, sem link de prévia pública.

Nome inicial: “Você”. Localização inicial: São Paulo. Mude **cidade, latitude, longitude e fuso** nas configurações. O nome da cidade é apenas um rótulo. Datas da agenda seguem o fuso escolhido, independentemente do fuso do sistema. Não há integração com calendários externos nem eventos recorrentes.

As configurações ficam em `config.json`, ignorado pelo Git. Faça backup desse arquivo antes de mover o projeto. Para restaurar os padrões, pare o servidor e mova esse arquivo para um backup. Não há dados fictícios de agenda nem previsão simulada.

## Instalar no Raspberry Pi 3

Use Raspberry Pi OS **com desktop**, preferencialmente uma versão atual. Tenha Raspberry Pi 3, fonte adequada, microSD, conexão de rede para o clima, monitor HDMI, espelho semitransparente e moldura ventilada. Monte e ventile o conjunto conforme as especificações dos fabricantes.

1. Copie esta pasta para um local permanente do usuário, por exemplo `~/espelho-inteligente`.
2. Instale os componentes usando o gerenciador oficial:

   ```bash
   sudo apt update
   sudo apt install -y python3 chromium tzdata
   ```

   Se sua versão do Raspberry Pi OS oferecer `chromium-browser` em vez de `chromium`, instale esse pacote. Os scripts aceitam ambos. Não é necessário executar o navegador como root.

3. Dentro da pasta, execute `bash scripts/iniciar.sh`. Em outro terminal da sessão gráfica, execute `bash scripts/quiosque.sh`. O quiosque espera o servidor responder antes de abrir.
4. Configure suas informações pelo navegador. Use `F11` para sair do modo tela cheia ou `Alt+F4` para fechar o navegador. No painel, a tecla `F` alterna a tela cheia do navegador; os controles aparecem ao mover o mouse ou receber foco por teclado.

## Iniciar automaticamente

Execute **no Raspberry Pi**, como o usuário que faz login no desktop:

```bash
cd ~/espelho-inteligente
bash scripts/instalar-autostart.sh
```

O instalador cria `~/.config/systemd/user/espelho.service` e `~/.config/autostart/espelho.desktop` (ou em `XDG_CONFIG_HOME`, se definido), sem sobrescrever arquivos existentes. Ativa o servidor imediatamente e abre Chromium no próximo login gráfico. Configure login automático no desktop pelo `raspi-config` se quiser iniciar sem intervenção após ligar. A inicialização do navegador depende do suporte XDG autostart da sessão gráfica.

Em sessões X11, o script tenta desativar o descanso de tela usando `xset`. Em Wayland, desative o apagamento de tela nas preferências do Raspberry Pi OS; não depende de `xset`. Configure rotação e resolução do monitor pelas preferências do sistema. O painel usa orientação vertical, como um celular. No computador, fica centralizado em uma faixa estreita; no celular, aproveita a largura da tela. Para um monitor fisicamente girado, configure também a orientação vertical nas preferências do sistema operacional.

Diagnóstico e remoção (no Pi):

```bash
systemctl --user status espelho.service
journalctl --user -u espelho.service -n 50
systemctl --user disable --now espelho.service
rm ~/.config/systemd/user/espelho.service ~/.config/autostart/espelho.desktop
systemctl --user daemon-reload
```

Se usar `XDG_CONFIG_HOME`, ajuste os caminhos da remoção. Não mova a pasta após instalar o autostart; remova e reinstale a configuração se mudar o local. O instalador não é executado na nuvem, pois depende da sessão gráfica real do Pi.

## Validação

```bash
python3 -m unittest discover -s tests -v
node --check static/app.js
node --check static/config.js
bash -n scripts/iniciar.sh scripts/quiosque.sh scripts/instalar-autostart.sh
```

Os testes usam porta temporária e diretório temporário: verificam páginas, API, persistência, validação e bloqueio de gravação de outra origem, sem tocar na configuração pessoal. Node é opcional para conferir a sintaxe; não é necessário para executar o sistema.

A consulta externa de clima precisa de HTTPS para `api.open-meteo.com`. Se houver restrições de rede, libere esse domínio. A precisão depende do provedor; estes dados não vêm de um sensor interno. A montagem física, o desempenho e o autostart precisam de uma verificação final no Raspberry Pi 3.
