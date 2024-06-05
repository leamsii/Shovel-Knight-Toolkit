import sys
sys.path.insert(0, 'include')

import struct
from node_structs import *
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

class ANBToJSON:
    def __init__(self, filename):
        self.metadata = {}
        
        with open(filename, 'rb') as file:
            header = HeaderStruct()
            file.readinto(header)
            
            assert header.sig == b'YCSN'
            
            self.metadata["file_header"] = {"sig": 'YCSN', "fixup": header.fixup, "version": header.version, "pad1": header.pad1, "pad2": header.pad2}
            self.recurr(file, self.get_node(file, None))
    
    def recurr(self, file, node):
        offsets = []
        for _ in range(node['num_children']):
            offsets.append(struct.unpack('<Q', file.read(8))[0])
        for o in offsets:
            file.seek(o)
            self.recurr(file, self.get_node(file, node))
            
    def get_node(self, file, parent):
        node = Node()
        file.readinto(node)
   
        node_name = NodeTypeName[node.type]
        node_struct = eval(node_name)()
        
        file.readinto(node_struct)
                
        body = {
        "type": node.type,
        "num_children": node.num_children,
        "child_pointer": node.child_pointer,
        "body": self.get_node_body(node_name, node_struct, file),
        "children": []
        }
        
        if parent:
            #print(node_name, node.num_children, NodeTypeName[parent['type']])
            """
            if node_name == "Sequence":
                print("Sequence", body["body"]["hash_name"], body["body"]["frame_count"])
            if node_name == "SequenceFrame":
                print("SequenceFrame", body["body"]["frame"])
            if node_name == "Texture":
                print("Texture", body["body"]["width"], body["body"]["height"])"""
                
            parent['children'].append(body)
        else:
            self.metadata["Node"] = body
            
        if node.num_children > 0:
            file.seek(node.child_pointer)
        
        return body
    
    def encode_blob(self, blob):
        return base64.b64encode(blob).decode('utf-8')
    
    def get_node_body(self, node_name, node, file):
            if node_name == 'Node': return {}
            
            body = dict((field, getattr(node, field)) for field, _ in node._fields_)
            
            if node_name == 'Vertex':
                file.seek(node.data_offset)
                
                body["hash_flag"] = struct.unpack('<I', file.read(4))[0]
                body["hash_size"] = struct.unpack('<I', file.read(4))[0]
                body["pieces"] = []
                
                for _ in range(node.num_verts):
                    posX  = struct.unpack('<f', file.read(4))[0]
                    posY  = struct.unpack('<f', file.read(4))[0]
                    texX  = struct.unpack('<H', file.read(2))[0]
                    texY  = struct.unpack('<H', file.read(2))[0]
                    width = struct.unpack('<H', file.read(2))[0]
                    height= struct.unpack('<H', file.read(2))[0]
                    body["pieces"].append({"posX":posX, "posY":posY, "texX":texX, "texY":texY, "width":width, "height":height})
                
            if node_name == 'MetaString':
                file.seek(node.string_offset)
                body['string_flag'] = struct.unpack('<I', file.read(4))[0]
                body['string_size'] = struct.unpack('<I', file.read(4))[0]
                body['string'] = file.read(body['string_size']).decode('utf-8')
                
            if node_name == 'MetaTable':
                if node.hashname_pointer != 0:
                    file.seek(node.hashname_pointer)
                    body["hash_flag"] = struct.unpack('<I', file.read(4))[0]
                    body["hash_size"] = struct.unpack('<I', file.read(4))[0]
                    body["hash"] = self.encode_blob(file.read(max(8, body["hash_size"])))
                    
            if node_name == 'Animation':
                file.seek(node.hashname_pointer)
                
                body["hash_flag"] = struct.unpack('<I', file.read(4))[0]
                body["hash_size"] = struct.unpack('<I', file.read(4))[0]
                body["hash"] = self.encode_blob(file.read(max(8, body["hash_size"])))
                
            if node_name == 'Texture':
                file.seek(node.data_offset)
                
                wflz_struct = WFLZStruct()
                file.readinto(wflz_struct)
                
                body["wflz"] = {"flag": wflz_struct.flag, "size": wflz_struct.size, "body": self.encode_blob(file.read(wflz_struct.size))}
                
            return body