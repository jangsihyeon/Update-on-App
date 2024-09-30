'''
monitoring diconnect 초기화 완료 
그래프 stop&keep 버튼 완료 

# 해야할 것
:  
    그래프 시간 빼고 얼추 다함
    타이밍 맞춰야함 

'''

# 라이브러리
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QThread, Signal, QObject, QTimer
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
# GUI form 
from GUI_final_ui_ver_1_0_6 import Ui_MainWindow
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
            self.event.wait(0.3)
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

            # 호밍 상태 비트 -> 나중에  변경 (지금 몰라서 서보 온오프 상태 비트로 같이함)
            # self.Status_Home = self.instrument.read_register(registeraddress=109, functioncode=3)

            # 인포지션 
            self.Inposition= self.instrument.read_register(registeraddress=136, functioncode=3)

            # 알람
            self.Alarm = self.instrument.read_register(registeraddress=108, functioncode=3)
        
            data = {"R_Cur": self.R_Current, "O_Cur": self.O_Current,
                    "R_Vel" : self.R_Vel, "O_Vel" : self.O_Vel,
                    "R_Pos": self.R_Pos,  "O_Pos" : self.O_Pos, 
                    "Status_Servo" : self.Status_Servo, "Status_Inposition" : self.Inposition, 
                    "Status_Alarm" : self.Alarm}
            
            self.dataReceived.emit(data)
            self.connected = True
        except:
            self.connected = False

    '''Page 01'''
    def Targeting (self, target_list):
        self.event.clear()
        time.sleep(0.3)
        self.target_list = target_list
        if self.isConnect():
            self.instrument.write_registers(registeraddress=313, values=self.target_list)
            self.instrument.write_register(registeraddress=323, value=1, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    def Velociting(self, velocity):
        self.event.clear()
        time.sleep(0.3)
        self.velocity = velocity
        if self.isConnect():
            self.instrument.write_register(registeraddress=306, value=self.velocity, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    def Acc_Dc(self, acc_dc):
        self.event.clear()
        time.sleep(0.3)
        self.acc_dc = acc_dc
        self.instrument.write_register(registeraddress=303, value=self.acc_dc, functioncode=6)
        time.sleep(0.3)
        self.event.set()
    
    # servo, home, Inposition 완료
    def Servo_On(self):
        self.event.clear()
        # 작동 코드
        time.sleep(0.3)
        self.instrument.write_register(registeraddress=414, value=0, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    def Servo_Off(self):
        self.event.clear()
        # 작동 코드
        time.sleep(0.3)
        self.instrument.write_register(registeraddress=414, value=1, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    def Home_Start(self):
        self.event.clear()
        time.sleep(0.3)
        self.instrument.write_register(registeraddress=400, value=12, functioncode=6)
        self.instrument.write_register(registeraddress=410, value=1, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    ''' Inpositon function 인데 read만 하면 되서 필요가 없어서 주석  
    def Inpos_Start(self):
        self.event.clear()
        time.sleep(0.5)
        #self.instrument.write_register(registeraddress=420, value=102, functioncode=6)
        time.sleep(0.5)
        self.event.set()
    '''
    
    '''Page 02'''
    def Read_Parameter(self, read_address):
        self.event.clear()
        time.sleep(0.3)
        # 파라미터 읽기
        self.read_addr = read_address
        self.instrument.read_register(registeraddress= self.read_addr, functioncode=3)
        time.sleep(0.3)
        self.event.set()

    def Write_Parameter(self, write_address, write_value):
        self.event.clear()
        time.sleep(0.3)
        # 파라미터 쓰기 
        self.write_addr = write_address
        self.write_val = write_value
        self.instrument.write_register(registeraddress=self.write_addr, value=self.write_val, functioncode=6)
        time.sleep(0.3)
        self.event.set()

    def Alarm_Clear(self):
        self.event.clear()
        time.sleep(0.3)
        self.instrument.write_register(registeraddress=323, value=13, functioncode=6)
        time.sleep(0.3)
        self.event.set()
        
    '''통신 disconnect '''
    def Disconnect(self):
        self.event.clear()
        # self.connected = False
        if self.isConnect() == False :
            self.connected = False
            self.thread.quit()
            self.thread.wait(1)

    '''통신 상태 '''
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
        self.start_scope_btn.hide()
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

        self.alarm_reset_btn_3.clicked.connect(self.On_clicked_Alarm_Reset)

        '''파라미터 -> 아직 확인 안해봄 기능만 물려놓음 '''
        self.read_btn.clicked.connect(self.Onclicked_Read)
        self.write_btn.clicked.connect(self.Onclicked_Read)

        # 그래프 
        self.modbus_comm.dataReceived.connect(self.update_scope)
        self.stop_scope_btn.clicked.connect(self.On_clicked_Stop_scope)
        self.start_scope_btn.clicked.connect(self.On_clicked_Start_scope)

        # 체크박스
        # self.cur_order_check.setChecked(True)
        # self.cur_real_check.setChecked(True)
        # self.pos_order_check.setChecked(True)
        # self.pos_real_check.setChecked(True)
        # self.vel_order_check.setChecked(True)
        # self.vel_real_check.setChecked(True)
        
        self.cur_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.pos_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.vel_order_check.stateChanged.connect(self.On_checkbox_state_changed)
        
        self.cur_real_check.stateChanged.connect(self.On_checkbox_state_changed)
        self.pos_order_check.stateChanged.connect(self.On_checkbox_state_changed)
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

    def On_clicked_Stop_scope(self):
        self.is_graph_update_enable = False
        self.stop_scope_btn.hide()
        self.start_scope_btn.show()

    def On_clicked_Start_scope(self):
        self.is_graph_update_enable = True
        self.start_scope_btn.hide()
        self.stop_scope_btn.show()

    '''  수정 전 
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
    

    # 그래프 업데이트 
    def update_scope(self, data):
        
        if not self.is_graph_update_enable or self.check_time is None:
            return 
    
        current = time.time()
        elapsed = round((current - self.check_time)*10, 1)
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

        time_window = 30*10
        window_start = int(elapsed/time_window)*time_window
        min_time = window_start/10
        max_time = (window_start+time_window)/10
        self.ax1.set_xlim(min_time, max_time)
        self.ax2.set_xlim(min_time, max_time)

        self.canvas.draw()        
        self.pos_order_check.stateChanged.connect(self.toggle_graph)
    ~
    # 체크박스 해제 시 그래프 보이게 
    def toggle_graph(self):

        if self.pos_order_check.isChecked() or self.pos_real_check.isChecked() or \
           self.vel_order_check.isChecked() or self.vel_real_check.isChecked() or \
           self.cur_order_check.isChecked() or self.cur_real_check.isChecked() :
            self.timer.start()

        else:
            self.timer.stop()
            self.ax1.clear()
            self.ax2.clear()
            self.canvas.draw()
    '''

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

    # 그래프 초기화
    def initialize_scope(self):
        self.timer = QTimer(self)
        self.toolbar = NavigationToolbar(self.canvas, self)
        '''그래프용 메뉴 '''
        menu_layout = QHBoxLayout(self.scope_menu_widget)
        menu_layout.addWidget(self.toolbar)
        menu_layout.addStretch()

        ''' 그래프 '''
        graph_layout = QVBoxLayout(self.scope_graph_widget)
        graph_layout.addWidget(self.canvas)
        graph_layout.addStretch()

        # ver 0.5 2/3성공 -> x 값 아직 설정 안함 
        self.host = self.figure.subplots()
        self.par1 = self.host.twinx()
        self.par2 = self.host.twinx()

        # 다크 그레이 색상의 그래프 배경으로 변경-> 다른 방법 필요 
        self.host.set_facecolor('#7d7c80')

        self.x_data=[]

        # 지령 데이터 리스트 
        self.y_data_O_Pos = []
        self.y_data_O_Vel = []
        self.y_data_O_Cur = []

        # 실제 데이터 리스트 
        self.y_data_R_Pos = []
        self.y_data_R_Vel = []
        self.y_data_R_Cur = []

# 그래프 업데이트 
    def update_scope(self, data):

        if not self.is_graph_update_enable :
            return 
        
        self.Position_data = []
        self.Velocity_data = []
        self.Current_data = []

        # 데이터 리스트에 값을 삽입 
        if self.pos_order_check.isChecked(): # red
            self.y_data_O_Pos.append(data["O_Pos"])
            self.Position_data.extend(self.y_data_O_Pos)

        if self.pos_real_check.isChecked(): # blue
            self.y_data_R_Pos.append(data["R_Pos"])
            self.Position_data.extend(self.y_data_R_Pos)

        if self.vel_order_check.isChecked(): # black
            self.y_data_O_Vel.append(data["O_Vel"])
            self.Velocity_data.extend(self.y_data_O_Vel)

        if self.vel_real_check.isChecked(): # purple
            self.y_data_R_Vel.append(data["R_Vel"])
            self.Velocity_data.extend(self.y_data_R_Vel)

        if self.cur_order_check.isChecked(): # green 
            self.y_data_O_Cur.append(data["O_Cur"])
            self.Current_data.extend(self.y_data_O_Cur)

        if self.cur_real_check.isChecked():  # pink
            self.y_data_R_Cur.append(data["R_Cur"])
            self.Current_data.extend(self.y_data_R_Cur)
        
        self.host.clear()
        self.par1.clear()
        self.par2.clear()

        # 위치, 속도, 전류 y범위 및 축 설정 
        if self.Position_data:
            self.min_val_pos = min(self.Position_data) 
            self.max_val_pos = max(self.Position_data)

        if self.Velocity_data:
            self.min_val_vel=min(self.Velocity_data)
            self.max_val_vel=max(self.Velocity_data)
            self.par1.set_ylim(self.min_val_vel-1, self.max_val_vel+1)
            self.ticks = np.linspace(self.min_val_vel, self.max_val_vel, num=5)
            self.par1.set_yticks(self.ticks)
            self.par1.set_yticklabels(['{:.0f}'.format(tick) for tick in self.ticks])
           
        if self.Current_data:
            self.min_val_cur = min(self.Current_data)
            self.max_val_cur = max(self.Current_data)
            self.par2.spines["right"].set_position(("outward", 45))
        
        # 체크박스 클릭 후 그래프를 그리는 부분     
        if self.pos_order_check.isChecked():
            self.host.plot(self.y_data_O_Pos, label="O_Pos", color='red', linestyle='--')
            self.host.grid(True)

        if self.pos_real_check.isChecked():
            self.host.plot(self.y_data_R_Pos, label="R_Pos", color='blue')
            #self.host.grid(True)

        if self.vel_order_check.isChecked():
            self.par1.plot(self.y_data_O_Vel, label="O_Vel", color='yellow', linestyle='--')
            #self.par1.grid(True)

        if self.vel_real_check.isChecked():
            self.par1.plot(self.y_data_R_Vel, label="R_Vel", color='orange')
            #self.par1.grid(True)

        if self.cur_order_check.isChecked():
            self.par2.plot(self.y_data_O_Cur, label="O_Cur", color='purple', linestyle='--')
            #self.par2.grid(True)

        if self.cur_real_check.isChecked():
            self.par2.plot(self.y_data_R_Cur, label="R_Cur", color='pink')
            #self.par2.grid(True)

        self.host.set_xlabel("Time")

        handles, labels = [], []

        for ax in [self.host, self.par1, self.par2]:
            for handle, label in zip(*ax.get_legend_handles_labels()):
                handles.append(handle)
                labels.append(label)
        self.host.legend(handles, labels)

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
            self.host.clear()
            self.par1.clear()
            self.par2.clear()
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
        
        self.Servo_first = int(data["Status_Servo"])

        if self.Servo_first == 1:
            self.servo_lbl_3.setStyleSheet(u"background-color:red; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid red;\n"
                                            "color : white; \n")
            self.servo_lbl_3.setText("OFF")
        
        self.Inpos = int(data["Status_Inposition"])

        if self.Inpos == 1 :
            self.inpos_lbl_3.setStyleSheet(u"background-color:green; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid green;\n")
        elif self.Inpos == 3 :
            self.inpos_lbl_3.setStyleSheet(u"background-color: orange; \n"
                                            "border-radius: 10px; \n"
                                            "border : 1px solid orange;\n")
            
        self.Alarm = int(data["Status_Alarm"])

        if self.Alarm == 0 : 
            self.alarm__sts_lbl_4.setStyleSheet("background-color: green; \n"
                                                "border-radius: 10px; \n"
                                                "border : 1px solid green;\n")
        if self.Alarm == 26 :
            self.alarm__sts_lbl_4.setStyleSheet("background-color: red; \n"
                                                "border-radius: 10px; \n"
                                                "border : 1px solid red;\n")
            
    def Disable_Home_value(self):
        # 홈밍상태, 서보 상태, 인포지션, 알람, 초기화 상태 추가 
        self.real_current_lbl_5.setText("")
        self.order_current_lbl_5.setText("")
        self.real_vel_lbl_5.setText("")
        self.order_vel_lbl_5.setText("")
        self.real_pos_lbl_5.setText("")
        self.order_pos_lbl_5.setText("")
        self.inpos_lbl_3.setStyleSheet(u"border-radius: 10px; \n"
                                        "border : 1px solid black;")
        self.alarm__sts_lbl_4.setStyleSheet(u"border-radius: 10px; \n"
                                             "border : 1px solid black;")
        self.homing_sts_lbl_3.setStyleSheet(u"border-radius: 10px; \n"
                                             "border : 1px solid black;")
        self.servo_lbl_3.setStyleSheet(u"border-radius: 10px; \n"
                                        "border : 1px solid black;")
        self.servo_lbl_3.setText("ON")

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

    '''servo, Inpos, Home은 제롬한테 파라미터 확인 받고 하기 -> 완료  '''
    def On_clicked_Servo_On(self):
        self.modbus_comm.Servo_On()

        self.modbus_comm.dataReceived.connect(self.Status_Servo)

    def On_clicked_Servo_Off(self):
        self.modbus_comm.Servo_Off()
        
        self.modbus_comm.dataReceived.connect(self.Status_Servo)

    def On_clicked_Home_Home(self):
        self.modbus_comm.Home_Start()

        # 호밍의 상태 읽는건 나중에 value 정해지고 나서 !!
        #self.modbus_comm.dataReceived.connect(self.Status_Home)

    def On_clicked_Alarm_Reset(self):
        self.modbus_comm.Alarm_Clear()
    
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
    
    '''호밍 상태 나중에 변경 -> 지금은 호밍 상태가 어떤 비트인지 몰라서 servo로  같이 함 
    # def Status_Home(self, data):
    #     self.Home_status = data["Status_Home"]

    #     if self.Home_status == 2:
    #         self.homing_sts_lbl_3.setStyleSheet(u"background-color:green; \n"
    #                                         "border-radius: 10px; \n"
    #                                         "border : 1px solid green;\n"
    #                                         "color : white; \n")
    #         self.homing_sts_lbl_3.setText("Home")

    #     elif self.Home_status == 3:
    #         self.homing_sts_lbl_3.setStyleSheet(u"background-color:orange; \n"
    #                                         "border-radius: 10px; \n"
    #                                         "border : 1px solid orange;\n"
    #                                         "color : white; \n")
    #         self.homing_sts_lbl_3.setText("RUN")
'''

    def Onclicked_Read(self):
        read_address = int(self.addr_txt.text())

        self.modbus_comm.Read_Parameter(read_address)

    def Onclicked_Write(self):
        write_address = int(self.addr_txt.text())
        write_value = int(self.val_txt.text())

        self.modbus_comm.Write_Parameter(write_address, write_value)

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
