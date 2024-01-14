"""
script for recording all messages to a file.
Note:
    1. needed to be run 7x24, otherwise messages will be lost
"""

import serial
import time
from datetime import datetime
from settings import LOG_FILE_PATH, DEVICE_NAME

def write_log(text):
    with open(LOG_FILE_PATH, 'a+', encoding='utf-8') as out:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_text = f"{current_time} recv [{DEVICE_NAME}] {text}\n"
        out.write(formatted_text)
        out.flush()

# keep reading and recording
while True:
    try:
        ser = serial.Serial(DEVICE_NAME, 115200)
        while True:
            line = ser.readline()
            decoded_text = line.decode('gbk', 'ignore')
            write_log(decoded_text)
    except Exception as e:
        # ignore all exceptions and retry
        write_log(f"exception: {e}")
        time.sleep(60)
        continue