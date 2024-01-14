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