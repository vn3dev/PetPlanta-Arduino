# PetPlanta Web

App web feito em Python, com o Flask, que mostra um bichinho-planta animado.
O humor dele muda conforme as leituras do Arduino no arquivo
`PetPlantaARDUINO.ino`: luz, umidade do solo e temperatura.

Os humores que existem são: feliz, seca quando o solo está seco, doente
quando está muito quente, com frio, dormindo quando não tem luz, aproveitando
o sol quando a luz está forte, e modo festa quando você aperta o botão de
música. Cada humor tem um GIF que fica repetindo. Quando troca de humor,
toca uma vez um GIF de passagem antes de começar o novo. Tem também o estado
crítico, explicado na seção 5, que liga um alarme de verdade no Arduino, com
LED e buzzer.

## 1. Instalar o que o app precisa

```bash
cd webapp
pip install -r requirements.txt
```
## 2. Rodar o app

```bash
python app.py
```

Abra **http://localhost:5000** no navegador.

O app tenta achar sozinho a porta serial onde o Arduino está ligado. Se não
achar, ou se o Arduino não estiver plugado, ele entra no modo simulação
sozinho. Nesse modo ele usa dados de mentira, só pra você ver a interface
funcionando.

### Escolher a porta serial na mão

Se o app não achar a porta certa sozinho, escolha você mesmo antes de rodar:

```bash
# Windows cmd
set PETPLANTA_PORT=COM6
python app.py

# Windows PowerShell
$env:PETPLANTA_PORT="COM6"
python app.py
```

A porta tem que ser a mesma que aparece no Arduino IDE, no menu Ferramentas,
em Porta. O baud rate certo é `9600`, igual ao que está escrito no `.ino` em
`Serial.begin(9600)`. Se você mudar esse número no programa do Arduino,
escolha também o `PETPLANTA_BAUD`.

**Importante:** o Serial Monitor do Arduino IDE precisa ficar **fechado**
enquanto o app Python estiver rodando. Só um programa pode usar a porta
serial de cada vez.

## 3. Ajustar os limites

Os valores que dizem o que é "solo seco", "sem luz", "sol forte", "frio" e
"calor" estão no arquivo `config.py`, com comentários explicando cada um. Os
sensores de luz e de solo mudam bastante de uma montagem pra outra, então:

1. Rode o app e olhe os valores que aparecem no terminal. Cada leitura
   aparece lá.
2. Anote o valor do **Solo** com a terra seca e com a terra acabada de molhar.
3. Anote o valor da **Luz** no escuro e com luz forte ou sol direto.
4. Mude `LUZ_ESCURO_MAX`, `LUZ_ENSOLARADO_MIN` e `SOLO_SECO_MAX` no `config.py`
   conforme o que você anotou. Se o comportamento parecer ao contrário, ou
   seja, mais luz dando um valor menor, é só inverter os sinais `<=` e `>=` no
   arquivo `mood.py`.

A temperatura vem do sensor DHT11 e não precisa de ajuste.

Em vez de mexer no `config.py` na mão, você também pode mudar esses mesmos
limites, e os do estado crítico, direto no navegador.

## 4. Estado crítico, com LED e buzzer de alarme

Além dos GIFs, o Arduino tem um alarme de verdade pra te avisar quando a
planta precisa de ajuda urgente. A planta entra em **estado crítico** quando
acontece qualquer uma destas coisas:

- Solo seco sem parar por mais tempo que `CRITICO_DURACAO_SECA`.
- Sem luz, ou seja, dormindo, sem parar por mais tempo que
  `CRITICO_DURACAO_DORMINDO`.
- Temperatura no momento igual ou acima de `CRITICO_TEMP_MAX`.
- Temperatura no momento igual ou abaixo de `CRITICO_TEMP_MIN`.

Esses 4 limites estão no `config.py`. Os valores que já vêm prontos são 24
horas, 1 hora, 40°C e 10°C. Você pode mudar eles a qualquer hora, pela tela
de configurações da seção 6 ou mexendo no arquivo. Dá até pra diminuir as
durações por um tempinho pra testar o alarme sem precisar esperar horas de
verdade.

Depois que a planta fica crítica, o estado **só volta ao normal quando a
planta estiver feliz ou aproveitando o sol**. Mesmo que o problema que ligou
o alarme já tenha passado, ele continua tocando se a planta estiver, por
exemplo, com frio ou dormindo. Enquanto está crítica, a tela mostra o GIF de
doente.

O app Python percebe o estado crítico e manda `CRITICO:1` pra ligar ou
`CRITICO:0` pra desligar, pela serial, pro `.ino`. O `.ino` acende o LED da
porta 10 e toca um alarme que fica ligando e desligando no buzzer da porta
11, até receber o aviso pra parar. **Depois de mudar o `.ino`, você precisa
enviar o programa de novo pro Arduino** pelo Arduino IDE pra essa parte
funcionar.

## 4.1. LEDs de status, verde, amarelo e vermelho

Além do alarme da seção 5, o `.ino` tem 10 LEDs simples, os mesmos que já
piscavam durante a música, juntados por cor. Eles mostram o humor da planta
num olhar só, sem precisar abrir o navegador:

- **Verde**, nos pinos `6`, `3`, `A4` e `A7`: aceso quando o humor é feliz
  ou aproveitando o sol.
- **Amarelo**, nos pinos `5`, `2` e `A6`: aceso quando o humor é seca, com
  frio ou doente. Aqui doente quer dizer calor forte, mas ainda sem ter
  virado estado crítico.
- **Vermelho**, nos pinos `4`, `A3` e `A5`: aceso sempre que o estado crítico
  da seção 5 estiver ligado. Ele vem na frente de tudo, mesmo que o humor do
  ambiente naquele momento seja outro.
- **Todos apagados**: quando o humor é dormindo, ou seja, sem luz, ou
  enquanto o Arduino ainda não recebeu nenhum aviso do app Python, logo
  depois de ligar ou resetar.

Esses pinos foram pensados pra uma placa com mais entradas, como o **Arduino
Mega**. Em placas como o Nano, os pinos `A6` e `A7` só servem pra ler e não
podem acender LED.

Só fica aceso um grupo de cor de cada vez. O app Python manda o humor do
ambiente pela serial com `MOOD:<nome>`, por exemplo `MOOD:feliz` ou
`MOOD:seca`, toda vez que ele muda. Isso é separado do `CRITICO:1/0` da seção
5, que continua mandando no LED de alarme da porta 10 e vem na frente da cor
dos LEDs de status. Se o Arduino for desligado e ligado de novo, ou resetado,
o app manda outra vez o último estado conhecido assim que a serial volta, pra
não deixar os LEDs errados.

Durante o **modo festa**, com a música tocando, esses mesmos 10 LEDs piscam
de forma aleatória, como já faziam antes. As cores voltam a valer sozinhas
assim que a música acaba.

O programa também faz uma leitura num pino solto pra criar um número
aleatório pro piscar da música. Isso é o `randomSeed`, dentro do `setup()`.
Como o `A5` passou a ter um LED, essa leitura agora usa o `A15`, que está
livre no Mega, em vez do `A5`.

## 5. Tela de configurações, mudar os limites pelo navegador

Clique no ícone de engrenagem ⚙️ no canto de cima, à direita da página, pra
abrir uma janela com todos os limites que dá pra mudar:

- **Limites de humor**: a luz "sem luz" e "sol forte", o solo "seco", a
  temperatura "frio" e "doente". São os mesmos 5 valores da seção 4.
- **Detecção de rega**: o limite usado pela seção 7.
- **Estado crítico**: as 4 regras do alarme da seção 5, com as durações em
  horas e as temperaturas crítica máxima e mínima.

Quando você clica em **Salvar**:

- os valores passam a valer **na hora**, sem precisar reiniciar o `app.py`
  nem o Arduino. O `mood.py` e o `serial_reader.py` sempre leem o valor mais
  novo do `config.py`.
- o formulário confere os dados antes de aplicar. Por exemplo, ele não deixa
  "sem luz" ser maior ou igual a "sol forte". Se algo estiver errado, nada
  muda e a mensagem de erro aparece no topo da janela.
- os valores são salvos no arquivo `config_overrides.json`, criado sozinho na
  pasta `webapp/`. Esse arquivo é lido de novo na próxima vez que você rodar
  o `python app.py`, ou seja, a mudança **fica guardada** mesmo depois de
  reiniciar. Pra voltar aos valores de fábrica do `config.py`, é só apagar
  esse arquivo.

## 6. Detecção de rega, "Última rega Xh Ym atrás"

O card de umidade do solo mostra há quanto tempo a planta foi regada pela
última vez. Isso funciona sozinho: toda vez que a leitura do Solo **sobe** e
passa do `REGA_DETECTADA_MIN`, que no `config.py` vem como `400`, ou seja,
estava abaixo e passou a ficar igual ou acima, o app entende que alguém regou
a planta agora e guarda a hora.

Só conta a subida. Ele não fica "re-regando" enquanto o solo continua
molhado, e o contador não some quando o solo seca de novo. Ele só muda na
próxima rega que for percebida. Se a planta ainda não foi regada desde que
você abriu o `app.py`, o contador fica escondido.

Esse limite ainda não tem campo na tela de configurações da seção 6. Pra
mudar o valor da detecção, mexa no `REGA_DETECTADA_MIN` no `config.py`.

## 7. Painel de simulação, controlar os dados de mentira

Quando o app está em **modo simulação**, com o aviso "modo simulação" no topo
e sem Arduino ligado, aparece um segundo ícone no cabeçalho, um alvo 🎯, que
abre a tela de simulação. Esse ícone só aparece nesse modo. Com um Arduino de
verdade ligado ele fica escondido, já que os dados vêm do aparelho.

A tela tem dois modos:

- **Aleatório**: o jeito de sempre. Os valores de luz, solo e temperatura
  mudam sozinhos aos poucos, de um jeito calmo, só pra a interface não ficar
  vazia.
- **Manual**: você digita os valores exatos de luz, solo e temperatura nos
  campos da tela e clica em **Aplicar**. O app passa a usar esses números
  certinhos, sem mudar sozinho, até você trocar de novo ou voltar pro modo
  aleatório. Serve pra testar um caso específico. Por exemplo, forçar "solo
  seco" pra ver o alarme do estado crítico disparar, sem ter que esperar os
  valores aleatórios chegarem lá por sorte.

Trocar de modo ou aplicar valores novos tem efeito **na hora**, sem precisar
reiniciar o `app.py`. Quando você volta do manual pro aleatório, a variação
continua a partir do último valor usado, sem dar um salto brusco. No modo
manual, o modo festa de demonstração, que liga sozinho mais ou menos a cada
30 segundos na simulação aleatória, fica desligado, pra não atrapalhar os
valores que você está controlando de propósito. Esses valores **não** são
salvos no `config_overrides.json`. Eles voltam ao padrão, que é o modo
aleatório, se você reiniciar o `app.py`.

## Estrutura

```
webapp/
  app.py                  -> servidor Flask, com as rotas /, /api/state, /api/config, /api/simulation
  config.py               -> limites editaveis, porta serial, baud rate
  config_overrides.json   -> criado ao salvar a tela de configuracoes; nao colocar no controle de versao
  mood.py                 -> regra que decide o humor a partir dos sensores
  serial_reader.py        -> parte que le a serial, ou simula, e guarda o estado
  generate_assets.py      -> gera os GIFs sozinho com a biblioteca Pillow
  templates/index.html    -> pagina, com as janelas de configuracoes e simulacao
  static/css/style.css    -> estilo
  static/js/app.js         -> fica perguntando o /api/state, troca o gif e cuida da tela de configuracoes
  static/gifs/            -> GIFs gerados
```

## Ordem de prioridade dos estados

Quando mais de uma coisa é verdade ao mesmo tempo, a ordem que decide qual
humor vale fica assim. Ela é decidida no `serial_reader.py`, que junta o
`mood.py` com os estados de festa e crítico:

1. **Modo festa**: toca enquanto o botão de música do Arduino estiver ligado.
   Ganha de todos.
2. **Estado crítico**: alarme de verdade ligado, visto na seção 5. Mostra o
   GIF de doente.
3. **Dormindo**, sem luz: se está escuro, a planta dorme, não importa o resto.
4. **Com frio**.
5. **Doente**, calor muito forte.
6. **Seca**, solo seco.
7. **Aproveitando o sol**: luz forte, sem nenhum problema acima.
8. **Feliz**: nada de especial.
