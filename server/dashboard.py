import sys
import signal
import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTabWidget, QVBoxLayout, QWidget, QTextEdit, QHBoxLayout, QLabel
from PyQt5.QtGui import QIcon, QPainter, QColor, QBrush, QFont, QPainterPath, QPainterPathStroker
import subprocess
import time
import os
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from PyQt5.QtCore import Qt, QTimer

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

def is_process_running():
    process_name="controlpanel.py"
    command = f"ps -ef | grep -v grep | grep {process_name}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0 and process_name in result.stdout.decode("utf-8")
def is_process_running_api():
    process_name="api.py"
    command = f"ps -ef | grep -v grep | grep {process_name}"
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0 and process_name in result.stdout.decode("utf-8")
    
    return len(output) > 0  # Check if the output is non-empty
class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tool_ready_1 = False
        self.tool_ready_2 = False
        self.tool_ready_3 = False

    def set_tool_ready_1(self, ready):
        self.tool_ready_1 = ready
        self.update()

    def set_tool_ready_2(self, ready):
        self.tool_ready_2 = ready
        self.update()

    def set_tool_ready_3(self, ready):
        self.tool_ready_3 = ready
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Circle 1 (Red)
        circle1_color = QColor(255, 0, 0) if not self.tool_ready_1 else QColor(0, 255, 0)
        painter.setBrush(QBrush(circle1_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(100, 100, 150, 150)
        painter.setPen(Qt.black)
        painter.drawText(100, 70, 150, 30, Qt.AlignCenter, "Anchor 1")

        # Circle 2 (Red)
        circle2_color = QColor(255, 0, 0) if not self.tool_ready_2 else QColor(0, 255, 0)
        painter.setBrush(QBrush(circle2_color))
        painter.drawEllipse(450, 100, 150, 150)
        painter.setPen(Qt.black)
        painter.drawText(450, 70, 150, 30, Qt.AlignCenter, "Anchor 2")

        # Circle 3 (Red)
        circle3_color = QColor(255, 0, 0) if not self.tool_ready_3 else QColor(0, 255, 0)
        painter.setBrush(QBrush(circle3_color))
        painter.drawEllipse(800, 100, 150, 150)
        painter.setPen(Qt.black)
        painter.drawText(800, 70, 150, 30, Qt.AlignCenter, "Anchor 3")


class DashboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_ui()

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect("192.168.0.166")
        self.mqtt_client.subscribe("esp32/jarak1")  # Subscribe to "esp32/jarak1" topic
        self.mqtt_client.subscribe("esp32/jarak2")  # Subscribe to "esp32/jarak2" topic
        self.mqtt_client.subscribe("esp32/jarak3")  # Subscribe to "esp32/jarak3" topic
        self.mqtt_client.loop_start()

        self.debug_tabs = []  # List to keep track of debug tabs
        self.status_tabs = []  # List to keep track of status tabs

        self.last_message_time_1 = 0
        self.last_message_time_2 = 0
        self.last_message_time_3 = 0

        self.status_timer = QTimer()  # Timer to check last message time
        self.status_timer.setInterval(5000)  # Check every 5 seconds
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start()

    def init_ui(self):
        self.setWindowTitle("Application Dashboard")
        self.setWindowIcon(QIcon('/home/shuvi/Downloads/ico.png'))

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.button_widget = QWidget()
        self.layout.addWidget(self.button_widget)

        self.button_layout = QVBoxLayout(self.button_widget)

        self.run_button = QPushButton("Run", self.button_widget)
        self.run_button.clicked.connect(self.run_code)
        self.button_layout.addWidget(self.run_button)

        self.restart_button = QPushButton("Show Debug", self.button_widget)
        self.restart_button.clicked.connect(self.show_debug)
        self.button_layout.addWidget(self.restart_button)

        self.status_button = QPushButton("Status", self.button_widget)
        self.status_button.clicked.connect(self.show_status)
        self.button_layout.addWidget(self.status_button)

        self.stop_button = QPushButton("Stop", self.button_widget)
        self.stop_button.clicked.connect(self.stop_code)
        self.button_layout.addWidget(self.stop_button)

        self.debug_text = QTextEdit()
        self.debug_text.setReadOnly(True)

        self.status_widget = StatusWidget()

    def run_code(self):
        # Code block to execute when the "Run" button is pressed
        if is_process_running():
            self.debug_text.append("proses sudah sedang berjalan")
            
        else:
            subprocess.Popen("python3 controlpanel.py", shell=True)
        if is_process_running_api():
            self.debug_text.append("API sudah sedang berjalan")
        else:
            subprocess.Popen("python3 api.py", shell=True)

        



    def show_debug(self):
        # Check if debug log tab already exists
        if len(self.debug_tabs) > 0:
            # If a debug tab already exists, activate it and return
            debug_tab = self.debug_tabs[0]
            self.tab_widget.setCurrentWidget(debug_tab)
            return

        # Code block to execute when the "Show Debug" button is clicked
        debug_widget = QWidget()
        debug_layout = QVBoxLayout(debug_widget)
        debug_layout.setContentsMargins(0, 0, 0, 0)
        debug_layout.setSpacing(0)

        # Create a QTextEdit widget to display the log file contents
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        debug_layout.addWidget(log_text)

        remove_button = QPushButton("Remove", debug_widget)
        remove_button.setStyleSheet("QPushButton { border: none; padding: 5px; }")
        remove_button.clicked.connect(lambda: self.remove_debug_tab(debug_widget))
        debug_layout.addWidget(remove_button, alignment=Qt.AlignTop | Qt.AlignRight)

        self.tab_widget.addTab(debug_widget, "Debug Log")
        self.tab_widget.setCurrentWidget(debug_widget)
        self.debug_tabs.append(debug_widget)

        # Get the initial path to the log file
        log_file_path = os.path.join(log_folder, "api_" + formatted_date + ".log")

        def update_log_contents():
            nonlocal log_text, log_file_path

            # Read the contents of the log file
            with open(log_file_path, "r") as file:
                log_contents = file.read()

            # Display the log contents in the QTextEdit widget
            log_text.setText(log_contents)

        # Update log contents initially
        update_log_contents()

        # Create a QTimer to trigger the update every 10 seconds
        timer = QTimer()
        timer.timeout.connect(update_log_contents)
        timer.start(10000)  # 10,000 milliseconds = 10 seconds

        # Keep a reference to the timer to prevent it from being garbage collected
        self.debug_timer = timer

    def show_status(self):
        # Check if status log tab already exists
        if len(self.status_tabs) > 0:
            # If a status tab already exists, activate it and return
            status_tab = self.status_tabs[0]
            self.tab_widget.setCurrentWidget(status_tab)
            return

        # Code block to execute when the "Status" button is clicked
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)
        status_layout.addWidget(self.status_widget)

        remove_button = QPushButton("Remove", status_widget)
        remove_button.setStyleSheet("QPushButton { border: none; padding: 5px; }")
        remove_button.clicked.connect(lambda: self.remove_status_tab(status_widget))
        remove_button_layout = QHBoxLayout()
        remove_button_layout.addWidget(remove_button, alignment=Qt.AlignRight)
        status_layout.addLayout(remove_button_layout)

        self.tab_widget.addTab(status_widget, "Status")
        self.tab_widget.setCurrentWidget(status_widget)
        self.status_tabs.append(status_widget)

    def remove_debug_tab(self, debug_widget):
        self.tab_widget.removeTab(self.tab_widget.indexOf(debug_widget))
        self.debug_tabs.remove(debug_widget)

    def remove_status_tab(self, status_widget):
        self.tab_widget.removeTab(self.tab_widget.indexOf(status_widget))
        self.status_tabs.remove(status_widget)

    def stop_code(self):
        # Code block to execute when the "Stop" button is pressed
        process_name="controlpanel.py"
        command = f"pgrep -f {process_name}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode().strip()
        dummy=False
        if output:
            pids = output.split('\n')
            for pid in pids:
                pid = int(pid)
                try:
                    subprocess.run(['kill', str(pid)])
                    print(f"Process with PID {pid} killed.")
                    if dummy==False:
                        self.debug_text.append("proses dihentikan")
                        dummy=True

                except subprocess.CalledProcessError:
                    print(f"Failed to kill process with PID {pid}.")
                    self.debug_text.append("gagal proses dihentikan")
    

        else:
            print(f"No process with name '{process_name}' is currently running.")
            self.debug_text.append("proses {process_name} tidak ditemukan")

        process_name="api.py"
        command = f"pgrep -f {process_name}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode().strip()
        dummy=False
        if output:
            pids = output.split('\n')
            for pid in pids:
                pid = int(pid)
                try:
                    subprocess.run(['kill', str(pid)])
                    print(f"Process with PID {pid} killed.")
                    if dummy==False:
                        logger.info("stoping api")

                        dummy=True

                except subprocess.CalledProcessError:
                    print(f"Failed to kill process with PID {pid}.")
                    logger.info("stoping api failed. proses is not found or not running")

        else:
            print(f"No process with name '{process_name}' is currently running.")
            logger.info("no proses api found")
        # process_name="api.py"
        # command = f"pgrep -f {process_name}"
        # result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # output = result.stdout.decode().strip()
        # dummy=False
        # if output:
        #     pids = output.split('\n')
        #     for pid in pids:
        #         pid = int(pid)
        #         try:
        #             subprocess.run(['kill', str(pid)])
        #             print(f"Process with PID {pid} killed.")
        #             if dummy==False:
        #                 self.debug_text.append("proses dihentikan")
        #                 dummy=True

        #         except subprocess.CalledProcessError:
        #             print(f"Failed to kill process with PID {pid}.")
        #             self.debug_text.append("gagal proses dihentikan")

        # else:
        #     print(f"No process with name '{process_name}' is currently running.")
        #     self.debug_text.append("proses {process_name} tidak ditemukan")
        process_name="kodenormal.py"
        command = f"pgrep -f {process_name}"
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode().strip()
        dummy=False
        if output:
            pids = output.split('\n')
            for pid in pids:
                pid = int(pid)
                try:
                    subprocess.run(['kill', str(pid)])
                    print(f"Process with PID {pid} killed.")
                    if dummy==False:
                        logger.info("stoping trilateration sucsses")
                        dummy=True

                except subprocess.CalledProcessError:
                    print(f"Failed to kill process with PID {pid}.")
                    logger.info("stoping trilateration faild")

        else:
            print(f"No process with name '{process_name}' is currently running.")
            logger.info("no proses trilateration found")
    def on_message(self, client, userdata, msg):
        if msg.topic == "Log":
            self.debug_text.append(msg.payload.decode())
        elif msg.topic == "esp32/jarak1":
            self.last_message_time_1 = time.time()
            distance_1 = float(msg.payload.decode())
            self.status_widget.set_tool_ready_1(distance_1 < 50)
        elif msg.topic == "esp32/jarak2":
            self.last_message_time_2 = time.time()
            distance_2 = float(msg.payload.decode())
            self.status_widget.set_tool_ready_2(distance_2 < 50)
        elif msg.topic == "esp32/jarak3":
            distance_3 = float(msg.payload.decode())
            self.status_widget.set_tool_ready_3(distance_3 < 50)
    
    def check_status(self):
        # Code block to check the status of the devices
        current_time = time.time()

        if current_time - self.last_message_time_1 > 5:
            self.status_widget.set_tool_ready_1(False)

        if current_time - self.last_message_time_2 > 5:
            self.status_widget.set_tool_ready_2(False)
            
        if current_time - self.last_message_time_2 > 5:
            self.status_widget.set_tool_ready_3(False)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    dashboard = DashboardWindow()
    dashboard.show()
    sys.exit(app.exec_())
