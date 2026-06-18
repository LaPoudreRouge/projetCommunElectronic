"""
receive.py — Capture audio from Tiva C LaunchPad over serial.

Tiva streams raw uint16_t values continuously at 20 kHz.
Python reads all bytes, unpacks samples, prints status every second.

Usage:
    python receive.py --port COM5
    python receive.py --port COM5 --output myrec

Press Ctrl+C to stop — last partial block is discarded.
"""

import argparse
import os
import struct
import sys
import time
from datetime import datetime
import requests
import serial

BAUD = 921600
SAMPLE_RATE = 20000
WAV_CHANNELS = 1
WAV_BITS = 16

STATUS_INTERVAL = 20000        # print status every 20000 samples (1s @ 20 kHz)
SAVE_INTERVAL = 100000         # save WAV every 100000 samples (5s @ 20 kHz)

ROVER_API_KEY = os.environ.get("ROVER_API_KEY", "rvr-G7E-a9f2c4d81b3e7056kX2mNpQw")
UPLOAD_URL = os.environ.get("UPLOAD_URL", "http://10.243.187.65:3000/api/audio/upload")


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


def upload_to_db(filepath, duration_sec):
    """Upload a WAV file to the ROVER API. Returns True on success."""
    try:
        with open(filepath, "rb") as f:
            r = requests.post(
                UPLOAD_URL,
                headers={"X-API-Key": ROVER_API_KEY},
                files={"file": f},
                data={"duration": duration_sec},
                timeout=10
            )
        if r.ok:
            print(f"  Uploaded to DB ({os.path.getsize(filepath)} bytes)")
            return True
        else:
            print(f"  Upload failed: HTTP {r.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"  Upload error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', '-p', required=True)
    parser.add_argument('--output', '-o', default='output')
    parser.add_argument('--db', action='store_true', help='Upload WAVs to DB instead of saving locally')
    args = parser.parse_args()

    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    print(f"Opening {args.port} ...")
    ser = serial.Serial(args.port, BAUD, timeout=0.1, write_timeout=1)
    time.sleep(3.0)
    ser.reset_input_buffer()

    mode = "uploading to DB" if args.db else f"saving to {out_dir}/"
    print(f"Recording at {SAMPLE_RATE} Hz, {mode}")
    print("  (status every 1s — Ctrl+C to stop)")

    buf_samples = []            # samples for current 5-second block
    total_samples = 0
    next_save_at = SAVE_INTERVAL   # save when total_samples reaches this
    leftover = b''              # incomplete byte from previous read
    start = time.time()

    try:
        while True:
            raw = leftover + ser.read(4096)
            leftover = b''

            # Process complete uint16_t pairs
            n = len(raw)
            i = 0
            while i <= n - 2:
                val = struct.unpack('<H', raw[i:i+2])[0]
                if val > 4095:
                    val = 4095
                buf_samples.append((val << 4) - 32768)
                total_samples += 1
                i += 2

            # Keep one leftover byte if odd-length
            if i < n:
                leftover = raw[i:]

            # Check if it's time to save WAV
            if total_samples >= next_save_at:
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                elapsed = time.time() - start
                rate = total_samples / elapsed if elapsed else 0
                count = len(buf_samples)

                if args.db:
                    # Write to temp file, upload, delete on success only
                    tmp = os.path.join(out_dir, f"{ts}.wav")
                    write_wav(tmp, buf_samples, SAMPLE_RATE)
                    if upload_to_db(tmp, 5):
                        print(f"  {count} samples @ {rate:.0f} Hz — uploaded")
                        os.remove(tmp)
                    else:
                        print(f"  {count} samples @ {rate:.0f} Hz — upload failed, saved {tmp}")
                else:
                    fname = os.path.join(out_dir, f"{ts}.wav")
                    write_wav(fname, buf_samples, SAMPLE_RATE)
                    print(f"  Saved {fname} ({count} samples @ {rate:.0f} Hz)")

                buf_samples = []
                next_save_at += SAVE_INTERVAL

            # Status every STATUS_INTERVAL samples
            if total_samples % STATUS_INTERVAL < 2:
                elapsed = time.time() - start
                rate = total_samples / elapsed if elapsed else 0
                print(f"  {total_samples} samples @ {rate:.0f} Hz")

    except KeyboardInterrupt:
        t = time.time() - start
        ser.close()
        rate = total_samples / t if t else 0
        print(f"\n{total_samples} samples in {t:.1f}s ({rate:.0f} Hz)")
        # Partial block discarded


if __name__ == '__main__':
    main()
