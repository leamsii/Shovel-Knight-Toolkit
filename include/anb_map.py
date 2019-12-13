import sys
import struct
from time import sleep
from pathlib import Path
from node_structs import *

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

def _exit(msg):
	print(msg)
	print("Exiting in 5 seconds..")
	sleep(5)
	sys.exit(-1)

class ANBStruct:
	def __init__(self, _file):
		self.nodes = []
		with open(_file, 'rb') as file:
			file.seek(0x10) # Unk header
			# Header
			h = HeaderStruct()
			file.readinto(h)

			assert h.sig == b'YCSN'
			self.recurr(file, self.get_node(file))

	def recurr(self, file, node):
		offsets = []
		for n in range(node.num_children):
			offsets.append(struct.unpack('<Q', file.read(8))[0])

		for o in offsets:
			file.seek(o + 0x10)
			self.recurr(file, self.get_node(file))

	def get_node(self, file):
		node = Node()
		file.readinto(node)

		try:
			_type = NodeTypeName[node.type]
			n = eval(_type)()
			file.readinto(n)
		
			self.nodes.append({'type' : node.type, 'node' : n})
		except Exception as e:
			_exit(f"Error: Unkown node type {_type} {e}")

		if node.num_children > 0:
			file.seek(node.child_pointer + 0x10)

		return node

