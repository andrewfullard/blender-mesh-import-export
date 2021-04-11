import bpy
import bmesh
import copy
import math

test_points = [
                ["Test", [0.12334, 343.32432, 123.576567], 
                    [3654.12334, 123.33452, 123.576567],
                    [0.12334, 12.123, 123.45],
                    [0.12334, 23.123, 56.45]
                ]
            ]

test_vertices = [
                    [
                        [0.12334, 343.32432, 123.576567], 
                        [3654.12334, 123.33452, 123.576567],
                        [0.12334, 12.123, 123.45],
                        0, 0.2344345, 0.34554654, 0.123343, 0.123343
                    ]
                ]

test_tris = [
                [0, 1, 2, 0]
            ]


def create_export_list(collection):
    export_list = []

    if(collection.hide_viewport):
        return export_list

    for object in collection.objects:
        if(object.type == 'MESH' and object.hide_viewport == False):
            export_list.append(object)
            
    for child in collection.children:
                export_list.extend(create_export_list(child))

    return export_list


def write_indented(string, level):
    return level * "\t" + string + "\n"   

def write_labeled_int(label, value):
    return label + " " + str(int(value))

def write_labeled_string(label, value):
    conv = lambda i : i or ''
    return label + " " + '"' + conv(value) + '"'

def write_labeled_hex(label, value):
    return label + " " + str(value)

def write_labeled_float(label, value):
    return label + " " + "{:.6f}".format(value)

def write_3list(list):
    return ("[ " + "{:.6f}".format(list[0]) + " " 
            + "{:.6f}".format(list[1]) + " " 
            + "{:.6f}".format(list[2]) + " ]")

def write_labeled_3list(label, list):
    return label + " " + write_3list(list)

def write_materials(diffuse_textures=[None], 
                            self_illum_textures=[None], 
                            normal_textures=[None], 
                            disp_textures=[None], 
                            tc_textures=[None], 
                            diffuses=["ffffffff"], 
                            ambients=["ffffffff"], 
                            speculars=["ffffffff"], 
                            emissives=["ffffffff"], 
                            glosses=[50.0]):
    """
    Writes Materials to string
    
    Materials should have textures and values in lists where list index = material index
    """
                                
    number_materials = len(diffuse_textures)                        
    output = write_indented(write_labeled_int("NumMaterials", number_materials), 1)
    
    for i in range(number_materials):
        print("Outputting material ", i+1)
        diffuse_tex = write_labeled_string("DiffuseTextureFileName", diffuse_textures[i])
        self_illum_tex = write_labeled_string("SelfIlluminationTextureFileName", self_illum_textures[i])
        normal_tex = write_labeled_string("NormalTextureFileName", normal_textures[i])
        disp_tex = write_labeled_string("DisplacementTextureFileName", disp_textures[i])
        tc_tex = write_labeled_string("TeamColorTextureFileName", tc_textures[i])
        diffuse = write_labeled_hex("Diffuse", diffuses[i])
        ambient = write_labeled_hex("Ambient", ambients[i])
        specular = write_labeled_hex("Specular", speculars[i])
        emissive = write_labeled_hex("Emissive", emissives[i])
        gloss =write_labeled_hex("Glossiness", glosses[i])
        
        output += write_indented("Material", 1)
        output += write_indented(diffuse_tex, 2)
        output += write_indented(self_illum_tex, 2)
        output += write_indented(normal_tex, 2)
        output += write_indented(disp_tex, 2)
        output += write_indented(tc_tex, 2)
        output += write_indented(diffuse, 2)
        output += write_indented(ambient, 2)        
        output += write_indented(specular, 2)
        output += write_indented(emissive, 2)
        output += write_indented(gloss, 2)
        
    return output

def write_points(points):
    """
    Writes Points to string
    
    Points should be in format
    
    [[Name, Position [x, y, z], Orientation [x, y, z], [x, y, z], [x, y, z]]]
    """
    number_points = len(points)                        
    output = write_indented(write_labeled_int("NumPoints", number_points), 1)
    
    print("Outputting ", number_points, " points")
    
    if number_points == 0:
        return output
    
    for point in points:
        datastring = write_labeled_string("DataString", point[0])
        position = write_labeled_3list("Position", point[1])
        orientation1 = " " + write_3list(point[2])
        orientation2 = " " + write_3list(point[3])
        orientation3 = " " + write_3list(point[4])
        
        output += write_indented("Point", 1)
        output += write_indented(datastring, 2)
        output += write_indented(position, 2)
        output += write_indented("Orientation", 2)
        output += write_indented(orientation1, 3)
        output += write_indented(orientation2, 3)
        output += write_indented(orientation3, 3)
    
    return output

def write_vertices(vertices):
    """
    Writes verts to string
    
    Vertices should be in format
    
    [[Position [x, y, z], Normal [x, y, z], Tangent [x, y, z], Color, U0, V0, U1, V1]]
    """
    
    number_verts = len(vertices)                        
    output = write_indented(write_labeled_int("NumVertices", number_verts), 1)
    
    print("Outputting ", number_verts, " vertices")
    
    for vert in vertices:
        position = write_labeled_3list("Position", vert[0])
        normal = write_labeled_3list("Normal", vert[1])
        tangent = write_labeled_3list("Tangent", vert[2])
        color = write_labeled_int("Color", vert[3])
        u0 = write_labeled_float("U0", vert[4])
        v0 = write_labeled_float("V0", vert[5])
        u1 = write_labeled_float("U1", vert[6])
        v1 = write_labeled_float("V1", vert[7])
        
        output += write_indented("Vertex", 1)
        output += write_indented(position, 2)
        output += write_indented(normal, 2)
        output += write_indented(tangent, 2)
        output += write_indented(color, 2)
        output += write_indented(u0, 2)
        output += write_indented(v0, 2)
        output += write_indented(u1, 2)
        output += write_indented(v1, 2)
    
    return output
    
def write_triangles(triangles):
    """
    Writes faces to string
    
    Triangles should be in format
    
    [[vertex0, vertex1, vertex2, material index]]
    """
    number_tris = len(triangles)                        
    output = write_indented(write_labeled_int("NumTriangles", number_tris), 1)
    
    print("Outputting ", number_tris, " triangles")
    
    for tri in triangles:
        vert0 = write_labeled_int("iVertex0", tri[0])
        vert1 = write_labeled_int("iVertex1", tri[1])
        vert2 = write_labeled_int("iVertex2", tri[2])
        mat = write_labeled_int("iMaterial", tri[3])
        
        output += write_indented("Triangle", 1)
        output += write_indented(vert0, 2)
        output += write_indented(vert1, 2)
        output += write_indented(vert2, 2)
        output += write_indented(mat, 2)
    
    return output
    

def write_mesh_data(context, filepath):
    print("running write_mesh_data...")
    
    mesh_list = create_export_list(bpy.context.scene.collection)
    
    for object in mesh_list:
        context.view_layer.objects.active = object
        object.select_set(True)
    
    bpy.ops.object.join()
    
    object = context.view_layer.objects.active
    
    #for obj in bpy.context.selected_objects:
    #    obj.rotation_euler[0] = math.radians(-90)
    #    bpy.ops.object.transform_apply(rotation=True)
    
    depsgraph = context.evaluated_depsgraph_get()
    object_eval = object.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(object_eval, preserve_all_data_layers=True, depsgraph=depsgraph)
        
    mesh.calc_tangents()
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
  
    bmesh.ops.split_edges(bm, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    
    #uv_layer = mesh.uv_layers.active.data
    
    vertices = [None] * len(bm.verts)
    triangles = [None] * len(bm.faces)
    
    bm.verts.index_update()
    bm.faces.index_update()
    
    uv_layer = bm.loops.layers.uv[0]
    
    for face in bm.faces:
        face_index = face.index
        faceverts = [0] * 4
        for i, loop in enumerate(face.loops):
            vert = loop.vert
            index = vert.index
            faceverts[i] = index
            vert_pos = vert.co
            vert_normal = vert.normal
            vert_tangent = copy.copy(mesh.loops[index].tangent)
            vert_u0 = loop[uv_layer].uv.x
            vert_v0 = loop[uv_layer].uv.y
            vert_u1 = vert_u0
            vert_v1 = vert_v0
            vertices[index] = [vert_pos, 
                        vert_normal, 
                        vert_tangent, 
                        0, 
                        vert_u0, 
                        vert_v0, 
                        vert_u1, 
                        vert_v1]
        faceverts[3] = face.material_index
        triangles[face_index] = faceverts
            
    #object.modifiers.remove(triangleModifier)
    
    bounding_box = object.bound_box

    #Creating giant string, top level
    file_out = "TXT\nMeshData\n"
    
    #Header info
    file_out += write_indented("maxDiffuseMipLevel 0", 1)
    file_out += write_indented("hasValidTangents TRUE", 1)
        
    summed_box = [xyz[0] + xyz[1] + xyz[2] for xyz in bounding_box]
    summed_sq_box = [xyz[0]**2 + xyz[1]**2 + xyz[2]**2 for xyz in bounding_box]
    
    max_extent = max(summed_box)
    min_extent = min(summed_box)
    
    max_ext_index = summed_box.index(max_extent)
    min_ext_index = summed_box.index(min_extent)
    
    radius = math.sqrt(max(summed_sq_box))
    
    bounding_rad = write_labeled_float("BoundingRadius", radius)
    max_bound = write_labeled_3list("MaxBoundingExtents", bounding_box[max_ext_index])
    min_bound = write_labeled_3list("MinBoundingExtents", bounding_box[min_ext_index])
    
    file_out += write_indented(bounding_rad, 1)
    file_out += write_indented(max_bound, 1)
    file_out += write_indented(min_bound, 1)
    
    #Important stuff; materials, bones, verts, faces
    file_out += write_materials()
    
    file_out += write_points([])
                                    
    file_out += write_vertices(vertices)
                            
    file_out += write_triangles(triangles)                                
    
    #Cached verts
    cached_up = write_labeled_int("NumCachedVertexIndicesInDirection:UP", 0)
    cached_down = write_labeled_int("NumCachedVertexIndicesInDirection:DOWN", 0)
    cached_left = write_labeled_int("NumCachedVertexIndicesInDirection:LEFT", 0)
    cached_right = write_labeled_int("NumCachedVertexIndicesInDirection:RIGHT", 0)
    cached_front = write_labeled_int("NumCachedVertexIndicesInDirection:FRONT", 0)
    cached_back = write_labeled_int("NumCachedVertexIndicesInDirection:BACK", 0)
    
    file_out += write_indented(cached_up, 1)
    file_out += write_indented(cached_down, 1)
    file_out += write_indented(cached_left, 1)
    file_out += write_indented(cached_right, 1)
    file_out += write_indented(cached_front, 1)
    file_out += write_indented(cached_back, 1)
    
    f = open(filepath, 'w', encoding='utf-8')
    
    f.write(file_out)
    
    f.close()
    print("Export complete")
    return {'FINISHED'}


# ExportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ExportMeshData(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "export_test.mesh_data"  # important since its how bpy.ops.import_test.mesh_data is constructed
    bl_label = "Export .mesh"

    # ExportHelper mixin class uses this
    filename_ext = ".mesh"

    filter_glob: StringProperty(
        default="*.mesh",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )


    def execute(self, context):
        return write_mesh_data(context, self.filepath)


# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportMeshData.bl_idname, text="SOASE (.mesh)")


def register():
    bpy.utils.register_class(ExportMeshData)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportMeshData)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.export_test.mesh_data('INVOKE_DEFAULT')
