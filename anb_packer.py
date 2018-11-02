from struct import pack, unpack
import os
import sys
import glob
import json
import time

if sys.version_info < (3,4):
	print("Error: Please update Python to version 3.4 or higher!")
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

try:
	from PIL import Image
except:
	print("Error: Couldn't find the pillow library! Try running 'pip install pillow'")
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

def overwright(target):
	with open(target, 'rb') as file:
		data = file.read()

	copy_data = b''
	for _ in range(data.count(b'WFLZ')):

		wflz_offset = data.find(b'WFLZ')
		if wflz_offset != -1:
			chunk_size = data[wflz_offset - 4: wflz_offset]
			chunk_size = unpack('<I', chunk_size)[0]

			#Get image width and height
			image_width = unpack('<I', data[wflz_offset - 0x20: (wflz_offset - 0x20) + 4])[0]
			image_height = unpack('<I', data[wflz_offset - 0x1c: (wflz_offset - 0x1c) + 4])[0]

			#Get bounding box rect
			bounds_offset = len(data[:wflz_offset]) + chunk_size
			prev = bounds_offset
			bounds_offset += data[bounds_offset:].find(b'\xFF\xFF\xFF') + 0x10
			prev -= (prev - bounds_offset)

			#Split data
			copy_data += data[ : prev]
			data = data[prev + 0x8 :]
			copy_data += bytes(4) + pack('<H', image_width) + pack('<H', image_height)
	copy_data += data

	#Now make the clone
	with open(target, 'wb') as file:
		file.write(copy_data)	

def get_pixels(png_images):
	print("Log: Extracting raw pixels from images...")
	for image in png_images:
		frame_name = os.path.basename(image)
		frame_name = frame_name[:frame_name.find('.')]

		try:
			target_width = JSON_DATA[frame_name]['width']
			target_height = JSON_DATA[frame_name]['height']
		except:
			log("Error: Could not find the image properties in the meta.json file!\n Error: Did you rename these images?")

		_image = Image.open(image)
		pixels = list(_image.getdata())
		width,height = _image.size

		if (width, height) != (target_width, target_height):
			log("Error: The image dimensions do not match! Expected: {}, Got: {}".format(
				(target_width, target_height), (width, height)))

		pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]

		file_name = os.path.basename(image)
		file_name = file_name[:file_name.find('.')]

		with open(file_name + '.dat', 'wb') as file:
			for arr in pixels:
				for tup in arr:
					r,g,b,a = tup

					r = pack('<B', r) #endianess doesn't matter
					g = pack('<B', g) #endianess doesn't matter
					b = pack('<B', b) #endianess doesn't matter
					a = pack('<B', a) #endianess doesn't matter

					file.write(r + g + b + a)
				

def set_json(directory):
	with open(directory + '\\meta.json', 'r') as file:
		global JSON_DATA
		JSON_DATA = json.loads(file.read())

def _sort(files):
	arr = [_ for _ in range(len(files))]
	for f in files:
		_id = f[f.find('_')+1:]
		_id = _id[:_id.find('.')]
		
		arr[int(_id)] = f
	return arr

def convert_to_image(data_files):
	print("Log: Converting extracted frames to images...")

	for f in data_files:
		with open(f, 'rb') as file:
			frame_name = f[:f.find('.')]
			image_name = frame_name + '.png'
			image_width = JSON_DATA[frame_name]['width']
			image_height = JSON_DATA[frame_name]['height']
			
			try:
				image_out = Image.frombuffer('RGBA', (image_width, image_height), file.read(), 'raw', 
					'RGBA', 0, 1)
				image_out.save(image_name)
			except:
				log("Error: Something wen't wrong when converting the image {} {} {}".format(image_name,
					image_width, image_height))

def compress():
	os.chdir(TARGET_FILE)
	print("Log: Compressing images...")

	png_images = glob.glob('*.png')
	if len(png_images) <= 0:
		log("Error: Could not find any .PNG images inside " + TARGET_FILE)
	if len(png_images) != len(JSON_DATA)-1:
		log("Error: Invalid number of frames found! Expected: {}, Got: {}".format(len(JSON_DATA)-1,
			len(png_images)))

	#Create .dat files with the raw pixel data
	get_pixels(png_images)
	data_files = glob.glob('*.dat')
	for f in data_files:
		file_name = os.path.basename(f)
		file_name = file_name[:f.find('.')]
		compressed_size = JSON_DATA[file_name]['compressed_size'] + 16

		#Call WFLZ compressor.
		os.system(HOME_DIRECTORY + "\\include" + "\\wflz_extractor\\extractor.exe " + f + ' ' + 
			str(compressed_size))

	#Now we locate the owner of the frames and swap the wflz headers.
	print("Log: Locating the owner .ANB file...")
	anb_file = JSON_DATA['owner']
	if not os.path.isfile(anb_file):
		print("Log: Could'nt find the owner .anb file for these frames...")
		anb_location = input("Input: Would you mind telling me where its located: ").strip().replace('"', '')
		if not os.path.isfile(anb_location):
			clean_files()
			log("Error: Could not find the anb file in {} or in {}".format(JSON_DATA['owner'],
				anb_location))

		anb_file = anb_location

	with open(anb_file, 'rb') as file:
		anb_data = file.read()

	wflz_files = glob.glob('*.wflz')
	wflz_files = _sort(wflz_files)
	wflz_data = []
	for f in wflz_files:
		with open(f, 'rb') as file:
			wflz_data.append(file.read())

	#Now replace the wflz chunks with the edited ones
	tmp = b''
	for data in wflz_data:
		wflz_offset = anb_data.find(b'WFLZ')
		if wflz_offset == -1:
			continue
		padding = anb_data[:wflz_offset]
		tmp += padding
		tmp += data
		anb_data = anb_data[len(data) + len(padding):]
	tmp += anb_data

	name = os.path.basename(anb_file)
	if os.path.isfile(name):
		name = 'modded_' + name
	with open(name,'wb') as file:
		file.write(tmp)

	overwright(name) #Overwright the bounding box values
	clean_files()
	log("Log: Finished, check inside " + TARGET_FILE)


def extract():
	with open(TARGET_FILE, 'rb') as file:
		if file.read(4) != b'YCSN':
			log("Error: This is not a valid .anb file!")

		file_data = file.read()

	wflz_chunks = file_data.count(b'WFLZ')
	if wflz_chunks <= 0:
		log("Error: No embedded images were found in this file!")

	print("Log: Creating a destination folder...")
	if not os.path.isdir(DESTINATON_FOLDER):
		os.system('mkdir ' + DESTINATON_FOLDER)
	os.chdir(DESTINATON_FOLDER)

	#Grab the whole data and split it for each wflz chunk
	print("Log: Extracting {} frames...".format(wflz_chunks))
	meta_data = {}
	meta_data['owner'] = TARGET_FILE
	for i in range(wflz_chunks):
		wflz_offset = file_data.find(b'WFLZ')
		wflz_name = 'frame_' + str(i) + '.wflz'

		data_size = file_data[wflz_offset + 4: wflz_offset + 8]
		data_size = unpack('<I', data_size)[0]
		data_size += 0x10
		image_width = file_data[wflz_offset - 0x20: (wflz_offset - 0x20) + 4]
		image_height = file_data[wflz_offset - 0x1c: (wflz_offset - 0x1c) + 4]
		compressed_size = file_data[wflz_offset + 4: wflz_offset + 8]

		meta_data['frame_' + str(i)] = { 
			'width' : unpack('<I', image_width)[0],
			'height' : unpack('<I', image_height)[0], 
			'compressed_size' : unpack('<I', compressed_size)[0]
			}

		with open(wflz_name, 'wb') as wflz_file:
			wflz_file.write(file_data[wflz_offset : wflz_offset + data_size])

		#Remove extracted chunk from the current data
		file_data = file_data[wflz_offset + 1:]

	#Create the meata.json file containing repacking information
	with open('meta.json', 'w') as meta_file:
		json.dump(meta_data, meta_file)

	set_json(os.getcwd())
	print("Log: Decompressing frames...")
	wflz_files = glob.glob('*.wflz')
	for f in wflz_files:
		os.system(HOME_DIRECTORY + "\\include" + "\\wflz_extractor\\extractor.exe " + f)

	#Now convert the decompressed wfzl files to png images
	convert_to_image(glob.glob('*.dat'))
	clean_files()
	log("Log: Finished, check inside " + DESTINATON_FOLDER)

def clean_files():
	print("Log: Cleaning up...")
	dat_files = glob.glob('*.dat')
	wflz_files = glob.glob('*.wflz')
	for file in zip(dat_files, wflz_files):
		os.system("del " + file[0])
		os.system("del " + file[1])

def log(msg):
	print(msg)
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

#Validate user input
if len(sys.argv) != 2:
	log("Error: Please specify a target .anb file or a target folder!")

#Define global variables
HOME_DIRECTORY = os.path.dirname(sys.argv[0])
if not os.path.isdir(HOME_DIRECTORY):
	HOME_DIRECTORY = sys.path[0]
TARGET_FILE = sys.argv[1]
TARGET_NAME = os.path.basename(TARGET_FILE)[:os.path.basename(TARGET_FILE).find('.')]
TARGET_FORMAT = TARGET_FILE[TARGET_FILE.find('.'):]
TARGET_DIRECTORY = os.path.dirname(TARGET_FILE)
DESTINATON_FOLDER = os.path.dirname(TARGET_FILE) + '\\' + TARGET_NAME
JSON_DATA = None

#Everthing went well start program
if os.path.isdir(TARGET_FILE):
	JSON_PATH = TARGET_FILE + '\\meta.json'
	if not os.path.isfile(JSON_PATH):
		log("Error: Could not find the generated meta.json file in " + JSON_PATH)

	set_json(TARGET_FILE)
	compress()
else:
	if not os.path.isfile(TARGET_FILE):
		log("Error: The target file '{}' was not found!".format(TARGET_FILE))
	extract()

log("Log: Program finished.")
