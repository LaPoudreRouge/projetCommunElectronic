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
- **Serial format**: Plain text. Each sample is one line: a decimal integer 0–4095 followed by CR+LF.
- **Chunk size**: 5000 samples buffered then printed all at once. No binary.
- **Firmware**: Auto-streams after `delay(2000)` in `setup()`. No handshake.
- **PC file format**: 16-bit mono WAV saved every 50000 samples (5 seconds of audio) to timestamped files in a folder.
- **Baud rate**: 500000.
- **Effective throughput**: ~4500 Hz wall-clock due to text overhead (500000 baud ~120µs per line). Samples themselves are at 10 kHz.
