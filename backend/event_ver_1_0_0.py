'''
기본 통신 구현 

통신 다듬기 완료 

'''


from PySide6.QtWidgets import QApplication, QMainWindow, QWidget
from PySide6.QtCore import QThread, Signal, QObject

from GUI_final_ui_ver_1_0_0 import Ui_MainWindow
from About_window_ui import Ui_About_Widget

import serial
import serial.tools.list_ports
import minimalmodbus


class ModBus_Communication:
    _instance = None

    def __new__(cls):
        if cls._instance is None :
            cls._instance = super(ModBus_Communication, cls).__new__(cls)
            cls._instance.connected = False
            cls._instance.port = None
            cls._instance.baudrate = None
            cls._instance.instrument = None
            
            cls.Current = None
        return cls._instance
    
    def Connect(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate
        self.slaveID = 1
        try:
            self.instrument = minimalmodbus.Instrument(self.port, self.slaveID)
            self.instrument.serial.baudrate = int(self.baudrate)
            self.instrument.serial.timeout = 1

            if self.instrument:
                self.R_Current = self.instrument.read_register(registeraddress=100, functioncode=3)
                self.O_Current = self.instrument.read_register(registeraddress=241, functioncode=3)
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
                    
                
                self.connected = True

                return self.instrument
        except :
            self.connected = False

    def Disconnect(self):
        self.connected = False

        # 통신 해제 

    def isConnect(self):
        return self.connected


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.modbus_comm = ModBus_Communication()
        self.setupUi(self)
        self.stackedWidget_Pages.setCurrentIndex(0)
        self.disconnect_btn_5.hide()

        self.menu_home_btn.clicked.connect(self.On_clicked_Home)
        self.menu_parameter_btn.clicked.connect(self.On_clicked_Parameter)
        self.menu_scope_btn.clicked.connect(self.On_clicked_Scope)
        self.menu_about_btn.clicked.connect(self.On_clicked_About)
        
        self.refresh_btn_4.clicked.connect(self.On_clicked_Refresh)
        self.connect_btn_4.clicked.connect(self.On_clicked_Connect)
        self.disconnect_btn_5.clicked.connect(self.On_clicked_Disconnect)

    def On_clicked_Home(self):
        self.stackedWidget_Pages.setCurrentIndex(0)
    
    def On_clicked_Parameter(self):
        self.stackedWidget_Pages.setCurrentIndex(1)
    
    def On_clicked_Scope(self):
        self.stackedWidget_Pages.setCurrentIndex(2)
    
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

            self.con_status_lbl.setStyleSheet("color : green")
            self.con_status_lbl.setText("● Connect Well")
            self.connect_btn_4.hide()
            self.disconnect_btn_5.show()
            self.port_comboBox_4.setDisabled(True)
            self.baudrate_comboBox_4.setDisabled(True)

            self.Home_value()

        elif self.modbus_comm.isConnect() == False:

            self.con_status_lbl.setStyleSheet("color : red")
            self.con_status_lbl.setText("※ Check Connect")
            
    def On_clicked_Disconnect(self):
        self.disconnect_btn_5.hide()
        # 통신 디스커넥트 클래스 함수 참조 
        self.connect_btn_4.show()

        self.Home_value()
        self.port_comboBox_4.setEnabled(True)
        self.baudrate_comboBox_4.setEnabled(True)

        self.con_status_lbl.setStyleSheet('color : black')
        self.con_status_lbl.setText("● Connect Status")

        self.real_current_lbl_5.setText("")
        self.order_current_lbl_5.setText("")
        self.real_vel_lbl_5.setText("")
        self.order_vel_lbl_5.setText("")
        self.real_pos_lbl_5.setText("")
        self.order_pos_lbl_5.setText("")

    def Home_value(self):
            self.real_current_lbl_5.setText(f"{(self.modbus_comm.R_Current)/1000:.2f}")
            self.order_current_lbl_5.setText(f"{(self.modbus_comm.O_Current):.0f}")
            self.real_vel_lbl_5.setText(f"{self.modbus_comm.R_Vel}")
            self.order_vel_lbl_5.setText(f"{self.modbus_comm.O_Vel}")
            self.real_pos_lbl_5.setText(f"{self.modbus_comm.R_Pos}")
            self.order_pos_lbl_5.setText(f"{self.modbus_comm.O_Pos}")

    def Update_value(self):
        pass
    
    
class About_window(QWidget, Ui_About_Widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)