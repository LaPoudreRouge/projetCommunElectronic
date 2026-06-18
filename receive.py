"""
receive.py — Capture audio from Tiva C LaunchPad over serial.

Tiva runs auto-stream firmware (micSend.ino) — no handshake needed.
Sends raw 12-bit ADC values in half-second chunks (no marker bit).
Python saves a WAV file every 5 seconds to recordings/ folder.

Usage:
    python receive.py --port COM5
    python receive.py --port COM5 --output myrec

Press Ctrl+C to stop — last partial chunk is discarded.
"""

import argparse
import os
import struct
import sys
import time
from datetime import datetime
import serial

BAUD = 500000
SAMPLE_RATE = 10000
WAV_CHANNELS = 1
WAV_BITS = 16

CHUNK_SAMPLES = 5000          # half second @ 10 kHz
CHUNK_BYTES = CHUNK_SAMPLES * 2
SAVE_INTERVAL = 10            # save WAV every 10 chunks (5 seconds)


def write_wav(filepath, samples, sample_rate):
    """Write a 16-bit mono WAV file."""
    n = len(samples)
    ds = n * 2
    with open(filepath, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + ds))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<HH', 1, 1))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<HH', 2, 16))
        f.write(b'data')
        f.write(struct.pack('<I', ds))
        for s in samples:
            f.write(struct.pack('<h', s))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', required=True)
    parser.add_argument('--output', '-o', default='output')
    args = parser.parse_args()

    # Create recordings folder
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    # Open port — DTR=True (default) resets Tiva, then it boots and auto-streams
    print(f"Opening {args.port} ...")
    ser = serial.Serial(args.port, BAUD, timeout=1.0, write_timeout=1)
    time.sleep(3.0)  # wait for Tiva boot + delay(2000)
    ser.reset_input_buffer()

    print(f"Recording at {SAMPLE_RATE} Hz, saving to {out_dir}/")
    print("  (saves WAV every 5 seconds — Ctrl+C to stop)")

    buf_samples = []          # accumulates samples for current 5-second block
    chunk_count = 0           # chunks received in current block
    total_chunks = 0          # total chunks received
    wav_index = 0             # WAV file number
    start = time.time()
    last_report = start

    try:
        while True:
            # Read one half-second chunk (10000 bytes)
            raw = ser.read(CHUNK_BYTES)
            if len(raw) < CHUNK_BYTES:
                continue  # incomplete chunk, retry

            # Parse 5000 samples from the chunk
            for i in range(0, CHUNK_BYTES, 2):
                val = (raw[i] << 4) | (raw[i + 1] >> 4)  # 12-bit ADC 0-4095
                buf_samples.append((val << 4) - 32768)    # to signed 16-bit WAV

            chunk_count += 1
            total_chunks += 1

            # Check if it's time to save a WAV
            if chunk_count >= SAVE_INTERVAL:
                wav_index += 1
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = os.path.join(out_dir, f"{ts}.wav")
                write_wav(fname, buf_samples, SAMPLE_RATE)
                print(f"  Saved {fname} ({len(buf_samples)} samples)")
                buf_samples = []
                chunk_count = 0

            # Status report every second
            now = time.time()
            if now - last_report >= 1.0:
                elapsed = now - start
                total_samples = total_chunks * CHUNK_SAMPLES
                rate = total_samples / elapsed if elapsed else 0
                print(f"  {total_samples} samples @ {rate:.0f} Hz")
                last_report = now

    except KeyboardInterrupt:
        t = time.time() - start
        ser.close()
        total_samples = total_chunks * CHUNK_SAMPLES
        rate = total_samples / t if t else 0
        print(f"\n{total_samples} samples in {t:.1f}s ({rate:.0f} Hz)")
        print(f"WAV files saved in {out_dir}/")
        # Discard partial chunk (buf_samples is incomplete block)


if __name__ == '__main__':
    main()
