from ctypes import *
class HeaderStruct(Structure):
	_fields_ = [
		('sig',c_char * 4),
		('fixup',c_uint32),
		('version',c_uint32),
		('pad1',c_uint32),
		('pad2', c_uint64)
	]

class WFLZStruct(Structure):
	_fields_ = [
		('flag',c_uint32),
		('size',c_uint32)
	]

class Node(Structure):
	_fields_ = [
		('type',c_uint32),
		('num_children',c_uint32),
		('child_pointer',c_uint64)
	]
class Texture(Structure):
	_fields_ = [
		('width',c_uint32),
		('height',c_uint32),
		('flags',c_uint32),
		('padding',c_uint32),
		('data_offset',c_uint64)
	]
class Vertex(Structure):
	_fields_ = [
		('num_verts',c_uint32),
		('flags',c_uint32),
		('data_offset',c_uint64)
	]
class Meta(Structure):
	_fields_ = [ # Describe
	]
class MetaScalar(Structure):
	_fields_ = [
	]
class MetaPoint(Structure):
	_fields_ = [
		('x',c_float),
		('y',c_float),
		('z',c_float),
		('padding',c_uint32)
	]
class MetaAnchor(Structure):
	_fields_ = [
		('x',c_float),
		('y',c_float),
		('z',c_float),
		('angle',c_float)
	]
class MetaRect(Structure):
	_fields_ = [
		('centerx',c_float),
		('centery',c_float),
		('centerz',c_float),
		('extentsx',c_float),
		('extentsy',c_float),
		('extentsz',c_float),
		('anglex',c_float),
		('padding',c_uint32)
	]
class MetaString(Structure):
	_fields_ = [
		('str_length',c_uint32),
		('padding',c_uint32), # Not sure
		('string_offset',c_uint64)
	]
class MetaTable(Structure):
	_fields_ = [
		('hash_names',c_uint64) # Not sure
	]
class Frame(Structure):
	_fields_ = [
		('minx',c_float),
		('maxx',c_float),
		('miny',c_float),
		('maxy',c_float)
	]
class SequenceFrame(Structure):
	_fields_ = [
		('frame',c_uint32),
		('delay',c_float)
	]
class Sequence(Structure):
	_fields_ = [
		('hash_name',c_uint32),
		('frame_count',c_uint32)
	]
class Animation(Structure):
	_fields_ = [
		('sequence_count',c_uint32),
		('frame_count',c_uint32),
		('single_texture',c_uint32),
		('palette_index',c_uint32),
		('hashname_pointer',c_uint64)
	]
