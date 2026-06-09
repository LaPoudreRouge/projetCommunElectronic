"""
receive.py — Capture audio from Tiva C LaunchPad over serial.

Usage:
    python receive.py                  # auto-detect Tiva port
    python receive.py --port COM3      # specify port manually
    python receive.py --output test.wav

Press Ctrl+C to stop recording and write the WAV file.
"""

import argparse
import struct
import sys
import time
import serial
import serial.tools.list_ports

HANDSHAKE_SEND = b'\xAA'
HANDSHAKE_REPLY = b'\xBB'
BAUD = 460800
SAMPLE_RATE = 10000
WAV_CHANNELS = 1
WAV_BITS = 16


def find_tiva_port() -> str | None:
    """Scan all COM ports, send handshake, return the port that replies."""
    ports = list(serial.tools.list_ports.comports())
    print(f"Scanning {len(ports)} port(s)...")

    for port in ports:
        try:
            ser = serial.Serial(
                port.device, BAUD, timeout=0.5, write_timeout=0.5
            )
            time.sleep(0.2)  # let the DTR reset settle
            ser.write(HANDSHAKE_SEND)
            reply = ser.read(1)
            ser.close()
            if reply == HANDSHAKE_REPLY:
                print(f"  -> Tiva found on {port.device}")
                return port.device
            else:
                print(f"  {port.device}: no handshake")
        except (serial.SerialException, OSError):
            print(f"  {port.device}: can't open")
            continue

    return None


def write_wav(filename: str, samples: list[int], sample_rate: int):
    """Write a WAV file from signed 16-bit samples."""
    num_samples = len(samples)
    data_size = num_samples * WAV_CHANNELS * (WAV_BITS // 8)
    fmt_size = 16
    audio_format = 1  # PCM

    with open(filename, 'wb') as f:
        # RIFF header
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')

        # fmt chunk
        f.write(b'fmt ')
        f.write(struct.pack('<I', fmt_size))
        f.write(struct.pack('<H', audio_format))
        f.write(struct.pack('<H', WAV_CHANNELS))
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * WAV_CHANNELS * (WAV_BITS // 8)))
        f.write(struct.pack('<H', WAV_CHANNELS * (WAV_BITS // 8)))
        f.write(struct.pack('<H', WAV_BITS))

        # data chunk
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        for s in samples:
            f.write(struct.pack('<h', s))


def main():
    parser = argparse.ArgumentParser(description="Capture audio from Tiva C LaunchPad")
    parser.add_argument('--port', '-p', help="Serial port (e.g. COM3)")
    parser.add_argument('--output', '-o', default='output.wav', help="Output WAV file")
    parser.add_argument('--list', '-l', action='store_true', help="List ports and exit")
    args = parser.parse_args()

    if args.list:
        for p in serial.tools.list_ports.comports():
            print(f"{p.device} — {p.description}")
        return

    # Find the Tiva
    port = args.port or find_tiva_port()
    if not port:
        print("ERROR: Tiva not found. Specify port with --port or check connection.")
        sys.exit(1)

    # Open and handshake
    ser = serial.Serial(port, BAUD, timeout=1, write_timeout=1)
    time.sleep(0.2)
    ser.reset_input_buffer()
    ser.write(HANDSHAKE_SEND)
    reply = ser.read(1)

    if reply != HANDSHAKE_REPLY:
        print(f"ERROR: Handshake failed on {port} (got {reply.hex() if reply else 'nothing'})")
        ser.close()
        sys.exit(1)

    print(f"Connected to {port}, recording at {SAMPLE_RATE} Hz…")
    print("Press Ctrl+C to stop.")

    samples: list[int] = []
    dropped = 0
    start = time.time()

    try:
        while True:
            raw = ser.read(2)
            if len(raw) < 2:
                continue

            b0, b1 = raw[0], raw[1]

            # Validate marker bit
            if not (b0 & 0x80):
                dropped += 1
                continue

            # Extract 12-bit sample
            sample = ((b0 & 0x0F) << 8) | b1
            # Convert to signed 16-bit for WAV
            wav_sample = (sample << 4) - 32768
            samples.append(wav_sample)

    except KeyboardInterrupt:
        duration = time.time() - start
        ser.write(b'\xCC')  # tell Tiva to stop
        ser.close()

        actual_rate = len(samples) / duration if duration > 0 else 0

        print(f"\nCaptured {len(samples)} samples in {duration:.1f}s ({actual_rate:.0f} Hz avg)")
        if dropped:
            print(f"Sync errors (dropped frames): {dropped}")

        write_wav(args.output, samples, SAMPLE_RATE)
        print(f"Written to {args.output} ({len(samples)} samples, {SAMPLE_RATE} Hz, {WAV_BITS}-bit)")


if __name__ == '__main__':
    main()
