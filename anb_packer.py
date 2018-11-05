import os
import sys
import glob
import time
import struct
import zlib

def log(msg):
	print(msg)
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

if sys.version_info < (3,4):
	log("Error: Please update Python to version 3.4 or higher!")
try:
	from PIL import Image
except:
	log("Error: Couldn't find the pillow library! Try running 'pip install pillow'")


anb_header = {
'offsets': {
	'magic' : 		{'offset' : 0 , 'size' : 4},
	'animations' : 	{'offset' : 56, 'size' : 4},
	'frames' : 		{'offset' : 60, 'size' : 4},
	'rgb_mask' : 	{'offset' : 68, 'size' : 4}
},
'values': {
	'magic' : 		None,
	'animations' : 	None,
	'frames' : 		None,
	'rgb_mask' : 	None,
	'raw_data' : 	None,
	'wflz_chunks' :	None
}
		}

def get_wflz_struct():
	return {
		'offsets': {
			'magic' : 			{'offset' : 0, 'size' : 4, 'value' : None},
			'compressed_size' : {'offset' : 4, 'size' : 4, 'value' : None},
			'decompressed_size':{'offset' : 8, 'size' : 4, 'value' : None},
			'image_width' : 	{'offset' : -0x20, 'size' : 4, 'value' : None},
			'image_height' : 	{'offset' : -0x1C, 'size' : 4, 'value' : None},
		},
		'compressed_data' : None,
		'decompressed_data' : None,
		'checksum' : None,
		'image_data' : None
	}

def clean_files():
	print("Log: Cleaning up..")
	dat_files = glob.glob('*.dat')
	wflz_files = glob.glob('*.wflz')
	for file in zip(dat_files, wflz_files):
		os.system("del " + file[0])
		os.system("del " + file[1])

def create_images(wflz_headers):
	print("Log: Creating images..")
	for k, chunk in enumerate(wflz_headers):
		decompressed_data = chunk['decompressed_data']
		image_width = struct.unpack('<I', chunk['offsets']['image_width']['value'])[0]
		image_height = struct.unpack('<I', chunk['offsets']['image_height']['value'])[0]
		image_name = 'frame_' + str(k) + '.png'

		try:
			image_out = Image.frombuffer('RGBA', (image_width, image_height), decompressed_data, 'raw', 
					'RGBA', 0, 1)
			image_out.save(image_name)
		except:
				log("Error: Something wen't wrong when converting the image {} {} {}".format(image_name,
					image_width, image_height))

		#Now set the checksums using png value
		with open(image_name, 'rb') as file:
			chunk['checksum'] = zlib.crc32(file.read())


def create_metafile(anb_data, checksums):
	with open('meta.dat', 'wb') as file:
		file.write(struct.pack('<I', len(checksums))) #The number of images for this anb file
		for k, c in enumerate(checksums):
			file.write(struct.pack('<I', c))
		file.write(zlib.compress(anb_data))

def set_pixels(image_name, compression_size):
	new_checksum = 0
	with open(image_name, 'rb') as file:
		new_checksum = zlib.crc32(file.read())

	_image = Image.open(image_name)
	pixels = list(_image.getdata())
	width, height = _image.size

	pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]

	dat_name = image_name[:image_name.find('.')] + '.dat'
	with open(dat_name, 'wb') as file:
		for arr in pixels:
			for tup in arr:
				r,g,b,a = tup

				r = struct.pack('<B', r) #endianess doesn't matter
				g = struct.pack('<B', g)
				b = struct.pack('<B', b)
				a = struct.pack('<B', a)

				file.write(r + g + b + a)

	os.system(sys.path[0] + "\\include" + "\\wflz_extractor\\extractor.exe " + dat_name + ' ' + 
		str(compression_size))

	return new_checksum

def get_wflz_headers(raw_data):
	wflz_chunks = []
	for i in range(raw_data.count(b'WFLZ')):
		current_chunk = get_wflz_struct()
		wflz_offset = raw_data.find(b'WFLZ')

		#Now get values
		chunk_offsets = current_chunk['offsets']
		for k, v in enumerate(chunk_offsets):
			offset = wflz_offset + chunk_offsets[v]['offset']
			size = offset + chunk_offsets[v]['size']
			chunk_offsets[v]['value'] = raw_data[offset : size]

		#Set compressed data and the checksum
		compressed_data = raw_data[wflz_offset : wflz_offset + struct.unpack('<I', 
			chunk_offsets['compressed_size']['value'])[0] + 16]
		current_chunk['compressed_data'] = compressed_data

		wflz_chunks.append(current_chunk)
		raw_data = raw_data[wflz_offset+1 : ]

	return wflz_chunks

def pack(f):
	os.chdir(f)
	if not os.path.isfile('meta.dat'):
		log("Error: Could not find the meta file for these images in " + f)

	#Get the original data sets
	checksums = []
	anb_data = b''

	with open('meta.dat', 'rb') as file:
		num_frames = struct.unpack('<I', file.read(4))[0]
		for _ in range(num_frames):
			checksums.append(struct.unpack('<I', file.read(4))[0])
		anb_data = zlib.decompress(file.read())

	#Collect the images
	image_names = ['frame_' + str(v) + '.png' for v in range(len(checksums))]
	
	#Check for any missing images
	missing_images = []
	for name in image_names:
		if not os.path.isfile(name):
			missing_images.append(name)

	if len(missing_images) != 0:
		for image in missing_images:
			print("Error: Missing file " + image)
		log("")

	print("Log: Repacking {} images..".format(len(image_names)))
	compression_sizes = []
	wflz_headers = get_wflz_headers(anb_data)
	for k, chunk in enumerate(wflz_headers):
		compression_sizes.append(chunk['offsets']['compressed_size']['value'])
	
	#Check what images were edited
	edited_images = {}
	for k, image_name in enumerate(image_names):
		with open(image_name, 'rb') as file:
			new_checksum = zlib.crc32(file.read())
			old_checksum = checksums[k]

			if new_checksum != old_checksum:
				edited_images[image_name] = {'key' : k, 'size' : 
					struct.unpack('<I', compression_sizes[k])[0] + 16}

	#Get the raw pixels from the edited images only
	if len(edited_images) > 0:
		print("Log: Detected {} edited images..".format(len(edited_images)))
		for k, v in enumerate(edited_images):
			new_checksum = set_pixels(v, edited_images[v]['size'])

			with open(v[:v.find('.')] + '.wflz', 'rb') as file:
				key = edited_images[v]['key']
				checksums[key] = new_checksum
				anb_data = anb_data.replace(wflz_headers[key]['compressed_data'],
					file.read())
		
		#Update the meta file
		create_metafile(anb_data, checksums)
		clean_files()

	else:
		print("Log: No changes in the images were found..")

	#Done
	with open(os.path.basename(f) + '.anb', 'wb') as file:
		file.write(anb_data)
	
	log("Log: Finished, check inside " + f)

def extract(f):
	os.chdir(os.path.dirname(f))
	with open(f, 'rb') as file:
		#Set basic values
		for k, v in enumerate(anb_header['offsets']):
			offset = anb_header['offsets'][v]['offset']
			size = anb_header['offsets'][v]['size']

			file.seek(offset)
			anb_header['values'][v] = file.read(size)

		#print("Log: Animations: ", struct.unpack('<I', anb_header['values']['animations'])[0])
		#print("Log: Total frames: ", struct.unpack('<I', anb_header['values']['frames'])[0])

		#Set raw data
		file.seek(0)
		raw_data = file.read()
		anb_header['values']['raw_data'] = raw_data
		anb_header['values']['wflz_chunks'] = raw_data.count(b'WFLZ')

		#Create wflz files for decompressing
		wflz_headers = get_wflz_headers(raw_data)
		wflz_filenames = ['frame_' + str(v)  + '.wflz' for v in range(raw_data.count(b'WFLZ'))]

		#Make the directory for the images
		destination_folder = f[:f.find('.')]
		if not os.path.isdir(destination_folder):
			os.mkdir(destination_folder)
		os.chdir(destination_folder)

		print("Log: Decompressing WFLZ chunks..")
		#Now dump the extacted wflz chunks
		for k, chunk in enumerate(wflz_headers):
			compressed_data = chunk['compressed_data']
			with open(wflz_filenames[k], 'wb') as file:
				file.write(compressed_data)

			#Decompress the created file
			os.system(sys.path[0] + "\\include" + "\\wflz_extractor\\extractor.exe " + wflz_filenames[k])

			#Now update the wflz chunk with the decompressed data
			dat_name = wflz_filenames[k]
			dat_name = dat_name[:dat_name.find('.')] + '.dat'
			with open(dat_name, 'rb') as file:
				chunk['decompressed_data'] = file.read()

		#Done, clean up the files
		clean_files()

		#Now create images using the raw pixels from the decompressed data
		create_images(wflz_headers)
		create_metafile(raw_data, [c['checksum'] for c in wflz_headers])

		log("Log: Finished, check inside " + destination_folder)

if len(sys.argv) != 2:
	print("Info: ###Commands###")
	print("Info: anb_packer.py target.anb, to unpack a file")
	print("Info: anb_packer.py target_folder, to pack a folder")
	log("")

#User input verified being script
try:
	target_file = sys.argv[1]
	if os.path.isfile(target_file):
		extract(target_file)

	if os.path.isdir(target_file):
		pack(target_file)

except Exception as e:
	clean_files()
	log(e)

log("Log: Program finished.")