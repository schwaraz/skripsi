import math
import paho.mqtt.client as mqtt
import mysql.connector
import threading
from decimal import Decimal
import time
from sympy import im, symbols, Eq, solve,solveset,re

dummymode1=False
dummymode2=False
dummymode3=False
jumlahx=0
jumlahy=0
jumlahz=0
data1=0
data2=0
data3=0
A=0
B=0
C=0
xanchor1=0
yanchor1=0
zanchor1=0
xanchor2=0
yanchor2=0
zanchor2=0
xanchor3=0
yanchor3=0
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
def save(koordinat):
    global xanchor1,yanchor1,xanchor2,yanchor2,xanchor3,yanchor3,zanchor3,zanchor2,zanchor1
    global dummymode1
    global dummymode2    
    global dummymode3
    query="INSERT INTO `kordinatanchor`(`x1`, `y1`, `z1`, `x2`, `y2`, `z2`, `x3`, `y3`, `z3`) VALUES (%s,%s,0,%s,%s,0,%s,%s,0)"
    
    if dummymode1==True:
        cursor.execute(query, (Decimal(str(koordinat[0])),Decimal(str(koordinat[1])),xanchor2,yanchor2,xanchor3,yanchor3))

    if dummymode2==True:
        cursor.execute(query, (xanchor1,yanchor1,Decimal(str(koordinat[0])),Decimal(str(koordinat[1])),xanchor3,yanchor3))
    if dummymode3==True:
        cursor.execute(query, (xanchor1,yanchor1,xanchor2,yanchor2,Decimal(str(koordinat[0])),Decimal(str(koordinat[1]))))
    connection.commit()
    return
def on_message(client, userdata, message):
    payload_str = message.payload.decode('utf-8')
    global jumlahx
    global jumlahy
    global jumlahz
    global data1
    global data2
    global data3
    global dummymode1
    global dummymode2
    global dummymode3
    if dummymode1 == True or dummymode2 == True or dummymode3 == True:
        if message.topic=="esp32/jarak1":
            measurement=float(payload_str)
            if(measurement<10 and measurement>=0):
                data1=measurement
        if message.topic=="esp32/jarak2":
            measurement=float(payload_str)
            if(measurement<10 and measurement>=0):
                data2=measurement
        if message.topic=="esp32/jarak3":
            measurement=float(payload_str)
            if(measurement<10 and measurement>=0):
                data3=measurement

    if message.topic=="esp32/comunicateanchor":
        if dummymode1 == False and dummymode2 == False and dummymode3 == False:
            if payload_str=="anchor1":
                dummymode1=True
            if payload_str=="anchor2":
                dummymode2=True
            if payload_str=="anchor3":
                dummymode3=True
def pilihhasil(koordinat):
    print("opisi1="+str(koordinat[0]))
    print("opsi2="+str(koordinat[1]))
    pilihan=input("tekan 1 untuk pilihan 1, tekan 2 untuk pilihan 2, tekan 3 jika keduanya salah")
    while pilihan not in ['1', '2', '3']:
        print("Invalid choice. Please try again.")
        print("opisi1="+str(koordinat[0]))
        print("opsi2="+str(koordinat[1]))
        pilihan = input("Please enter your choice (1, 2, or 3): ")
    if pilihan=="1" :
        save(koordinat[0])
        reset()
    if pilihan=="2":
        save(koordinat[1])
        reset()
    if pilihan=="3":
        pass
    return
    

def reset():
    global dummymode1
    global dummymode2    
    global dummymode3
    global data1
    global data2
    global data3
    dummymode1=False
    dummymode2=False
    dummymode3=False
    data1=0
    data2=0
    data3=0
    datakoordinatanchor()
    return
def solve_equations(x1, y1, x2, y2, r1, r2):
    x, y  = symbols('x y')
    eq1 = Eq((x - x1)**2 + (y - y1)**2 , r1**2)
    eq2 = Eq((x - x2)**2 + (y - y2)**2 , r2**2)
    solutions = solve((eq1, eq2), (x, y )) 

    for solution in solutions:
        x_val = solution[0]
        y_val = solution[1]
        if x_val.is_real and y_val.is_real :
            # data.write("trianggulasi berhasil data real")
            # data.write("\n")
            # print("berhasil")
            return solutions
    # print("gagal")
    return None
def conecttopic():
    # Create MQTT client instance
    client = mqtt.Client()
    # Set the callback function
    client.on_message = on_message
    # Connect to MQTT broker
    client.connect("192.168.1.12")
    #list subs
    client.subscribe("esp32/comunicateanchor")
    client.subscribe("esp32/jarak1")
    client.subscribe("esp32/jarak2")
    client.subscribe("esp32/jarak3")
    client.loop_forever()

t1 = threading.Thread(target=conecttopic, args=())
t1.start()
datakoordinatanchor()

while True:
    # print("msk")
    if dummymode1==True:
        # print("msk1")
        hasil=solve_equations(xanchor2, yanchor2, xanchor3, yanchor3, data2,data3)
        if hasil is not None:
            # print(hasil)
            pilihhasil(hasil)
    elif dummymode2==True:
            # print("msk2")
            hasil= solve_equations(xanchor1, yanchor1, xanchor2, yanchor2, data1, data2)
            if hasil is not None:
                pilihhasil(hasil)
    elif dummymode3==True:
            # print("msk3")

            hasil=solve_equations(xanchor1, yanchor1, xanchor3, yanchor3, data1, data3)
            if hasil is not None:
                pilihhasil(hasil)
    time.sleep(0.5)
