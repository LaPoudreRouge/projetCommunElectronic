// micSend.ino — Tiva C LaunchPad microphone streaming (half-second chunks)
// MAX4466 -> ADC @ 10 kHz -> 5000-sample buffer -> serial -> PC
// Auto-streams after 2s boot delay. No handshake needed.
// Frame format: raw 12-bit ADC, no marker bit
//   byte1 = (val >> 4) & 0xFF    // high 8 bits
//   byte2 = (val & 0x0F) << 4    // low 4 bits in upper nibble

#define MIC_PIN A0
#define BAUD 500000
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

  // --- When half-second buffer is full, send it ---
  if (count >= CHUNK_SAMPLES) {
    // Print buffer as space-separated hex for serial monitor debugging
    for (uint16_t i = 0; i < CHUNK_SAMPLES; i++) {
      if (i > 0) Serial.print(' ');
      Serial.print(buf[i], HEX);
    }
    Serial.println();

    // Send binary chunk to Python (no marker bit, raw 12-bit)
    uint8_t tx[CHUNK_SAMPLES * 2];
    for (uint16_t i = 0; i < CHUNK_SAMPLES; i++) {
      uint16_t val = buf[i];
      tx[i * 2]     = (val >> 4) & 0xFF;   // high 8 bits
      tx[i * 2 + 1] = (val & 0x0F) << 4;   // low 4 bits in upper nibble
    }
    Serial.write(tx, CHUNK_SAMPLES * 2);

    count = 0;
  }
}
