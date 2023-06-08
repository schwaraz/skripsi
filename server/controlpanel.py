import paho.mqtt.client as mqtt
import subprocess
import mysql.connector
import json
import time
start_time = time.time()- (5 * 60)
connection = mysql.connector.connect(
    host='localhost',
    user='ta',
    password='Ta2023!',
    database='ta2023'
)
cursor = connection.cursor()
def stop_program1():
    # Execute the command to stop the other Python program
    subprocess.run(["pkill", "-f", "kodenormal.py"])
def stop_program2():
    # Execute the command to stop the other Python program
    subprocess.run(["pkill", "-f", "segitiga.py"])
    
def on_message(client, userdata, message):
    payload_str = message.payload.decode('utf-8')
    global start_time
    elapsed_time = time.time() - start_time
    if message.topic=="esp32/calibrasianchor":
        pass

    if message.topic=="controlpanel":
        if payload_str=="1":
            run_program1()
        elif payload_str=="0":
            stop_program1()
    if message.topic=="hasilkoordinat":
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
    
    # subprocess.Popen("python3 kodenormal.py", shell=True)
    pass
def run_program2():
    pass
    # subprocess.Popen("python3 segitiga.py", shell=True)

# Create MQTT client instance
client = mqtt.Client()
# Set the callback function
client.on_message = on_message
# Connect to MQTT broker
client.connect("192.168.1.12")
#list subs
client.subscribe("controlpanel")
client.subscribe("hasilkoordinat")
client.subscribe("esp32/calibrasianchor")


run_program1()

client.loop_forever()