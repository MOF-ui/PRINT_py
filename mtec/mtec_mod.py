
# I modified this library to use it in a QThread, original by m-tec.com, 
# see https://github.com/m-tec-com/m-tecConnectModbus (2023-06-27)

####################################################   IMPORTS   ####################################################

import serial
import math
import time




####################################################    CLASS     ####################################################

class MtecMod:
    def __init__(self, frequencyInverterID = "01"):
        self.settings_frequencyInverterID   = frequencyInverterID
        self.settings_keepAlive_command     = "03FD000001"
        self.settings_keepAlive_active      = True

        self.settings_serial_baudRate       = 19200
        self.settings_serial_dataBits       = serial.EIGHTBITS
        self.settings_serial_stopBits       = serial.STOPBITS_TWO
        self.settings_serial_parity         = serial.PARITY_NONE
        
        self.temp_sendBuffer    = []
        self.temp_valueBuffer   = []
        self.temp_readBuffer    = []
        self.temp_sendReady     = False
        self.temp_lastSpeed     = 0

        self.connected          = False
    


    def connect(self):
        if( not self.connected ):
            self.serial         = serial.Serial( baudrate   = self.settings_serial_baudRate
                                                ,parity     = self.settings_serial_parity
                                                ,stopbits   = self.settings_serial_stopBits
                                                ,bytesize   = self.settings_serial_dataBits
                                                ,port       = self.serial_port)
            self.connected      = True
            self.temp_sendReady = True
        
        

    def disconnect(self):
        self.serial.close()
        self.connected      = False
        self.temp_sendReady = False





####################################################   SEND COMs   ####################################################

    def sendCommand(self, parameter, value):
        return self.sendHexCommand( self.settings_frequencyInverterID
                                   + parameter
                                   + self.int2hex(value,4))



    def sendHexCommand(self, data):
        crc     = self.calcCRC(data)
        command = data + crc

        self.temp_sendBuffer.append(command)
        return self.sendHex()



    def sendHex(self):
        if self.temp_sendReady and len(self.temp_sendBuffer) > 0:
            command = self.temp_sendBuffer.pop()
            self.send(command)
            self.temp_sendReady = True
            if len(self.temp_valueBuffer) > 0:  
                return command,self.temp_valueBuffer.pop()
            else:
                return command, None
    


    def keepAlive(self):
        command = self.settings_keepAlive_command
        return self.sendHexCommand(self.settings_frequencyInverterID + command) 
    
    


    def send(self, command):
        self.temp_sendReady = False
        self.serial.write(bytes.fromhex(command))
        self.waitForResponse()
        




####################################################   RECEIVE   ####################################################

    def waitForResponse(self):
        command = ""
        timeout = time.time_ns() + (200 * 1000 * 1000)  #200ms

        while True:
            if self.serial.inWaiting() >= 2:
                break
            if time.time_ns() > timeout:
                print("MtecMod: timeout on read")
                print(self.serial.read(self.serial.inWaiting()))
                return False
            
        message_fcID    = int.from_bytes(self.serial.read(1), "little")
        command         += self.int2hex(message_fcID,2)
        message_type    = int.from_bytes(self.serial.read(1), "little")
        command         += self.int2hex(message_type,2)
        
        completeDataLength = 0
        if (message_type == 3): # Type: read
            message_length      = int.from_bytes(self.serial.read(1), "little")
            command             += self.int2hex(message_length, 2)
            completeDataLength  = 3 + message_length + 2 - 3# ID, Type, Length, <Length>, checksum, checksum - alreadyRead

        elif (message_type == 6): # Type: send
            completeDataLength  = 8 - 2 # 8 - alreadyRead

        while True:
            if self.serial.inWaiting() >= completeDataLength:
                break
            if time.time_ns() > timeout:
                print("MtecMod: timeout on read")
                print(self.serial.read(self.serial.inWaiting()))
                return False    
        
        if (message_type == 3): # Type: read
            message_value = 0
            for i in range(message_length):
                message_value   *= 256
                m               = int.from_bytes(self.serial.read(1), "little")
                message_value   += m
                command         += self.int2hex(m, 2)

        elif (message_type == 6): # Type: send
            message_param   = self.int2hex(int.from_bytes(self.serial.read(1), "little"), 2) + self.int2hex(int.from_bytes(self.serial.read(1), "little"), 2)
            command         += message_param
            message_value0  = int.from_bytes(self.serial.read(1), "little")
            message_value1  = int.from_bytes(self.serial.read(1), "little")
            message_value   = message_value0 * 256 + message_value1
            command         += self.int2hex(message_value, 4)

        message_crc = self.int2hex(int.from_bytes(self.serial.read(1), "little"), 2) + self.int2hex(int.from_bytes(self.serial.read(1), "little"), 2)

        if (self.calcCRC(command) != message_crc):
            # ToDo: bad CRC
            print("bad crc")
        
        self.temp_valueBuffer.append(message_value)
        self.temp_sendReady = True
        return True
        
        
        


#################################################  INTERNAL FUNCTIONs  #################################################

    def int2hex(self, value, length):
        s = hex(value)[2:]
        while (len(s) < length):   s = "0" + s
        return s.upper()
            


    def calcCRC(self, command):
        buffer  = bytearray.fromhex(command)
        crc     = 0xFFFF

        for pos in range(len(buffer)):
            crc ^= buffer[pos]
            for k in range(8):
                i = 8 - k
                if ((crc & 0x0001) != 0):
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1

        return self.int2hex((crc % 256) * 256 + math.floor(crc / 256),4)
    
    




#################################################  EASY TO USE FUNCTIONS  #################################################

    def start(self):
        return self.sendHexCommand(self.settings_frequencyInverterID + "06FA00C400")
    

    def startReverse(self):
        return self.sendHexCommand(self.settings_frequencyInverterID + "06FA00C600")
    

    def stop(self):
        return self.sendHexCommand(self.settings_frequencyInverterID + "06FA000000")
    

    def ermergencyStop(self):
        return self.sendHexCommand(self.settings_frequencyInverterID + "06FA001000")
    

    def setSpeed(self, value):
        
        ans = None
        if value != self.temp_lastSpeed:

            if value == 0:      ans = self.stop()
            else:
                if value < 0 and not self.temp_lastSpeed < 0:       ans = self.startReverse()
                elif value > 0 and  not self.temp_lastSpeed > 0:    ans = self.start()

                
            ans = self.sendCommand("06FA01", abs(value) * 100)

        self.temp_lastSpeed = value
        return ans
    
    




###################################################    PROPERTIES    ###################################################

    @property
    def speed(self):
        raise Exception("speed not getable")

    @property
    def ready(self):
        command,switches = self.sendCommand("03FD06", 1)
        if(switches is None): 
            return None
        return ((switches % 32) - (switches % 16) != 0)
    
    @ready.setter
    def ready(self, value):
        raise Exception("ready not setable")
    
    @property
    def frequency(self):
        command,freq = self.sendCommand("03FD00", 1)
        if (freq is None): 
            return None
        return  freq / 100
    
    @frequency.setter
    def frequency(self, value):
        command,freq = self.sendCommand("06FA01", value * 100)
        if (freq is None): 
            return None
        return  freq / 100
        
    @property
    def voltage(self):
        command,volt = self.sendCommand("03FD05", 1)
        if (volt is None): 
            return None
        return  volt / 100
    
    @voltage.setter
    def voltage(self, value):
        raise Exception("voltage not setable")
    
    @property
    def current(self):
        command,amps = self.sendCommand("03FD03", 1)
        if (amps is None): 
            return None
        return  amps / 100
    
    @current.setter
    def current(self, value):
        raise Exception("current not setable")
    
    @property
    def torque(self):
        command,torq = self.sendCommand("03FD18", 1)
        if (torq is None): 
            return None
        return  torq / 100
    
    @torque.setter
    def torque(self, value):
        raise Exception("torque not setable")
