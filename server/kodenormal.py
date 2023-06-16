import paho.mqtt.client as mqtt
import numpy as np
import threading
import os
import json
import sys
from sympy import symbols, Eq, solve
import mysql.connector
import datetime
import time
import math
import numpy as np
import queue


jumlahdata=0
data_queue1 = queue.Queue()
dummtx=0
dummty=0
data_queue2 = queue.Queue()
data_queue3 = queue.Queue()
xanchor1=0
yanchor1=0
zanchor1=0
xanchor2=0
yanchor2=0
zanchor2=0
xanchor3=0
yanchor3=0
restartx=0
restarty=0
restartz=0

zanchor3=0
i1=0
i2=0
i3=0
connection = mysql.connector.connect(
    host='localhost',
    user='ta',
    password='Ta2023!',
    database='ta2023'
)
cursor = connection.cursor()
def datakoordinatanchor():
    global xanchor1,yanchor1,xanchor2,yanchor2,xanchor3,yanchor3,zanchor3,zanchor2,zanchor1
    select_query = "SELECT x1,y1,z1,x2,y2,z2,x3,y3,z3 FROM kordinatanchor ORDER BY time DESC LIMIT 1"
    cursor.execute(select_query)
    rows = cursor.fetchall()
    xanchor1,yanchor1,zanchor1,xanchor2,yanchor2,zanchor2,xanchor3,yanchor3,zanchor3=rows[0]
state1= False
state2= False
state3= False
dummytopic1=None
dummytopic2=None
dummytopic3=None
def calculate_reduction(input_data):
    if input_data < 3:
        reduction = 0
    elif input_data > 3 and input_data<3.3:
        reduction = 0
    elif input_data >= 3.3 and input_data<4.8:
        reduction = 0.1
    elif input_data >= 3.8 and input_data<4.4:
        reduction = 0.15
    elif input_data >= 4.5 and input_data < 4.7:
        reduction = 0.2
    elif input_data >= 4.7 and input_data<4.9:
        reduction = 0.5
    elif input_data < 5:
        reduction = 0.7
    else:
        reduction = (input_data - 4) * 0.2 

    return reduction
def jaraksesungguhnya(xanchor1,yanchor1,zanchor1,xanchor2,yanchor2,zanchor2,xanchor3,yanchor3,zanchor3,a1,a2,a3,center):
    inputx=0
    inputy=-3
    inputz=0

    r1=math.sqrt((inputx-xanchor1)**2+(inputy-yanchor1)**2+(inputz-zanchor1)**2)
    r2=math.sqrt((inputx-xanchor2)**2+(inputy-yanchor2)**2+(inputz-zanchor2)**2)
    r3=math.sqrt((inputx-xanchor3)**2+(inputy-yanchor3)**2+(inputz-zanchor3)**2)
    return r1,r2,r3

barrier = threading.Barrier(3)  # Number of threads
class KalmanFilter(object):
    def __init__(self, F = None, B = None, H = None, Q = None, R = None, P = None, x0 = None):

        if(F is None or H is None):
            raise ValueError("Set proper system dynamics.")

        self.n = F.shape[1]
        self.m = H.shape[1]

        self.F = F
        self.H = H
        self.B = 0 if B is None else B
        self.Q = np.eye(self.n) if Q is None else Q
        self.R = np.eye(self.n) if R is None else R
        self.P = np.eye(self.n) if P is None else P
        self.x = np.zeros((self.n, 1)) if x0 is None else x0

    def predict(self, u = 0):
        self.x = np.dot(self.F, self.x) + np.dot(self.B, u)
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self.x

    def update(self, z):
        y = z - np.dot(self.H, self.x)
        S = self.R + np.dot(self.H, np.dot(self.P, self.H.T))
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        self.x = self.x + np.dot(K, y)
        I = np.eye(self.n)
        self.P = np.dot(np.dot(I - np.dot(K, self.H), self.P), 
            (I - np.dot(K, self.H)).T) + np.dot(np.dot(K, self.R), K.T)


def solve_inequalities(x1, y1, z1, x2, y2, z2, x3, y3, z3,r1,r2, r3):
    global kx,ky,kf1,kf2,kf3
    global dummtx,dummty
    x, y, z = symbols('x y z')
    print(x1, y1, z1, x2, y2, z2, x3, y3, z3,r1,r2, r3)
    eq1 = Eq((x - x1)**2 + (y - y1)**2 + (z - z1)**2 , r1**2)
    eq2 = Eq((x - x2)**2 + (y - y2)**2 + (z - z2)**2 , r2**2)
    eq3 = Eq((x - x3)**2 + (y - y3)**2 + (z - z3)**2 , r3**2)
    
    solutions = solve((eq1, eq2, eq3), (x, y, z))  
    for solution in solutions:
        x_val = solution[0]
        y_val = solution[1]
        z_val = solution[2]
        if x_val.is_real and y_val.is_real and z_val.is_real:
            # print("trianggulasi berhasil data real")
            
            return (x_val,y_val)
        else:
            return None

    
    
def conecttopic1(dummy):
    client = mqtt.Client()
    client.on_message = handle_topic1_message     # Set the callback function
    client.connect(dummy)     # Connect to MQTT broker
    client.subscribe("esp32/jarak1")     # Handler function for topic1
    client.loop_forever()
def conecttopic2(dummy):
    client = mqtt.Client()
    client.on_message = handle_topic2_message     # Set the callback function
    client.connect(dummy)     # Connect to MQTT broker
    client.subscribe("esp32/jarak2")     # Handler function for topic1
    client.loop_forever()
    x=0
    dummy=0
def conecttopic3(dummy):
    client = mqtt.Client()
    client.on_message = handle_topic3_message     # Set the callback function
    client.connect(dummy)     # Connect to MQTT broker
    client.subscribe("esp32/jarak3")     # Handler function for topic1
    client.loop_forever()
def senddata(dummy,koordinat,hslsesungguhnya,data1,data2,data3):
        # Extract x and y values from the koordinat tuple
    global xanchor1,yanchor1,xanchor2,yanchor2,xanchor3,yanchor3,zanchor3,zanchor2,zanchor1
    if koordinat != "error":
        x= koordinat[0]
        y= koordinat[1]
        
        # Convert x and y to strings
        x = str(x)
        y = str(y)
    else:
        x="gagal"
        y="gagal"
    
    r1,r2,r3=hslsesungguhnya
    r1 = str(r1)
    r2 = str(r2)
    r3 = str(r3)
    data1 = str(data1)
    data2 = str(data2)
    data3 = str(data3)
    # Create a dictionary with x and y keys
    data_dict = {'x': x, 'y': y, 'harusnyaa1':r1,'harusnyaa2':r2,'harusnyaa3':r3,'a1':data1,'a2':data2,'a3':data3,'xa1':xanchor1,'ya1':yanchor1,'za1':zanchor1,'xa2':xanchor2,'ya2':yanchor2,'za2':zanchor2,'xa3':xanchor3,'ya3':yanchor3,'za3':zanchor3}
    potition={'x': x, 'y': y}
    tes = json.dumps(data_dict)
    potition=json.dumps(potition)
    client = mqtt.Client()
    client.connect(dummy)     # Connect to MQTT broker
    print(tes)
    if koordinat != "error":
        client.publish("xy",potition)
        client.publish("hasilkoordinat",tes)
    client.disconnect()

def handle_topic1_message(client, userdata, message,):
    payload = message.payload.decode("utf-8")
    global i1
    global kf1
    global jumlahdata
    global state1
    global dummytopic1
    global restartx
    jumlahdata+=1

    try:
        measurement=float(payload)
        measurement= round(measurement,2)
        if(measurement<10 and measurement>=0):
            # print(measurement)
            restartx+=1
            if state1 == False:
                if dummytopic1 is None:
                    kf1.update(measurement)
                    prediction = np.dot(H, kf1.predict())[0]
                    dummytopic1=prediction
                    data_queue1.put((prediction))
                    state1 = True
                    time.sleep(0.5)
                else:
                    delta=dummytopic1-measurement
                    kf1.update(measurement)
                    prediction = np.dot(H, kf1.predict())[0]
                    dummytopic1=prediction
                    data_queue1.put((prediction))
                    state1 = True
                    i1=0
                    time.sleep(0.5)

            else:
                delta=dummytopic1-measurement
                if -3-i1<delta<3+i1:
                #     pass
                    kf1.update(measurement)
    except ValueError:
        pass
# Handler function for topic2
def handle_topic2_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    global kf2
    global state2
    global dummytopic2
    global i2
    global restarty

    try:
        measurement=float(payload)
        measurement= round(measurement,2)

        if(measurement<10 and measurement>=0):
            restarty+=1

            if state2 == False:
                if dummytopic2 is None:
                    kf2.update(measurement)
                    prediction = np.dot(H, kf2.predict())[0]
                    dummytopic2=prediction
                    data_queue2.put((prediction))
                    state2 = True
                    time.sleep(0.5)
                else:
                    delta=dummytopic2-measurement
                    kf2.update(measurement)
                    prediction = np.dot(H, kf2.predict())[0]
                    dummytopic2=prediction
                    data_queue2.put((prediction))
                    i2=0
                    state2 = True
                    time.sleep(0.5)
            else:
                delta=dummytopic2-measurement
                if -3-i2<delta<3+i2:
                #     pass
                    kf2.update(measurement)
    except ValueError:
        pass



# Handler function for topic3
def handle_topic3_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    global state3
    global kf3
    global i3
    global restartz
    global dummytopic3

    try:
        measurement=float(payload)
        measurement= round(measurement,2)

        if(measurement<15 and measurement>=0):
            # print(measurement)
            restartz+=1
            if state3 == False:
                if dummytopic3 is None:
                    kf3.update(measurement)
                    prediction = np.dot(H, kf3.predict())[0]
                    dummytopic3=prediction
                    data_queue3.put((prediction))
                    state3 = True
                    time.sleep(0.5)
                else:
                    delta=dummytopic3-measurement
                    kf3.update(measurement)
                    prediction = np.dot(H, kf3.predict())[0]
                    dummytopic3=prediction
                    data_queue3.put((prediction))
                    state3 = True
                    i3=0
                    time.sleep(0.5)

            else:
                delta=dummytopic3-measurement
                if -3<delta<3:
                    kf3.update(measurement)
    except ValueError:
        pass

if __name__ == '__main__':
    dt = 1.0/60
    F = np.array([[1, dt, 0], [0, 1, dt], [0, 0, 1]])
    H = np.array([1, 0, 0]).reshape(1, 3)
    Q = np.array([[0.05, 0.05, 0.0], [0.05, 0.05, 0.0], [0.0, 0.0, 0.0]])
    Q1 = np.array([[0.5, 0.5, 0.0], [0.5, 0.5, 0.0], [0.0, 0.0, 0.0]])

    R = np.array([0.1]).reshape(1, 1)

    kf1 = KalmanFilter(F = F, H = H, Q = Q, R = R)
    kf2 = KalmanFilter(F = F, H = H, Q = Q, R = R)
    kf3 = KalmanFilter(F = F, H = H, Q = Q, R = R)
    kx  = KalmanFilter(F = F, H = H, Q = Q1, R = R)
    ky  = KalmanFilter(F = F, H = H, Q = Q1, R = R)
    with open('broker.txt', 'r') as file:
        broker_address = file.read().strip()
        print(broker_address)
t1 = threading.Thread(target=conecttopic1, args=(broker_address,))
t2 = threading.Thread(target=conecttopic2, args=(broker_address,))
t3 = threading.Thread(target=conecttopic3, args=(broker_address,))

t1.start()
t2.start()
t3.start()
data1=0
data2=0
data3=0
x=0
start_time = datetime.datetime.now()
datakoordinatanchor()

while True:
    current_time = datetime.datetime.now()
    elapsed_time = current_time - start_time
    while not data_queue1.empty() and not data_queue2.empty() and not data_queue3.empty() :
        try:
            data1 = data_queue1.get(timeout=5)  # Timeout of 1 second
            data2 = data_queue2.get(timeout=5)  # Timeout of 1 second
            data3 = data_queue3.get(timeout=5)  # Timeout of 1 second
            restartz
            restartx
            restarty
            if state1 == True and state2 == True and state3 == True:
                state1 = False
                state2 = False
                state3 = False
            data1[0] = round(data1[0], 2)
            data2[0] = round(data2[0], 2)
            data3[0] = round(data3[0], 2)
            # kurang = calculate_reduction(data1[0]) 
            # data1[0]= data1[0]-kurang   
            # kurang = calculate_reduction(data2[0]) 
            # data2[0]= data2[0]-kurang 
            # kurang = calculate_reduction(data3[0]) 
            # data3[0]= data3[0]-kurang  
            center = solve_inequalities(xanchor1,yanchor1,zanchor1,xanchor2,yanchor2,zanchor2,xanchor3,yanchor3,zanchor3,data1[0],data2[0],data3[0])
            hitung = jaraksesungguhnya(xanchor1,yanchor1,zanchor1,xanchor2,yanchor2,zanchor2,xanchor3,yanchor3,zanchor3,data1[0],data2[0],data3[0],center)
            if center is not None:
                print(center[0])
                print(center[1])
                kirimdata = threading.Thread(target=senddata, args=(broker_address,center,hitung,data1[0],data2[0],data3[0],))
                kirimdata.start()

            else:
                pesan= "error"
                kirimdata = threading.Thread(target=senddata, args=(broker_address,pesan,hitung,data1[0],data2[0],data3[0],))
                kirimdata.start()

            # if center is not None:
            #     print(center)
            #     kirimdata = threading.Thread(target=senddata, args=(broker_address,center))
            #     kirimdata.start()


            # else:
            #     print("nothing")
            #     # kirimdata.join()


        except queue.Empty:
            pass

    
    if x>=10:
        # print(f"state1= {state1},state2= {state2},state3= {state3}")
        # print("restart")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    time.sleep(0.5)
         
