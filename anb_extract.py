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
import json
from time import sleep
from pathlib import Path
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
	def __init__(self, file):
		self.nodes = ANBStruct(file).nodes

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

	def get_buffer(self, file, offset):
		with open(file, 'rb') as file:
			file.seek(offset + 0x10) #0x10 is the unk header for the ANB files.
			wflz_struct = WFLZStruct()
			file.readinto(wflz_struct)
			return file.read(wflz_struct.size)

	def create_image(self, name, width, height):
		# Using the PIL lib here to create a PNG image from raw pixels
		_buffer = Path(name).read_bytes()
		try:
			image_out = Image.frombytes('RGBA', (width, height), _buffer, 'raw')
			image_out.save(Path(name).with_suffix('.png'))

		except Exception as e:
			os.remove(name)
			_exit(f"Error: Could not convert raw pixels to image. Width: {width}, Height: {height} \n {e}")

		os.remove(name)
		
if __name__ == '__main__':
	# Verify the file exist and an arg was giving
	if not len(sys.argv) == 2:
		_exit("Error: Please specify a target .anb file.")
	if not Path(sys.argv[1]).is_file():
		_exit(f"Error: The file '{sys.argv[1]}' was not found.")

	m = Main(sys.argv[1])
	_exit(f"Log: Program finished, look inside '{m.directory}' folder.")