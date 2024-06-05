#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
try:
	from PIL import Image
except:
	print("Error: Couldn't find the pillow library! Try running 'pip install pillow'")
	sys.exit(-1)

import os
import struct
from pathlib import Path
import glob
import json
import base64
NodeTypeName = {
	0 : 'Node',
	1 : 'Texture',
	2 : 'Vertex',
	3 : 'Meta',
	4 : 'MetaScalar',
	5 : 'MetaPoint',
	6 : 'MetaAnchor',
	7 : 'MetaRect',
	8 : 'MetaString',
	9 : 'MetaTable',
	10 :'Frame',
	11 :'SequenceFrame',
	12 :'Sequence',
	13 :'Animation'
}
NodeStructureSize = {
	'Node': 24,
	'Texture': 24,
	'Vertex': 16,
	'MetaScalar': 8,
	'MetaPoint': 16,
	'MetaAnchor': 16,
	'MetaRect': 32,
	'MetaString': 16,
	'MetaTable': 8,
	'Frame': 16,
	'SequenceFrame': 8,
	'Sequence': 8,
	'Animation': 24,
}
TraversedNodes = {}

class ANBPack:
    def __init__(self, folder):
        self.directory = Path(folder)
        metadata_dir = self.directory.joinpath('metadata.json')
        self.metadata = json.loads(metadata_dir.read_text())
        self.hash_chunk = b''
        self.hash_chunk_size = 0
        self.main_body_node_size = 0
        self.previous_wflz_size = 0
        
        os.chdir(self.directory)
        sequence_hashes = [d for d in glob.glob('*') if Path(d).is_dir()]
        frames = self.get_nodes(10, self.metadata['Node'], [])
        sequences = {}
        old_sequences = self.get_nodes(12, self.metadata['Node']['children'][0], [])
        print(f"Log: Packing {len(old_sequences)} Animation(s)..")
        new_image_sizes = {}
        
        for sequence_hash in sequence_hashes:
            sequences[sequence_hash] = {}
            sequences_path = Path(self.directory.joinpath(sequence_hash))
            os.chdir(sequences_path)
            
            for image in glob.glob("*.png"):
                (width, height) = Image.open(image).size
                new_image_sizes[image] = {"width": self.align_image(width, 8), "height": self.align_image(height, 8)}
                compressed_image_path = sequences_path.joinpath(image)
                compressed_wflz = self.compress_image(compressed_image_path)
                sequences[sequence_hash][Path(image).stem] = compressed_wflz
                
        for sequence in old_sequences:
            for sequence_frame in self.get_nodes(11, sequence, []):
                frame_index = sequence_frame['body']['frame']
                
                frame = frames[frame_index]
                texture = [n for n in frame['children'] if n['type'] == 1][0]
                vertex = [n for n in frame['children'] if n['type'] == 2][0]
                
                image_width = new_image_sizes[f"frame_{frame_index}.png"]["width"]
                image_height = new_image_sizes[f"frame_{frame_index}.png"]["height"]
                
                vertex_chunk = self.build_vertex_chunk(vertex, image_width, image_height, frame, frame_index)
                                
                new_sequence = sequences[str(sequence['body']['hash_name'])]
                wflz_data = new_sequence[f"frame_{frame_index}"]
                
                texture['body']['width'] = image_width
                texture['body']['height'] = image_height
                texture['body']['wflz']['size'] = len(wflz_data)
                texture['body']['wflz']['body'] = wflz_data + bytes((self.align(len(wflz_data), 8) - len(wflz_data))) + vertex_chunk
                
        with open(self.directory.joinpath(self.directory.name + '.anb'), 'wb') as file:
            header = self.metadata['file_header']
            
            file.write(b'YCSN')
            file.write(struct.pack('<IIIQ', header["fixup"], header["version"], header["pad1"], header["pad2"]))
            
            node = self.metadata['Node']
            file.write(struct.pack('<IIQ', node["type"], node["num_children"], node["child_pointer"]))
            
            self.get_chunk_sizes(node)
            
            self.traverse(file, node['children'][0], node)
            file.write(self.hash_chunk)
            
            for texture in self.get_nodes(1, self.metadata['Node']['children'][0], []):
                file.write(struct.pack('<I', texture['body']['wflz']['flag']))
                file.write(struct.pack('<I', texture['body']['wflz']['size']))
                file.write(texture['body']['wflz']['body'])
        
        print("Log: Finished.")
                
    def align(self, v: int, m: int):
        mask = m - 1
        return (v + mask) & ~mask    
            
    def get_nodes(self, node_type, node, nodes):
        if node['type'] == node_type:
            nodes.append(node)
        for _node in node['children']:
            self.get_nodes(node_type, _node, nodes)
        return nodes
    
    def build_vertex_chunk(self, vertex, image_width, image_height, frame, frame_index):
        vertex_chunk = b''
                    
        vertex_chunk += struct.pack('<I', vertex["body"]["hash_flag"])
        vertex_chunk += struct.pack('<I', 16)
        vertex_chunk += struct.pack('<f', -(image_width / 2))
        vertex_chunk += struct.pack('<f', -image_height)
        vertex_chunk += struct.pack('<H', 0)
        vertex_chunk += struct.pack('<H', 0)
        vertex_chunk += struct.pack('<H', image_width)
        vertex_chunk += struct.pack('<H', image_height)
   
        return vertex_chunk
        
    
    def traverse(self, file, node, parent):
        self.unpack_node(node, file, parent)
    
        TraversedNodes[NodeTypeName[parent['type']]] = TraversedNodes.get(NodeTypeName[parent["type"]], 0) + 1
        if TraversedNodes[NodeTypeName[parent["type"]]] >= parent["num_children"]:
            TraversedNodes[NodeTypeName[parent["type"]]] = 0
            for child in parent['children']:
                file.write(struct.pack('<Q', child['offset']))

        for _node in node['children']:
            self.traverse(file, _node, node)
            
    def get_chunk_sizes(self, node):
        self.main_body_node_size += NodeStructureSize[NodeTypeName[node['type']]]
        self.main_body_node_size += 16
        self.main_body_node_size += 8 * node['num_children']
  
        if 'hash_size' in node['body'] and NodeTypeName[node['type']] != 'Vertex' :
            self.hash_chunk_size += 4 # Flag
            self.hash_chunk_size += 4 # Size
            self.hash_chunk_size += node['body']['hash_size'] + (self.align(node['body']['hash_size'], 8) - node['body']['hash_size'])
            
        if 'string_size' in node['body']:
            self.hash_chunk_size += 4 # Flag
            self.hash_chunk_size += 4 # Size
            self.hash_chunk_size += node['body']['string_size']
            self.hash_chunk_size += self.align(node["body"]["string_size"], 8) - node["body"]["string_size"]
            
        for _node in node['children']:
            self.get_chunk_sizes(_node)
            
    def compress_image(self, image_name):
        _image = Image.open(image_name) 
        padded_image = self.get_padded_image(_image.width, _image.height, _image)
        
        width, height = padded_image.size
        pixels = list(padded_image.getdata())
        
        pixels = [pixels[i * width:(i + 1) * width] for i in range(height)]
        compression_size = width * height * 4
        
        image_data_file_name = image_name.with_suffix('.dat')
        with open(image_data_file_name, 'wb') as file:
            for row in pixels:
                for r,g,b,a in row:
                    file.write(struct.pack('<BBBB', r, g, b, a))
                    
        
        image_data_file_name = f'"{str(image_data_file_name)}"'
    
        script_dir = os.path.dirname(__file__)
        full_path = os.path.join(script_dir, "wflz_extractor", "extractor.exe")
        
        os.system(full_path + ' ' + image_data_file_name + ' ' + str(compression_size))
        with open(Path(image_name).with_suffix('.wflz'), 'rb') as file:
            file.seek(4)
            compression_size = struct.unpack('<I', file.read(4))[0]
        os.system(full_path + ' ' + image_data_file_name + ' ' + str(compression_size + 16))
        wflz_data = Path(image_name).with_suffix('.wflz').read_bytes()
        
        os.remove(Path(image_name).with_suffix('.wflz'))
        os.remove(Path(image_name).with_suffix('.dat'))
        
        return wflz_data
    
    def get_padded_image(self, width, height, image):
        new_width = self.align_image(width, 8)
        new_height = self.align_image(height, 8)
        
        padding_top = new_height - height
        
        new_image = Image.new("RGBA", (new_width, new_height))
        new_image.paste(image, (0, padding_top))
        return new_image
    
    def align_image(self, v: int, m: int):
        mask = m - 1
        aligned_value = (v + mask) & ~mask
        if aligned_value < v:
            aligned_value += m
        return aligned_value
    
    def unpack_node(self, node, file, parent):
        _type = NodeTypeName[node['type']]
        
        node['offset'] = file.tell()
        node_chunk_body = struct.pack('<IIQ', node["type"], node["num_children"], node["child_pointer"])
        
        if _type == 'Texture':
            node_chunk_body += struct.pack('<I', node["body"]["width"])
            node_chunk_body += struct.pack('<I', node["body"]["height"])
            node_chunk_body += struct.pack('<I', node["body"]["flags"])
            node_chunk_body += struct.pack('<I', node["body"]["padding"])
            
            data_offset = self.main_body_node_size + self.hash_chunk_size + self.previous_wflz_size
            node_chunk_body += struct.pack('<Q', data_offset)

        if _type == 'Vertex':
            node_chunk_body += struct.pack('<I', 1)
            node_chunk_body += struct.pack('<I', node["body"]["flags"])
            
            parent_texture = [n for n in parent['children'] if n['type'] == 1][0]
            self.previous_wflz_size += len(parent_texture['body']['wflz']['body']) + 8
            hash_offset = (self.main_body_node_size + self.hash_chunk_size + (self.previous_wflz_size - 24))
            node_chunk_body += struct.pack('<Q', hash_offset)
            
    
        if _type == 'MetaPoint':
            node_chunk_body += struct.pack('<f', node["body"]["x"])
            node_chunk_body += struct.pack('<f', node["body"]["y"])
            node_chunk_body += struct.pack('<f', node["body"]["z"])
            node_chunk_body += struct.pack('<I', node["body"]["padding"])

        if _type == 'MetaAnchor':
            node_chunk_body += struct.pack('<f', node["body"]["x"])
            node_chunk_body += struct.pack('<f', node["body"]["y"])
            node_chunk_body += struct.pack('<f', node["body"]["z"])
            node_chunk_body += struct.pack('<f', node["body"]["angle"])
        
        if _type == 'MetaRect':
            node_chunk_body += struct.pack('<f', node["body"]["centerx"])
            node_chunk_body += struct.pack('<f', node["body"]["centery"])
            node_chunk_body += struct.pack('<f', node["body"]["centerz"])
            node_chunk_body += struct.pack('<f', node["body"]["extentsx"])
            node_chunk_body += struct.pack('<f', node["body"]["extentsy"])
            node_chunk_body += struct.pack('<f', node["body"]["extentsz"])
            node_chunk_body += struct.pack('<f', node["body"]["anglex"])
            node_chunk_body += struct.pack('<I', node["body"]["padding"])
        
        if _type == 'MetaString':
            
            node_chunk_body += struct.pack('<I', node["body"]["str_length"])
            node_chunk_body += struct.pack('<I', node["body"]["padding"])
            
            hash_offset = self.main_body_node_size + len(self.hash_chunk)

            node_chunk_body += struct.pack('<Q', hash_offset)
            self.hash_chunk += struct.pack('<I', node["body"]["string_flag"])
            self.hash_chunk += struct.pack('<I', node["body"]["string_size"])
            
            hash = node["body"]["string"].encode('utf-8')
            self.hash_chunk += hash + bytes(self.align(node["body"]["string_size"], 8) - node["body"]["string_size"])

        if _type == 'MetaTable':
            hashname_pointer = node['body']['hashname_pointer']
            hash_offset = self.main_body_node_size + len(self.hash_chunk)
            if hashname_pointer != 0:
                node_chunk_body += struct.pack('<Q', hash_offset)
                self.hash_chunk += struct.pack('<I', node["body"]["hash_flag"])
                self.hash_chunk += struct.pack('<I', node["body"]["hash_size"])
             
                hash = base64.b64decode(node["body"]["hash"])
                self.hash_chunk += hash + bytes(self.align(len(hash), 8) - len(hash))
            else:
                node_chunk_body += bytes(8)
                

        if _type == 'SequenceFrame':
            node_chunk_body += struct.pack('<I', node["body"]["frame"])
            node_chunk_body += struct.pack('<f', node["body"]["delay"])
        
        if _type == 'Sequence':
            node_chunk_body += struct.pack('<I', node["body"]["hash_name"])
            node_chunk_body += struct.pack('<I', node["body"]["frame_count"])

        if _type == 'Animation':
            node_chunk_body += struct.pack('<I', node["body"]["sequence_count"])
            node_chunk_body += struct.pack('<I', node["body"]["frame_count"])
            node_chunk_body += struct.pack('<I', node["body"]["single_texture"])
            node_chunk_body += struct.pack('<I', node["body"]["palette_index"])
            
            node_chunk_body += struct.pack('<Q', self.main_body_node_size)
            self.hash_chunk += struct.pack('<I', node["body"]["hash_flag"])
            self.hash_chunk += struct.pack('<I', node["body"]["hash_size"])
            
            hash = base64.b64decode(node["body"]["hash"])
            self.hash_chunk += hash + bytes(self.align(len(hash), 8) - len(hash))
   
        if _type == 'Frame':
            node_chunk_body += struct.pack('<f', node["body"]["minx"])
            node_chunk_body += struct.pack('<f', node["body"]["maxx"])
            node_chunk_body += struct.pack('<f', node["body"]["miny"])
            node_chunk_body += struct.pack('<f', node["body"]["maxy"])

        if _type == 'MetaScalar':
            node_chunk_body += struct.pack('<Q', node["body"]["unk"])
            
        file.write(node_chunk_body)