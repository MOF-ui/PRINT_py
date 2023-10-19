import socket
import struct
from threading import Thread
from time import sleep

def stt_update():
	global ID
	global toggle

	while toggle:
		conn.sendall(struct.pack('<fifffffff',99.0,ID,1.0,2.0,3.0,4.0,5.0,6.0,7.0))
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
				
				ID  			= struct.unpack('<i',data[0:4])[0]
			
				MT  			= struct.unpack('c',data[4:5])[0]
				PT  			= struct.unpack('c',data[5:6])[0]
			
				X1  			= struct.unpack('<f',data[6:10])[0]
				Y1  			= struct.unpack('<f',data[10:14])[0]
				Z1  			= struct.unpack('<f',data[14:18])[0]
				Rx  			= struct.unpack('<f',data[18:22])[0]
				Ry  			= struct.unpack('<f',data[22:26])[0]
				Rz  			= struct.unpack('<f',data[26:30])[0]
				Q   			= struct.unpack('<f',data[30:34])[0]
				EXT 			= struct.unpack('<f',data[34:38])[0]	
			
				X2  			= struct.unpack('<f',data[38:42])[0]
				Y2  			= struct.unpack('<f',data[42:46])[0]
				Z2  			= struct.unpack('<f',data[46:50])[0]
				Rx2 			= struct.unpack('<f',data[50:54])[0]
				Ry2 			= struct.unpack('<f',data[54:58])[0]
				Rz2 			= struct.unpack('<f',data[58:62])[0]
				Q2  			= struct.unpack('<f',data[62:66])[0]
				EXT2			= struct.unpack('<f',data[66:70])[0]
				
				ACR 			= struct.unpack('<i',data[70:74])[0]
				DCR 			= struct.unpack('<i',data[74:78])[0]
				TS  			= struct.unpack('<i',data[78:82])[0]
				OS  			= struct.unpack('<i',data[82:86])[0]
	
				T   			= struct.unpack('<i',data[86:90])[0]
				
				SC  			= struct.unpack('c',data[90:91])[0]
				
				Z   			= struct.unpack('<i',data[91:95])[0]
				
				m1_id 	 		= struct.unpack('<i',data[95:99])[0]
				m1_steps 		= struct.unpack('<i',data[99:103])[0]
				m2_id 	 		= struct.unpack('<i',data[103:107])[0]
				m2_steps 		= struct.unpack('<i',data[107:111])[0]
				m3_id 	 		= struct.unpack('<i',data[111:115])[0]
				m3_steps 		= struct.unpack('<i',data[115:119])[0]
				pnmtcClamp_id 	= struct.unpack('<i',data[119:123])[0]
				pnmtcClamp_yn 	= struct.unpack('<i',data[123:127])[0]
				knife_id 		= struct.unpack('<i',data[127:131])[0]
				knife_yn 		= struct.unpack('<i',data[131:135])[0]
				m4_id	 		= struct.unpack('<i',data[135:139])[0]
				m4_steps 		= struct.unpack('<i',data[139:143])[0]
				pnmtcFiber_id 	= struct.unpack('<i',data[143:147])[0]
				pnmtcFiber_yn 	= struct.unpack('<i',data[147:151])[0]
				time_id	 		= struct.unpack('<i',data[151:155])[0]
				time_time 		= struct.unpack('<i',data[155:159])[0]
			
				print(f"ID: {ID}\nMT: {MT}\nPT: {PT}\
					    \nX1: {X1}\tY1: {Y1}\tZ1: {Z1}\
					 	\tRx: {Rx}\tRy: {Ry}\tRz: {Rz}\tQ: {Q}\
						\tExt: {EXT}\
						\nX2: {X2}\tY2: {Y2}\tZ2: {Z2}\
						\tRx2: {Rx2}\tRy2: {Ry2}\tRz2: {Rz2}\tQ2: {Q2}\
						\tExt2: {EXT2}\
						\nACR: {ACR}\tDCR: {DCR}\tTS: {TS}\tOS: {OS}\
						\tT: {T}\tSC: {SC}\tZ: {Z}\
						\nM1_ID: {m1_id}\tM1_ST: {m1_steps}\tM2_ID: {m2_id}\tM2_ST: {m2_steps}\
						\tM3_ID: {m3_id}\tM3_ST: {m3_steps}\tPC_ID: {pnmtcClamp_id}\tPC_YN: {pnmtcClamp_yn}\
						\tK_ID: {knife_id}\tK_YN: {knife_yn}\tM4_ID: {m4_id}\tM4_ST: {m4_steps}\
						\tPF_ID: {pnmtcFiber_id}\tPF_YN: {pnmtcFiber_yn}\tT_ID: {time_id}\tT_T: {time_time}")
				

	a = input("Connection closed...  Wait for reconnect? Y/N\n")
	if (a != 'Y'): 
		print("Exiting...")
		s.close()
	else:
		toggle = 1
		print("Restarting socket...")