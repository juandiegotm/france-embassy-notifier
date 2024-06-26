import time
import logging  
import json
import os
import subprocess
import requests
import tarfile
import random

import io

from helpers import Time

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
FFMPEG_STATIC_URL = "https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz"
OUTPUT_FOLDER = "./ffmpeg"

def as_loop():
    logging.info("Process started")
    logging.info("Delay between queries around %ds (+- 10)", Time.RETRY_TIME)
    from embassy_service import EmbassyService

    handler = EmbassyService()
    while True:        
        try:
            result = handler.main()
            # next_launch = random.randint(Time.RETRY_TIME - 10, Time.RETRY_TIME + 10)
            next_launch = Time.RETRY_TIME
            logging.info(f"Next launch in: {next_launch}s")
            time.sleep(next_launch)
        except Exception as e:
            logging.error("Exception occurred", exc_info=True)
            time.sleep(Time.EXCEPTION_TIME)

def as_lambda_function():
    if not os.path.exists(OUTPUT_FOLDER):
        get_ffmpeg_folder()

    data = {"retry_value": Time.RETRY_TIME // 60}
    temp_file = "json_var.json"
    with open(temp_file, "w") as write_file:
        json.dump(data, write_file, indent=4)
    subprocess.run(["sls", "deploy"], shell=True)
    os.remove(temp_file)

def get_ffmpeg_folder():
    response = requests.get(FFMPEG_STATIC_URL)
    completed = False
    logging.info("Downloading file...")
    if response.status_code != 200:
        raise Exception("Can't download ffmpeg file. Try again.")
    
    binary_data = io.BytesIO(response.content)
    with tarfile.open(fileobj=binary_data, mode='r:xz') as tar:
        logging.info("Decompressing file...")
        tar.extractall("./")

    for entry in os.listdir("./"): 
        if entry.startswith("ffmpeg"):
            os.rename(entry, OUTPUT_FOLDER)
            completed = True
    
    if not completed:
        raise Exception("Can't download ffmpeg file. Try again.")