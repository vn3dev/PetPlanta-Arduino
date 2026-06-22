# -*- coding: utf-8 -*-
"""
Configuracoes do PetPlanta Web.

IMPORTANTE - CALIBRACAO:
Os valores abaixo sao chutes razoaveis para os sensores tipicos (LDR e sensor
resistivo de umidade de solo) ligados como divisor de tensao num Arduino.
Cada sensor/fiacao se comporta de um jeito diferente, entao quase certamente
voce vai precisar ajustar esses numeros depois de observar os valores reais
no Serial Monitor do Arduino (ou no terminal onde este app roda, que tambem
imprime cada leitura recebida).

Como calibrar:
1. Rode o app (veja README.md) e olhe os valores "Luz" e "Solo" no console.
2. Anote o valor de Solo com terra seca e com terra bem molhada (regada).
3. Anote o valor de Luz no escuro (tampando o LDR) e com luz forte/sol direto.
4. Ajuste as constantes abaixo de acordo.
"""

import os

# --- Conexao serial com o Arduino ---
# Deixe None para o app tentar auto-detectar uma porta com Arduino conectado.
# No Windows normalmente e algo como "COM3", "COM4", etc.
# Fixado em COM6 (porta confirmada do seu Arduino). Pode trocar aqui ou via
# variavel de ambiente PETPLANTA_PORT antes de rodar "python app.py".
SERIAL_PORT = os.environ.get("PETPLANTA_PORT") or "COM6"
SERIAL_BAUD = int(os.environ.get("PETPLANTA_BAUD", "9600"))  # igual ao Serial.begin(9600) do .ino

# Se nao conseguir abrir a porta serial em ate N segundos, cai em modo simulacao
# (dados ficticios variando aleatoriamente) so para a interface nao ficar vazia.
SERIAL_CONNECT_TIMEOUT = 5

# --- Thresholds dos sensores ---
# Luz (LDR), leitura analogica 0-1023. Assumindo: quanto MAIOR o valor, MAIS luz.
# Se no seu circuito for o contrario (maior valor = mais escuro), inverta os
# sinais de comparacao em mood.py ou troque a fiacao do LDR.
LUZ_ESCURO_MAX = 400       # abaixo disso: considera "sem luz" (dormindo)
LUZ_ENSOLARADO_MIN = 800   # acima disso: considera "sol forte" (oculos)

# Solo (sensor resistivo), leitura analogica 0-1023. Nesse sensor/fiacao,
# quanto MENOR o valor, MAIS SECO o solo. Se for o contrario no seu sensor,
# inverta o sinal de comparacao em mood.py.
SOLO_SECO_MAX = 250        # abaixo disso: solo seco (seca)

# Temperatura do ar (DHT11), graus Celsius.
TEMP_FRIO_MAX = 15.0       # abaixo disso: com frio
TEMP_DOENTE_MIN = 40.0     # acima disso: calor extremo -> planta fica doente

# --- Estado critico (LED da porta 10 + buzzer de alarme no Arduino) ---
# A planta entra em estado critico quando QUALQUER uma destas acontece:
#   - "seca" (solo < SOLO_SECO_MAX) continua por mais de CRITICO_DURACAO_SECA;
#   - "dormindo" (luz <= LUZ_ESCURO_MAX) continua por mais de
#     CRITICO_DURACAO_DORMINDO;
#   - temperatura instantanea >= CRITICO_TEMP_MAX;
#   - temperatura instantanea <= CRITICO_TEMP_MIN.
# Uma vez critico, so volta ao normal quando o mood ambiental (sem contar
# festa) for "feliz" ou "oculos" - ver SharedState._recompute_mood_locked em
# serial_reader.py. Enquanto critico, o app manda "CRITICO:1"/"CRITICO:0"
# pela serial pro .ino ligar/desligar o LED e o alarme, e o front-end mostra
# o gif de "doente".
CRITICO_DURACAO_SECA = 24 * 3600        # 24h, em segundos
CRITICO_DURACAO_DORMINDO = 1 * 3600    # 24h, em segundos
CRITICO_TEMP_MAX = 40.0                 # acima disso: critico na hora
CRITICO_TEMP_MIN = 10.0                 # abaixo disso: critico na hora

# --- Deteccao de rega ---
# Sempre que a leitura de Solo estiver igual ou acima desse valor e na leitura
# anterior NAO estava, o app considera que a planta acabou de ser regada e
# guarda o horario - ver SharedState._recompute_mood_locked em
# serial_reader.py. O front-end usa isso pra mostrar "Ultima rega Xh Ym atras"
# no card de umidade do solo. So conta a TRANSICAO (subida), nao fica
# reativando enquanto o solo continuar acima disso. Editavel pela tela de
# configuracoes (ver EDITABLE_FIELDS abaixo).
REGA_DETECTADA_MIN = 300

# --- Janela de leitura ---
# O .ino le os sensores a cada 2000ms (INTERVALO). O app espera receber uma
# linha nova nesse intervalo; se ficar mais que isso sem noticia, marca como
# "desconectado" na interface.
READING_STALE_AFTER = 6.0  # segundos

# --- Duracao das animacoes (deve combinar com generate_assets.py) ---
TRANSITION_FRAMES = 8
TRANSITION_FRAME_MS = 90
TRANSITION_DURATION_MS = TRANSITION_FRAMES * TRANSITION_FRAME_MS

# --- Servidor Flask ---
HOST = "0.0.0.0"
PORT = int(os.environ.get("PETPLANTA_WEB_PORT", "5000"))
DEBUG = False

# --- Estados possiveis (ordem nao importa aqui, prioridade fica em mood.py) ---
# "festa" e ativado/desativado pelas mensagens ">> Tocando musica!" e
# ">> Musica interrompida!/finalizada!" que o .ino imprime na serial quando
# o botao de musica e apertado (ver serial_reader.py).
MOODS = ["festa", "dormindo", "frio", "doente", "seca", "oculos", "feliz"]

MOOD_LABELS = {
    "feliz": "Feliz",
    "seca": "Seca",
    "doente": "Doente",
    "frio": "Com frio",
    "dormindo": "Dormindo",
    "oculos": "Aproveitando o sol",
    "festa": "Modo festa!",
}

# Cor de fundo de cada GIF (tem que ser EXATAMENTE igual ao dict BG em
# generate_assets.py), usada pelo front-end pra estender a cor de fundo do
# bichinho por toda a tela. Se regerar a arte com cores de fundo diferentes,
# atualize aqui tambem.
MOOD_BG = {
    "feliz": "rgb(224, 247, 217)",
    "seca": "rgb(250, 240, 205)",
    "doente": "rgb(238, 230, 214)",
    "frio": "rgb(213, 238, 250)",
    "dormindo": "rgb(28, 36, 64)",
    "oculos": "rgb(255, 244, 188)",
    "festa": "rgb(255, 198, 224)",
}

# --- Limiares editaveis pela tela de configuracoes (front-end) ---
# As constantes acima (LUZ_ESCURO_MAX, SOLO_SECO_MAX, CRITICO_TEMP_MAX, etc.)
# continuam sendo os valores padrao/de fabrica. Quando o usuario salva algo
# na tela de configuracoes, este modulo SOBRESCREVE essas constantes em
# memoria (efeito imediato, sem reiniciar o app.py - mood.py e
# serial_reader.py sempre leem "config.NOME_DA_CONSTANTE" na hora, nunca
# guardam copia local) e tambem grava um snapshot em config_overrides.json,
# que e relido automaticamente na proxima vez que o app.py iniciar.
import json
import threading

_OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_overrides.json")
_config_lock = threading.Lock()

# Nomes das constantes que a tela de configuracoes pode alterar.
EDITABLE_FIELDS = (
    "LUZ_ESCURO_MAX",
    "LUZ_ENSOLARADO_MIN",
    "SOLO_SECO_MAX",
    "TEMP_FRIO_MAX",
    "TEMP_DOENTE_MIN",
    "CRITICO_DURACAO_SECA",
    "CRITICO_DURACAO_DORMINDO",
    "CRITICO_TEMP_MAX",
    "CRITICO_TEMP_MIN",
    "REGA_DETECTADA_MIN",
)


def _load_overrides():
    """Le config_overrides.json (se existir) e sobrescreve as constantes
    correspondentes. Chamado uma vez, na importacao deste modulo."""
    if not os.path.exists(_OVERRIDES_PATH):
        return
    try:
        with open(_OVERRIDES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"[PetPlanta] AVISO: nao consegui ler config_overrides.json: {exc}")
        return

    for key in EDITABLE_FIELDS:
        if key in data:
            globals()[key] = data[key]
    print("[PetPlanta] Limiares customizados carregados de config_overrides.json")


def get_editable_config():
    """Devolve os limiares atualmente em vigor, no formato usado pela API
    /api/config (chaves em snake_case, duracoes do critico em HORAS)."""
    with _config_lock:
        return {
            "luz_escuro_max": LUZ_ESCURO_MAX,
            "luz_ensolarado_min": LUZ_ENSOLARADO_MIN,
            "solo_seco_max": SOLO_SECO_MAX,
            "temp_frio_max": TEMP_FRIO_MAX,
            "temp_doente_min": TEMP_DOENTE_MIN,
            "critico_duracao_seca_horas": int(round(CRITICO_DURACAO_SECA / 3600)),
            "critico_duracao_dormindo_horas": int(round(CRITICO_DURACAO_DORMINDO / 3600)),
            "critico_temp_max": CRITICO_TEMP_MAX,
            "critico_temp_min": CRITICO_TEMP_MIN,
            "rega_detectada_min": REGA_DETECTADA_MIN,
        }


def update_editable_config(values):
    """Valida e aplica novos limiares (dict no mesmo formato de
    get_editable_config()). Levanta ValueError (com mensagem em portugues,
    pronta pra mostrar na tela) se algo for invalido - nesse caso NADA e
    alterado. Se tudo for valido, aplica em memoria (efeito imediato) e
    grava config_overrides.json. Devolve o novo get_editable_config()."""
    global LUZ_ESCURO_MAX, LUZ_ENSOLARADO_MIN, SOLO_SECO_MAX
    global TEMP_FRIO_MAX, TEMP_DOENTE_MIN
    global CRITICO_DURACAO_SECA, CRITICO_DURACAO_DORMINDO
    global CRITICO_TEMP_MAX, CRITICO_TEMP_MIN
    global REGA_DETECTADA_MIN

    def _num(key, label, lo, hi):
        if key not in values or values[key] is None or values[key] == "":
            raise ValueError(f"Campo obrigatorio faltando: {label}")
        try:
            v = float(values[key])
        except (TypeError, ValueError):
            raise ValueError(f"Valor invalido em '{label}': precisa ser um numero")
        if not (lo <= v <= hi):
            raise ValueError(f"'{label}' precisa estar entre {lo} e {hi}")
        return v

    def _int(key, label, lo, hi):
        # Igual a _num, mas exige numero INTEIRO (sem casas decimais) - usado
        # pelas duracoes em horas do estado critico.
        v = _num(key, label, lo, hi)
        if not float(v).is_integer():
            raise ValueError(f"'{label}' precisa ser um numero inteiro (sem casas decimais)")
        return int(v)

    luz_escuro = _num("luz_escuro_max", "Luz - sem luz (dormindo)", 0, 1023)
    luz_ensolarado = _num("luz_ensolarado_min", "Luz - sol forte (oculos)", 0, 1023)
    solo_seco = _num("solo_seco_max", "Solo - seco", 0, 1023)
    temp_frio = _num("temp_frio_max", "Temperatura - frio", -40, 100)
    temp_doente = _num("temp_doente_min", "Temperatura - doente (calor)", -40, 100)
    duracao_seca_h = _int("critico_duracao_seca_horas", "Duracao seca para critico (horas)", 1, 999)
    duracao_dormindo_h = _int("critico_duracao_dormindo_horas", "Duracao sem luz para critico (horas)", 1, 999)
    critico_temp_max = _num("critico_temp_max", "Temperatura critica maxima", -40, 150)
    critico_temp_min = _num("critico_temp_min", "Temperatura critica minima", -40, 150)
    rega_detectada_min = _num("rega_detectada_min", "Limiar de rega detectada", 0, 1023)

    if luz_escuro >= luz_ensolarado:
        raise ValueError("Luz 'sem luz (dormindo)' precisa ser menor que 'sol forte (oculos)'")
    if temp_frio >= temp_doente:
        raise ValueError("Temperatura 'frio' precisa ser menor que 'doente (calor)'")
    if critico_temp_min >= critico_temp_max:
        raise ValueError("Temperatura critica minima precisa ser menor que a maxima")

    with _config_lock:
        LUZ_ESCURO_MAX = int(round(luz_escuro))
        LUZ_ENSOLARADO_MIN = int(round(luz_ensolarado))
        SOLO_SECO_MAX = int(round(solo_seco))
        TEMP_FRIO_MAX = round(temp_frio, 1)
        TEMP_DOENTE_MIN = round(temp_doente, 1)
        CRITICO_DURACAO_SECA = duracao_seca_h * 3600
        CRITICO_DURACAO_DORMINDO = duracao_dormindo_h * 3600
        CRITICO_TEMP_MAX = round(critico_temp_max, 1)
        CRITICO_TEMP_MIN = round(critico_temp_min, 1)
        REGA_DETECTADA_MIN = int(round(rega_detectada_min))

        snapshot = {key: globals()[key] for key in EDITABLE_FIELDS}
        try:
            with open(_OVERRIDES_PATH, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
        except Exception as exc:
            print(f"[PetPlanta] AVISO: nao consegui salvar config_overrides.json: {exc}")

    return get_editable_config()


_load_overrides()
