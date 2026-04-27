from pathlib import Path
import subprocess
import sys

DEFAULT_OUTPUT_PATH = Path("/tmp/vigilia_prompt.wav")
DEFAULT_TEXT = "Hola."


def build_greeting(text, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_audio_path = output_path.with_suffix(".aiff")

    say_result = subprocess.run(
        [
            "say",
            "-v",
            "Monica",
            "-o",
            str(temp_audio_path),
            text,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if say_result.returncode != 0:
        raise RuntimeError("could_not_generate_greeting_with_say")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(temp_audio_path),
            "-ar",
            "8000",
            "-ac",
            "1",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    temp_audio_path.unlink(missing_ok=True)
    return output_path


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEXT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result_path = build_greeting(text=text, output_path=output_path)
    print(result_path)
