X3D to glTF-binary conversion
==================

Suite of XSLT and Python scripts to convert mesh data in an X3D file into glTF digital assets; along with an X3D file which loads
these assets in place of standard X3D nodes.

Dependencies
------------
1. An XSLT 1.0 engine. Command line examples below use the xsltproc utility, part of [Libxslt](http://xmlsoft.org/XSLT/) package.

2. Python 2.7 interpreter with standard Python library + [NumPy package](http://www.numpy.org/).

Command Line Operations
---------------------------

Command line procedure to create derived `cutting_tool.x3d` and glTF asset file `cutting_tool.glb` from
original X3D file `source/cutting_tool.x3d`



    1: xsltproc -novalid assign_mesh_names.xsl source/cutting_tool.x3d > temp1.xml
    2: xsltproc extract_gltf_data.xsl temp1.xml > temp2.xml
    3: python -m generate_glb temp2.xml cutting_tool.glb
    4: xsltproc -param glTF_binary_url "'cutting_tool.glb'" insert_glb_geometry.xsl temp1.xml > cutting_tool.x3d


step 1 prepares a temporary xml file (`temp1.xml`) in which the IndexedTriangleSet nodes are assigned unique identifying names.

steps 2-3 extract the mesh data from the nodes identified in step 1 and pack them in a binary glTF asset file written
to file path `cutting_tool.glb`

step 4 prepares an X3D file from the temporary file in step 1 in which the identified mesh nodes are replaced with
ExternalGeometry nodes referenced by a URL 'cutting_tool.glb'

intermediate files `temp1.xml` and `temp2.xml` may be deleted after step 4 is completed.


