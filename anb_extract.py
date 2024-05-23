#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'include')

try:
	from PIL import Image
except:
	print("Error: Couldn't find the pillow library! Try running 'pip install pillow'")
	sys.exit(-1)

import os
import struct
from time import sleep
from pathlib import Path
import zlib
import glob
from node_structs import WFLZStruct
from anb_map import ANBStruct


def _exit(msg):
	print(msg)
	print("Exiting in 5 seconds..")
	sleep(5)
	sys.exit(-1)

def extract_wflz(file_name):
	file_name = f'"{str(file_name)}"'
	os.system("include\\wflz_extractor\\extractor.exe " + file_name)

class Main:
	def __init__(self):
		pass

	def unpack(self, file):
		anb_instance = ANBStruct(file)
		self.nodes = anb_instance.nodes
		self.unk_offset = anb_instance.unk_offset
		self.image_data_checksums = [] # 4 Bytes used to detect image changes

		# Make the destination dir
		self.directory = Path(str(Path(file).parent) + '\\' + Path(file).stem)
		self.directory.mkdir(exist_ok=True)

		frames = [n for n in self.nodes if n['type'] == 1]

		print(f"Log: Extracting {len(frames)} frames..")
		for k, n in enumerate(frames):
			node = n['node']
			_buffer	=	self.get_buffer(file, node.data_offset)

			file_name =	self.directory.joinpath(f'frame_{str(k)}.wflz')

			# Decompress the WFLZ, delete the temp file, create the PNG with raw pixel data
			open(file_name, 'wb').write(_buffer)
			extract_wflz(file_name)
			os.remove(file_name)

			self.create_image(Path(file_name).with_suffix('.dat'), node.width, node.height)

		self.create_metafile(anb_instance.all_file_data, self.image_data_checksums)

	def get_buffer(self, file, offset):
		with open(file, 'rb') as file:
			file.seek(offset + self.unk_offset) # 0x10 is the unk header for some ANB files.
			wflz_struct = WFLZStruct()
			file.readinto(wflz_struct)
			return file.read(wflz_struct.size)

	def create_image(self, name, width, height):
		# Using the PIL lib here to create a PNG image from raw pixels
		_buffer = Path(name).read_bytes()
		try:
			image_out = Image.frombytes('RGBA', (width, height), _buffer, 'raw')
			image_out.save(Path(name).with_suffix('.png'))

			#Now set the checksums using png value
			with open(Path(name).with_suffix('.png'), 'rb') as file:
				self.image_data_checksums.append(zlib.crc32(file.read()))


		except Exception as e:
			os.remove(name)
			_exit(f"Error: Could not convert raw pixels to image. Width: {width}, Height: {height} \n {e}")

		os.remove(name)

	def create_metafile(self, anb_data, image_data_checksums):
		print(f"Log: Creating Metadata File..")
		with open(self.directory.joinpath('meta.data'), 'wb') as file:
			file.write(struct.pack('<I', len(image_data_checksums))) #The number of images for this anb file
			for k, chunk in enumerate(image_data_checksums):
				file.write(struct.pack('<I', chunk))
			file.write(zlib.compress(anb_data))


	def set_pixels(self, image_name, compression_size):
		new_checksum = 0
		with open(image_name, 'rb') as file:
			new_checksum = zlib.crc32(file.read())

		_image = Image.open(image_name)
		pixels = list(_image.getdata())
		width, height = _image.size

		pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]

		image_data_file_name = Path(image_name).stem + '.dat'
		with open(image_data_file_name, 'wb') as file:
			for arr in pixels:
				for tup in arr:
					r,g,b,a = tup

					r = struct.pack('<B', r) # Endianess doesn't matter
					g = struct.pack('<B', g)
					b = struct.pack('<B', b)
					a = struct.pack('<B', a)

					file.write(r + g + b + a)

		image_data_file_name = self.directory.joinpath(image_data_file_name)
		image_data_file_name = f'"{str(image_data_file_name)}"'

		script_dir = os.path.dirname(__file__)  # Directory where the script is located
		full_path = os.path.join(script_dir, "include", "wflz_extractor", "extractor.exe")

		#os.system(sys.path[0] + "\\include" + "\\wflz_extractor\\extractor.exe " + image_data_file_name + ' ' + str(compression_size))
		os.system(full_path + ' ' + image_data_file_name + ' ' + str(compression_size))

		return new_checksum
	
	def clean_files(self):
		print("Log: Cleaning up..")
		dat_files = glob.glob('*.dat')
		wflz_files = glob.glob('*.wflz')
		for file in zip(dat_files, wflz_files):
			os.remove(file[0])
			os.remove(file[1])


	def pack(self, file_dir):
		self.directory = Path(str(Path(file_dir).parent) + '\\' + Path(file_dir).stem)
		os.chdir(file_dir)
		if not os.path.isfile('meta.data'):
			_exit("Error: Could not find the meta file for these images in " + file_dir)

		# Get original ANB raw data and image checksums
		checksums = []
		anb_data = b''

		with open('meta.data', 'rb') as file:
			num_frames = struct.unpack('<I', file.read(4))[0]
			for _ in range(num_frames):
				checksums.append(struct.unpack('<I', file.read(4))[0])
			anb_data = zlib.decompress(file.read())

		# TEMP
		with open('anb_data.data', 'wb') as file:
			file.write(anb_data)

		# Check for any missing images
		image_names = ['frame_' + str(v) + '.png' for v in range(len(checksums))]
		for name in image_names:
			if not os.path.isfile(name):
				_exit("Error: Missing image " + name)

		print("Log: Repacking {} images..".format(len(image_names)))

		# Get all the WFLZ Chunks
		anb_instance = ANBStruct('anb_data.data')
		self.nodes = anb_instance.nodes
		self.unk_offset = anb_instance.unk_offset
	
		frames = [n for n in self.nodes if n['type'] == 1]
		wflz_chunks = []
		for k, n in enumerate(frames):
			node = n['node']
			wflz_chunk = self.get_buffer('anb_data.data', node.data_offset)
			wflz_chunks.append(wflz_chunk)

		os.remove('anb_data.data')

		# Get every WFLZ's compressed size
		compression_sizes = []
		for k, chunk in enumerate(wflz_chunks):
			compression_sizes.append(len(chunk)) # anb_instance.unk_offset Mess around with this offset, works for no header ones

		# Check which images were edited
		edited_images = {}
		for k, image_name in enumerate(image_names):
			with open(image_name, 'rb') as file:
				new_checksum = zlib.crc32(file.read())
				old_checksum = checksums[k]

				if new_checksum != old_checksum:
					edited_images[image_name] = {'key' : k, 'size' : compression_sizes[k]}

		# Get the raw pixels from the edited images only
		if len(edited_images) > 0:
			print("Log: Detected {} edited images..".format(len(edited_images)))
			for k, v in enumerate(edited_images):
				new_checksum = self.set_pixels(v, edited_images[v]['size'])

				with open(Path(v).stem + '.wflz', 'rb') as file:
					key = edited_images[v]['key']
					checksums[key] = new_checksum

					anb_data = anb_data.replace(wflz_chunks[key],file.read())
					

		with open(os.path.basename(file_dir) + '.anb', 'wb') as file:
			file.write(anb_data)

		#Update the meta file
		self.create_metafile(anb_data, checksums)
		self.clean_files()
		
if __name__ == '__main__':
	# Verify the file exist and an arg was giving
	main = Main()
	if not len(sys.argv) == 2:
		_exit("Error: Please specify a target .anb file or directory")
	if not Path(sys.argv[1]).is_file():
		main.pack(sys.argv[1])
	else:
		main.unpack(sys.argv[1])

	_exit(f"Log: Program finished, look inside '{main.directory}' folder.")