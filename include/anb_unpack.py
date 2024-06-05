
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from anbjson import ANBToJSON
import sys

try:
	from PIL import Image
except:
	print("Error: Couldn't find the pillow library! Try running 'pip install pillow'")
	sys.exit(-1)

import os
from pathlib import Path
import base64
import json

class ANBUnpack:
    def __init__(self, filename):
        self.metadata = ANBToJSON(filename).metadata
        
        self.directory = Path(str(Path(filename).parent) + '\\' + Path(filename).stem)
        self.directory.mkdir(exist_ok=True)
        
        with open(self.directory.joinpath('metadata.json'), 'w') as file:
            json.dump(self.metadata, file)
        
        frames = self.get_nodes(10, self.metadata['Node'], [])
        sequences = self.get_nodes(12, self.metadata['Node']['children'][0], [])
        
        print(f"Log: Unpacking {len(sequences)} Animation(s)..")
        
        for sequence in sequences:
            directory_name = str(sequence['body']['hash_name'])
            directory_path = self.directory.joinpath(directory_name)
            directory_path.mkdir(exist_ok=True)
            
            sequence_frames = self.get_nodes(11, sequence, [])
            for sequence_frame in sequence_frames:
                frame_index = sequence_frame['body']['frame']
                frame = frames[frame_index]
                texture = [n for n in frame['children'] if n['type'] == 1][0]
                vertex = [n for n in frame['children'] if n['type'] == 2][0]
  
                texture_width = texture['body']['width']
                texture_height = texture['body']['height']
                
                #print(frame_index, vertex['body']['pieces'], texture_width,texture_height)
                
                wflz_data = base64.b64decode(texture['body']['wflz']['body'])
                wflz_file_name = directory_path.joinpath(f'frame_{str(frame_index)}.wflz')
                open(wflz_file_name, 'wb').write(wflz_data)
                
                self.extract_wflz(wflz_file_name)
                self.create_image(wflz_file_name.with_suffix('.dat'), texture_width, texture_height, vertex['body']['pieces'], frame_index)
                os.remove(wflz_file_name)
                
        print("Log: Finished.")
            
    
    def get_nodes(self, node_type, node, nodes):
        if node['type'] == node_type:
            nodes.append(node)
        for _node in node['children']:
            self.get_nodes(node_type, _node, nodes)
        return nodes
    
    def create_image(self, name, width, height, vertices, frame_index):
        _buffer = Path(name).read_bytes()
        image_out = Image.frombytes('RGBA', (width, height), _buffer, 'raw')
        image_out.save(Path(name).with_suffix('.png'))
        
        min_posX = min(piece["posX"] for piece in vertices)
        min_posY = min(piece["posY"] for piece in vertices)
        
        # Adjust coordinates to ensure all are non-negative
        adjusted_vertices = [
            {
                "posX": vertex["posX"] - min_posX,
                "posY": vertex["posY"] - min_posY,
                "texX": vertex["texX"],
                "texY": vertex["texY"],
                "width": vertex["width"],
                "height": vertex["height"]
            }
            for vertex in vertices
        ]
        
        adjusted_max_width = max(int(piece["posX"]) + piece["width"] for piece in adjusted_vertices)
        adjusted_max_height = max(int(piece["posY"]) + piece["height"] for piece in adjusted_vertices)
        
        # Create a new blank image with RGBA mode to handle transparency
        final_image = Image.new("RGBA", (adjusted_max_width, adjusted_max_height))
        
        #print(frame_index, (width, height), (adjusted_max_width, adjusted_max_height))
        
        for vertex in adjusted_vertices:
            region = (vertex["texX"],
                    vertex["texY"],
                    vertex["texX"] + vertex["width"],
                    vertex["texY"] + vertex["height"])
            
            piece = image_out.crop(region)
            
            paste_x = int(vertex["posX"])
            paste_y = int(vertex["posY"])
            
            final_image.paste(piece, (paste_x, paste_y), piece)
        
        final_image.save(Path(name).with_suffix('.png'))
        
        os.remove(name)

        
    def extract_wflz(self, filename):
        filename = f'"{str(filename)}"'
        os.system("include\\wflz_extractor\\extractor.exe " + filename)