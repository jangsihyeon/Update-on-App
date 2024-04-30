'''
그래프 완료 + 마지막 정지 상태에서 다시 출발 완료 , about 화면 구성 및 웹사이트 연동

홈버튼 연결, 서보 온오프 버튼 연결, Inposition 상태, 서보 상태 완료 

# 해야할 것
:  
   1.0.4의 형태로 하기 그래프는 !!!!!!!!!!!!!
   x축 동작 시간으로 표현(그래프에 표현되는거와 달리 아예 따로 체크된 후 부터 1초 단위씩 표현// 그러), 
   y 값이 각각의 max, min 값에 맞춰서 움직이게 
   제어 부분 이벤트 , 
   데이터 프레임(로깅으로 -> 추후에)
   monitoring 화면 servo 스타일시트 적용 

# 그래프 현재 된 부분 
- 30초 간격으로 보여주기 (x값 확인)
- 모든 체크 박스 동적 그래프 확인 

# 그래프 해야할 부분 
- 마지막 저장된 타임을 기준으로 다른 체크박스 체크 시 마지막 지점에서 새로운 그래프가 시작되는 문제 
- y 값의 범위가 달라서 범위 다른 2개 확인 시 더 작은 값이 직선 그래프로 표현 되는 부분 
==> y 값의 스케일을 각각 정해서 fully border로 보기 

'''

# 라이브러리
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QThread, Signal, QObject, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
# GUI form 
from GUI_final_ui_ver_1_0_5 import Ui_MainWindow
from About_window_ui import Ui_About_Widget
# 통신용 
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

            self.R_Pos = self.instrument.read_registers(registeraddress=126, number_of_registers=2, functioncode=3)
            self.R_Pos = (self.R_Pos[1] << 16) | self.R_Pos[0]

            if self.R_Pos & 0x80000000 :
                self.R_Pos -= 0x100000000

            self.O_Pos = self.instrument.read_registers(registeraddress=117, number_of_registers=2, functioncode=3)
            self.O_Pos = (self.O_Pos[1] << 16) | self.O_Pos[0]

            if self.O_Pos & 0x80000000 :
                self.O_Pos -= 0x100000000

            # 서보 온오프 상태 비트 
            self.Status_Servo = self.instrument.read_register(registeraddress=109, functioncode=3)
            
            # 호밍 0으로 상태 변경용
            self.instrument.write_register(registeraddress=410, value=0, functioncode=6)

            # 호밍 상태 비트 -> 나중에 
            # self.Status_Home = self.instrument.read_register(registeraddress=109, functioncode=3)

            # 인포지션 
            self.Inposition= self.instrument.read_register(registeraddress=136, functioncode=3)
        
            data = {"R_Cur": self.R_Current/1000, "O_Cur": self.O_Current,
                    "R_Vel" : self.R_Vel, "O_Vel" : self.O_Vel,
                    "R_Pos": self.R_Pos,  "O_Pos" : self.O_Pos, 
                    "Status_Servo" : self.Status_Servo, "Status_Inposition" : self.Inposition}
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
        self.event.clear()
        time.sleep(0.5)
        self.acc_dc = acc_dc
        self.instrument.write_register(registeraddress=303, value=self.acc_dc, functioncode=6)
        self.event.set()
    
    '''서보, Inpos, Home은 제롬한테 파라미터 확인 받고 하기 '''
    def Servo_On(self):
        self.event.clear()
        # 작동 코드
        time.sleep(0.5)
        self.instrument.write_register(registeraddress=414, value=0, functioncode=6)
        time.sleep(0.5)
        self.event.set()

    def Servo_Off(self):
        self.event.clear()
        # 작동 코드
        time.sleep(0.5)
        self.instrument.write_register(registeraddress=414, value=1, functioncode=6)
        time.sleep(0.5)
        self.event.set()

    def Home_Start(self):
        self.event.clear()
        # 작동은 되는데 약간 버벅거림 
        time.sleep(0.2)
        self.instrument.write_register(registeraddress=400, value=12, functioncode=6)
        self.instrument.write_register(registeraddress=410, value=1, functioncode=6)
        time.sleep(0.2)
        self.event.set()

    def Inpos_Start(self):
        self.event.clear()
        time.sleep(0.5)
        #self.instrument.write_register(registeraddress=420, value=102, functioncode=6)
        time.sleep(0.5)
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
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        # 그래프 초기화 호출 
        self.initialize_scope()
        # 그래프 업데이터 제어 플러그 
        self.is_graph_update_enable = True
        # 체크 시점의 시간 저장 
        self.check_time= None
        self.last_update_time = None

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

        self.servo_on_btn_3.clicked.connect(self.On_clicked_Servo_On)
        self.servo_off_btn_3.clicked.connect(self.On_clicked_Servo_Off)

        self.homing_home_btn_3.clicked.connect(self.On_clicked_Home_Home)

        # 그래프 
        self.modbus_comm.dataReceived.connect(self.update_scope)
        self.stop_btn.clicked.connect(self.On_Stop_button_clicked)

        # 체크박스
        self.cur_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.pos_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.vel_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.cur_real_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.pos_real_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.vel_real_check.stateChanged.connect(self.On_checkbox_state_changed)

    def On_clicked_Home(self):
        self.stackedWidget_Pages.setCurrentIndex(0)

    def On_clicked_Parameter(self):
        self.stackedWidget_Pages.setCurrentIndex(1)

    def On_clicked_Scope(self):
        self.stackedWidget_Pages.setCurrentIndex(2)

    def On_clicked_About(self):
        self.About = About_window()
        self.About.show()

    def On_Stop_button_clicked(self):
        self.is_graph_update_enable = False
        
    ''' 그래프 한번 싹 수정 해야함''' 
    # 그래프 초기화 
    def initialize_scope(self):
        self.timer = QTimer()
        self.toolbar = NavigationToolbar(self.canvas, self)
        menu_layout = QHBoxLayout(self.scope_menu_widget)
        # 메뉴용 위젯
        menu_layout.addWidget(self.toolbar)
        menu_layout.addStretch()
        # 그래프 패널용 위젯 
        graph_layout = QVBoxLayout(self.scope_graph_widget)
        graph_layout.addWidget(self.canvas)
        graph_layout.addStretch()
        
        # 지령 데이터 
        self.ax1 = self.figure.add_subplot()

        # 실제 데이터 
        self.ax2 = self.ax1.twinx()

        self.x_data = []

        # 지령 데이터 
        self.y_data_O_Pos = []
        self.y_data_O_Vel = []
        self.y_data_O_Cur = []
        # 실제 데이터 
        self.y_data_R_Pos = []
        self.y_data_R_Vel = []
        self.y_data_R_Cur = []
    
    # 체크 박스 상태 
    def On_checkbox_state_changed(self):
        
        if self.check_time is None:
            self.check_time = time.time()
        else:
            if self.last_update_time is not None:
                self.check_time += (time.time() - self.last_update_time)
            self.last_update_time = None 
        self.is_graph_update_enable = True

        current_legnth = len(self.x_data)

        if self.pos_order_check.isChecked() and len(self.y_data_O_Pos) < current_legnth:
            self.y_data_O_Pos += [None]*(current_legnth-len(self.y_data_O_Pos))

        if self.pos_real_check.isChecked() and len(self.y_data_R_Pos) < current_legnth:
            self.y_data_R_Pos += [None]*(current_legnth-len(self.y_data_R_Pos))

        if self.vel_order_check.isChecked() and len(self.y_data_O_Vel) < current_legnth:
            self.y_data_O_Vel += [None]*(current_legnth-len(self.y_data_O_Vel))

        if self.vel_real_check.isChecked() and len(self.y_data_R_Vel) < current_legnth:
            self.y_data_R_Vel += [None]*(current_legnth-len(self.y_data_R_Vel))
        
        if self.cur_order_check.isChecked() and len(self.y_data_O_Cur) < current_legnth:
            self.y_data_O_Cur += [None]*(current_legnth-len(self.y_data_O_Cur))

        if self.cur_real_check.isChecked() and len(self.y_data_R_Cur) < current_legnth:
            self.y_data_R_Cur += [None]*(current_legnth-len(self.y_data_R_Cur))

    # 그래프 업데이트 
    def update_scope(self, data):
        
        if not self.is_graph_update_enable or self.check_time is None:
            return 
    
        current = time.time()
        elapsed = int(current - self.check_time)
        self.x_data.append(elapsed)

        if self.pos_order_check.isChecked(): # red
            self.y_data_O_Pos.append(data["O_Pos"])
        else:
            self.y_data_O_Pos.append(None)

        if self.pos_real_check.isChecked(): # blue
            self.y_data_R_Pos.append(data["R_Pos"])
        else:
            self.y_data_R_Pos.append(None)

        if self.vel_order_check.isChecked(): # black
            self.y_data_O_Vel.append(data["O_Vel"])
        else:
            self.y_data_O_Vel.append(None)

        if self.vel_real_check.isChecked(): # purple
            self.y_data_R_Vel.append(data["R_Vel"])
        else:
            self.y_data_R_Vel.append(None)

        if self.cur_order_check.isChecked(): # green 
            self.y_data_O_Cur.append(data["O_Cur"])
        else:
            self.y_data_O_Cur.append(None)

        if self.cur_real_check.isChecked():  # pink
            self.y_data_R_Cur.append(data["R_Cur"])
        else:
            self.y_data_R_Cur.append(None)
        
        self.ax1.clear()
        self.ax2.clear()

        if self.pos_order_check.isChecked(): # red
            self.ax1.plot(self.x_data, self.y_data_O_Pos, 'red')

        if self.pos_real_check.isChecked(): # blue
            self.ax2.plot(self.x_data, self.y_data_R_Pos, 'blue' )

        if self.vel_order_check.isChecked(): # black
            self.ax1.plot(self.x_data, self.y_data_O_Vel, 'black')

        if self.vel_real_check.isChecked(): # purple
            self.ax2.plot(self.x_data, self.y_data_R_Vel, 'purple')

        if self.cur_order_check.isChecked(): # green 
            self.ax1.plot(self.x_data, self.y_data_O_Cur, 'green')

        if self.cur_real_check.isChecked():  # pink
            self.ax2.plot(self.x_data, self.y_data_R_Cur, 'pink')

        time_window = 30
        window_start = int(elapsed/time_window)*time_window
        min_time = window_start
        max_time = window_start+time_window
        self.ax1.set_xlim(min_time, max_time)
        self.ax2.set_xlim(min_time, max_time)

        self.canvas.draw()        
        self.pos_order_check.stateChanged.connect(self.toggle_graph)
    
    # 체크박스 해제 시 그래프 보이게 
    def toggle_graph(self, state):

        if self.pos_order_check.isChecked() or self.pos_real_check.isChecked() or \
           self.vel_order_check.isChecked() or self.vel_real_check.isChecked() or \
           self.cur_order_check.isChecked() or self.cur_real_check.isChecked() :
            self.timer.start()

        else:
            self.timer.stop()
            self.ax1.clear()
            self.ax2.clear()
            self.canvas.draw()

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
        self.real_current_lbl_5.setText(str(data["R_Cur"])+" mA")
        self.order_current_lbl_5.setText(str(data["O_Cur"]))
        self.real_vel_lbl_5.setText(str(data["R_Vel"]))
        self.order_vel_lbl_5.setText(str(data["O_Vel"]))
        self.real_pos_lbl_5.setText(str(data["R_Pos"]))
        self.order_pos_lbl_5.setText(str(data["O_Pos"]))
        
        self.Inpos = int(data["Status_Inposition"])

        if self.Inpos == 1 :
            self.inpos_lbl_3.setStyleSheet(u"background-color:green; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid green;\n"
                                            "color : white; \n")
        else:
            # 초기화 상태로 
            self.inpos_lbl_3.setStyleSheet(u"background-color:green; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid green;\n"
                                            "color : white; \n")
            
    def Disable_Home_value(self):
        # 홈밍상태, 서보 상태, 인포지션, 알람, 초기화 상태 추가 
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

        Targeting_list = [second_, first_]

        self.modbus_comm.Targeting(Targeting_list)
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    def On_clicked_Max_Vel(self):
        velocity = int(self.max_vel_txt_3.text())

        self.modbus_comm.Velociting(velocity)
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    def On_clicked_Acc_Dc(self):
        acc_dc = int(self.acc_dc_txt.text())
        self.modbus_comm.Acc_Dc(acc_dc)
        self.modbus_comm.dataReceived.connect(self.Enable_Home_value)

    '''servo, Inpos, Home은 제롬한테 파라미터 확인 받고 하기 '''
    def On_clicked_Servo_On(self):
        self.modbus_comm.Servo_On()

        self.modbus_comm.dataReceived.connect(self.Status_Servo)

    def On_clicked_Servo_Off(self):
        self.modbus_comm.Servo_Off()
        
        self.modbus_comm.dataReceived.connect(self.Status_Servo)

    def On_clicked_Home_Home(self):
        self.modbus_comm.Home_Start()

        #self.modbus_comm.dataReceived.connect(self.Status_Home)
        

    def Status_Servo(self, data):
        self.Servo_status = data["Status_Servo"]

        if self.Servo_status == 2:
            self.servo_lbl_3.setStyleSheet(u"background-color:green; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid green;\n"
                                            "color : white; \n")
            self.servo_lbl_3.setText("ON")
        elif self.Servo_status == 1:
            self.servo_lbl_3.setStyleSheet(u"background-color:red; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid red;\n"
                                            "color : white; \n")
            self.servo_lbl_3.setText("OFF")
        elif self.Servo_status == 3:
            self.servo_lbl_3.setStyleSheet(u"background-color:orange; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid orange;\n"
                                            "color : white; \n")
            self.servo_lbl_3.setText("RUN")
    
    '''
    def Status_Home(self, data):
        self.Home_status = data["Status_Home"]

        if self.Home_status == 2:
            self.homing__sts_lbl_3.setStyleSheet(u"background-color:green; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid green;\n"
                                            "color : white; \n")
            self.homing__sts_lbl_3.setText("Home")

        elif self.Home_status == 3:
            self.homing__sts_lbl_3.setStyleSheet(u"background-color:orange; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid orange;\n"
                                            "color : white; \n")
            self.homing__sts_lbl_3.setText("RUN")
        '''

    def closeEvent(self, event):
        if self.modbus_comm.isConnect():
            self.modbus_comm.Disconnect()
            self.modbus_comm.thread.quit()
            self.modbus_comm.thread.wait(1)
        super().closeEvent(event)

# About 클래스 
class About_window(QWidget, Ui_About_Widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
