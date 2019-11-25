# Blender 2.76 import script for MCM2 slt text files, paste it and run in script editor.
import bpy 
from os import path

from mathutils import Matrix
import sys   
from struct import *
from collections import namedtuple
import re

# Set this path to file you wish to load
fpath = "~/MCM2/models/ECO/Grass02.SLT"
# Set this path to directory where all needed texture images are in png format
texturepath = "~/MCM2/models/ECO/"

class SLTFile:
    def __init__(self, f):
        self.data = f.read()
    
    def loadBodies(self):
        bodies = re.search(".*\[Object Hierarchy\][\W]*(.+)", self.data).group(1)
        bodies = bodies.split(",")
        #print(bodies)
        
        self.bodies = []
        self.bodies.append({"ObjName": bodies[0]})
    
    def loadMaterials(self):
        self.NumberOfMaterials = int(re.search(".*NumberOfMaterials=(\d+)", self.data).group(1))
        self.materials = []
        texture = re.search(".*TextureMap=(.+)", self.data).group(1)
        self.materials.append({"textureFileName": texture})
        for i in range(0, self.NumberOfMaterials):
            pass
        #print(self.materials)
            
    def getSurface(self):
        NumberOfVertices = int(re.search(".*NumberOfVertices=(\d+)", self.data).group(1))
        NumberOfFaces = int(re.search(".*NumberOfFaces=(\d+)", self.data).group(1)) 
        
        verts = re.search(".*\[LOD 0 - Surface 0 - Vertices\]([\w\W]+)\[LOD 0 - Surface 0 - Faces\]", self.data).group(1)
        verts = verts.split("\n")
        #print(verts)
        fcs = re.search(".*\[LOD 0 - Surface 0 - Faces\]([\w\W]+)\[LOD 0 - Surface 0 - Object Pointer List\]", self.data).group(1)
        fcs  = fcs.split("\n")
        #print(fcs)
        
        # vertices
        vertices = []
        # normals
        normals = []
        # uvs
        uvs = []
        for v in verts:
            if len(v) < 1:
                continue
            vertex = [float(num) for num in v.split(",")]
            vertices.append({"point":vertex[0:3]})
            normals.append({"indexes":vertex[3:6]})
            uvs.append({"uv":vertex[6:8]})
        if len(vertices) != NumberOfVertices:
            print("WARN: vertices number mismatch")
        #print(vertices)
        #print(normals)
        #print(uvs)
        

        # triangles
        faces = []
        for f in fcs:
            if len(f) < 1:
                continue
            face = [int(v) for v in f.split(",")]
            faces.append({"indexes":face})
        if len(faces) != NumberOfFaces:
            print("WARN: faces number mismatch")
   
        return {'vertices':vertices, 'normals':normals, 'faces':faces, 'uvs':uvs, 'surface':0 }
    
    def loadLODs(self):
        self.lods = [{"Surfaces":[]}]
        self.lods[0]["Surfaces"].append(self.getSurface())
        
    def load(self):
        self.loadMaterials()
        self.loadBodies()
        self.loadLODs()

# BLENDER SPECIFIC STUFF
################################################
class MyMaterial:
    """ blender material object """
    def __init__(self):
        self.material = None
        self.texture = None
        self.name = ''
        
    def __init__(self, name, textureFileName, color = (1,0,0)):
        self.createMaterial(name, textureFileName, color)
    
    def createMaterial(self, name, textureFileName, color):
        mat = bpy.data.materials.new(name)
        mat.diffuse_shader = 'LAMBERT' 
        mat.diffuse_color = color
        mat.diffuse_intensity = 0.5
        mat.alpha = 1.0
        mat.use_face_texture=True
        mat.use_shadeless=True
        
        tex = bpy.data.textures.new(name+'.tex', type = 'IMAGE')
        tex.image = bpy.data.images.load(textureFileName)
        # Add texture slot for bump texture
        mtex = mat.texture_slots.add()
        mtex.texture = tex
        mtex.texture_coords = 'UV'
        mtex.use_map_color_diffuse = True 
        mtex.use_map_color_emission = True 
        mtex.emission_color_factor = 0.5
        
        # Add texture slot for color texture
        
        self.texture = mtex
        self.material = mat
        self.name = name
        
        return mat
        
def createObject(name, verts, faces, uvs, faceMaterials, materials, normals, transform = ((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.0, 0.0, 0.0, 1.0))):
    """ creates single scene blender object from supplied data arrays"""
    mesh = bpy.data.meshes.new(name+".mesh")
    ob = bpy.data.objects.new(name, mesh)
    #ob.location = location
    ob.matrix_local = transform
    mesh.from_pydata(verts, [], faces)

    mesh.uv_textures.new()
    #matrix = Matrix.Translation((0, 0, 0))
    #mesh.transform(matrix)
    
    #create materials list
    for material in materials:
        mesh.materials.append(material.material)    

    #print(len(mesh.uv_layers.active.data))
    #for each vertex in mesh
    for n in range(0,len(mesh.vertices)):
        #set up UV's
        #print(mesh.uv_layers)
        ##mesh.uv_layers.active.data[n].uv=uvs[n]
        #print(mesh.uv_layers.active.data[n].uv)
        
        #setup normals
        #mesh.loops[n].normal = normals[n];
        mesh.vertices[n].normal = normals[n]
        #print (mesh.vertices[n].index, " ", mesh.vertices[n].co)


    for triangle in mesh.polygons:
        vertices = list(triangle.vertices)
        i = 0
        for vertex in vertices:
            for uv_layer in mesh.uv_layers:
                uvCoord = uv_layer.data[triangle.loop_indices[i]].uv
                #print(uvCoord, " in triangle vertex: ", i, " index", triangle.index, " vertex", triangle.vertices[i])
                
                uv_layer.data[triangle.loop_indices[i]].uv = uvs[triangle.vertices[i]]
            i += 1

    mesh.calc_normals()

    #setup poly materials for polys
    for i in range(0, len(mesh.polygons)):
        textureIndex = faceMaterials[i]
        mesh.polygons[i].material_index = textureIndex
        # mesh.polygons[i].image??
        mesh.uv_textures.active.data[i].image =  materials[textureIndex].texture.texture.image

    #setup textures for polys
    #for face in mesh.uv_textures.active.data:
        #faceIndex = face.index
        #face.image =  materials[0].texture.texture.image
        
    bpy.context.scene.objects.link(ob)

def createBones(bones, hierarchy):

    amt = bpy.data.armatures.new('MyRigData')
    rig = bpy.data.objects.new('MyRig', amt)
    rig.location = (0,0,0)
    rig.show_x_ray = True
    amt.show_names = True
    # Link object to scene
    scn = bpy.context.scene
    scn.objects.link(rig)
    scn.objects.active = rig
    scn.update()

    bpy.ops.object.mode_set(mode='EDIT')

    newBones = []
    for i, bone in enumerate(bones):
        b = amt.edit_bones.new(bone[1])
        b.use_local_location = True
        tm = Matrix(bone[0])
        tm.transpose()
        # swap coordinate system
        tmp = tm[1][3]
        tm[1][3] = tm[2][3]
        tm[2][3] = tmp
        
        #b.tail = Vector([0,0,0.2]) 
        if i > 0:
            b.parent = newBones[hierarchy[i-1]]
            b.head = b.parent.tail
            b.tail = (tm * Matrix.Translation(b.parent.tail)).to_translation()
        else:
            b.head = (0,0,0)
            b.tail = tm.to_translation()
        #print(tm)
        #print(b.matrix)
        newBones.append(b)

def createObjectFromMesh(mesh, allMaterials, texturesDir = ''):
    transform = mesh.transform
    verts = mesh.vertices
    faces = mesh.faces
    uvs = mesh.uvs
    faceMaterials = mesh.faceMaterials
    name = mesh.name
    normals = mesh.normals
    materials = []
    
    for material in mesh.materials:
        material = material.replace(';','')
        materialDetails = allMaterials[material]
        materials.append(MyMaterial(materialDetails.name, texturesDir+materialDetails.textureFileName, materialDetails.color))
    
    #print (verts , '\n', uvs)
    
    createObject(name, verts, faces, uvs, faceMaterials, materials, normals, transform)


def main():
    fdir = path.dirname(fpath)
    f = open(fpath, "rt")
    slt = SLTFile(f)
    slt.load()
    
    # ADDING MESH
    materials = []
    for material in slt.materials:
        tga_file = material['textureFileName']
        MyMat = MyMaterial(tga_file.replace('.tga', ''), path.join(texturepath, tga_file.replace('.tga', '.png')))
        materials.append(MyMat)
        
    for materialID, current_surface in enumerate(slt.lods[0]['Surfaces']):
        verts = [(v['point'][0], v['point'][2], v['point'][1]) for v in current_surface['vertices']]
        faces = [s['indexes'][::-1] for s in current_surface['faces']]
        normals = [s['indexes'] for s in current_surface['normals']]
        #uvs = [uv['uv'] for uv in current_surface['uvs']]
        uvs = [(uv['uv'][0],1.0-uv['uv'][1]) for uv in current_surface['uvs']]
        
        name = path.basename(path.splitext(fpath)[0])
        
        faceMaterials = [materialID for i in range(0, len(faces))]
        verts = verts[0:len(uvs)]
        createObject(name, verts, faces, uvs, faceMaterials, materials, normals )
        
    #ADDING BONES
    '''bones = [((b['transform'][0:4], b['transform'][4:8],b['transform'][8:12],b['transform'][12:16]),b['ObjName']) for b in slt.bodies]
    createBones(bones, slt.bodiesHierarchy)'''

main()

