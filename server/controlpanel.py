import paho.mqtt.client as mqtt
import subprocess
import mysql.connector
import json
import time
import os
import logging
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler

# Inisialisasi logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Get the path to the log folder
log_folder = os.path.join(os.getcwd(), "log")

# Create the log folder if it doesn't exist
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

current_date = datetime.date.today()
# Convert the current_date object to a string representation
formatted_date = current_date.strftime("%Y-%m-%d")
# Specify the log file path
log_filename = os.path.join(log_folder, "api_" + formatted_date + ".log")

file_handler = TimedRotatingFileHandler(log_filename, when="midnight", interval=1, backupCount=7)

# Menentukan format log
log_format = "%(asctime)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)
file_handler.setFormatter(formatter)

# Menambahkan handler ke logger
logger.addHandler(file_handler)
logger.info("starting trilateration proses")
start_time = time.time()- (5 * 60)
connection = mysql.connector.connect(
    host='localhost',
    user='ta',
    password='Ta2023!',
    database='ta2023'
)
cursor = connection.cursor()
def stop_program1():
    process_name="kodenormal.py"
    # Execute the command to stop the other Python program
    command = f"pgrep -f {process_name}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode().strip()

    if output:
        pids = output.split('\n')
        for pid in pids:
            pid = int(pid)
            try:
                subprocess.run(['kill', str(pid)])
                print(f"Process with PID {pid} killed.")
            except subprocess.CalledProcessError:
                print(f"Failed to kill process with PID {pid}.")
    else:
        print(f"No process with name '{process_name}' is currently running.")
    client.publish("Log","mode perhitungan normal berhenti")

def stop_program2():
    client.publish("Log","mode kalibrasi berhenti")

    # Execute the command to stop the other Python program
    process_name="segitiga.py"
    # Execute the command to stop the other Python program
    command = f"pgrep -f {process_name}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode().strip()

    if output:
        pids = output.split('\n')
        for pid in pids:
            pid = int(pid)
            try:
                subprocess.run(['kill', str(pid)])
                print(f"Process with PID {pid} killed.")
            except subprocess.CalledProcessError:
                print(f"Failed to kill process with PID {pid}.")
    else:
        print(f"No process with name '{process_name}' is currently running.")
    
def on_message(client, userdata, message):
    payload_str = message.payload.decode('utf-8')
    global start_time
    elapsed_time = time.time() - start_time


    if message.topic=="xy":
        data_list = json.loads(payload_str)
        print(data_list)
        insert_query = "INSERT INTO location (x, y) VALUES (%s, %s)"
        if elapsed_time>300:
            cursor.execute(insert_query, (data_list['x'], data_list['y']))
            connection.commit()  # Commit the changes to the database
            start_time = time.time()
    if message.topic=="esp32/calibrasianchor":
        if payload_str=="start":
            stop_program1()
            run_program2()
        if payload_str=="finish":
            stop_program2()      
            run_program1()
def run_program1():
    logging.info("proses perhitungan menyala")
    subprocess.Popen("python3 kodenormal.py", shell=True)
    client.publish("Log","mode perhitungan normal")

    pass
def run_program2():
    pass
    subprocess.Popen("python3 segitiga.py", shell=True)

# Create MQTT client instance
client = mqtt.Client()
# Set the callback function
client.on_message = on_message
# Connect to MQTT broker
client.connect("192.168.0.166")
#list subs
client.subscribe("xy")
client.subscribe("esp32/calibrasianchor")


run_program1()

client.loop_forever()