# Context

## Hardware

- **Tiva C LaunchPad (EK-TM4C123GXL)**: Microcontroller board with TM4C123GH6PM (ARM Cortex-M4F, 80 MHz).
- **MAX4466**: Adafruit electret microphone amplifier (Product ID 1063). Output is Vcc/2 biased, rail-to-rail, adjustable gain 25x–125x.
- **ADC**: 12-bit, 1 MSPS, 0–3.3V input range, on the TM4C123GH6PM.

## Software

- **Energia**: Arduino-like IDE/ framework for TI LaunchPad boards.
- **Python**: PC-side audio capture and file writing.

## Design decisions

- **Sample rate**: 10 kHz (voice-grade, 5 kHz Nyquist).
- **Communication**: Serial over USB (virtual COM port via ICDI).
- **Serial format**: Raw binary, 2 bytes per sample, no marker bit.
  - `byte1 = (adc_val >> 4) & 0xFF` — high 8 bits of 12-bit ADC
  - `byte2 = (adc_val & 0x0F) << 4` — low 4 bits in upper nibble
- **Chunk size**: 5000 samples per chunk (half second), sent as one `Serial.write()`.
- **Firmware**: Auto-streams after `delay(2000)` in `setup()`. No handshake.
- **PC file format**: 16-bit mono WAV saved every 5 seconds (10 chunks) to timestamped files in a folder.
- **Baud rate**: 500000.
