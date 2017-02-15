
## (MIT License)
## 
## Copyright 2017 Vincent Marchetti  vmarchetti@kshell.com
## 
## Permission is hereby granted, free of charge, to any person obtaining a
## copy of this software and associated documentation files (the
## "Software"), to deal in the Software without restriction, including
## without limitation the rights to use, copy, modify, merge, publish,
## distribute, sublicense, and/or sell copies of the Software, and to
## permit persons to whom the Software is furnished to do so, subject to
## the following conditions:
## 
## The above copyright notice and this permission notice shall be included
## in all copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
## OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
## MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
## IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
## CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
## TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
## SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import logging
logging.getLogger().addHandler(logging.NullHandler())
logger = logging.getLogger("glTF")
logger.setLevel(logging.WARN)

import xml.etree.ElementTree as ET
from numpy import array, int_
import struct, json


# glTF type constants
# see spec for bufferView.target
ARRAY_BUFFER         = 34962
ELEMENT_ARRAY_BUFFER = 34963

# see glTF spec for parameter.type
UNSIGNED_SHORT = 5123
FLOAT          = 5126

TRIANGLES_MODE = 4

def generate_glb( mesh_tuples, json_output=None, binary_output=None ):
    """
    input: a sequence/generator of key-node tuples
    output: a file-like object, open for reading a 0 point, with glTF binary content
    """
    from cStringIO import StringIO
    
    accessors = dict()
    bufferViews = dict()
    
    class BufferView:
        instances = list()
        
        bufferCount = 0
        def __init__(self):
            self.data = StringIO()
            self.key  = u"bufferView_%i" % self.bufferCount
            self.current_accessor = None
            
            BufferView.bufferCount += 1
         
        def size(self):
            self.data.flush()
            return self.data.tell()
            
        @classmethod
        def new_bufferView(cls):
            me = cls()
            bufferViews[me.key] = {
                u"buffer" : u"binary_glTF",
                u"target" : me.target
            }
            BufferView.instances.append(me)
            return me
            
        def open_accessor(self):
            accessor_key = "accessor_%i" % len(accessors)
            self.accessor_count = 0
            accessors[accessor_key] = {
                u"bufferView" : self.key,
                u"byteOffset" : self.size(),
                u"type": self._type,
                u"componentType" : self.componentType,
                u"byteStride"    : self.byteStride,
            }
            self.current_accessor = accessors[accessor_key]
            return accessor_key
            
        def write_data(self, *a):
            if self.current_accessor is None:
                raise RuntimeError()
            try:
                packed_data = struct.pack(self.pack_format, *a)
            except struct.error, exc:
                raise ValueError("packing data %s gave error %s" % ( repr(a), str(exc) ))
            self.data.write( packed_data )
            self.accessor_count += 1
            
        def close_accessor(self):
            self.current_accessor[u"count"] = self.accessor_count
            self.current_accessor = None
            
            
    class IndexBufferView(BufferView):
        componentType = UNSIGNED_SHORT
        target        = ELEMENT_ARRAY_BUFFER
        _type         = "SCALAR"
        byteStride    = 2
        pack_format   = "<H"
    
    class CoordinateBufferView(BufferView):
        componentType = FLOAT
        target        = ARRAY_BUFFER
        _type         = "VEC3"
        byteStride    = 12
        pack_format   = "<fff"
        
        
    index_bufferView =      IndexBufferView.new_bufferView()
    coordinate_bufferView = CoordinateBufferView.new_bufferView()
    
    
    DEFAULT_MATERIAL = u"default_red"   # material defined below
    
    meshes = dict()
    
    for mesh_id, mesh_node in mesh_tuples:
        
        mesh_data = parse_mesh_node( mesh_node )
        
        primitive = {
            u"attributes" : {},
            u"material"   : DEFAULT_MATERIAL,
            u"mode"       : TRIANGLES_MODE
        }
        
        
        ## pack the point coordinate date
        acc = coordinate_bufferView.open_accessor()
        primitive[u"attributes"][u"POSITION"] = acc
        for p in mesh_data.point:
            coordinate_bufferView.write_data( *tuple(p))
        coordinate_bufferView.close_accessor()
        accessors[acc].update( {
            u"max"   : list( mesh_data.point.max(axis=0) ),
            u"min"   : list( mesh_data.point.min(axis=0) )
        })
        
        if mesh_data.normal is not None:
            ## pack the normal vector data
            acc = coordinate_bufferView.open_accessor()
            primitive[u"attributes"][u"NORMAL"] = acc
            for p in mesh_data.normal:
                coordinate_bufferView.write_data( *tuple(p))
            coordinate_bufferView.close_accessor()
            accessors[acc].update( {
                u"max"   : [1.0,1.0,1.0],
                u"min"   : [-1.0,-1.0,-1.0],
            })
            

        if mesh_data.index is not None:
            ## pack the point coordinate date
            acc = index_bufferView.open_accessor()
            primitive[u"indices"] = acc
            for ix in mesh_data.index:
                index_bufferView.write_data(ix)
            index_bufferView.close_accessor()
            accessors[acc].update( {
                u"max"   : [len(mesh_data.point)-1],
                u"min"   : [0],
            })
            
        # finish 
        meshes[mesh_id] = {
            "primitives" : [primitive,]
        }
        
    # update bufferView lengths and offsets
    buffer_offset = 0
    for bv in BufferView.instances:
        bv_dict = bufferViews[bv.key]
        bv_size = bv.size()
        bv_dict[u'byteOffset'] = buffer_offset
        bv_dict[u'byteLength'] = bv_size;
        buffer_offset += bv_size
    # buffer_offset is now the total length of the binary buffer
    buffer_length=buffer_offset
        
    
    # see the specification of the common materials extension to glTF
    # https://github.com/KhronosGroup/glTF/tree/master/extensions/Khronos/KHR_materials_common
    materials = {
        DEFAULT_MATERIAL : {
            u"extensions":{
                u"KHR_materials_common":{
                    u"doubleSided" : True,    # analogous to X3D solid attribute
                    u"technique" : u"CONSTANT",
                    u"transparent" : False,
                    u"values" : {
                        u"emission":[1.0,0.0,0.0,1.0]   # bright red
                    }
                }
            }
        }
    }
        
    asset = {
        u"generator" : u"KShell X3D to glTF-binary tool",
        u"profile":{
            u"api" : u"WebGL",
            u"version" : "1.0.2",
        },
        u"version" : u"1.0"
    }
    
    extensions = [
        "KHR_materials_common", 
        "KHR_binary_glTF"
    ] 

        
    content = {
        u"asset"            : asset,
        u"accessors"        : accessors,
        u"bufferViews"      : bufferViews,
        u"meshes"           : meshes,
        u"extensionsUsed"   : extensions,
        u"materials"        : materials,
    }
    
    #logger.debug("\n%s" % json.dumps(content, sort_keys=True, indent=4) )
    if json_output is not None:
        json_output.write( json.dumps(content, sort_keys=True, indent=4) )

    
    logger.debug("final buffer size: %i" % buffer_length)
    if binary_output is not None:
        for bv in BufferView.instances:
            binary_output.write( bv.data.getvalue() )
        
    content_json = json.dumps(content, encoding="utf-8")
    content_length = len( content_json)
    npad = (-content_length) % 4
    if npad > 0:
        content_json += (" " * npad)
    content_length = len( content_json) 
    logger.debug("json content %s : length %i" % (type(content_json), content_length))
           
    # for 20 byte preamble format see Kronos binary glTF extension specification
    # https://github.com/KhronosGroup/glTF/blob/master/extensions/Khronos/KHR_binary_glTF
    MAGIC="glTF"
    VERSION = 1         # latest version as of 10 Feb 2017
    length = 20 + content_length + buffer_length
    contentLength = content_length
    contentFormat = 0   # specifies JSON format
    
    message = "magic: %s ; version: %i ; length: %i ; contentLength: %i ; contentFormat: %i" % \
                (MAGIC, VERSION, length, contentLength, contentFormat)
    logger.debug("preamble: %s" % message)
    
    # format string for pack command specifies little-endian: string (byte[]) followed by 4 unsigned 32 bit integers
    preamble = struct.pack("<4s4I", MAGIC, VERSION, length, contentLength, contentFormat)
    logger.debug("preamble data length: %i" % len(preamble))
    
    # prepare a temporary file-object to return
    from tempfile import TemporaryFile
    rv = TemporaryFile()
    rv.write(preamble)
    rv.write(content_json)
    for bv in BufferView.instances:
        rv.write( bv.data.getvalue() )

    rv.seek(0)
    return rv
    
    
def parse_mesh_node( element ):
    """
    reads coordinate, index data from an ElementTree element from X3D
    returns an object with attributes:
        
    """
    class retType(object):
        def __init__(self, point ):
            self.point = point
            self.index = None
            self.normal = None
            self.texCoord = None
            
    def parse_x3d_vector( a, dimension):
        """
        a the string value of the attribute encoding MFVec2f or MFVec3f
        dimension is 2 or 3
        returns array of shape (N,dimension)
        """
        floats = list()
        for s1 in a.split(','):
            for s2 in s1.split():
                try:
                    floats.append( float( s2 ) )
                except ValueError:
                    raise Exception("unable to parse %s as float" % repr(s2))
        
        if len(floats) % dimension != 0:
            raise ValueError("vector encoding of incorrect length %i for dimension %i" % ( len(floats) , dimension))
        return array(floats).reshape( (-1,dimension))
    
    def parse_MFVec2f(a):
        return parse_x3d_vector(a,2)
        
    def parse_MFVec3f(a):
        return parse_x3d_vector(a,3)
       
    coord = element.find("Coordinate")
    if coord is not None and coord.get("point") is not None:
        a = coord.get("point")
        point_array = parse_MFVec3f(a)
        retVal = retType( point_array)
    else:
        raise ValueError("unable to evaluate Coordinate/@point")

    normal = element.find("Normal")
    if normal is not None:
        a = normal.get("vector")
        normal_array = parse_MFVec3f(a)
        retVal.normal = normal_array
        
    index_value = element.get("index")
    if index_value is not None:
        retVal.index = array( [int(s) for s in index_value.split()], int_ )
        
    return retVal
        
if __name__ == '__main__':
    # running as a script, write logging output to
    # stderr
    import sys
    handler = logging.StreamHandler(sys.stderr)
    logging.getLogger().addHandler(handler)
    handler.setFormatter(logging.Formatter("%(name)s %(levelname)6s %(message)s"))
    
    import argparse
    parser = argparse.ArgumentParser(description="generate glTF-binary file from X3D triangle set nodes")
    parser.add_argument('input_file', metavar="INPUT_FILE", help="input xml text file or '-' for STDIN")
    parser.add_argument('output_file', metavar="OUTPUT_FILE", type=argparse.FileType('wb'),help="output binary file")
    parser.add_argument('-v', '--verbose', action="store_true",  dest="verbose", help="write verbose messages to STDERR")
    parser.add_argument('--json-output', dest="json_debug_file", type = argparse.FileType('wb'), help="json content for debugging")    
    namespace = parser.parse_args()
    
    if namespace.verbose:
        logger.setLevel(logging.DEBUG)
        
    try:
        if namespace.input_file.strip() == '-':
            inp = sys.stdin
        else:
            inp = file(namespace.input_file, 'rb')
        with inp:
            doc = ET.parse( inp )
         
        def fn():
            """
            generator of (key, node) tuples
            """
            for nd in doc.getroot().findall('mesh'):
                yield nd.get('name'), nd[0]
        
        retFile = generate_glb( fn(), json_output = namespace.json_debug_file)
        namespace.output_file.write( retFile.read() )
    
    finally:
        namespace.output_file.close()
        if namespace.json_debug_file:
            namespace.json_debug_file.close()
            
