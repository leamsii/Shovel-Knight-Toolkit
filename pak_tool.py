#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import struct
from pathlib import Path
import os
import json

FILENAME_OFFSET_SIZE = 8
FILE_NAME_HASHES = {}
ANB_HEADER_SIZE = 32
PAK_HEADER_SIZE = 24

class PAKTool:
    def __init__(self, filename):
        if Path(filename).is_file():
            self.unpack(filename)
        else:
            self.pack(filename)
    
    def unpack(self, filename):
        parent_dir = Path(filename.stem)
        parent_dir.mkdir(exist_ok=True)
        
        with open(filename, 'rb') as file:
            magic, file_count, file_header_table_offs, file_name_table_offs = struct.unpack('<IIQQ', file.read(struct.calcsize('<IIQQ')))
            assert magic == 0
        
            file_names = self.get_file_names(file, file_name_table_offs, file_count)
            file_data_offsets = self.get_data_offsets(file, file_header_table_offs, file_count)
            
            for name, data_offset in zip(file_names, file_data_offsets):
                print(f"Log: Unpacking {name.decode()}")
                
                new_directory = Path(name.decode()).parent
                new_directory = parent_dir.joinpath(new_directory)
                new_directory.mkdir(parents=True, exist_ok=True)
                
                with open(new_directory.joinpath(Path(name.decode()).name), 'wb') as ff:
                    ff.write(self.get_file_data(file, data_offset, name))
                    
        with open(parent_dir.joinpath('metadata.json'), 'w') as file:
            json.dump(FILE_NAME_HASHES, file)
            
    def pack(self, foldername):
        os.chdir(foldername)
        
        assert Path('metadata.json').exists
        global FILE_NAME_HASHES
        FILE_NAME_HASHES = json.loads(Path('metadata.json').read_text())
        
        file_count = len(FILE_NAME_HASHES)
        file_names = [name for name in FILE_NAME_HASHES]
        
        file_names_chunk = self.build_file_names_chunk(file_names)
        data_chunks = self.build_data_chunks(file_names)
        data_chunks_size = sum(len(chunk) for chunk in data_chunks)
        file_name_table_offs_size = FILENAME_OFFSET_SIZE * file_count
        file_header_table_offs_size = FILENAME_OFFSET_SIZE * file_count
        
        with open(foldername.name + '.pak', 'wb') as file:
            file_name_table_offs = PAK_HEADER_SIZE + file_header_table_offs_size + data_chunks_size
            file.write(struct.pack('<IIQQ', 0, file_count, PAK_HEADER_SIZE, file_name_table_offs))
            
            file_header_table_offsets = self.build_file_header_table_offsets(file_name_table_offs_size, data_chunks)
            file.write(file_header_table_offsets)
            
            for chunk in data_chunks:
                file.write(chunk)
                
            file_name_table_offsets = self.build_file_name_table_offsets(file, file_name_table_offs_size, file_names)
            file.write(file_name_table_offsets)
            
            file.write(file_names_chunk)
                
    
    def build_file_name_table_offsets(self, file, file_name_table_offs_size, file_names):
        previous_file_name_size = 0
        current_file_position = file.tell()
        file_name_table_offsets = b''
        for name in file_names:
            offset = current_file_position + file_name_table_offs_size + previous_file_name_size
            previous_file_name_size += len(name) + 1
            file_name_table_offsets += struct.pack('<Q', offset)
        return file_name_table_offsets
              
    
    def build_file_header_table_offsets(self, file_name_table_offs_size, data_chunks):
        previous_data_chunks_size = 0
        file_name_table_offsets = b''
        for data_chunk in data_chunks:
            offset = PAK_HEADER_SIZE + file_name_table_offs_size + previous_data_chunks_size
            previous_data_chunks_size += len(data_chunk)
            file_name_table_offsets += struct.pack('<Q', offset)
        return file_name_table_offsets
          
            
    def build_data_chunks(self, file_names):
        data_chunks = []
        for name in file_names:
            with open(name, 'rb') as file:
                print(f"Log: Packing {name}")
                file_data = file.read()
                anb_header = self.build_anb_header(name, len(file_data))
                assert len(anb_header) == ANB_HEADER_SIZE
                data_chunks.append(anb_header + file_data)
        return data_chunks
        
        
    def build_anb_header(self, filename, file_data_size):
        return struct.pack('<QQIIII', file_data_size, 0, FILE_NAME_HASHES[filename], 1, 1, 0)
    
    def build_file_names_chunk(self, file_names):
        encoded_names = [name.encode('utf-8') + bytes(1) for name in file_names]
        name_chunk = b''.join(encoded_names)
        return name_chunk 
            
    def get_file_names(self, file, file_name_table_offs, file_count):
        file.seek(file_name_table_offs + (FILENAME_OFFSET_SIZE * file_count))
        file_name_chunk = file.read()
        return [name for name in file_name_chunk.split(b'\x00') if name]
    
    def get_data_offsets(self, file, file_header_table_offs, file_count):
        file.seek(file_header_table_offs)
        return [struct.unpack('<Q', file.read(8))[0] for _ in range(file_count)]
    
    def get_file_data(self, file, data_offset, name):
        file.seek(data_offset)
        size, time, filename_hash, flags, specials, pad = struct.unpack('<QQIIII', file.read(struct.calcsize('<QQIIII')))
        FILE_NAME_HASHES[name.decode()] = filename_hash
        return file.read(size)
    
    
if __name__ == '__main__':
	if len(sys.argv) != 2: print("Error: Please specify a target .pak file or directory to pack.")

	os.chdir(Path(sys.argv[1]).parent)
	PAKTool(Path(sys.argv[1]))