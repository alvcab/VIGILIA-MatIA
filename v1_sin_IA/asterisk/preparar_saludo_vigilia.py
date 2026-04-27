from pathlib import Path
import subprocess
import sys

try:
    from v1_sin_IA.runtime_paths import PROMPT_AUDIO_BASE, ensure_runtime_directories
except ModuleNotFoundError:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from v1_sin_IA.runtime_paths import PROMPT_AUDIO_BASE, ensure_runtime_directories

DEFAULT_OUTPUT_PATH = PROMPT_AUDIO_BASE.with_suffix(".wav")
DEFAULT_TEXT = "Hola. Por favor espere."


def render_asterisk_audio_variants(source_audio_path, output_base_path):
    output_base_path = Path(output_base_path)
    wav_path = output_base_path.with_suffix(".wav")
    alaw_path = output_base_path.with_suffix(".alaw")
    ulaw_path = output_base_path.with_suffix(".ulaw")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-af",
            "adelay=120|120,apad=pad_dur=0.4,volume=1.8",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(wav_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-af",
            "adelay=120|120,apad=pad_dur=0.4,volume=1.8",
            "-f",
            "alaw",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(alaw_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-af",
            "adelay=120|120,apad=pad_dur=0.4,volume=1.8",
            "-f",
            "mulaw",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(ulaw_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def build_greeting(text, output_path):
    ensure_runtime_directories()
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

    render_asterisk_audio_variants(
        source_audio_path=temp_audio_path,
        output_base_path=output_path.with_suffix(""),
    )
    temp_audio_path.unlink(missing_ok=True)
    return output_path


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEXT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT_PATH
    result_path = build_greeting(text=text, output_path=output_path)
    print(result_path)
