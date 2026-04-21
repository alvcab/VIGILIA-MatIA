import subprocess
import sys
from datetime import datetime
from pathlib import Path


VTO_IP = "192.168.100.108"
VTO_USER = "admin"
VTO_PASS = "Splitreset6901"
VTO_RTSP_PORT = 554
VTO_CHANNEL = 1
VTO_SUBTYPE = 0


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


def show_live_view(channel=VTO_CHANNEL, subtype=VTO_SUBTYPE):
    rtsp_url = build_rtsp_url(channel=channel, subtype=subtype)
    print(f"[VTO] Opening live view for channel={channel}, subtype={subtype}")
    print(f"[VTO] URL: {rtsp_url}")

    return subprocess.run(
        ["ffplay", "-rtsp_transport", "tcp", rtsp_url],
        check=False,
    )


def capture_snapshot(output_path=None, channel=VTO_CHANNEL, subtype=VTO_SUBTYPE):
    rtsp_url = build_rtsp_url(channel=channel, subtype=subtype)
    snapshot_path = Path(output_path) if output_path else default_snapshot_path()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-rtsp_transport",
            "tcp",
            "-i",
            rtsp_url,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(snapshot_path),
        ],
        capture_output=True,
        text=True,
        check=False,
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
    print("  python3 v1_sin_IA/vto_camera.py live")
    print("  python3 v1_sin_IA/vto_camera.py snapshot [output_path]")
    print("  python3 v1_sin_IA/vto_camera.py url")


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
