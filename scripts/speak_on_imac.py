import argparse
import subprocess
import sys
from pathlib import Path


def speak_text(text):
    try:
        result = subprocess.run(
            ["say", "-v", "Monica", text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=6,
            check=False,
        )
    except Exception as exc:
        print(f"method=local_say_failed detail={exc}")
        return False
    if result.returncode == 0:
        print("method=local_say")
        return True
    print(f"method=local_say_failed detail=returncode={result.returncode}")
    return False


def play_audio(audio_path: Path):
    try:
        result = subprocess.run(
            ["afplay", str(audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=6,
            check=False,
        )
    except Exception as exc:
        print(f"method=local_afplay_failed detail={exc}")
        return False
    if result.returncode == 0:
        print("method=local_afplay")
        return True
    print(f"method=local_afplay_failed detail=returncode={result.returncode}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("text", nargs="?", default="")
    parser.add_argument("--audio-path", dest="audio_path")
    args = parser.parse_args()

    if args.audio_path:
        audio_path = Path(args.audio_path)
        if audio_path.exists() and play_audio(audio_path):
            return 0

    if args.text and speak_text(args.text):
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
