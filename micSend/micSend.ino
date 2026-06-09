// micSend.ino — Tiva C LaunchPad microphone streaming
// MAX4466 → ADC @ 10 kHz → 2-byte frames → serial → PC
// Uses only Energia built-in API (analogRead, micros, Serial).
// Protocol: 0x80 | (sample>>8) as byte1, sample & 0xFF as byte2
// Handshake: PC sends 0xAA, Tiva replies 0xBB

#define MIC_PIN A0
#define BAUD 460800
#define SAMPLE_INTERVAL 100       // 100 µs = 10 kHz
#define BUF_SIZE 256              // sample ring buffer
#define TX_CHUNK 32               // samples per serial flush

uint16_t buf[BUF_SIZE];
uint16_t head = 0;
uint16_t count = 0;
bool streaming = false;
unsigned long lastSample = 0;

void setup() {
  Serial.begin(BAUD);
}

void loop() {
  // --- Handshake ---
  if (Serial.available() > 0) {
    uint8_t c = Serial.read();
    if (c == 0xAA && !streaming) {
      head = 0; count = 0;
      lastSample = micros();
      streaming = true;
      Serial.write(0xBB);
    } else if (c == 0xCC) {
      streaming = false;
    }
  }
  if (!streaming) return;

  // --- Sample ADC at precise 10 kHz intervals ---
  unsigned long now = micros();
  while (now - lastSample >= SAMPLE_INTERVAL) {
    lastSample += SAMPLE_INTERVAL;
    if (count < BUF_SIZE) {
      buf[(head + count) % BUF_SIZE] = analogRead(MIC_PIN);
      count++;
    }
  }

  // --- Flush buffer to serial in chunks ---
  if (count >= TX_CHUNK) {
    uint16_t todo = (count < TX_CHUNK) ? count : TX_CHUNK;
    uint8_t out[TX_CHUNK * 2];
    for (uint16_t i = 0; i < todo; i++) {
      uint16_t s = buf[head];
      head = (head + 1) % BUF_SIZE;
      out[i * 2]     = 0x80 | ((s >> 8) & 0x0F);
      out[i * 2 + 1] = s & 0xFF;
    }
    Serial.write(out, todo * 2);
    count -= todo;
  }
}
