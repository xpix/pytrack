import picamera
import threading
import time
import os
import fnmatch

class RecordVideo(object):
	"""
	Simple Pi camera library that uses the picamera library and the SSDV encoder
	"""
	
	def __init__(self):
		# self.camera = picamera.PiCamera()
		self.Schedule = []
	
	def __record_thread(self):
		while True:
			for item in self.Schedule:
				# Take photo if needed
				if time.monotonic() > item['LastTime']:
					item['LastTime'] = time.monotonic() + item['Period']
					filename = item['TargetFolder'] +  time.strftime("%H_%M_%S", time.gmtime()) + '.h264'
					print("Taking video " + filename)
					with picamera.PiCamera() as camera:
					camera.start_preview()
					camera.start_recording(filename)
					sleep(item['Duration'])
					camera.stop_recording()
					camera.stop_preview()

			time.sleep(1)

	def clear_schedule(self):
		"""Clears the schedule."""
		self.Schedule = []
		
	def add_schedule(self, Channel, Callsign, TargetFolder, Period, Duration):
		"""
		Adds a schedule for a specific "channel", and normally you would set a schedule for each radio channel (RTTY and LoRa) and also one for full-sized images that are not transmitted.
		- Channel is a unique name for this entry, and is used to retrieve/convert photographs later
		- Callsign is used for radio channels, and should be the same as used by telemetry on that channel (it is embedded into SSDV packets)
		- TargetFolder is where the JPG files should be saved.  It will be created if necessary.  Each channel should have its own target folder.
		- Period is the time in seconds between photographs.  This should be much less than the time taken to transmit an image, so that there are several images to choose from when transmitting.  Depending on the combination of schedules, and how long each photograph takes, it may not always (or ever) be possible to maintain the specified periods for all channels.
		- Width and Height are self-evident.  Take care not to create photographs that take a long time to send.  If Width or Height are zero then the full camera resolution (as determined by checking the camera model - Omnivision or Sony) is used.
		- VFlip and HFlip can be used to correct images if the camera is not physically oriented correctly. 	
		"""
		TargetFolder = os.path.join(TargetFolder, '')	

		if not os.path.exists(TargetFolder):
			os.makedirs(TargetFolder)
		
		self.Schedule.append({'Channel': Channel,
							  'Callsign': Callsign,
							  'TargetFolder': TargetFolder,
							  'Period': Period,
                       'Duration' : Duration,
							  'LastTime': 0,
							  'ImageNumber': 0,
							  'PacketIndex': 0,
							  'PacketCount': 0,
							  'File': None})
		# print("schedule is: ", self.Schedule)
		