import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = PROJECT_ROOT / ".runtime" / "audio"
RTSP_PATTERN = "vigilia_in_*_rtsp.wav"


def print_usage():
    print("Uso:")
    print("  python3 v1/ver_ultimo_rtsp_audio.py")
    print("  python3 v1/ver_ultimo_rtsp_audio.py --play")


def find_latest_rtsp_audio():
    matches = sorted(
        TMP_DIR.glob(RTSP_PATTERN),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def run_command(command):
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def print_ffprobe(path):
    result = run_command(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-of",
            "default=noprint_wrappers=1",
            str(path),
        ]
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())


def print_volume(path):
    result = run_command(
        [
            "ffmpeg",
            "-i",
            str(path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    lines = result.stderr.splitlines()
    interesting = [
        line.strip()
        for line in lines
        if "mean_volume" in line or "max_volume" in line
    ]
    if interesting:
        print("\n".join(interesting))


def main():
    play_audio = False

    if len(sys.argv) > 2:
        print_usage()
        sys.exit(1)

    if len(sys.argv) == 2:
        if sys.argv[1] != "--play":
            print_usage()
            sys.exit(1)
        play_audio = True

    latest = find_latest_rtsp_audio()

    if latest is None:
        print(f"No encontre audios RTSP en {TMP_DIR}.")
        sys.exit(1)

    print(f"path: {latest}")
    print_ffprobe(latest)
    print_volume(latest)

    if play_audio:
        subprocess.run(["afplay", str(latest)], check=False)


if __name__ == "__main__":
    main()
