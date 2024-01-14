"""
Send message using air780e usb version.
Note:
    1. designed to be used in command line.
    2. it is intended to add a delay after each sending, to avoid flooding services.
"""
import serial
from settings import LOG_FILE_PATH, DEVICE_NAME
from datetime import datetime
import time
import argparse

DEVICE_NAME = '/dev/ttyUSB0'

ser = serial.Serial(DEVICE_NAME, 115200)


def write_log(text):
    with open(LOG_FILE_PATH, 'a+', encoding='utf-8') as out:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_text = f"{current_time} {text}\n"
        out.write(formatted_text)
        out.flush()


def write(raw: str):
    write_log(f"attempt send to [{DEVICE_NAME}]: {raw}")
    time.sleep(1)  # change sending delay here
    try:
        ser.write(raw.encode('gbk'))
    except Exception as e:
        write_log(f"failed")
        raise e
    print(f"sent: {raw}")


# Methods for different commands
def write_raw(raw: str):
    if not raw.endswith('\r\n'):
        raw += '\r\n'
    write(raw)


def send_file(phone: str, path: str):
    with open(path, 'r') as f:
        text = f.read()
        raw = f'AT+SMSSEND="{phone}","{text}"\r\n'
        write(raw)


def send_message(phone: str, text: str):
    raw = f'AT+SMSSEND="{phone}","{text}"\r\n'
    write(raw)


# parse arguments and execute
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--phone', help='phone number')
parser.add_argument('-f', '--file', help='file path')
parser.add_argument('-t', '--text', help='text')
parser.add_argument('-r', '--raw', help='raw command')
args = parser.parse_args()

if args.raw:
    write_raw(args.raw)
    exit(0)

if args.phone and args.file:
    send_file(args.phone, args.file)
    exit(0)

if args.phone and args.text:
    send_message(args.phone, args.text)
    exit(0)

print('invalid arguments')
exit(1)
