import os
import sys
import struct
import zlib
from time import sleep
from glob import glob

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

def create_metafile(directory, data_sets, pak_data):
	#checksum, raw data
	with open(directory + '\\meta.dat', 'wb') as file:
		file.write(struct.pack('<H', len(data_sets))) #How many checksums to read
		for data in data_sets:
			file.write(struct.pack('<I', zlib.crc32(data))) #Create a checksum for the current data set

		#Now the original data
		file.write(zlib.compress(pak_data))

def get_filenames(file):
	with open(file, 'rb') as file:
		file.seek(0x10)
		name_offset = struct.unpack('<I', file.read(4))[0]
		file.seek(name_offset)
		name_offset = struct.unpack('<I', file.read(4))[0]
		file.seek(name_offset)
		names = [v for v in file.read().split(b'\x00') if v]
	return names


def get_datasets(file):
	data_sets = []
	with open(file, 'rb') as file:
		file.seek(4)
		num_files = struct.unpack('<I', file.read(4))[0]
		data_offset = struct.unpack('<I', file.read(4))[0]

		#Get data offsets
		data_offsets = []
		file.seek(data_offset)

		for _ in range(num_files):
			data_offsets.append(struct.unpack('<I', file.read(4))[0] + 0x20)
			file.read(4) #Skip 4 bytes

		#Get data chunks 
		for k, offset in enumerate(data_offsets):
			file.seek(offset - 0x20)
			data_size = struct.unpack('<I', file.read(4))[0]
			file.seek(offset)
			data = file.read(data_size)
			data_sets.append(data)

	return data_sets

def pack(f):
	os.chdir(f)
	if not os.path.isfile('meta.dat'):
		log("Error: Could not find the meta.dat file in " + f)

	with open('meta.dat', 'rb') as file:
		num_checksums = struct.unpack('<H', file.read(2))[0]
		checksums = []
		pak_data = b''
		for _ in range(num_checksums):
			checksums.append(struct.unpack('<I', file.read(4))[0])
		pak_data = zlib.decompress(file.read())

	#We have the checksums and the data collected
	with open('tmp.bin', 'wb') as file:
		file.write(pak_data)

	file_names = get_filenames('tmp.bin')
	data_sets = get_datasets('tmp.bin')
	os.system('del tmp.bin')

	missing_files = False
	edited_files = {}
	for k, v in enumerate(file_names):
		v = v.decode('utf-8')
		try:
			with open(v, 'rb') as file:
				if missing_files:
					return
				new_checksum = zlib.crc32(file.read())
				old_checksum = checksums[k]
				if new_checksum != old_checksum:
					file.seek(0)
					new_data = file.read()
					old_data = data_sets[k]
					data_sets[k] = new_data

					edited_files[v] = {'new_data' : new_data, 'old_data' : old_data}
		except:
			missing_files = True
			print("Error: Missing file " + v)
			#Continue running to see if any more missing files
			
	if missing_files:
		log("")

	if len(edited_files) > 0:
		print("Log: Detected {} edited files...".format(len(edited_files)))

		for ff in edited_files:
			old_data = edited_files[ff]['old_data']
			new_data = edited_files[ff]['new_data']
			pak_data = pak_data.replace(old_data, new_data)

		#Now overwright the metafile
		create_metafile(os.getcwd(), data_sets, pak_data)
	else:

		print("Log: No change in the files was found...")

	with open(os.path.basename(f) + '.pak', 'wb') as file:
		file.write(pak_data)

	log("Log: Finished, check inside " + os.path.basename(f))


def unpack(f):
	if os.stat(f).st_size <= 50:
		log("Error: The PAK file is too small " + f)

	file_names = get_filenames(f)
	data_sets = get_datasets(f)

	print("Log: Extracting {} files...".format(len(file_names)))

	os.chdir(os.path.dirname(f))
	
	#Create the directory
	pak_filename = os.path.basename(f)
	pak_filename = pak_filename[:pak_filename.find('.')]
	if not os.path.isdir(pak_filename):
		os.system('mkdir ' + pak_filename)

	#The meta file will just be the compressed .pak original file for refrencing
	with open(f, 'rb') as file:
		pak_data = file.read()

	create_metafile(pak_filename, data_sets, pak_data)

	#Create the directories and files needed
	for k, name in enumerate(file_names):
		directory = os.path.dirname(name.decode()).replace('/', '\\')
		file_name = os.path.basename(name.decode())
		path = pak_filename + '\\' + directory
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