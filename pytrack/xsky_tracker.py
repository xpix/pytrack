from pytrack.tracker import *
from time import sleep
from PIL  import Image, ImageDraw, ImageFont
from pprint import pprint

import Python_BMP.BMP085 as BMP085
sensor = BMP085.BMP085()

def extra_telemetry():
	 # sample code to add one telemetry field
	 return "{:.1f}".format(sensor.read_pressure()/100)


def take_photo(filename, width, height, gps):
	# Use the gps object if you want to add a telemetry overlay, 
	# or use different image sizes at different altitudes, for example
	with picamera.PiCamera() as camera:
		camera.resolution = (width, height)
		camera.start_preview()
		time.sleep(2)
		camera.capture(filename)
		camera.stop_preview()

		position = gps.position()
		print ("Posn: ", position.time, position.lat, position.lon, position.alt, position.fix)
		# create Image object with the input image
		image = Image.open(filename)
		image = image.rotate(180)
		draw = ImageDraw.Draw(image)

		myImageText = "%s UTC\nLat %s\nLon %s\nAlt %sm\nFix %s\nTmp %s\n" % (position.time, position.lat, position.lon, position.alt, position.fix, sensor.read_temperature())
		myBoschText = "Bosch BMP180 Temperature %s C  Pressure %s hPa Altitude %sm\n" % (str(sensor.read_temperature()), str((sensor.read_pressure()/100)), str(sensor.read_altitude()))
		fontBig   = ImageFont.truetype('VeraMoBd.ttf', size=14)
		fontSmall = ImageFont.truetype('VeraMoBd.ttf', size=11)
		color = 'rgb(255, 255, 255)' # white color
		draw.text((3, 3), myImageText, fill=color, font=fontBig)
		draw.text((3, 465), myBoschText, fill=color, font=fontSmall)

		image.save(filename)

mytracker = Tracker()
mytracker.set_lora(payload_id='XSK4', channel=0, frequency=434.451, mode=1, image_packet_ratio=6)

mytracker.add_lora_camera_schedule('images/LORA', period=300, width=640, height=480) 
mytracker.add_full_camera_schedule('images/FULL', period=120)

mytracker.set_image_callback(take_photo)

mytracker.add_lora_video_schedule('videos', period=300, duration=5) 


mytracker.set_sentence_callback(extra_telemetry)

mytracker.start()

while True:
	sleep(1)
