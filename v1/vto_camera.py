import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


VTO_IP = os.environ.get("VTO_IP", "192.168.100.108")
VTO_USER = os.environ.get("VTO_USER", "admin")
VTO_PASS = os.environ.get("VTO_PASS", "Splitreset6901")
VTO_HTTP_PORT = int(os.environ.get("VTO_HTTP_PORT", "80"))
VTO_RTSP_PORT = int(os.environ.get("VTO_RTSP_PORT", "554"))
VTO_CHANNEL = int(os.environ.get("VTO_RTSP_CHANNEL", "1"))
VTO_SUBTYPE = int(os.environ.get("VTO_RTSP_SUBTYPE", "0"))
VTO_FAST_FACE_SUBTYPE = int(os.environ.get("VIGILIA_FAST_FACE_RTSP_SUBTYPE", "0"))
VTO_SNAPSHOT_TIMEOUT_SECONDS = float(
    os.environ.get("VIGILIA_VTO_SNAPSHOT_TIMEOUT_SECONDS", "5")
)
VTO_HTTP_SNAPSHOT_ENABLED = os.environ.get(
    "VIGILIA_VTO_HTTP_SNAPSHOT_ENABLED",
    "1",
).strip().lower() in {"1", "true", "yes", "on"}
VTO_HTTP_SNAPSHOT_PATH = os.environ.get(
    "VIGILIA_VTO_HTTP_SNAPSHOT_PATH",
    "/cgi-bin/snapshot.cgi",
)


def build_rtsp_url(
    ip=VTO_IP,
    user=VTO_USER,
    password=VTO_PASS,
    port=VTO_RTSP_PORT,
    channel=VTO_CHANNEL,
    subtype=VTO_SUBTYPE,
):
    return (
        f"rtsp://{user}:{password}@{ip}:{port}/cam/realmonitor"
        f"?channel={channel}&subtype={subtype}"
    )


def build_http_snapshot_url(
    ip=VTO_IP,
    port=VTO_HTTP_PORT,
    channel=VTO_CHANNEL,
    path=VTO_HTTP_SNAPSHOT_PATH,
):
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"http://{ip}:{port}{normalized_path}?channel={channel}"


def capture_snapshot_http(snapshot_path, channel=VTO_CHANNEL):
    snapshot_url = build_http_snapshot_url(channel=channel)
    result = subprocess.run(
        [
            "curl",
            "--silent",
            "--show-error",
            "--fail",
            "--location",
            "--anyauth",
            "--user",
            f"{VTO_USER}:{VTO_PASS}",
            "--connect-timeout",
            str(int(max(1, VTO_SNAPSHOT_TIMEOUT_SECONDS))),
            "--max-time",
            str(int(max(2, VTO_SNAPSHOT_TIMEOUT_SECONDS))),
            snapshot_url,
            "--output",
            str(snapshot_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=VTO_SNAPSHOT_TIMEOUT_SECONDS + 1,
    )

    if result.stdout.strip():
        print(f"[VTO] curl stdout: {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"[VTO] curl stderr: {result.stderr.strip()}")

    if result.returncode != 0:
        raise RuntimeError("HTTP snapshot capture failed")

    if not snapshot_path.exists() or snapshot_path.stat().st_size == 0:
        raise RuntimeError("HTTP snapshot saved empty file")

    print(f"[VTO] HTTP snapshot saved to {snapshot_path}")
    return snapshot_path


def show_live_view(channel=VTO_CHANNEL, subtype=VTO_SUBTYPE):
    rtsp_url = build_rtsp_url(channel=channel, subtype=subtype)
    print(f"[VTO] Opening live view for channel={channel}, subtype={subtype}")
    print(f"[VTO] URL: {rtsp_url}")

    return subprocess.run(
        ["ffplay", "-rtsp_transport", "tcp", rtsp_url],
        check=False,
    )


def capture_snapshot(output_path=None, channel=VTO_CHANNEL, subtype=VTO_SUBTYPE):
    snapshot_path = Path(output_path) if output_path else default_snapshot_path()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    if VTO_HTTP_SNAPSHOT_ENABLED:
        try:
            return capture_snapshot_http(snapshot_path=snapshot_path, channel=channel)
        except Exception as exc:
            print(f"[VTO] HTTP snapshot failed: {exc}")

    rtsp_url = build_rtsp_url(channel=channel, subtype=subtype)
    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-rtsp_transport",
            "tcp",
            "-i",
            rtsp_url,
            "-an",
            "-frames:v",
            "1",
            "-q:v",
            "4",
            "-update",
            "1",
            str(snapshot_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=VTO_SNAPSHOT_TIMEOUT_SECONDS + 1,
    )

    if result.stdout.strip():
        print(f"[VTO] ffmpeg stdout: {result.stdout.strip()}")
    if result.stderr.strip():
        print(f"[VTO] ffmpeg stderr: {result.stderr.strip()}")

    if result.returncode != 0:
        raise RuntimeError("Snapshot capture failed")

    print(f"[VTO] Snapshot saved to {snapshot_path}")
    return snapshot_path


def default_snapshot_path():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("captures") / f"vto_snapshot_{timestamp}.jpg"


def print_usage():
    print("Usage:")
    print("  python3 v1/vto_camera.py live")
    print("  python3 v1/vto_camera.py snapshot [output_path]")
    print("  python3 v1/vto_camera.py url")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    if command == "live":
        result = show_live_view()
        sys.exit(result.returncode)

    if command == "snapshot":
        output_path = sys.argv[2] if len(sys.argv) > 2 else None
        capture_snapshot(output_path=output_path)
        return

    if command == "url":
        print(build_rtsp_url())
        return

    print_usage()
    sys.exit(1)


if __name__ == "__main__":
    main()
