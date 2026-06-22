# -*- coding: utf-8 -*-
"""
Le os dados que o PetPlantaARDUINO.ino manda pela porta serial e mantem um
estado compartilhado e thread-safe com as ultimas leituras + o mood atual.

Linha esperada (impressa pelo .ino a cada ~2s):
    Luz: 512  |  Solo: 300  |  Temperatura: 24.00 *C

Se o DHT11 falhar na leitura, o .ino imprime so a primeira parte e corta:
    Luz: 512  |  Solo: 300  |  DHT11: falha na leitura

Se nenhuma porta serial com Arduino for encontrada (ou pyserial nao estiver
disponivel), o reader cai automaticamente em modo SIMULACAO, gerando valores
ficticios que variam suavemente, so para a interface nunca ficar vazia
enquanto o hardware real nao esta conectado.

Modo festa: quando o botao de musica do Arduino e apertado, o .ino fica
preso dentro de tocarMusica() (loop() para de mandar leituras de sensor
enquanto a musica toca) e imprime:
    >> Tocando musica!            <- no inicio
    >> Musica interrompida!       <- se o botao for apertado de novo no meio
    >> Musica finalizada!         <- se a musica tocar até o fim
Esse modulo escuta essas linhas pra ligar/desligar o mood "festa".

Modo critico: este modulo tambem rastreia, a partir das proprias leituras
(ver SharedState._recompute_mood_locked), se a planta esta em "estado
critico" e AVISA o .ino mandando de volta pela serial:
    CRITICO:1\n   <- liga o LED da porta 10 + buzzer de alarme
    CRITICO:0\n   <- desliga os dois
O .ino fica responsavel por de fato acender o LED e tocar o alarme; este
modulo so manda a ordem quando o estado muda (nao fica repetindo a cada
leitura - se o Arduino reiniciar e perder o estado, o app reenvia na
proxima vez que o critico mudar, ou se reconectar com critico ja ativo
basta o estado mudar uma vez pra ressincronizar).
"""

import random
import re
import threading
import time

import config
import mood as mood_module

LINE_RE = re.compile(
    r"Luz:\s*(\d+)\s*\|\s*Solo:\s*(\d+)\s*\|\s*Temperatura:\s*([\d.]+)"
)
PARTIAL_RE = re.compile(r"Luz:\s*(\d+)\s*\|\s*Solo:\s*(\d+)")
MUSIC_START_RE = re.compile(r">>\s*Tocando\s*musica", re.IGNORECASE)
MUSIC_STOP_RE = re.compile(r">>\s*Musica\s*(interrompida|finalizada)", re.IGNORECASE)


class SharedState:
    """Guarda a ultima leitura conhecida, protegida por um lock."""

    def __init__(self):
        self._lock = threading.Lock()
        self.luz = None
        self.solo = None
        self.temperatura = None
        self.festa = False
        self.critico = False
        self.seca_since = None       # time.time() de quando "seca" comecou, ou None
        self.dormindo_since = None   # idem para "dormindo" (sem luz)
        self.ultima_rega = None      # time.time() da ultima vez que detectou rega, ou None
        self._solo_acima_rega = False  # assume "seco" no boot, pra disparar logo se a 1a leitura ja vier molhada
        self._last_raw_mood_sent = None  # ultimo "mood ambiental" (sem festa/critico) mandado pro Arduino via MOOD:
        # --- modo simulacao: "random" (passeio aleatorio, comportamento
        # original) ou "manual" (usa os valores de sim_manual em vez de
        # gerar numeros aleatorios). So tem efeito quando self.simulated for
        # True (ou seja, quando nao ha Arduino conectado) - ver
        # _simulation_loop() mais abaixo. Editavel pela tela de simulacao
        # no front-end (GET/POST /api/simulation).
        self.sim_mode = "random"
        self.sim_manual = {"luz": 600, "solo": 400, "temperatura": 23.0}
        self.mood = "feliz"
        self.connected = False
        self.simulated = False
        self.last_update = 0.0
        self.raw_line = ""
        self.serial_conn = None      # pyserial.Serial ativa (modo real), ou None

    def _send_critico_command_locked(self):
        """Avisa o Arduino (se conectado de verdade) que o critico mudou."""
        conn = self.serial_conn
        if conn is None:
            return
        try:
            conn.write(b"CRITICO:1\n" if self.critico else b"CRITICO:0\n")
        except Exception as exc:
            print(f"[PetPlanta] Nao consegui mandar comando CRITICO pra serial: {exc}")

    def _send_mood_command_locked(self, raw_mood):
        """Avisa o Arduino qual e o "mood ambiental" atual (dormindo/frio/
        doente/seca/oculos/feliz - SEM considerar festa nem critico, que sao
        tratados separadamente pelo CRITICO:1/0). O .ino usa isso pra decidir
        qual grupo de LED (verde/amarelo/vermelho) acender - ver
        atualizarLedsStatus() no .ino, que da prioridade ao critico sobre
        este valor."""
        conn = self.serial_conn
        if conn is None:
            return
        try:
            conn.write(f"MOOD:{raw_mood}\n".encode("ascii"))
        except Exception as exc:
            print(f"[PetPlanta] Nao consegui mandar comando MOOD pra serial: {exc}")

    def resync_arduino_locked(self):
        """Reenvia pro Arduino o ultimo estado conhecido de critico e mood -
        usado logo apos (re)conectar numa porta serial, pra cobrir o caso do
        Arduino ter perdido o estado anterior (reset, cabo desconectado e
        reconectado) e ficar com os LEDs desincronizados do app."""
        self._send_critico_command_locked()
        if self._last_raw_mood_sent is not None:
            self._send_mood_command_locked(self._last_raw_mood_sent)

    def resync_arduino(self):
        with self._lock:
            self.resync_arduino_locked()

    def _recompute_mood_locked(self):
        # so chamar com o lock ja adquirido
        now = time.time()
        raw_mood = mood_module.compute_mood(self.luz, self.solo, self.temperatura)

        # --- avisa o Arduino se o mood ambiental mudou, pra ele acender o
        # grupo de LED certo (verde/amarelo/vermelho - ver atualizarLedsStatus
        # no .ino). Manda tambem na PRIMEIRA vez (self._last_raw_mood_sent
        # comeca None), senao o Arduino ficaria sem nenhuma cor ate o mood
        # realmente mudar pela primeira vez.
        if raw_mood != self._last_raw_mood_sent:
            self._send_mood_command_locked(raw_mood)
            self._last_raw_mood_sent = raw_mood

        # --- rastreia ha quanto tempo cada condicao "critica" esta ativa ---
        seca_now = self.solo is not None and self.solo < config.SOLO_SECO_MAX
        escuro_now = self.luz is not None and self.luz <= config.LUZ_ESCURO_MAX
        temp_extrema_now = self.temperatura is not None and (
            self.temperatura >= config.CRITICO_TEMP_MAX
            or self.temperatura <= config.CRITICO_TEMP_MIN
        )

        self.seca_since = (self.seca_since or now) if seca_now else None
        self.dormindo_since = (self.dormindo_since or now) if escuro_now else None

        # --- deteccao de rega: dispara sempre que o solo estiver "acima do
        # limiar" e da ultima leitura conhecida nao estava (comeca assumindo
        # "seco" no boot, entao se a 1a leitura ja vier >= REGA_DETECTADA_MIN
        # ja conta como rega - e nao fica esperando uma descida real abaixo
        # do limiar pra so depois disparar, que era o bug: em modo simulacao
        # (ou Arduino real) o solo podia ficar OSCILANDO sempre acima do
        # limiar por muito tempo sem nunca descer, e nesse caso o contador
        # nunca aparecia).
        solo_acima_rega_agora = self.solo is not None and self.solo >= config.REGA_DETECTADA_MIN
        if solo_acima_rega_agora and not self._solo_acima_rega:
            self.ultima_rega = now
        self._solo_acima_rega = solo_acima_rega_agora

        seca_ha_muito_tempo = (
            self.seca_since is not None
            and (now - self.seca_since) >= config.CRITICO_DURACAO_SECA
        )
        dormindo_ha_muito_tempo = (
            self.dormindo_since is not None
            and (now - self.dormindo_since) >= config.CRITICO_DURACAO_DORMINDO
        )

        was_critico = self.critico
        if seca_ha_muito_tempo or dormindo_ha_muito_tempo or temp_extrema_now:
            self.critico = True
        elif raw_mood in ("feliz", "oculos"):
            self.critico = False

        if self.critico != was_critico:
            self._send_critico_command_locked()

        if self.festa:
            self.mood = "festa"
        elif self.critico:
            self.mood = "doente"
        else:
            self.mood = raw_mood

    def update(self, *, luz=None, solo=None, temperatura=None,
               simulated=False, raw_line=""):
        with self._lock:
            if luz is not None:
                self.luz = luz
            if solo is not None:
                self.solo = solo
            if temperatura is not None:
                self.temperatura = temperatura
            self._recompute_mood_locked()
            self.connected = True
            self.simulated = simulated
            self.last_update = time.time()
            self.raw_line = raw_line

    def set_festa(self, active):
        """Liga/desliga o modo festa (chamado quando a musica comeca/para)."""
        with self._lock:
            if self.festa == active:
                return
            self.festa = active
            self._recompute_mood_locked()
            self.last_update = time.time()

    def set_sim_mode(self, mode):
        """Troca entre simulacao "random" (passeio aleatorio) e "manual"
        (usa sim_manual). So faz sentido enquanto o app estiver em modo
        simulacao (sem Arduino conectado), mas pode ser chamado a qualquer
        momento - se nao houver Arduino, _simulation_loop() ja confere o
        valor atual a cada ciclo."""
        if mode not in ("random", "manual"):
            raise ValueError("Modo de simulacao precisa ser 'random' ou 'manual'")
        with self._lock:
            self.sim_mode = mode

    def set_sim_manual_values(self, *, luz=None, solo=None, temperatura=None):
        """Atualiza os valores usados pelo modo simulacao "manual"."""
        with self._lock:
            if luz is not None:
                self.sim_manual["luz"] = luz
            if solo is not None:
                self.sim_manual["solo"] = solo
            if temperatura is not None:
                self.sim_manual["temperatura"] = temperatura

    def get_sim_snapshot(self):
        """Devolve (sim_mode, copia de sim_manual) - usado por
        _simulation_loop() pra decidir o que fazer em cada ciclo."""
        with self._lock:
            return self.sim_mode, dict(self.sim_manual)

    def to_dict(self):
        with self._lock:
            now = time.time()
            stale = (now - self.last_update) > config.READING_STALE_AFTER

            # Quanto falta (em segundos) pra "seca"/"dormindo" virarem critico,
            # se a condicao estiver ativa agora (None = condicao nao ativa).
            seca_restante_s = None
            if self.seca_since is not None:
                seca_restante_s = max(0.0, config.CRITICO_DURACAO_SECA - (now - self.seca_since))

            dormindo_restante_s = None
            if self.dormindo_since is not None:
                dormindo_restante_s = max(
                    0.0, config.CRITICO_DURACAO_DORMINDO - (now - self.dormindo_since)
                )

            # Ha quanto tempo (em segundos) foi a ultima rega detectada, ou
            # None se nenhuma rega foi detectada ainda nesta execucao do app.
            ultima_rega_s_atras = None
            if self.ultima_rega is not None:
                ultima_rega_s_atras = max(0.0, now - self.ultima_rega)

            return {
                "luz": self.luz,
                "solo": self.solo,
                "temperatura": self.temperatura,
                "mood": self.mood,
                "mood_label": config.MOOD_LABELS.get(self.mood, self.mood),
                "festa": self.festa,
                "critico": self.critico,
                "seca_restante_s": seca_restante_s,
                "dormindo_restante_s": dormindo_restante_s,
                "ultima_rega_s_atras": ultima_rega_s_atras,
                "connected": self.connected and not stale,
                "simulated": self.simulated,
                "stale": stale,
                "last_update": self.last_update,
                "raw_line": self.raw_line,
                # Limiares ATUAIS (refletem qualquer alteracao feita na tela de
                # configuracoes) - o front-end usa isso pra colorir as barras
                # de progresso de cada sensor sem precisar recarregar a pagina.
                "luz_escuro_max": config.LUZ_ESCURO_MAX,
                "solo_seco_max": config.SOLO_SECO_MAX,
                "temp_frio_max": config.TEMP_FRIO_MAX,
                "temp_doente_min": config.TEMP_DOENTE_MIN,
                # Modo de simulacao atual e os valores manuais configurados -
                # so tem efeito pratico quando "simulated" for True, mas o
                # front-end usa isso pra preencher o painel de simulacao.
                "sim_mode": self.sim_mode,
                "sim_manual": dict(self.sim_manual),
            }


state = SharedState()


def _find_arduino_port():
    """Tenta achar automaticamente uma porta com um Arduino plugado."""
    try:
        from serial.tools import list_ports
    except ImportError:
        print("[PetPlanta] AVISO: nao consegui importar 'serial.tools.list_ports'. "
              "Isso normalmente significa que o pacote pyserial nao esta instalado "
              "no MESMO python/venv que esta rodando este app.py. "
              "Rode: pip install pyserial (ou pip install -r requirements.txt) "
              "usando o mesmo 'python'/'pip' que voce usa pra dar 'python app.py'.")
        return None

    candidates = list(list_ports.comports())
    if not candidates:
        print("[PetPlanta] AVISO: nenhuma porta serial foi detectada no sistema "
              "(list_ports.comports() voltou vazio). Verifique se o Arduino esta "
              "plugado e se apareceu em Gerenciador de Dispositivos / Arduino IDE.")
        return None

    print("[PetPlanta] Portas seriais detectadas:")
    for p in candidates:
        print(f"    - {p.device}  ({p.description})")

    keywords = ("arduino", "ch340", "usb-serial", "usb serial", "wch", "ftdi", "cp210")
    for p in candidates:
        desc = f"{p.description} {p.manufacturer or ''}".lower()
        if any(k in desc for k in keywords):
            return p.device

    # Nenhum nome obviamente reconhecido: usa a primeira porta disponivel
    # como ultimo recurso (melhor que nada quando ha so uma porta no PC).
    return candidates[0].device


def _parse_line(line):
    line = line.strip()
    if not line:
        return None

    m = LINE_RE.search(line)
    if m:
        luz, solo, temp = m.groups()
        return {
            "luz": int(luz),
            "solo": int(solo),
            "temperatura": float(temp),
        }

    m = PARTIAL_RE.search(line)
    if m:
        luz, solo = m.groups()
        return {"luz": int(luz), "solo": int(solo)}

    return None


def _serial_loop(port):
    import serial

    print(f"[PetPlanta] Conectando na porta serial {port} @ {config.SERIAL_BAUD} baud...")
    with serial.Serial(port, config.SERIAL_BAUD, timeout=2) as ser:
        state.serial_conn = ser
        # Reenvia o ultimo critico/mood conhecido pro Arduino recem-conectado
        # (ele pode ter perdido o estado anterior num reset/desconexao).
        state.resync_arduino()
        try:
            print("[PetPlanta] Conectado! Esperando leituras do Arduino...")
            while True:
                try:
                    raw = ser.readline().decode("utf-8", errors="ignore")
                except Exception as exc:  # porta caiu / Arduino desconectado
                    print(f"[PetPlanta] Erro lendo serial: {exc}")
                    raise

                line = raw.strip()
                if not line:
                    continue

                if MUSIC_START_RE.search(line):
                    state.set_festa(True)
                    print(f"[PetPlanta] {line}  -> MODO FESTA ativado!")
                    continue

                if MUSIC_STOP_RE.search(line):
                    state.set_festa(False)
                    print(f"[PetPlanta] {line}  -> modo festa encerrado, mood={state.mood}")
                    continue

                parsed = _parse_line(line)
                if parsed:
                    state.update(simulated=False, raw_line=line, **parsed)
                    flag = " [CRITICO]" if state.critico else ""
                    print(f"[PetPlanta] {line}  -> mood={state.mood}{flag}")
        finally:
            state.serial_conn = None


def _simulation_loop():
    print("[PetPlanta] Nenhum Arduino encontrado - rodando em MODO SIMULACAO "
          "(dados ficticios so para demonstracao da interface).")

    luz, solo, temp = 600, 400, 23.0
    ciclo = 0
    while True:
        ciclo += 1

        # Confere a cada ciclo se o usuario esta no modo "manual" (tela de
        # simulacao no front-end) - se estiver, usa os valores que ele
        # configurou em vez de gerar numeros aleatorios. Trocar de volta pra
        # "random" continua o passeio aleatorio a partir de onde "luz"/
        # "solo"/"temp" ficaram (sem pulo brusco).
        mode, manual = state.get_sim_snapshot()
        if mode == "manual":
            luz = manual["luz"]
            solo = manual["solo"]
            temp = manual["temperatura"]
        else:
            # random walk suave, com limites realistas (0-1023 sensores)
            luz = max(0, min(1023, luz + random.randint(-80, 80)))
            solo = max(0, min(1023, solo + random.randint(-40, 40)))
            temp = max(5.0, min(40.0, temp + random.uniform(-1, 1)))

        state.update(
            luz=luz, solo=solo,
            temperatura=round(temp, 1), simulated=True,
            raw_line="(simulado manual)" if mode == "manual" else "(simulado)",
        )

        # so pra demonstrar o modo festa sem precisar de um Arduino real:
        # liga por ~6s a cada ~30s. Em produção (com Arduino conectado) o
        # festa e controlado de verdade pelas mensagens de musica. No modo
        # manual fica desligado, pra nao interferir nos valores que o
        # usuario esta controlando de proposito.
        state.set_festa(mode != "manual" and (ciclo % 15) >= 12)

        time.sleep(2)


def start_background_reader():
    """Inicia a thread de leitura (serial real ou simulacao) e devolve o state."""

    if config.SERIAL_PORT:
        print(f"[PetPlanta] Usando porta fixada em config.py / PETPLANTA_PORT: {config.SERIAL_PORT}")
        port = config.SERIAL_PORT
    else:
        print("[PetPlanta] config.SERIAL_PORT nao foi definido, tentando auto-detectar...")
        port = _find_arduino_port()

    def runner():
        if port:
            try:
                _serial_loop(port)
                return
            except Exception as exc:
                print(f"[PetPlanta] Nao foi possivel usar a porta {port}: {type(exc).__name__}: {exc}")
        else:
            print("[PetPlanta] Nenhuma porta serial disponivel para tentar.")
        _simulation_loop()

    t = threading.Thread(target=runner, daemon=True)
    t.start()
    return state
