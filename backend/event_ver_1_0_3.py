'''
스레드로 통신 구현 완료 

실시간 값 모니터링 값 출력 확인

통신 다듬어야함

컨트롤 부분 완료 -> 제어 이벤트는 제롬한테 파라미터 확인후 가능 

# 해야할 것 
: 제어 부분 이벤트 , 데이터 프레임(로깅으로 -> 추후에)

'''

# 라이브러리 
from typing import Optional
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import QThread, Signal, QObject
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from GUI_final_ui_ver_1_0_2 import Ui_MainWindow
from About_window_ui import Ui_About_Widget

import serial
import serial.tools.list_ports
import minimalmodbus
import time
import threading

# 통신 클래스 
class ModBus_Thread(QObject):
    _instance = None
    dataReceived = Signal(object)

    def __new__(cls) :
        if cls._instance is None :

            cls._instance = super(ModBus_Thread, cls).__new__(cls)
            cls._instance.connected = False
            cls._instance.port = None
            cls._instance.baudrate = None
            cls._instance.target_list = None
            cls._instance.instrument = None
        return cls._instance
    
    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        self.event =threading.Event()
        self.event.set()

    def Connect(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.slaveID = 1

        self.instrument = minimalmodbus.Instrument(self.port, self.slaveID)
        self.instrument.serial.baudrate = int(self.baudrate)
        self.instrument.serial.timeout = 3

        if self.instrument:
            self.connected = True
            self.thread.start()
        else : 
            self.Disconnect()

    def run(self):
        while self.connected:
            self.event.wait(0.5)
            try:
                self.Connect_Func()
                self.connected = True
            except:
                self.connected = False

    def Connect_Func(self):
        try:
            self.R_Current = float(self.instrument.read_register(registeraddress=100, functioncode=3))
            self.O_Current = float(self.instrument.read_register(registeraddress=241, functioncode=3))

            self.R_Vel = self.instrument.read_register(registeraddress=119, functioncode=3)
            self.O_Vel = self.instrument.read_register(registeraddress=306, functioncode=3)
            
            self.R_Pos = self.instrument.read_registers(registeraddress=117, number_of_registers=2, functioncode=3)
            self.R_Pos = (self.R_Pos[1] << 16) | self.R_Pos[0] 

            if self.R_Pos & 0x80000000 :
                self.R_Pos -= 0x100000000

            self.O_Pos = self.instrument.read_registers(registeraddress=126, number_of_registers = 2,functioncode=3)
            self.O_Pos = (self.O_Pos[1] << 16) | self.O_Pos[0] 

            if self.O_Pos & 0x80000000 :
                self.O_Pos -= 0x100000000

            data = {"R_Current": self.R_Current, "O_Current": self.O_Current, 
                    "R_Vel" : self.R_Vel, "O_Vel" : self.O_Vel,
                    "R_Pos": self.R_Pos,  "O_Pos" : self.O_Pos}
            self.dataReceived.emit(data)
            self.connected = True
        except:
            self.connected = False
    
    def Targeting (self, target_list):
        self.event.clear()
        time.sleep(0.5)
        self.target_list = target_list
        if self.isConnect():
            self.instrument.write_registers(registeraddress=313, values=self.target_list)
            self.instrument.write_register(registeraddress=323, value=1, functioncode=6)
        time.sleep(0.5)
        self.event.set()

    def Velociting(self, velocity):
        self.event.clear()
        time.sleep(0.5)
        self.velocity = velocity
        if self.isConnect():
            self.instrument.write_register(registeraddress=306, value=self.velocity, functioncode=6)
        time.sleep(0.5)
        self.event.set()

    def Acc_Dc(self, acc_dc):
        # 뭔가 애매 
        self.event.clear()
        time.sleep(0.5)
        self.acc_dc = acc_dc
        self.instrument.write_register(registeraddress=303, value=self.acc_dc, functioncode=6)
        self.event.set()

    def Servo_On(self):
        self.event.clear()
        # 작동 코드 
        self.event.set()

    def Servo_Off(self):
        self.event.clear()
        # 작동 코드 
        self.event.set()

    def Disconnect(self):
        self.event.clear()
        self.connected = False
        if self.isConnect() == False :
            self.thread.quit()
            self.thread.wait(1)

    def isConnect(self):
        return self.connected
		
# 이벤트 클래스 
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.modbus_comm = ModBus_Thread()
        self.setupUi(self)
        self.stackedWidget_Pages.setCurrentIndex(0)
        self.disconnect_btn_5.hide()
        self.target_pos_txt_3.setDisabled(True)
        self.max_vel_txt_3.setDisabled(True)
        self.acc_dc_txt.setDisabled(True)

        # 메뉴 버튼
        self.menu_home_btn.clicked.connect(self.On_clicked_Home)
        self.menu_parameter_btn.clicked.connect(self.On_clicked_Parameter)
        self.menu_scope_btn.clicked.connect(self.On_clicked_Scope)
        self.menu_about_btn.clicked.connect(self.On_clicked_About)
        
        # 통신 버튼
        self.refresh_btn_4.clicked.connect(self.On_clicked_Refresh)
        self.connect_btn_4.clicked.connect(self.On_clicked_Connect)
        self.disconnect_btn_5.clicked.connect(self.On_clicked_Disconnect)

        # 컨트롤 버튼 
        self.target_pos_btn_3.clicked.connect(self.On_clicked_Target_Pos)
        self.max_vel_btn_3.clicked.connect(self.On_clicked_Max_Vel)
        self.acc_dc_btn_3.clicked.connect(self.On_clicked_Acc_Dc)
        self.serve_on_btn_3.clicked.connect(self.On_clicked_Servo_On)
        # 제어 버튼 -> 제롬한테 메일 받고 확인 
        self.serve_on_btn_3.clicked.connect(self.On_clicked_Servo_Off)
        self.inpos_start_btn_3.clicked.connect(self.On_clicked_Inpos_Start)
        self.inpos_stop_btn_3.clicked.connect(self.On_clicked_Inpos_Stop)


    def On_clicked_Home(self):
        self.stackedWidget_Pages.setCurrentIndex(0)
   
    def On_clicked_Parameter(self):
        self.stackedWidget_Pages.setCurrentIndex(1)
    
    def On_clicked_Scope(self):
        self.stackedWidget_Pages.setCurrentIndex(2)

    def initialize_scope(self):
        pass

    def update_scope(self):
        pass
    
    def On_clicked_About(self):
        self.About = About_window()
        self.About.show()

    def On_clicked_Refresh(self):
        self.ports = [port.device for port in serial.tools.list_ports.comports()]

        if (len(self.ports) != 0):
            self.port_comboBox_4.clear()
            self.port_comboBox_4.addItems(self.ports)

    def On_clicked_Connect(self):
        
        port = str(self.port_comboBox_4.currentText())
        baudrate = str(self.baudrate_comboBox_4.currentText())
        
        # 통신 커넥트 클래스 함수 참조 
        self.modbus_comm.Connect(port, baudrate)

        if self.modbus_comm.isConnect():

            self.connect_btn_4.hide()
            self.disconnect_btn_5.show()
            self.port_comboBox_4.setDisabled(True)
            self.baudrate_comboBox_4.setDisabled(True)
            self.target_pos_txt_3.setEnabled(True)
            self.max_vel_txt_3.setEnabled(True)
            self.acc_dc_txt.setEnabled(True)

            self.modbus_comm.dataReceived.connect(self.Enable_Home_value)
            self.con_status_lbl.setStyleSheet("color : green")
            self.con_status_lbl.setText("● Connect Well")

        elif self.modbus_comm.isConnect() == False:

            self.con_status_lbl.setStyleSheet("color : red")
            self.con_status_lbl.setText("※ Check Connect")
              
    def On_clicked_Disconnect(self):
        self.disconnect_btn_5.hide()
        # 통신 디스커넥트 클래스 함수 참조 
        self.connect_btn_4.show()
        self.modbus_comm.dataReceived.connect(self.Disable_Home_value)
        self.modbus_comm.Disconnect()
        self.port_comboBox_4.setEnabled(True)
        self.baudrate_comboBox_4.setEnabled(True)
        self.target_pos_txt_3.setDisabled(True)
        self.max_vel_txt_3.setDisabled(True)
        self.acc_dc_txt.setDisabled(True)
        self.con_status_lbl.setStyleSheet("color : black")
        self.con_status_lbl.setText("● Connect Status")
  
    def Enable_Home_value(self, data):

        self.real_current_lbl_5.setText(str(data["R_Current"]))
        self.order_current_lbl_5.setText(str(data["O_Current"]))
        self.real_vel_lbl_5.setText(str(data["R_Vel"]))
        self.order_vel_lbl_5.setText(str(data["O_Vel"]))
        self.real_pos_lbl_5.setText(str(data["R_Pos"]))
        self.order_pos_lbl_5.setText(str(data["O_Pos"]))

    def Disable_Home_value(self):
        self.real_current_lbl_5.setText("")
        self.order_current_lbl_5.setText("")
        self.real_vel_lbl_5.setText("")
        self.order_vel_lbl_5.setText("")
        self.real_pos_lbl_5.setText("")
        self.order_pos_lbl_5.setText("")

    def On_clicked_Target_Pos(self):
        target= int(self.target_pos_txt_3.text())
        target = target&0xFFFFFFFF
        first_ = (target >> 16)&0xFFFF
        second_ = target&0xFFFF

        self.modbus_comm.Targeting([second_, first_])
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    def On_clicked_Max_Vel(self):
        velocity = int(self.max_vel_txt_3.text())

        self.modbus_comm.Velociting(velocity)
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    def On_clicked_Acc_Dc(self):
        acc_dc = int(self.acc_dc_txt.text())
        self.modbus_comm.Acc_Dc(acc_dc)
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    '''서보는 제롬한테 파라미터 확인 받고 하기 '''
    def On_clicked_Servo_On(self):
        self.modbus_comm.Servo_On()
        
        if self.modbus_comm.Servo_On():
            self.servo_lbl_3.setStyleSheet(u"background-color:green; */\n"
                                            "border-radius: 10px; */\n"
                                            "border : 1px solid black")
            self.servo_lbl_3.setText("ON")

    def On_clicked_Servo_Off(self):
        self.modbus_comm.Servo_Off()

        if self.modbus_comm.Servo_Off() :
            self.servo_lbl_3.setStyleSheet(u"background-color:red; */\n"
                                            "border-radius: 10px; */\n"
                                            "border : 1px solid black")
            self.servo_lbl_3.setText("OFF")

    def On_clicked_Inpos_Start(self):
        pass
    
    def On_clicked_Inpos_Stop(self):
        pass

    def closeEvent(self, event):
        if self.modbus_comm.isConnect():
            self.modbus_comm.Disconnect()
            self.modbus_comm.thread.quit()
            self.modbus_comm.thread.wait(1)
        super().closeEvent(event)

# about 윈도우 
class About_window(QWidget, Ui_About_Widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)