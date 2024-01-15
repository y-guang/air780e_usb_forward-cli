# AIR780E USB FORWARD CLI

Command line tool that forwards sms messages from an AIR780E USB version to a local file and sends messages.

Never use it for illegal purposes.

## Preparation

Change the encoding of the device to gbk.

## Usage

1. Edit [settings.py](air780e_usb_forward/settings.py) to set the device path and the path to the file that will be used to store the messages.
2. Run [air780e_recording.py](air780e_usb_forward/air780e_recording.py) to listen to the device and store the messages in the file.
3. Run [air780e_send.py](air780e_usb_forward/air780e_send.py) to send messages. run `python3 air780e_usb_forward/air780e_send.py` for help.

## Dependencies

No dependencies. Although poetry is used for dependency management, it is not required for installation.

## How to auto start

After setup you may want to automatically start the recorder when the system starts.

### For Recorder

Modify following template and save in `/etc/systemd/system` as server. e.g. `/etc/systemd/system/air780e_recording.service`

```ini
[Unit]
Description=air780e_recording
After=network.target

[Service]
User=<your-username>
WorkingDirectory=/path/to/the/project
ExecStart=/usr/bin/python3 /path/to/your/air780e_recording.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

run

```bash
sudo systemctl daemon-reload
sudo systemctl enable air780e_recording.service
sudo systemctl start air780e_recording.service
```

Then, send some command, e.g. `python3 air780e_usb_forward-cli/air780e_send.py -r ATI`, check your log file.

### auto check log

alias `sms_check` to tail the log file. Tip: put it in your `.bashrc` or `.zshrc` for permanent effect.

```bash
alias sms_check='tail /path/to/your/log/file'
```

### for Sender

alias `sms_send` to send message.

```bash
alias sms_send='python3 /path/to/your/air780e_send.py'
```