// micSend.ino — Tiva C LaunchPad microphone streaming (raw binary)
// MAX4466 -> ADC @ 10 kHz -> 5000-sample buffer -> serial -> PC
// Auto-streams after 2s boot delay. No handshake needed.
// Output: raw uint16_t values, 10000 bytes per chunk.

#define MIC_PIN A0
#define BAUD 921600
#define SAMPLE_INTERVAL 100        // 100 us = 10 kHz
#define CHUNK_SAMPLES 5000         // half second @ 10 kHz

uint16_t buf[CHUNK_SAMPLES];
uint16_t count = 0;
bool streaming = false;
unsigned long lastSample = 0;

void setup() {
  Serial.begin(BAUD);
  delay(2000);
  lastSample = micros();
  streaming = true;
}

void loop() {
  if (!streaming) return;

  // --- Sample ADC at precise 10 kHz intervals ---
  unsigned long now = micros();
  while (now - lastSample >= SAMPLE_INTERVAL) {
    lastSample += SAMPLE_INTERVAL;
    if (count < CHUNK_SAMPLES) {
      buf[count++] = analogRead(MIC_PIN);
    }
  }

  // --- When buffer is full, send raw binary ---
  if (count >= CHUNK_SAMPLES) {
    Serial.write((uint8_t*)buf, CHUNK_SAMPLES * 2);
    count = 0;
  }
}
