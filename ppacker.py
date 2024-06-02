#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct
from time import sleep
from pathlib import Path
import os

def _exit(msg):
	print(msg)
	print("Exiting in 5 seconds..")
	sleep(5)
	sys.exit(-1)

def unpack(file, _bytes):
	return struct.unpack({2: 'H', 4 : 'I', 8 : 'Q'}[_bytes], file.read(_bytes))[0]

def pack(val, _bytes):
	return struct.pack({2: 'H', 4 : 'I', 8 : 'Q'}[_bytes], val)

class PAKClass:
	def __init__(self, pak_file):
		if pak_file.suffix == '.pak':
			self.unpack(pak_file)
		elif Path(pak_file).is_dir():
			self.pack(pak_file)
		else:
			_exit("Error: This is not a valid .PAK file or a directory to pack!")

	
	def unpack(self, pak_file):
		# Get the packed file names and data offsets
		file_names = self.get_filenames(pak_file)
		data_sets  = self.get_datasets(pak_file)

		print(f"Log: Extracting {len(file_names)} files..")

		# Make the output folder
		parent_dir = Path(pak_file.stem)
		parent_dir.mkdir(exist_ok=True)

		# Create a metafile to contain the file names for future repacking
		with open(parent_dir.joinpath('meta.dat'), 'wb') as ff:
			ff.write(pack(len(file_names), 4))
			for n in file_names:
				ff.write(pack(len(n), 2))
				ff.write(n)

		# Create the directories and files needed
		for k,name in enumerate(file_names):
			_dir = Path(name.decode()).parent
			_dir = parent_dir.joinpath(_dir)
			_dir.mkdir(parents=True, exist_ok=True)

			child_dir = _dir.joinpath(Path(name.decode()).name)

			# Write the file's unpacked data
			with open(child_dir, 'wb') as ff:
				ff.write(data_sets[k])

	def pack(self, pak_dir):
		os.chdir(pak_dir)
		file_names = []
		try:
			# Get the number of files and file names
			with open(pak_dir.joinpath('meta.dat'), 'rb') as file:
				num_files = unpack(file, 4)
				file_names = [file.read(unpack(file, 2)).decode() for _ in range(num_files)]

		except FileNotFoundError:
			_exit("Error: The meta file was not found in the current directory.")
		except Exception as e:
			_exit(e)

		# Create the PAK file header
		_buffer = bytes(4) + pack(len(file_names), 4) + pack(24, 8)
		

		# Verify all files exist and get their sizes, data
		files = {}
		print(f"Log: Packing {len(file_names)} files..")
		for name in file_names:
			if not Path(name).exists():
				_exit("Error: Missing file " + name)

			with open(name, 'rb') as file:
				size =  os.path.getsize(name) - 16

				data = pack(size, 8)  + bytes(8) + file.read()
				size = len(data)

				files[name] = {'data_size' : size, 'name_size' : len(name) + 1, 'data' : data}
				

		# Set the name offsets and data offsets and raw data
		_buffer += self.get_body(len(file_names), files)
		
		# Write to the new packed file
		with open(pak_dir.name + '.pak', 'wb') as ff:
			ff.write(_buffer)

	def get_body(self, num_file, files):
		# Get the size of the chunk that contains the offsets
		data_offset_offset = (num_file * 8) + 24
		name_offset_chunksize  = num_file * 8

		# Get the total size of all the files
		total_filesizes = 0
		offset = data_offset_offset
		data_offsets = []
		alldata = b''
		file_name_sizes = []
		name_chunk = b''

		for f in files:
			size = files[f]['data_size']
			data = files[f]['data']
			name_length = files[f]['name_size']

			total_filesizes += size
			offset += size
			alldata += data

			name_chunk += f.encode() + bytes(1)

			file_name_sizes.append(name_length)
			data_offsets.append(offset)

		data_offsets.pop() # Don't need the last one
		file_name_sizes.pop() # Don't need the last one

		name_offsets = total_filesizes + name_offset_chunksize + 24
		_buffer = pack(name_offsets, 4) + bytes(4) + pack(data_offset_offset, 4) + bytes(4)

		# Pack the data offsets
		for i in data_offsets:
			_buffer += pack(i, 4) + bytes(4)

		# Pack all the data
		_buffer += alldata

		# Add the file name offsets and file names
		name_offset_chunksize += len(_buffer) + 16
		_buffer += pack(name_offset_chunksize, 4) + bytes(4)

		# Name offsets
		previous_name_sizes = 0
		# Size = size of file name
		for size in file_name_sizes:
			c = name_offset_chunksize + size + previous_name_sizes
			previous_name_sizes += size
			_buffer += pack(c, 8)

		# Write the file names
		_buffer += name_chunk

		return _buffer

	def get_datasets(self, pak_file):
		data_sets = []
		with open(pak_file, 'rb') as file:
			file.seek(4)
			num_files = unpack(file, 4) # Number of files
			file.seek(unpack(file, 8)) # The data offset value

			# Get data offsets
			data_offsets = []
			for _ in range(num_files):
				data_offsets.append(unpack(file, 8))

			# Get data chunks 
			for offset in data_offsets:
				file.seek(offset)
				size = unpack(file, 8) + 0x10

				file.seek(offset + 0x10)
				data_sets.append(file.read(size))

		return data_sets

	def get_filenames(self, pak_file):
		with open(pak_file, 'rb') as file:
			file.seek(0x10)
			name_offset = unpack(file, 8)
			file.seek(name_offset)
			name_offset = unpack(file, 8)
			file.seek(name_offset)
			names = [v for v in file.read().split(b'\x00') if v]
		return names


if __name__ == '__main__':
	# Verify the file exist and an arg was giving
	if not len(sys.argv) >= 2:
		_exit("Error: Please specify a target .pak file.")
	if not Path(sys.argv[1]).is_file() and not Path(sys.argv[1]).is_dir():
		_exit(f"Error: The file '{sys.argv[1]}' was not found.")

	# Run it
	os.chdir(Path(sys.argv[1]).parent)
	p = PAKClass(Path(sys.argv[1]))

_exit("Log: Program finished.")