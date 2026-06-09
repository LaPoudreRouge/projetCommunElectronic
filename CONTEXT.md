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
- **Serial format**: Raw binary, 2 bytes per sample (12-bit value in 16-bit frame).
- **Sync**: High bit of first byte acts as marker bit for per-frame sync.
- **PC file format**: 16-bit WAV (12-bit values left-aligned in 16-bit slots).
- **Port detection**: Scan all COM ports, send handshake, listen for Tiva reply.
- **Sampling method**: Timer-triggered at 10 kHz, ADC read in ISR, buffer flushed by main loop.
- **Baud rate**: 460800 (USB virtual serial handles the speed; this gives headroom).
