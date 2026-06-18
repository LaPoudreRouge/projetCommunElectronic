"""
receive.py — Capture audio from Tiva C LaunchPad over serial.

Tiva sends ADC values as comma-separated decimal ints, one line per chunk.
Python reads lines, converts to signed 16-bit, saves WAV every 5 seconds.

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

CHUNK_SAMPLES = 5000           # samples per half-second buffer
SAVE_INTERVAL = 10             # save WAV every 10 chunks (50000 samples = 5s)


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

    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    print(f"Opening {args.port} ...")
    ser = serial.Serial(args.port, BAUD, timeout=1.0, write_timeout=1)
    time.sleep(3.0)  # wait for Tiva boot + delay(2000)
    ser.reset_input_buffer()

    print(f"Recording at {SAMPLE_RATE} Hz, saving to {out_dir}/")
    print("  (saves WAV every 5 seconds of audio — Ctrl+C to stop)")

    buf_samples = []        # samples for current 5-second block
    sample_count = 0        # samples in current block
    total_samples = 0
    start = time.time()
    last_report = start

    try:
        while True:
            line = ser.readline()
            if not line:
                continue

            # Parse comma-separated ADC values
            for token in line.strip().split(','):
                try:
                    val = int(token)
                except ValueError:
                    continue
                buf_samples.append((val << 4) - 32768)
                sample_count += 1
                total_samples += 1

            # Check if this finishes a 5000-sample chunk
            if sample_count >= CHUNK_SAMPLES * SAVE_INTERVAL:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                fname = os.path.join(out_dir, f"{ts}.wav")
                write_wav(fname, buf_samples, SAMPLE_RATE)
                print(f"  Saved {fname} ({len(buf_samples)} samples)")
                buf_samples = []
                sample_count = 0

            # Status every second
            now = time.time()
            if now - last_report >= 1.0:
                elapsed = now - start
                rate = total_samples / elapsed if elapsed else 0
                print(f"  {total_samples} samples @ {rate:.0f} Hz")
                last_report = now

    except KeyboardInterrupt:
        t = time.time() - start
        ser.close()
        rate = total_samples / t if t else 0
        print(f"\n{total_samples} samples in {t:.1f}s ({rate:.0f} Hz)")
        print(f"WAV files saved in {out_dir}/")
        # Partial chunk discarded


if __name__ == '__main__':
    main()
