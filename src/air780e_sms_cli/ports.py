from pathlib import Path

DEVICE_DIR = Path("/dev/serial/by-id")
DEVICE_PREFIX = "usb-EigenComm_EigenComm_Compo"


def _read_sysfs_interface(dev_path: Path) -> str:
    """Best-effort read of the USB interface name from sysfs.

    The symlink /dev/ttyX usually maps to /sys/class/tty/ttyX/device.
    The USB interface string is exposed as the "interface" file either on
    that path or one of its parents.
    """
    # /sys/class/tty/<name>/device/interface is the common location.
    sys_class_path = Path("/sys/class/tty") / dev_path.name / "device"
    candidates = [sys_class_path / "interface"]

    # Walk a few parents in case the interface file sits higher up the tree.
    current = sys_class_path
    for _ in range(3):
        current = current.parent
        candidates.append(current / "interface")

    for candidate in candidates:
        try:
            text = candidate.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            continue
        if text:
            return text
    return ""


def list_at_devices() -> list[str]:
    """Return /dev paths whose USB interface string is "AT".

    We scan /dev/serial/by-id for EigenComm composite device symlinks and read
    the sysfs "interface" attribute to confirm the AT interface.
    """
    try:
        candidates = list(DEVICE_DIR.glob(f"{DEVICE_PREFIX}*"))
    except FileNotFoundError:
        return []

    results: list[str] = []

    for link in candidates:
        try:
            dev_path = link.resolve(strict=True)
            interface = _read_sysfs_interface(dev_path).strip().lower()
        except Exception:
            continue

        if interface == "at":
            results.append(str(dev_path))

    return results


if __name__ == "__main__":
    ports = list_at_devices()
    if not ports:
        print("[]")
    else:
        print(ports)
