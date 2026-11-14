# Evidências de validação — 14/11/2026

## Executado

- Oito testes de servidor/API passaram: assets, persistência e releitura em nova instância, rejeição de configuração inválida, origem de escrita, arquivos privados, demonstração/LED, desconexão sem leituras fictícias, captura explícita e telemetria expirada.
- Dois testes de integração também passaram com pyserial instalado: porta serial virtual POSIX (receber telemetria e enviar comando) e câmera HTTP local simulada (cabeçalho de chave e repasse JPEG). Total: dez testes, nenhum ignorado nessa execução. Esses testes não simulam os circuitos elétricos nem validam a qualidade da imagem.
- Verificação de sintaxe JavaScript e scripts Bash sem erro.
- Aplicação iniciada em modo demo na porta 8010 e validada no Chromium headless: edição de nome/agenda, salvamento, luz simulada, temporizador com pausa, erro de câmera ausente, quatro resoluções sem transbordamento horizontal e ausência de erros JavaScript.
- Captura de interface em 1080 × 1920 salva em `docs/imagens/painel-demonstracao.png`; valores internos são simulados e identificados. A captura mostra clima externo indisponível.
- OpenSCAD exportou o contorno frontal DXF e a frente STL sem erro de geometria. Essas exportações não comprovam resistência ou encaixe nas peças a comprar.
- Pinagem AI Thinker e campos de configuração da câmera conferidos no exemplo/header oficial do Arduino-ESP32 2.0.17.

## Bloqueado ou não realizado

- `pio run` dos dois alvos não chegou à compilação: instalação de `atmelavr@5.1.0` e `espressif32@6.9.0` falhou em HTTPClientError. Uma consulta direta ao registro `api.registry.platformio.org` produziu erro de proxy; a política da máquina permite apenas os destinos configurados e não inclui esse domínio.
- Não há binários `.hex`/`.bin` entregues. Compile localmente, com a rede liberada, antes de gravar. Não foram usados pacotes sem verificação ou desativação de TLS para contornar o bloqueio.
- Consulta ao serviço Open-Meteo depende de rede; no ambiente desta conversa o domínio ainda não estava aplicado à política ativa. O tratamento de indisponibilidade foi exercitado; não se afirma validação de uma previsão real nesta entrega.
- Nenhuma placa, câmera, monitor touch, vidro, fonte, fixação ou estrutura física estava disponível. Upload de firmware, calibração touch, óptica, montagem, carga, temperatura, corrente, estabilidade e autostart no Pi são testes de aceitação pendentes.

## Como repetir

```bash
python -m unittest discover -s tests -v
node --check app/static/app.js
bash -n scripts/instalar-pi.sh scripts/quiosque.sh scripts/ativar-autostart.sh
pio run -d firmware/arduino_uno
pio run -d firmware/esp32_cam
```

Antes do último comando, copie e configure `secrets.example.h` como `secrets.h`. Os testes Python usam diretório e porta temporários, sem tocar nos dados pessoais. O modo demo não atesta o comportamento dos circuitos físicos.
