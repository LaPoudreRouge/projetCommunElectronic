// micSend.ino — Tiva C LaunchPad microphone real-time streaming
// MAX4466 -> ADC @ 20 kHz -> immediate serial output -> PC
// Auto-streams after 2s boot delay. No handshake needed.

#define MIC_PIN A0
#define BAUD 921600
#define SAMPLE_INTERVAL 50         // 50 us = 20 kHz

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

  unsigned long now = micros();
  if (now - lastSample >= SAMPLE_INTERVAL) {
    lastSample += SAMPLE_INTERVAL;
    uint16_t val = analogRead(MIC_PIN);
    Serial.write((uint8_t*)&val, 2);
  }
}
