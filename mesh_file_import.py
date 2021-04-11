import bpy
import bmesh
import mathutils
import os
import math
import bpy_extras

class Node:
    def __init__(self, indented_line):
        self.children = []
        self.level = len(indented_line) - len(indented_line.lstrip())
        self.text = indented_line.strip()

    def add_children(self, nodes):
        childlevel = nodes[0].level
        while nodes:
            node = nodes.pop(0)
            if node.level == childlevel: # add node as a child
                self.children.append(node)
            elif node.level > childlevel: # add nodes as grandchildren of the last child
                nodes.insert(0,node)
                self.children[-1].add_children(nodes)
            elif node.level <= self.level: # this node is a sibling, no more children
                nodes.insert(0,node)
                return

    def as_dict(self):
        if len(self.children) > 1:
            return {self.text: [node.as_dict() for node in self.children]}
        elif len(self.children) == 1:
            return {self.text: self.children[0].as_dict()}
        else:
            return self.text

def get_total(type_name, entry):
    total = 0
    if type_name in entry:
        total = int(entry.split()[1])
        print(type_name+": ", total)
        return total

def get_float_value(entry):
    return float(entry.split()[1])

def get_string_value(entry):
    return str(entry.split()[1])

def get_int_value(entry):
    return int(entry.split()[1])

def get_3list_value(entry):
    list = entry.split()
    x = float(list[2])
    y = float(list[3])
    z = float(list[4])
    return (x, y, z)

def get_3list_value_unnamed(entry):
    list = entry.split()
    x = float(list[1])
    y = float(list[2])
    z = float(list[3])
    return (x, y, z)

def create_mesh(ob_name, coords, edges=[], faces=[]):
    """Create point cloud object based on given coordinates and name.

    Keyword arguments:
    ob_name -- new object name
    coords -- float triplets eg: [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0)]
    """

    # Create new mesh and a new object
    me = bpy.data.meshes.new(ob_name + "Mesh")
    ob = bpy.data.objects.new(ob_name, me)

    # Make a mesh from a list of vertices/edges/faces
    me.from_pydata(coords, edges, faces)

    # Display name and update the mesh
    ob.show_name = True
    me.update(calc_edges=True)
    return ob

def read_mesh_data(context, filepath):
    print("running...")
    f = open(filepath, 'r', encoding='utf-8')
    mesh = f.read()
    f.close()
    
    model_name = os.path.basename(filepath)[:-5]
    
    root = Node('root')
    
    root.add_children([Node(line) for line in mesh.splitlines() if line.strip()])
    d = root.as_dict()['root']
    
    bpy.ops.object.armature_add(radius=0) 
    skeleton = bpy.data.objects['Armature']
    skeleton.name = model_name + " skeleton"
    bpy.context.view_layer.objects.active = skeleton
    
    bpy.ops.object.editmode_toggle()
    
    edit_bones = skeleton.data.edit_bones
    
    axis_convertor = bpy_extras.io_utils.axis_conversion(from_forward='Z', from_up='-Y')
    
    #Loop data
    for key, value in d[1].items():
        verts = []
        triangles = []
        face_materials = []
        uv0 = []
        uv1= []
        
        #Loop data entries
        for index, entry in enumerate(value):
            #Get total counts, may be useful
            total_materials = get_total("NumMaterials", entry)
            total_bones = get_total("NumPoints", entry)
            total_verts = get_total("NumVertices", entry)
            total_tris = get_total("NumTriangles", entry)

            #getting data from dict type entries
            if type(entry) is dict:
                try:
                    bone = entry["Point"]
                    name = get_string_value(bone[0])
                    position = mathutils.Vector(get_3list_value(bone[1])) @ axis_convertor
                    b = edit_bones.new(name.strip('"'))
                    b.tail = (0, 10, 0)
                    direction = bone[2]["Orientation"]
                    x = get_3list_value_unnamed(direction[0]) + (position[0], )
                    y = get_3list_value_unnamed(direction[1]) + (position[1], )
                    z = get_3list_value_unnamed(direction[2]) + (position[2], )
                    last_row = (0, 0, 0, 1)
                    bone_matrix = mathutils.Matrix((x, y, z, last_row)) @ axis_convertor.to_4x4()
                    b.matrix = bone_matrix
                except KeyError:
                    pass    
                  
                try:
                    vertex = entry["Vertex"]
                    vertex_transformed = mathutils.Vector(get_3list_value(vertex[0])) @ axis_convertor
                    verts.append(vertex_transformed)   
                    uv0.append([get_float_value(vertex[4]), get_float_value(vertex[5])])
                    uv1.append([get_float_value(vertex[6]), get_float_value(vertex[7])])
                except KeyError:
                    pass
                
                try:
                    tri = entry["Triangle"]
                    triangles.append([get_int_value(tri[0]), get_int_value(tri[1]),  get_int_value(tri[2])])
                    face_materials.append(get_int_value(tri[3]))
                except KeyError:
                    pass
    
    bpy.ops.object.editmode_toggle()
    
    name = model_name
    obj = create_mesh(name, verts, faces=triangles)
    
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)  
    bpy.context.view_layer.objects.active = obj
        
    bpy.ops.object.editmode_toggle()
    mesh = bmesh.from_edit_mesh(bpy.context.edit_object.data)
    
    #Set UVs
    uv_layer = mesh.loops.layers.uv.verify()

    for f in mesh.faces:
        for l in f.loops:
            i = l.vert.index
            loop_uv = l[uv_layer]
            loop_uv.uv = (uv0[i][0], 1 - uv0[i][1])
        
    
    bmesh.ops.remove_doubles(mesh, verts=mesh.verts, dist=0.0001)
    bpy.ops.object.editmode_toggle()
    
    print("Import complete")

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportMeshData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_mesh.mesh_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import .mesh file"

    # ImportHelper mixin class uses this
    filename_ext = ".mesh"

    filter_glob: StringProperty(
        default="*.mesh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    #use_setting: BoolProperty(
    #    name="Example Boolean",
    #    description="Example Tooltip",
    #    default=True,
    #)

    #type: EnumProperty(
    #    name="Example Enum",
    #    description="Choose between two items",
    #    items=(
     #       ('OPT_A', "First Option", "Description one"),
    #        ('OPT_B', "Second Option", "Description two"),
     #   ),
    #    default='OPT_A',
    #)

    def execute(self, context):
        return read_mesh_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportMeshData.bl_idname, text="SOASE (.mesh)")


def register():
    bpy.utils.register_class(ImportMeshData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportMeshData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_mesh.mesh_data('INVOKE_DEFAULT')
