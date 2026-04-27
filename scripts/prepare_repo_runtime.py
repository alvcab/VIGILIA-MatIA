import getpass
import grp
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from v1_sin_IA.runtime_paths import (  # noqa: E402
    ASTERISK_ETC_DIR,
    ASTERISK_VAR_DIR,
    AUDIO_DIR,
    LOG_DIR,
    PROJECT_ROOT,
    RUNTIME_ROOT,
    ensure_runtime_directories,
)


TEMPLATE_FILES = {
    PROJECT_ROOT / "v1_sin_IA" / "asterisk" / "asterisk.conf": ASTERISK_ETC_DIR / "asterisk.conf",
    PROJECT_ROOT / "v1_sin_IA" / "asterisk" / "extensions.conf": ASTERISK_ETC_DIR / "extensions.conf",
    PROJECT_ROOT / "v1_sin_IA" / "asterisk" / "pjsip.conf": ASTERISK_ETC_DIR / "pjsip.conf",
}


def render_template(source_path: Path, target_path: Path, replacements: dict[str, str]):
    content = source_path.read_text()
    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content)


def main():
    ensure_runtime_directories()

    runtime_user = os.environ.get("VIGILIA_RUNTIME_USER", getpass.getuser())
    runtime_group = os.environ.get(
        "VIGILIA_RUNTIME_GROUP",
        grp.getgrgid(os.getgid()).gr_name,
    )
    replacements = {
        "__VIGILIA_PROJECT_DIR__": str(PROJECT_ROOT),
        "__VIGILIA_RUNTIME_DIR__": str(RUNTIME_ROOT),
        "__VIGILIA_AUDIO_DIR__": str(AUDIO_DIR),
        "__VIGILIA_LOG_DIR__": str(LOG_DIR),
        "__VIGILIA_ASTERISK_ETC_DIR__": str(ASTERISK_ETC_DIR),
        "__VIGILIA_ASTERISK_VAR_DIR__": str(ASTERISK_VAR_DIR),
        "__VIGILIA_RUNTIME_USER__": runtime_user,
        "__VIGILIA_RUNTIME_GROUP__": runtime_group,
    }

    for source_path, target_path in TEMPLATE_FILES.items():
        render_template(source_path, target_path, replacements)

    for relative_dir in (
        "lib",
        "keys",
        "agi-bin",
        "spool",
        "run",
        "log",
    ):
        (ASTERISK_VAR_DIR / relative_dir).mkdir(parents=True, exist_ok=True)

    print(str(RUNTIME_ROOT))


if __name__ == "__main__":
    main()
