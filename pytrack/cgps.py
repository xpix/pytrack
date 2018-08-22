import math
import socket
import json
import threading
import psutil
import serial
import pynmea2
from os import	system
from time import sleep

class	GPSPosition(object):
	def __init__(self, when_new_position=None, when_lock_changed=None):
		self.GPSPosition = None
		
	@property
	def time(self):
		return self.GPSPosition['time']

	@property
	def lat(self):
		return self.GPSPosition['lat']
			
	@property
	def lon(self):
		return self.GPSPosition['lon']
			
	@property
	def alt(self):
		return self.GPSPosition['alt']
			
	@property
	def sats(self):
		return self.GPSPosition['sats']
			
	@property
	def fix(self):
		return self.GPSPosition['fix']
		
class	GPS(object):
	"""
	Gets position from UBlox GPS receiver,	using	external	program for	s/w i2c to GPIO pins
	Provides	callbacks on change of state (e.g. lock attained, lock lost, new position received)
	"""
	PortOpen	= False
	
	def __init__(self, when_new_position=None, when_lock_changed=None):
		self._WhenLockChanged =	when_lock_changed
		self._WhenNewPosition =	when_new_position
		self._GotLock = False
		self._GPSPosition	= {'time': '00:00:00', 'lat':	0.0, 'lon':	0.0, 'alt':	0,	'sats': 0, 'fix':	0}
		self._GPSPositionObject	= GPSPosition()
		
		# Start thread	to	talk to GPS	program
		t = threading.Thread(target=self.__gps_thread)
		t.daemon	= True
		t.start()
		
	def __process_gps(self,	s):
		while	1:
			reply	= s.recv(4096)													
			if	reply:
				inputstring	= reply.split(b'\n')
				for line	in	inputstring:
					if	line:
						temp = line.decode('utf-8')
						j = json.loads(temp)
						self._GPSPosition	= j
						if	self._WhenNewPosition:
							self._WhenNewPosition(self._GPSPosition)
						GotLock = self._GPSPosition['fix'] >= 1
						if	GotLock != self._GotLock:
							self._GotLock = GotLock
							if	self._WhenLockChanged:
								self._WhenLockChanged(GotLock)
			else:
				sleep(1)
			
		s.close()

	def __process_gps_serial(self, s):
		c=0
		while	1:
			data = "".join( chr(x) for x in s.readline())
			if (data.startswith('$GPGGA')):
				try:
					c+=1
					if c == 5:
						self.setPowerMode(s, 0)
					if c == 10:
						self.setFlightMode(s)
					else:
						msg = pynmea2.parse(data)
						self._GPSPosition	= {
							'time':msg.timestamp, 
							'lat':float(msg.lat or 0.00), 
							'lon':float(msg.lon or 0.00), 
							'alt':int(msg.altitude or 0),
							'sats':msg.num_sats,
							'fix':msg.gps_qual
						}
						#print(self._GPSPosition)
				except:
					 print("GPS parse error")
			else:
				sleep(1)
			
		s.close()

	def setPowerMode(self, ser, SavePower):
		print("GPS: Set power mode")
		listofbytes = ['0xB5', '0x62', '0x06', '0x11', '0x02', '0x00', '0x08', '0x01', '0x22', '0x92']
		listofbytes[7] = '0x01' if SavePower==1 else '0x00'
		ser.write(bytes([int(x,0) for x in listofbytes]))

	def setFlightMode(self, ser):
		print("GPS: Set flight mode")
		listofbytes = ['0xB5', '0x62', '0x06', '0x24', '0x24', '0x00', '0xFF', '0xFF', '0x06', '0x03', '0x00', '0x00', '0x00', '0x00', '0x10', '0x27', '0x00', '0x00', '0x05', '0x00', '0xFA', '0x00', '0xFA', '0x00', '0x64', '0x00', '0x2C', '0x01', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x16', '0xDC']
		ser.write(bytes([int(x,0) for x in listofbytes]))

	
	def _ServerRunning(self):
		return "gps" in [psutil.Process(i).name()	for i	in	psutil.pids()]
		
	def _StartServer(self):
		system("pytrack-gps > /dev/null &")
		sleep(1)
		
	def __doGPS(self,	host,	port):
		try:		
			# Connect socket to GPS	server
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
			s.connect((host, port))													
			self.__process_gps(s)
			s.close()
		except:
			# Start GPS	server if it's	not running
			if	not self._ServerRunning():
				self._StartServer()

	def __doGPSSerial(self,	device):
		# Connect socket to GPS	server
		s = serial.Serial()
		s.port =	device
		s.baudrate = 9600
		s.timeout =	1
		s.open()
		self.__process_gps_serial(s)
		s.close()

		
	def __gps_thread(self):
		host = '127.0.0.1'
		port = 6005
		device =	'/dev/serial0'
				
		while	1:
			#self.__doGPS(host, port)
			self.__doGPSSerial(device)

					
	def position(self):
		"""returns the	current GPS	position	as	a dictionary, containing the latest	GPS data	('time',	'lat', 'lon', alt', 'sats', 'fix').
		These	values can be access	individually using the properties below (see	the descriptions for	return types etc.).
		"""
		self._GPSPositionObject.GPSPosition	= self._GPSPosition
		return self._GPSPositionObject

		
	@property
	def time(self):
		"""Returns latest	GPS time	(UTC)"""
		return self._GPSPosition['time']
			
	@property
	def lat(self):
		"""Returns latest	GPS latitude"""
		return self._GPSPosition['lat']
			
	@property
	def lon(self):
		"""Returns latest	GPS longitude"""
		return self._GPSPosition['lon']
			
	@property
	def alt(self):
		"""Returns latest	GPS altitude"""
		return self._GPSPosition['alt']
			
	@property
	def sats(self):
		"""Returns latest	GPS satellite count.	 Needs at least 4	satellites for	a 3D position"""
		return self._GPSPosition['sats']
			
	@property
	def fix(self):
		"""Returns a number >=1	for a	fix, or 0 for no fix"""
		return self._GPSPosition['fix']
			
