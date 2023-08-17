import socket
import struct
from threading import Thread
from time import sleep

def stt_update():
	global ID
	global toggle

	while toggle:
		if(ID > 0): conn.sendall(struct.pack('<fifffffff',99.0,ID,1.0,2.0,3.0,4.0,5.0,6.0,7.0))
		sleep(1)
	

HOST = "localhost"
PORT = 10001
ID = 0

toggle = 1
print("Booting server...")

while toggle:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.bind((HOST,PORT))
		s.listen()
		print("Listening...")
		conn,addr = s.accept()
		with conn:
			print("Connected by " + str(addr))
			thread = Thread(target=stt_update)
			thread.start()
			while True:
				data = conn.recv(159)
				if not data:	
					toggle = 0
					thread.join()
					print("Client disconnected...\nWaiting for stt_update...")
					break	
				
				ID = struct.unpack('<i',data[0:4])[0]
			
				MT = struct.unpack('c',data[4:5])[0]
				PT = struct.unpack('c',data[5:6])[0]
			
				X1 = struct.unpack('<f',data[6:10])[0]
				Y1 = struct.unpack('<f',data[10:14])[0]
				Z1 = struct.unpack('<f',data[14:18])[0]
				Rx = struct.unpack('<f',data[18:22])[0]
				Ry = struct.unpack('<f',data[22:26])[0]
				Rz = struct.unpack('<f',data[26:30])[0]
				Q = struct.unpack('<f',data[30:34])[0]
				EXT = struct.unpack('<f',data[34:38])[0]	
			
				X2 = struct.unpack('<f',data[38:42])[0]
				Y2 = struct.unpack('<f',data[42:46])[0]
				Z2 = struct.unpack('<f',data[46:50])[0]
				Rx2 = struct.unpack('<f',data[50:54])[0]
				Ry2 = struct.unpack('<f',data[54:58])[0]
				Rz2 = struct.unpack('<f',data[58:62])[0]
				Q2 = struct.unpack('<f',data[62:66])[0]
				EXT2 = struct.unpack('<f',data[66:70])[0]
				
				ACR = struct.unpack('<i',data[70:74])[0]
				DCR = struct.unpack('<i',data[74:78])[0]
				TS = struct.unpack('<i',data[78:82])[0]
				OS = struct.unpack('<i',data[82:86])[0]
	
				T = struct.unpack('<i',data[86:90])[0]
				
				SC = struct.unpack('c',data[90:91])[0]
				
				Z = struct.unpack('<i',data[91:95])[0]
				S1 = struct.unpack('<i',data[95:99])[0]
				S2 = struct.unpack('<i',data[99:103])[0]
				S3 = struct.unpack('<i',data[103:107])[0]
				
				BA = struct.unpack('<i',data[107:111])[0]
				BAP = struct.unpack('<i',data[111:115])[0]
			
				print("ID: " + str(ID) + "\nMT: " + str(MT) + "\nPT: " + str(PT) + \
				"\nX1: " + str(X1) + "\tY1: " + str(Y1) + "\tZ1: " + str(Z1) + \
				"\tRx: " + str(Rx) + "\tRy: " + str(Ry) + "\tRz: " + str(Rz) + "\tQ: " + str(Q) + \
				"\tExt: " + str(EXT) +\
				"\nX2: " + str(X2) + "\tY2: " + str(Y2) + "\tZ2: " + str(Z2) + \
				"\tRx2: " + str(Rx2) + "\tRy2: " + str(Ry2) + "\tRz2: " + str(Rz2) + "\tQ2: " + str(Q2) + \
				"\tExt2: " + str(EXT2) + \
				"\nACR: " + str(ACR) + "\tDCR: " + str(DCR) + "\tTS: " + str(TS) + "\tOS: " + str(OS) + \
				"\tT: " + str(T) + "\tSC: " + str(SC) + "\tZ: " + str(Z) + \
				"\nS1: " + str(S1) + "\tS2: " + str(S2) + "\tS3: " + str(S3) + \
				"\tBA: " + str(BA) + "\tBAP: " + str(BAP))
				#print(ID)
				#print(MT)
				#print(PT)
				#print(X1)

	a = input("Connection closed...  Wait for reconnect? Y/N\n")
	if (a != 'Y'): 
		print("Exiting...")
		s.close()
	else:
		toggle = 1
		print("Restarting socket...")