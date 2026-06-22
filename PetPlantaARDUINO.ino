#include <DHT.h>

#define NOTE_B0  31
#define NOTE_C1  33
#define NOTE_CS1 35
#define NOTE_D1  37
#define NOTE_DS1 39
#define NOTE_E1  41
#define NOTE_F1  44
#define NOTE_FS1 46
#define NOTE_G1  49
#define NOTE_GS1 52
#define NOTE_A1  55
#define NOTE_AS1 58
#define NOTE_B1  62
#define NOTE_C2  65
#define NOTE_CS2 69
#define NOTE_D2  73
#define NOTE_DS2 78
#define NOTE_E2  82
#define NOTE_F2  87
#define NOTE_FS2 93
#define NOTE_G2  98
#define NOTE_GS2 104
#define NOTE_A2  110
#define NOTE_AS2 117
#define NOTE_B2  123
#define NOTE_C3  131
#define NOTE_CS3 139
#define NOTE_D3  147
#define NOTE_DS3 156
#define NOTE_E3  165
#define NOTE_F3  175
#define NOTE_FS3 185
#define NOTE_G3  196
#define NOTE_GS3 208
#define NOTE_A3  220
#define NOTE_AS3 233
#define NOTE_B3  247
#define NOTE_C4  262
#define NOTE_CS4 277
#define NOTE_D4  294
#define NOTE_DS4 311
#define NOTE_E4  330
#define NOTE_F4  349
#define NOTE_FS4 370
#define NOTE_G4  392
#define NOTE_GS4 415
#define NOTE_A4  440
#define NOTE_AS4 466
#define NOTE_B4  494
#define NOTE_C5  523
#define NOTE_CS5 554
#define NOTE_D5  587
#define NOTE_DS5 622
#define NOTE_E5  659
#define NOTE_F5  698
#define NOTE_FS5 740
#define NOTE_G5  784
#define NOTE_GS5 831
#define NOTE_A5  880
#define NOTE_AS5 932
#define NOTE_B5  988
#define NOTE_C6  1047
#define NOTE_CS6 1109
#define NOTE_D6  1175
#define NOTE_DS6 1245
#define NOTE_E6  1319
#define NOTE_F6  1397
#define NOTE_FS6 1480
#define NOTE_G6  1568
#define NOTE_GS6 1661
#define NOTE_A6  1760
#define NOTE_AS6 1865
#define NOTE_B6  1976
#define NOTE_C7  2093
#define NOTE_CS7 2217
#define NOTE_D7  2349
#define NOTE_DS7 2489
#define NOTE_E7  2637
#define NOTE_F7  2794
#define NOTE_FS7 2960
#define NOTE_G7  3136
#define NOTE_GS7 3322
#define NOTE_A7  3520
#define NOTE_AS7 3729
#define NOTE_B7  3951
#define NOTE_C8  4186
#define NOTE_CS8 4435
#define NOTE_D8  4699
#define NOTE_DS8 4978
#define REST      0

#define DHTPIN A0
#define DHTTYPE DHT11
#define LDRPIN A1
#define SOLOPIN A2
#define LEDPIN 10
#define BTNPIN 7
#define BUZZER 11

// LEDs que piscam durante a musica
const int ledPins[] = {6, 5, 4, 3, 2, A4, A3, A7, A6, A5};
const int NUM_LEDS = 10;

// --- LEDs de status (mesmos pinos acima, agrupados por cor) ---
// Mostram o "humor ambiental" da planta (calculado pelo app Python a partir
// dos sensores, ver MOOD: mais abaixo) e o estado critico (alarme). Usam os
// MESMOS pinos fisicos que piscam durante a musica (ledPins[]/tocarMusica())
// - durante a musica esse comportamento de status fica suspenso (o piscar
// aleatorio toma conta), e volta a valer automaticamente sozinho assim que
// a musica termina, porque atualizarLedsStatus() e chamada de novo a cada
// volta do loop().
const int LED_VERDE[]    = {6, 3, A4, A7};
const int LED_AMARELO[]  = {5, 2, A6};
const int LED_VERMELHO[] = {4, A3, A5};
const int NUM_VERDE = 4;
const int NUM_AMARELO = 3;
const int NUM_VERMELHO = 3;

DHT dht(DHTPIN, DHTTYPE);

int tempo = 114;

int melody[] = {

  NOTE_D5,-4, NOTE_E5,-4, NOTE_A4,4, //1
  NOTE_E5,-4, NOTE_FS5,-4, NOTE_A5,16, NOTE_G5,16, NOTE_FS5,8,
  NOTE_D5,-4, NOTE_E5,-4, NOTE_A4,2,
  NOTE_A4,16, NOTE_A4,16, NOTE_B4,16, NOTE_D5,8, NOTE_D5,16,
  NOTE_D5,-4, NOTE_E5,-4, NOTE_A4,4, //repeat from 1
  NOTE_E5,-4, NOTE_FS5,-4, NOTE_A5,16, NOTE_G5,16, NOTE_FS5,8,
  NOTE_D5,-4, NOTE_E5,-4, NOTE_A4,2,
  NOTE_A4,16, NOTE_A4,16, NOTE_B4,16, NOTE_D5,8, NOTE_D5,16,
  REST,4, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_D5,8, NOTE_E5,8, NOTE_CS5,-8,
  NOTE_B4,16, NOTE_A4,2, REST,4,

  REST,8, NOTE_B4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,4, NOTE_A4,8, //7
  NOTE_A5,8, REST,8, NOTE_A5,8, NOTE_E5,-4, REST,4,
  NOTE_B4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, NOTE_D5,8, NOTE_E5,8, REST,8,
  REST,8, NOTE_CS5,8, NOTE_B4,8, NOTE_A4,-4, REST,4,
  REST,8, NOTE_B4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, NOTE_A4,4,
  NOTE_E5,8, NOTE_E5,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,4, REST,4,

  NOTE_D5,2, NOTE_E5,8, NOTE_FS5,8, NOTE_D5,8, //13
  NOTE_E5,8, NOTE_E5,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,4, NOTE_A4,4,
  REST,2, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8,
  REST,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,

  NOTE_E5,-8, NOTE_E5,-8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,-8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16, //18
  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,8, NOTE_A4,8, NOTE_A4,8,
  NOTE_E5,4, NOTE_D5,2, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_A5,4, NOTE_CS5,8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,

  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,4, NOTE_A4,8,  //23
  NOTE_E5,4, NOTE_D5,2, REST,4,
  REST,8, NOTE_B4,8, NOTE_D5,8, NOTE_B4,8, NOTE_D5,8, NOTE_E5,4, REST,8,
  REST,8, NOTE_CS5,8, NOTE_B4,8, NOTE_A4,-4, REST,4,
  REST,8, NOTE_B4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, NOTE_A4,4,
  REST,8, NOTE_A5,8, NOTE_A5,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,8, NOTE_D5,8,

  REST,8, NOTE_A4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, //29
  REST,8, NOTE_CS5,8, NOTE_B4,8, NOTE_A4,-4, REST,4,
  NOTE_B4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, NOTE_A4,4, REST,8,
  REST,8, NOTE_E5,8, NOTE_E5,8, NOTE_FS5,4, NOTE_E5,-4,
  NOTE_D5,2, NOTE_D5,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,4,
  NOTE_E5,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,8, NOTE_A4,8, NOTE_A4,4,

  REST,-4, NOTE_A4,8, NOTE_B4,8, NOTE_CS5,8, NOTE_D5,8, NOTE_B4,8, //35
  REST,8, NOTE_E5,8, NOTE_FS5,8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_E5,-8, NOTE_E5,-8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,4, NOTE_A4,8,

   NOTE_E5,4, NOTE_D5,2, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16, //40
  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_A5,4, NOTE_CS5,8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,4, NOTE_A4,8,
  NOTE_E5,4, NOTE_D5,2, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,

  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16, //45
  NOTE_A5,4, NOTE_CS5,8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,4, NOTE_A4,8,
  NOTE_E5,4, NOTE_D5,2, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_FS5,-8, NOTE_FS5,-8, NOTE_E5,-4, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16, //45

  NOTE_A5,4, NOTE_CS5,8, NOTE_D5,-8, NOTE_CS5,16, NOTE_B4,8, NOTE_A4,16, NOTE_B4,16, NOTE_D5,16, NOTE_B4,16,
  NOTE_D5,4, NOTE_E5,8, NOTE_CS5,-8, NOTE_B4,16, NOTE_A4,4, NOTE_A4,8,

  NOTE_E5,4, NOTE_D5,2, REST,4
};

int notes = sizeof(melody) / sizeof(melody[0]) / 2;
int wholenote = (60000 * 4) / tempo;
int divider = 0, noteDuration = 0;

// controle de tempo nao-bloqueante pros sensores
unsigned long ultimaLeitura = 0;
const unsigned long INTERVALO = 2000;

// --- estado critico: LED da porta 10 + alarme no buzzer ---
// O app Python (webapp) decide QUANDO a planta esta em estado critico
// (seca ha mais de 24h, sem luz ha mais de 24h, ou temperatura extrema) e
// avisa este sketch mandando "CRITICO:1" (liga) ou "CRITICO:0" (desliga)
// pela serial. Aqui a gente so obedece: acende o LED e toca um alarme
// (bip-bip) enquanto criticoAtivo for true, sem travar o resto do loop().
bool criticoAtivo = false;
bool alarmeLigadoAgora = false;
unsigned long ultimoToggleAlarme = 0;
const unsigned long ALARME_ON_MS = 250;
const unsigned long ALARME_OFF_MS = 250;
const int ALARME_FREQ_HZ = 1800;

// --- LEDs de status: ultimo "mood ambiental" recebido do app Python pelo
// comando MOOD:<nome> (dormindo/frio/doente/seca/oculos/feliz - SEM
// considerar festa nem critico, que sao tratados a parte por criticoAtivo).
// Comeca vazio - enquanto nao chegar nenhum MOOD:, fica tudo apagado (em
// vez de mostrar uma cor errada por engano).
String moodAtual = "";

// le comandos vindos do app Python pela serial, byte a byte, sem bloquear
void processarComandosSerial() {
  static String bufferComando = "";
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      bufferComando.trim();
      if (bufferComando.equalsIgnoreCase("CRITICO:1")) {
        criticoAtivo = true;
      } else if (bufferComando.equalsIgnoreCase("CRITICO:0")) {
        criticoAtivo = false;
      } else if (bufferComando.startsWith("MOOD:") || bufferComando.startsWith("mood:")) {
        moodAtual = bufferComando.substring(5);
        moodAtual.toLowerCase();
      }
      bufferComando = "";
    } else if (c != '\r') {
      bufferComando += c;
    }
  }
}

// pisca/bipa o alarme em pedacinhos de tempo (nao bloqueia o loop)
void atualizarAlarme() {
  digitalWrite(LEDPIN, criticoAtivo ? HIGH : LOW);

  if (!criticoAtivo) {
    if (alarmeLigadoAgora) {
      noTone(BUZZER);
      alarmeLigadoAgora = false;
    }
    return;
  }

  unsigned long agora = millis();
  unsigned long intervalo = alarmeLigadoAgora ? ALARME_ON_MS : ALARME_OFF_MS;
  if (agora - ultimoToggleAlarme >= intervalo) {
    ultimoToggleAlarme = agora;
    alarmeLigadoAgora = !alarmeLigadoAgora;
    if (alarmeLigadoAgora) {
      tone(BUZZER, ALARME_FREQ_HZ);   // sem duracao = toca continuo até noTone()
    } else {
      noTone(BUZZER);
    }
  }
}

void apagarGrupo(const int pinos[], int n) {
  for (int i = 0; i < n; i++) digitalWrite(pinos[i], LOW);
}

void acenderGrupo(const int pinos[], int n) {
  for (int i = 0; i < n; i++) digitalWrite(pinos[i], HIGH);
}

// Acende so o grupo de cor certo dos LEDs de status (verde/amarelo/
// vermelho), com esta prioridade:
//   1. critico (criticoAtivo) -> so vermelho, sempre, independente do mood
//   2. feliz/oculos           -> so verde
//   3. seca/frio/doente       -> so amarelo (doente = calor forte mas ainda
//                                 sem ter virado critico)
//   4. dormindo (ou moodAtual ainda vazio, no boot) -> tudo apagado
// Chamada a cada volta do loop(), entao volta a valer sozinha assim que
// tocarMusica() termina (ela usa os mesmos pinos pra piscar durante a
// festa).
void atualizarLedsStatus() {
  if (criticoAtivo) {
    acenderGrupo(LED_VERMELHO, NUM_VERMELHO);
    apagarGrupo(LED_VERDE, NUM_VERDE);
    apagarGrupo(LED_AMARELO, NUM_AMARELO);
  } else if (moodAtual == "feliz" || moodAtual == "oculos") {
    apagarGrupo(LED_VERMELHO, NUM_VERMELHO);
    acenderGrupo(LED_VERDE, NUM_VERDE);
    apagarGrupo(LED_AMARELO, NUM_AMARELO);
  } else if (moodAtual == "seca" || moodAtual == "frio" || moodAtual == "doente") {
    apagarGrupo(LED_VERMELHO, NUM_VERMELHO);
    apagarGrupo(LED_VERDE, NUM_VERDE);
    acenderGrupo(LED_AMARELO, NUM_AMARELO);
  } else {
    // "dormindo" ou moodAtual=="" (ainda nao recebeu nada do app Python)
    apagarGrupo(LED_VERMELHO, NUM_VERMELHO);
    apagarGrupo(LED_VERDE, NUM_VERDE);
    apagarGrupo(LED_AMARELO, NUM_AMARELO);
  }
}

// detecta o instante em que o botao e apertado (borda de descida)
bool botaoApertado() {
  static bool estadoAnterior = HIGH;   // solto, por causa do pull-up
  bool estadoAtual = digitalRead(BTNPIN);
  bool apertouAgora = (estadoAnterior == HIGH && estadoAtual == LOW);
  estadoAnterior = estadoAtual;
  if (apertouAgora) delay(30);         // anti-trepidacao simples (debounce)
  return apertouAgora;
}

// sorteia um estado novo (aceso/apagado) pra cada LED
void piscarLeds() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(ledPins[i], random(2));   // random(2) da 0 ou 1
  }
}

// apaga todos os LEDs
void apagarLeds() {
  for (int i = 0; i < NUM_LEDS; i++) {
    digitalWrite(ledPins[i], LOW);
  }
}

// toca a musica, mas pode ser interrompida apertando o botao de novo
void tocarMusica() {
  for (int thisNote = 0; thisNote < notes * 2; thisNote = thisNote + 2) {
    divider = melody[thisNote + 1];
    if (divider > 0) {
      noteDuration = (wholenote) / divider;
    } else if (divider < 0) {
      noteDuration = (wholenote) / abs(divider);
      noteDuration *= 1.5;
    }

    piscarLeds();   // troca as luzes a cada nota
    tone(BUZZER, melody[thisNote], noteDuration * 0.9);

    // em vez de um delay() unico, espera em pedacinhos checando o botao
    unsigned long inicio = millis();
    while (millis() - inicio < (unsigned long)noteDuration) {
      if (botaoApertado()) {
        noTone(BUZZER);   // corta o som
        apagarLeds();     // apaga as luzes
        Serial.println(">> Musica interrompida!");
        return;           // sai da musica no meio
      }
    }

    noTone(BUZZER);
  }

  apagarLeds();   // apaga tudo quando a musica termina normalmente
  Serial.println(">> Musica finalizada!");   // avisa o app Python que a festa acabou
}

void setup() {
  Serial.begin(9600);
  Serial.println("Teste DHT11 + LDR + Solo");
  pinMode(LEDPIN, OUTPUT);
  digitalWrite(LEDPIN, LOW);       // LED do estado critico comeca apagado
  pinMode(BUZZER, OUTPUT);
  pinMode(BTNPIN, INPUT_PULLUP);   // botao com pull-up interno

  // configura os LEDs que piscam na musica
  for (int i = 0; i < NUM_LEDS; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
  // semeia o sorteio com ruido de um pino solto - usa A15 (Arduino Mega) em
  // vez de A5, porque A5 agora tem um LED de status ligado nele e deixou de
  // estar solto/flutuante (deixaria de dar ruido aleatorio de verdade)
  randomSeed(analogRead(A15));

  dht.begin();
}

void loop() {
  // --- comandos vindos do app Python (ex: CRITICO:1/0) ---
  processarComandosSerial();

  // --- LED da porta 10 + buzzer: refletem o estado critico, sempre ---
  atualizarAlarme();

  // --- LEDs de status (verde/amarelo/vermelho): refletem o mood/critico ---
  atualizarLedsStatus();

  // --- botao checado a cada volta do loop (responsivo) ---
  // com INPUT_PULLUP: apertado = LOW
  if (botaoApertado()) {
    Serial.println(">> Tocando musica!");
    tocarMusica();
  }

  // --- sensores a cada 2s, sem travar o loop ---
  if (millis() - ultimaLeitura >= INTERVALO) {
    ultimaLeitura = millis();

    int luz = analogRead(LDRPIN);
    int solo = analogRead(SOLOPIN);

    Serial.print("Luz: ");
    Serial.print(luz);
    Serial.print("  |  Solo: ");
    Serial.print(solo);

    float temperatura = dht.readTemperature();

    if (isnan(temperatura)) {
      Serial.println("  |  DHT11: falha na leitura");
      return;
    }

    Serial.print("  |  Temperatura: ");
    Serial.print(temperatura);
    Serial.println(" *C");
  }
}
