# AIR780E USB SMS CLI

A command-line tool for **sending and receiving SMS** via the **AIR780E (USB version)**.
Incoming messages are forwarded to a local file, and outgoing messages can be sent directly from the CLI.

## Usage

### Preparation

Ensure your user account has permission to access serial devices:

```bash
sudo usermod -aG dialout $USER
```

Log out and log back in for the change to take effect.

### Python Environment

Run `uv sync` to set up a virtual environment with dependencies installed.

### Listening for Incoming SMS

To start listening for incoming SMS messages and logging them to `messages.jsonl`:

```bash
uv run air780e listen
```

### Sending a Test SMS

To send a test SMS message to a specified phone number:

```bash
uv run air780e send-sms --phone 1234567890 --message "Hello, World!"
```

## Current Firmware Compatibility

Current version is based on AIR780E v7.2 firmware, and the AT command set [v1.6.7](https://docs.openluat.com/cdn/%E4%B8%8A%E6%B5%B7%E5%90%88%E5%AE%99Cat.1%E6%A8%A1%E7%BB%84(%E7%A7%BB%E8%8A%AFEC618&EC716&EC718%E5%B9%B3%E5%8F%B0%E7%B3%BB%E5%88%97)AT%E5%91%BD%E4%BB%A4%E6%89%8B%E5%86%8CV1.6.7.pdf).

Tested with Ubuntu 24.04 and Python 3.12.

### Previous Versions

Earlier versions of this tool are available on the branch:

```
archive/v2.0
```

⚠️ **Note:**
The archived version is **no longer maintained** and is **not compatible** with newer AIR780E firmware, as the AT command set has changed.
For current firmware, please use the latest version on `main`.

## References

- [AT Command Intro (合宙模组典型上网业务的 AT 上网流程)](https://docs.openluat.com/air780e/common/Air_AT/)
- [AT Command Set (Air780E模块AT指令手册)](https://docs.openluat.com/air780e/at/app/at_command/)
