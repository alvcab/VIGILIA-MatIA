#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rtsp-url", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-seconds", type=float, default=10.0)
    parser.add_argument("--log-prefix", default="[RTSP_CAPTURE]")
    return parser.parse_args()


def main():
    args = parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
      print(f"{args.log_prefix} ffmpeg_not_found")
      return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_output_path = output_path.with_name(output_path.stem + "_partial" + output_path.suffix)

    if tmp_output_path.exists():
        tmp_output_path.unlink()

    cmd = [
        ffmpeg,
        "-y",
        "-rtsp_transport",
        "tcp",
        "-i",
        args.rtsp_url,
        "-vn",
        "-t",
        str(args.max_seconds),
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(tmp_output_path),
    ]

    print(
        f"{args.log_prefix} starting output={output_path} "
        f"max_seconds={args.max_seconds}"
    )

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    assert process.stderr is not None
    for line in process.stderr:
        line = line.rstrip()
        if line:
            print(line)

    return_code = process.wait()

    if return_code != 0 and not tmp_output_path.exists():
        print(f"{args.log_prefix} ffmpeg_failed exit_code={return_code}")
        return return_code

    if tmp_output_path.exists():
        os.replace(tmp_output_path, output_path)
        print(f"{args.log_prefix} completed output={output_path}")
        return 0

    print(f"{args.log_prefix} no_output_generated exit_code={return_code}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
