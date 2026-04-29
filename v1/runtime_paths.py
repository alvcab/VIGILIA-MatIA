import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = Path(os.environ.get("VIGILIA_RUNTIME_DIR", PROJECT_ROOT / ".runtime"))
RUN_DIR = Path(os.environ.get("VIGILIA_RUN_DIR", RUNTIME_ROOT / "run"))
LOG_DIR = Path(os.environ.get("VIGILIA_LOG_DIR", RUNTIME_ROOT / "logs"))
AUDIO_DIR = Path(os.environ.get("VIGILIA_AUDIO_DIR", RUNTIME_ROOT / "audio"))
ASTERISK_DIR = Path(os.environ.get("VIGILIA_ASTERISK_DIR", RUNTIME_ROOT / "asterisk"))
ASTERISK_ETC_DIR = Path(
    os.environ.get("VIGILIA_ASTERISK_ETC_DIR", ASTERISK_DIR / "etc" / "asterisk")
)
ASTERISK_VAR_DIR = Path(
    os.environ.get("VIGILIA_ASTERISK_VAR_DIR", ASTERISK_DIR / "var")
)

INFERENCE_SOCKET_PATH = Path(
    os.environ.get("VIGILIA_INFERENCE_SOCKET", RUN_DIR / "vigilia_inference.sock")
)
INFERENCE_LOG_PATH = Path(
    os.environ.get("VIGILIA_INFERENCE_LOG", LOG_DIR / "vigilia_inference.log")
)
DEFAULT_AUDIO_PATH = Path(
    os.environ.get("VIGILIA_DEFAULT_AUDIO_PATH", AUDIO_DIR / "vecino.wav")
)
DEFAULT_RESPONSE_AUDIO_PATH = Path(
    os.environ.get("VIGILIA_DEFAULT_RESPONSE_AUDIO_PATH", AUDIO_DIR / "ia_dice.wav")
)
PROMPT_AUDIO_BASE = Path(
    os.environ.get("VIGILIA_PROMPT_AUDIO_BASE", AUDIO_DIR / "vigilia_prompt")
)
LISTEN_AUDIO_BASE = Path(
    os.environ.get("VIGILIA_LISTEN_AUDIO_BASE", AUDIO_DIR / "vigilia_listen")
)
ASTERISK_LOG_PATH = Path(
    os.environ.get("VIGILIA_ASTERISK_LOG_PATH", LOG_DIR / "vigilia_asterisk.log")
)


def ensure_runtime_directories():
    for directory in (
        RUNTIME_ROOT,
        RUN_DIR,
        LOG_DIR,
        AUDIO_DIR,
        ASTERISK_DIR,
        ASTERISK_ETC_DIR,
        ASTERISK_VAR_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
