# PetPlanta Web

App web em Python (Flask) que mostra um bichinho-planta animado cujo humor
muda de acordo com as leituras do Arduino (`PetPlantaARDUINO.ino`): luz, umidade
do solo e temperatura.

Estados implementados: **feliz**, **seca** (solo seco), **doente** (calor
extremo), **com frio**, **dormindo** (sem luz), **aproveitando o sol**
(óculos, luz forte) e **modo festa** (toca quando aperta o botão de música).
Cada estado tem um GIF em loop; ao trocar de estado, toca uma vez um GIF de
transição antes do novo loop. Tem também um **estado crítico** (ver seção 5)
que liga um alarme físico (LED + buzzer) no Arduino.

Toda a arte é gerada por código (Pillow) em `generate_assets.py` — são
placeholders para você já ter o app funcionando hoje. Quando quiser, troque os
GIFs em `static/gifs/` pela arte final, mantendo os mesmos nomes de arquivo
(`loop_<estado>.gif` e `transition_<de>_to_<para>.gif`).

## 1. Instalar dependências

No computador onde o Arduino está conectado (ex: seu Windows):

```bash
cd webapp
pip install -r requirements.txt
```

## 2. (Re)gerar os GIFs

Já vêm gerados, mas se editar `generate_assets.py` rode de novo:

```bash
python generate_assets.py
```

Isso cria `static/gifs/loop_*.gif`, `static/gifs/transition_*_to_*.gif` e
`static/preview.png` (uma grade com 1 frame de cada estado, útil pra conferir
a arte rapidamente).

## 3. Rodar o app

```bash
python app.py
```

Abra **http://localhost:5000** no navegador.

O app tenta achar automaticamente uma porta serial com Arduino conectado. Se
não achar (ou o Arduino não estiver plugado), ele cai em **modo simulação**
automaticamente, com dados fictícios, só para você ver a interface funcionando.

### Apontar manualmente para a porta serial

Se a detecção automática não pegar a porta certa, defina antes de rodar:

```bash
# Windows (cmd)
set PETPLANTA_PORT=COM6
python app.py

# Windows (PowerShell)
$env:PETPLANTA_PORT="COM6"
python app.py
```

A porta deve ser a mesma que aparece no Arduino IDE (Ferramentas > Porta).
O baud rate esperado é `9600` (igual ao `Serial.begin(9600)` no `.ino`); se
mudar isso no sketch, defina `PETPLANTA_BAUD` também.

**Importante:** o Arduino IDE precisa estar com o Serial Monitor **fechado**
enquanto o app Python estiver rodando — só um programa pode usar a porta
serial por vez.

## 4. Calibrar os limites (thresholds)

Os valores que definem "solo seco", "sem luz", "sol forte", "frio" e "calor"
estão em `config.py`, com comentários explicando cada um. Os sensores
analógicos (luz e solo) variam bastante de fiação para fiação, então:

1. Rode o app e observe os valores impressos no terminal (cada leitura é logada).
2. Anote o valor de **Solo** com terra seca e com terra recém molhada.
3. Anote o valor de **Luz** no escuro e com luz forte/sol direto.
4. Ajuste `LUZ_ESCURO_MAX`, `LUZ_ENSOLARADO_MIN`, `SOLO_SECO_MAX` em `config.py`
   de acordo com o que você observou (se o comportamento parecer invertido,
   ou seja, mais luz = valor menor, é só inverter os sinais `<=`/`>=` em
   `mood.py`).

A temperatura vem do DHT11 e não precisa de calibração.

Em vez de editar `config.py` na mão, você também pode ajustar esses mesmos
limites (e os do estado crítico) direto no navegador — ver seção 6.

## 5. Estado crítico (LED + buzzer de alarme)

Além dos GIFs, o Arduino tem um alarme físico pra te avisar quando a planta
precisa de atenção urgente. A planta entra em **estado crítico** quando
qualquer uma destas acontece:

- Solo seco continuamente por mais tempo que `CRITICO_DURACAO_SECA`;
- Sem luz (dormindo) continuamente por mais tempo que `CRITICO_DURACAO_DORMINDO`;
- Temperatura instantânea ≥ `CRITICO_TEMP_MAX`;
- Temperatura instantânea ≤ `CRITICO_TEMP_MIN`.

Esses 4 limites estão em `config.py` (valores de fábrica: 24h / 1h / 40°C /
10°C) e podem ser ajustados a qualquer momento — direto pela tela de
configurações (seção 6) ou editando o arquivo, inclusive reduzindo
temporariamente as durações pra testar o alarme sem esperar horas de verdade.

Uma vez crítico, o estado **só volta ao normal quando a planta estiver
feliz ou aproveitando o sol** — mesmo que a condição que disparou o alarme
já tenha passado, ele continua tocando se a planta estiver, por exemplo,
com frio ou dormindo. Enquanto crítico, a tela mostra o GIF de **doente**.

O app Python detecta o estado crítico e manda `CRITICO:1` (liga) ou
`CRITICO:0` (desliga) pela serial pro `.ino`, que acende o LED da **porta
10** e toca um alarme intermitente no buzzer (porta 11) até receber o
comando pra desligar. **Depois de atualizar o `.ino`, é preciso reenviar o
sketch pro Arduino** pela Arduino IDE pra essa parte funcionar.

## 5.1. LEDs de status (verde/amarelo/vermelho)

Além do alarme da seção 5, o `.ino` tem 10 LEDs simples (os mesmos que já
piscavam durante a música) agrupados por cor, que mostram o humor da planta
de uma olhada, sem precisar abrir o navegador:

- **Verde** (pinos `6`, `3`, `A4`, `A7`): aceso quando o mood é **feliz** ou
  **aproveitando o sol**.
- **Amarelo** (pinos `5`, `2`, `A6`): aceso quando o mood é **seca**,
  **com frio** ou **doente** (calor forte, mas ainda sem ter virado estado
  crítico).
- **Vermelho** (pinos `4`, `A3`, `A5`): aceso sempre que o **estado crítico**
  (seção 5) estiver ativo — tem prioridade sobre tudo, mesmo que o mood
  ambiental no momento seja outro.
- **Todos apagados**: quando o mood é **dormindo** (sem luz), ou enquanto o
  Arduino ainda não recebeu nenhuma informação do app Python (logo depois
  de ligar/resetar).

(Pinos pensados pra uma placa com analógicos extras, como o **Arduino Mega**
— em placas como o Nano, os pinos `A6`/`A7` são só entrada analógica e não
servem como saída digital pra LED.)

Só um grupo de cor fica aceso por vez. O app Python manda o mood ambiental
pela serial com `MOOD:<nome>\n` (ex: `MOOD:feliz`, `MOOD:seca`) sempre que
ele muda — separado do `CRITICO:1/0` da seção 5, que continua controlando o
LED de alarme (porta 10) e tem prioridade sobre a cor dos LEDs de status. Se
o Arduino for desconectado e reconectado (ou resetado), o app reenvia o
último estado conhecido assim que a conexão serial volta, pra não deixar os
LEDs desincronizados.

Durante o **modo festa** (música tocando), esses mesmos 10 LEDs piscam
aleatoriamente como já faziam antes — o comportamento de cor volta a valer
automaticamente assim que a música termina.

O sketch também usa `analogRead()` num pino solto pra gerar uma semente
aleatória pro piscar da música (`randomSeed`, no `setup()`); como o `A5`
passou a ter um LED, essa leitura agora usa o `A15` (livre no Mega) em vez
de `A5`.

## 6. Tela de configurações (editar limiares pelo navegador)

Clique no ícone de engrenagem (⚙️) no canto superior direito da página pra
abrir uma janela com todos os limiares editáveis:

- **Limiares de humor**: luz "sem luz"/"sol forte", solo "seco", temperatura
  "frio"/"doente" — os mesmos 5 valores da seção 4.
- **Detecção de rega**: o limiar usado pela seção 7.
- **Estado crítico**: as 4 regras do alarme da seção 5 (durações em horas e
  as temperaturas críticas máxima/mínima).

Ao clicar em **Salvar**:

- os valores passam a valer **imediatamente** (sem precisar reiniciar o
  `app.py` nem o Arduino) — `mood.py` e `serial_reader.py` sempre leem o
  valor mais recente de `config.py`;
- o formulário valida antes de aplicar (ex: não deixa "sem luz" ser maior ou
  igual a "sol forte"); se algo estiver inválido, nada é alterado e a
  mensagem de erro aparece no topo da janela;
- os valores são gravados em `config_overrides.json` (criado automaticamente
  na pasta `webapp/`), que é relido sozinho na próxima vez que você rodar
  `python app.py` — ou seja, a alteração **persiste** entre reinícios. Pra
  voltar aos valores de fábrica de `config.py`, basta apagar esse arquivo.

## 7. Detecção de rega ("Última rega Xh Ym atrás")

O card de **umidade do solo** mostra ha quanto tempo a planta foi regada pela
última vez. A detecção é automática: toda vez que a leitura de Solo **sobe**
e cruza `REGA_DETECTADA_MIN` (config.py, padrão `400`) — ou seja, estava
abaixo e passou a estar igual ou acima — o app entende que alguém regou a
planta agora e guarda o horário.

Só conta a transição de subida, não fica "re-regando" enquanto o solo
continuar molhado, e o contador não desaparece quando o solo seca de novo —
ele só atualiza na próxima rega detectada. Se a planta ainda não foi regada
desde que o `app.py` foi iniciado, o contador fica escondido.

Esse limite não tem campo na tela de configurações (seção 6) por enquanto —
pra mudar o valor de detecção, edite `REGA_DETECTADA_MIN` em `config.py`.

## 8. Painel de simulação (controlar os dados fictícios)

Quando o app está em **modo simulação** (badge "modo simulação" no topo, sem
Arduino conectado), aparece um segundo ícone no cabeçalho — um alvo (🎯) —
que abre a tela de simulação. Esse ícone só aparece nesse modo; com um
Arduino real conectado ele fica escondido, já que os dados vêm do hardware.

A tela tem dois modos:

- **Aleatório**: comportamento padrão de sempre — os valores de luz, solo e
  temperatura variam sozinhos num passeio aleatório suave, só pra a interface
  não ficar vazia.
- **Manual**: você digita os valores exatos de luz, solo e temperatura nos
  campos da tela e clica em **Aplicar** — o app passa a usar exatamente esses
  números (sem variação automática) até você mudar de novo ou trocar de volta
  pro modo aleatório. Útil pra testar um cenário específico (por exemplo,
  forçar "solo seco" pra ver o alarme de estado crítico disparar, sem
  precisar esperar o passeio aleatório chegar lá por acaso).

Trocar de modo ou aplicar novos valores tem efeito **imediato**, sem precisar
reiniciar o `app.py`. Voltar de manual pra aleatório continua o passeio a
partir do último valor usado (sem pulo brusco). No modo manual, o "modo
festa" de demonstração (que liga sozinho a cada ~30s na simulação aleatória)
fica desligado, pra não interferir nos valores que você está controlando de
propósito. Esses valores **não** são salvos em `config_overrides.json` —
voltam ao padrão (modo aleatório) se o `app.py` for reiniciado.

## Estrutura

```
webapp/
  app.py                  -> servidor Flask (rotas /, /api/state, /api/config, /api/simulation)
  config.py               -> thresholds (com overrides editaveis), porta serial, baud rate
  config_overrides.json   -> gerado ao salvar a tela de configuracoes (nao versionar)
  mood.py                 -> regra que decide o humor a partir dos sensores
  serial_reader.py        -> thread que lê a serial (ou simula) e mantém o estado
  generate_assets.py      -> gera os GIFs proceduralmente com Pillow
  templates/index.html    -> página (inclui os modais de configuracoes e simulacao)
  static/css/style.css    -> estilo
  static/js/app.js        -> polling de /api/state, troca de gif e tela de configuracoes
  static/gifs/            -> GIFs gerados
```

## Prioridade dos estados

Quando mais de uma condição é verdadeira ao mesmo tempo, a ordem de
prioridade final (decidida em `serial_reader.py`, que combina `mood.py` com
os estados de festa e crítico) é:

1. **Modo festa** — toca enquanto o botão de música do Arduino estiver ativo, ganha de tudo.
2. **Estado crítico** — alarme físico ligado (ver seção 5); mostra o GIF de doente.
3. **Dormindo** (sem luz) — se está escuro, a planta dorme independente do resto.
4. **Com frio**
5. **Doente** (calor extremo)
6. **Seca** (solo seco)
7. **Aproveitando o sol** (luz forte, sem nenhum problema acima)
8. **Feliz** (nada de especial)
