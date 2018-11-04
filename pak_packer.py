import os
import sys
import struct
from time import sleep
from glob import glob
from zlib import crc32

def log(msg):
	print(msg)
	print("Exiting in 5 seconds...")
	sleep(5)
	sys.exit(-1)

if sys.version_info < (3 , 4):
	log("Error: Please update Python to version 3.4 or higher!")

def get_extension(filename):
	extension_offset = filename.find('.')
	if extension_offset == -1:
		log("Error: {} has no extension!".format(filename))
	return filename[extension_offset:]

def create_metafile(directory, names, sub_data, pak_data, pak_name):
	#Name then checksum then at the end the pak data
	with open(directory + '\\meta.dat', 'wb') as file:
		file.write(struct.pack('<H', len(names)))
		for k, v in enumerate(names):
			file.write(struct.pack('<H', len(v)) + v)

			#Generate the checksum
			file.write(struct.pack('<I', crc32(sub_data[k])))

			#include original data
			file.write(struct.pack('<I', len(sub_data[k])))
			file.write(sub_data[k])

		#Write the original .pak data
		file.write(struct.pack('<H', len(pak_name)))
		file.write(pak_name.encode('utf-8'))
		file.write(pak_data)

def pack(f):
	os.chdir(f)
	if not os.path.isfile('meta.dat'):
		log("Error: Could not find the meta.dat file in " + f)

	_pack = struct.pack
	_unpack = struct.unpack

	#Collect file information
	file_names = {}
	pak_data = b''
	pak_name = b''
	with open('meta.dat', 'rb') as file:
		num_files = _unpack('<H', file.read(2))[0]
		for _ in range(num_files):
			name_size = _unpack('<H', file.read(2))[0]
			name = file.read(name_size).decode('utf-8')
			checksum = _unpack('<I', file.read(4))[0]

			data_size = _unpack('<I', file.read(4))[0]
			data = file.read(data_size)

			file_names[name] = {'checksum' : checksum, 'data' : data}

		pak_name_size = _unpack('<H', file.read(2))[0]
		pak_name = file.read(pak_name_size).decode('utf-8')
		pak_data = file.read()

	#Locate any edited files or missing files
	changed_files = {}
	missing_files = []
	for k, name in enumerate(file_names):
		checksum = file_names[name]['checksum']
		try:
			with open(name, 'rb') as file:
				if crc32(file.read()) != checksum: #We found an edited file lets swap the values
					file.seek(0)
					changed_files[name] = {'changed_data' : file.read(), 
					'original_data' : file_names[name]['data']}
		except:
			missing_files.append(name)

	if len(missing_files) != 0:
		print("Error: Missing required files...")
		for file in missing_files:
			print("Missing: " + file)
		log("")

	#Now swap any edited files
	print("Log: Repacking files...")
	for k, file in enumerate(changed_files):
		pak_data = pak_data.replace(changed_files[file]['original_data'], changed_files[file]['changed_data'])

	with open(pak_name, 'wb') as file:
		file.write(pak_data)

	log("Log: Finished, check inside " + f)



def unpack(f):
	if os.stat(f).st_size <= 50:
		log("Error: The PAK file is too small " + f)

	_pack = struct.pack
	_unpack = struct.unpack

	#Get header values
	with open(f, 'rb') as file:
		fseek = file.seek
		fread = file.read

		pak_data = fread() #Used for repacking
		fseek(0)

		fseek(4)
		num_files = _unpack('<I', fread(4))[0]
		data_offset = _unpack('<I', fread(4))[0]
		fseek(0x10)
		name_offset = _unpack('<I', fread(4))[0]
		fseek(name_offset)
		name_offset = _unpack('<I', fread(4))[0]
		fseek(name_offset)
		names = [v for v in fread().split(b'\x00') if v]

		#Get data offsets
		data_offsets = []
		fseek(data_offset)
		for _ in range(num_files):
			data_offsets.append(_unpack('<I', fread(4))[0] + 0x20)
			fread(4) #Skip 4 bytes

		data_sets = []
		#Get data chunks 
		for k, offset in enumerate(data_offsets):
			fseek(offset - 0x20)
			data_size = _unpack('<I', fread(4))[0]
			fseek(offset)
			data = fread(data_size)
			data_sets.append(data)

		if len(data_sets) != num_files or len(names) != num_files:
			log("Error: Some values did not match: Files: {}, Data Sets: {}, Names: {}".format(num_files, 
				len(data_sets), len(names)))

		#We have the required values now create the metafile for repacking
		os.chdir(os.path.dirname(f))
		print("Log: Extracting {} files...".format(num_files))

		pak_file = os.path.basename(f)
		pak_file = pak_file[:pak_file.find('.')]
		os.system('mkdir ' + pak_file)

		create_metafile(pak_file, names, data_sets, pak_data, os.path.basename(f))

		for k, name in enumerate(names):
			directory = os.path.dirname(name.decode()).replace('/', '\\')
			file_name = os.path.basename(name.decode())
			path = pak_file + '\\' + directory
			if not os.path.isdir(path):
				os.system('mkdir ' + path)

			with open(path + '\\' + file_name, 'wb') as file:
				file.write(data_sets[k])


args = sys.argv
if len(args) != 2:
	print("Info: ###Commands###")
	print("Info: sk_packer.py target.pak, to unpack a file")
	print("Info: sk_packer.py target_folder, to pack a folder")
	log("")

target = args[1]
if os.path.isfile(target):
	if get_extension(target) != '.pak':
		log("Error: This is not a valid .pak file!")

	unpack(target)
elif os.path.isdir(target):
	pack(target)
else:
	log("Error: File or folder was not found " + target)

log("Log: Program finished.")