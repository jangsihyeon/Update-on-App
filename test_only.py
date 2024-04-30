'''
실험용 파일 
'''

import serial
import serial.tools.list_ports
import minimalmodbus
import time

instrument = minimalmodbus.Instrument("COM4", 1)
instrument.serial.baudrate = 19200
instrument.serial.timeout = 1

# instrument.write_register(registeraddress=414, value=0, functioncode=6)

#instrument.write_register(registeraddress=400, value=12, functioncode=6)
#instrument.write_register(registeraddress=410, value=1, functioncode=6)
Inpos=instrument.read_register(registeraddress=136, functioncode=3)
print(Inpos)
# O_Pos = instrument.read_registers(registeraddress=126, number_of_registers = 2, functioncode=3)
# O_Pos = (O_Pos[1] << 16) | O_Pos[0] 

# if O_Pos & 0x80000000 :
#     O_Pos -= 0x100000000

# print(f"first O Pos : {O_Pos}") 
# first_ = 0x7d0&0xFFFF
# second_ = 0xFFFF

# combine_list = [first_, second_]
# instrument.write_register(registeraddress=303, value=500, functioncode=6)
# start =time.time()
# instrument.write_registers(registeraddress=313, values=combine_list)
# end = time.time()
# instrument.write_register(registeraddress=323, value=1, functioncode=16)

# O_Pos = instrument.read_registers(registeraddress=117, number_of_registers = 2, functioncode=3)
# O_Pos = (O_Pos[1] << 16) | O_Pos[0] 

# if O_Pos & 0x80000000 :
#     O_Pos -= 0x100000000

# Val = (second_ << 16) | first_

# if Val & 0x80000000 :
#     Val -= 0x100000000

# print(f"{round(end-start, 1)} : {O_Pos}") 


