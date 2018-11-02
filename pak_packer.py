import struct
import os
import sys
import time
import glob

if sys.version_info < (3,4):
	print("Error: Please update Python to version 3.4 or higher!")
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

def sort_files(files):
	#Remove directories
	subfiles = [f for f in files if not os.path.isdir(f)]
	sorted_files = []

	#Sort by order id
	for f in subfiles:
		with open(f, 'rb') as file:
			metadata = file.read()
			metadata_offset = metadata.find(b'LIAM')
			if metadata_offset == -1:
				print("Warning: The META header in {} was not found, skipping...".format(f))
			else:
				metadata = metadata[metadata_offset + 4 : ]
				order_id = struct.unpack('<I', metadata[0x20 : ])[0]
				sorted_files.append((order_id, f))

	sorted_files.sort()
	subfiles = []
	for k,v in enumerate(sorted_files):
		subfiles.append(v[1])
	return subfiles


def create_name_chunk(names):
	data = b''
	for name in names:
		name = name.replace('\\', '/')
		data += name.encode() + bytes(2)
	return data

def get_names(file, offset):
	file.seek(offset)
	names = [v for v in file.read().split(b'\x00') if v]
	return names

def log(msg):
	print(msg)
	print("Exiting in 5 seconds...")
	time.sleep(5)
	sys.exit(-1)

def pack(folder):
	os.chdir(folder)
	files = glob.glob('**', recursive=True)
	if len(files) <= 0:
		log("Error: No files were found in " + folder)

	print("Log: Repacking files...")

	subfiles = sort_files(files)
	file_datas = []
	file_size = 0

	#Seperate the files and get raw data
	print("Log: Collecting raw data...")
	for f in subfiles:
		with open(f, 'rb') as file:
			v = file.read()
			file_datas.append(v)
			file_size += len(v) - 8 # -8 is for the metadata header and order id

	print("Log: Writing header...")
	#Files collected now begin writing header
	data = bytes(4) #First empty 4 bytes
	data += struct.pack('<I', len(subfiles)) #number of files
	data += struct.pack('<I', 0x18) #data offset
	data += bytes(4) #padding
	name_offset = struct.pack('<I', 0x18 + (8 * len(subfiles))  + file_size)
	data += bytes(name_offset)
	data += bytes(4) #padding

	print("Log: Writing offsets...")
	#Begin adding the data offsets
	max_length = 0x20 + (8 * (len(subfiles) - 1))
	last_length = 0
	for k,v in enumerate(file_datas):
		offset = max_length + last_length
		data += struct.pack('<I', offset) + bytes(4)
		last_length += (len(v) - 8)


	print("Log: Writing raw data...")
	#Add raw data
	for k,v in enumerate(file_datas):
		metadata_offset = v.find(b'LIAM')
		if metadata_offset != -1:
			metadata = v[metadata_offset + 4 : (metadata_offset + 4) + 0x20] #Thus removing the order id
			v = v[ : metadata_offset]
			data += metadata + v
		else:
			data += v

	print("Log: Writing name offsets...")
	#Writes names
	max_length = 8 * len(subfiles)
	start_offset = len(data) + max_length
	last_length = 0
	for k,v in enumerate(subfiles):
		v = v.replace('\\', '/')
		start_offset += last_length
		data += struct.pack('<I', start_offset) + bytes(4)
		last_length = len(v) + 2 # +2 for the padding

	names = create_name_chunk(subfiles)
	data += names

	with open(os.path.basename(folder) + '.pak', 'wb') as file:
		file.write(data)

	print("Log: Finished, check inside " + folder)


def unpack(f):
	#Get header values
	with open(f, 'rb') as file:
		if len(file.read()) <= 50:
			log("Error: The PAK file is too small " + f)

		file.seek(4)
		num_files = struct.unpack('<I', file.read(4))[0]
		data_offset = struct.unpack('<I', file.read(4))[0]
		file.seek(0x10)
		name_offset = struct.unpack('<I', file.read(4))[0]
		file.seek(name_offset)
		name_offset = struct.unpack('<I', file.read(4))[0]
		names = get_names(file, name_offset)

		#Get data offsets
		data_offsets = []
		data_sets = []
		file.seek(data_offset)
		for i in range(num_files):
			data_offsets.append(struct.unpack('<I', file.read(4))[0] + 0x20)
			file.read(4) #Skip 4

		#Get data chunk and metadata for repacking.
		for k, offset in enumerate(data_offsets):
			file.seek(offset - 0x20)
			metadata = b'LIAM' + file.read(0x20) + struct.pack('<I', k)
			file.seek(offset - 0x20)
			data_size = struct.unpack('<I', file.read(4))[0]
			file.seek(offset)
			data = file.read(data_size)
			data_sets.append(data + metadata)

		if len(data_sets) != num_files or len(names) != num_files:
			log("Error: Some values did not match: Files: {}, Data Sets: {}, Names: {}".format(num_files, len(data_sets), len(names)))

		pak_file = os.path.basename(f)
		pak_file = pak_file[:pak_file.find('.')]
		os.chdir(os.path.dirname(f))
		os.system('mkdir ' + pak_file)

		for k, name in enumerate(names):
			directory = os.path.dirname(name.decode()).replace('/', '\\')
			file_name = os.path.basename(name.decode())
			path = pak_file + '\\' + directory

			print("Log: Extracting {} to {}".format(file_name, path))
			if os.path.isdir(path) == False:
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
	unpack(target)
elif os.path.isdir(target):
	pack(target)
else:
	log("Error: File or folder was not found " + target)

print("Log: Program finished.")
log("")