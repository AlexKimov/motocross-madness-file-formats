# Blender 2.76 import script for MCM2 slb binary files, paste it and run in script editor.
# It even cope with rigs, go into pose mode and have a fun!
import bpy 
from os import path

from mathutils import Matrix
import sys
    
from struct import *
from collections import namedtuple
import re

# Set this path to file you wish to load
# Place all needed texture images within same directory as model in png format
fpath = "~/MCM2/models/Soda_Machine01.slb"

groups_re = re.compile("\((.*?)\)+")

class SLBFile:
    def __init__(self, f):
        self.data = f.read()
        self.dataIndex = 0
    
    def loadINT(self):
        result = Struct('<i').unpack_from(self.data[self.dataIndex:self.dataIndex+4])
        self.dataIndex += 4
        return result[0]
    def loadArray(self, structDef):
        struct_len = calcsize(structDef)
        result = Struct(structDef).unpack_from(self.data[self.dataIndex:self.dataIndex+struct_len])
        self.dataIndex += struct_len
        return result
        
    def loadStruct(self, structDef, tupleDef):
        tupleDef = namedtuple(*tupleDef)
        
        #groups_re.findall(structDef)
        result = []
        for current_struct in structDef:
            struct_len = calcsize(current_struct)
            value = Struct(current_struct).unpack_from(self.data[self.dataIndex:self.dataIndex+struct_len])
            self.dataIndex += struct_len
            if len(value) > 1:
                result.append(value)
            else:
                result.append(*value)
        result = tupleDef._asdict(tupleDef._make(result))
        
        return result
    
    def loadBodies(self):
        self.NumberOfBodies = self.loadINT()
        print("NumberOfBodies: %d" % self.NumberOfBodies)
        
        #struct = self.loadStruct('<128s16fii13f')
        
        self.bodies = []
        for i in range(0, self.NumberOfBodies):
            struct = self.loadStruct(('<128s', '<16f', '<i', '<i', '<13f'), ('Body', 'ObjName, transform uk0 uk1 transform2'))
            struct["ObjName"] = struct["ObjName"].split(b'\x00')[0].decode()
            print("Body: %s" % str(struct["ObjName"]))
            self.bodies.append(struct)
    
    def loadMaterials(self):
        self.NumberOfMaterials = self.loadINT()
        print("NumberOfMaterials: %d" % self.NumberOfMaterials)
        self.materials = []
        for i in range(0, self.NumberOfMaterials):
            struct = self.loadStruct(('<64s', '<i', '<12s', '<7i', '<4f', 'h' , 'f'), ('Material', 'textureFileName, key555 someStr uk color uk2 color2'))
            if struct['key555'] != 555 and struct['key555'] != 4444:
                print("Load material error")
                raise Exception('Format mismatch') 
            struct["textureFileName"] = struct["textureFileName"].split(b'\x00')[0].decode()
            print("Material: %s" % struct["textureFileName"])
            self.materials.append(struct)
            
    def getSurface(self):
        endingCnt = self.loadINT()
        NumberOfVertices = self.loadINT()
        NumberOfFaces = self.loadINT() 
        NumberOfMaterials = self.loadINT()
        # vertices
        vertices = []
        for i in range(0, NumberOfVertices*2):
            struct = self.loadStruct(('<3f', '<i', '<i', '<i', '<2f'), ('Vertex', 'point, keyCD keyFFF materialRef coord'))
            if struct['keyCD'] != -842150451:
                print("Vertex loading error")
                raise Exception('Format mismatch') 
            vertices.append(struct)
        # normals
        normals = []
        for i in range(0, NumberOfVertices):
            struct = self.loadStruct(('<3f',), ('Normal', 'indexes'))
            normals.append(struct)
        # triangles
        faces = []
        for i in range(0, NumberOfFaces):
            struct = self.loadStruct(('<3h',), ('Face', 'indexes'))
            faces.append(struct)
        # uvs
        uvs = []
        for i in range(0, NumberOfVertices):
            struct = self.loadStruct(('<2f',), ('UV', 'uv'))
            uvs.append(struct)
        Surface = self.loadINT()
        # vertex groups
        groups = []
        groupsPtrList = []
        for i in range(0, endingCnt):
            groups.append(self.loadStruct(('<i', '<i', '<3i'), ('Group', 'uk, vertexCnt uk2')))
        for i in range(0, endingCnt):
            groupsPtrList.append(self.loadStruct(('<i', '<i'), ('GroupPtr', 'bodyIndex, startVertexIndex')))
        #ending = self.loadArray("<"+"%df"%(7*endingCnt))
        Vg = namedtuple("VertexGroup", "bodyIndex vertexIndex vertexCnt")
        for i in range(0, endingCnt):
            groups[i] = Vg(groupsPtrList[i]["bodyIndex"], groupsPtrList[i]["startVertexIndex"],  groups[i]["vertexCnt"])
            
        return {'endingCnt':endingCnt, 'vertices':vertices, 'normals':normals, 'faces':faces, 'uvs':uvs, 'groups':groups, 'surface':Surface }
    
    def loadLODs(self):
        self.NumberOfLOD = self.loadINT()
        self.AutoLOD =  self.loadArray("<"+"f"*self.NumberOfLOD)
        #print(self.AutoLOD)
        self.lods = []
        for i in range(0, self.NumberOfLOD):
            lod = {"Surfaces":[]}
            NumberOfSurfaces = self.loadINT()
            for j in range(0, NumberOfSurfaces):
                srfc = self.getSurface()
                lod['Surfaces'].append(srfc)
            self.lods.append(lod)
        
    def load(self):
        self.loadBodies()
        # check for gurad? magic value
        if self.loadINT() != -1:
            print("Load error")
            raise Exception('Format mismatch') 
        self.bodiesHierarchy = self.loadArray("<"+"%di"%(self.NumberOfBodies-1))
        #print(self.bodiesHierarchy)
        self.loadMaterials()
        
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
    return ob

def createBones(bones, hierarchy, name = "SLB"):

    amt = bpy.data.armatures.new(name+'RigData')
    rig = bpy.data.objects.new(name+'Rig', amt)
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
            parentIndex = hierarchy[i-1]
            # level 1 bones
            if parentIndex == 0:
                b.parent = newBones[parentIndex]
                b.head = (tm * Matrix.Translation(b.parent.head)).to_translation()
                b.tail = b.head
                b.tail[2] -= 0.01
            else:    
                b.parent = newBones[parentIndex]
                b.parent.tail = (tm * Matrix.Translation(b.parent.head)).to_translation()
                b.head = b.parent.tail
                b.tail = b.head
                b.tail[2] -= 0.01                         

        # root bone
        else:
            b.tail = (0,0,0)
            b.head = tm.to_translation()
            if b.length < 0.00001:
                b.tail[2] += 0.00001
        #print(tm)
        #print(b.matrix)
        newBones.append(b)
    # old way of loading
    '''if i > 0:
            b.parent = newBones[hierarchy[i-1]]
            b.head = b.parent.tail
            b.tail = (tm * Matrix.Translation(b.parent.tail)).to_translation()
        else:
            b.head = (0,0,0)
            b.tail = tm.to_translation()
            # prevents 0 length bones from deletion, blender does not support them
            if b.length < 0.00001:
                b.tail[2] += 0.00001
        #print(tm)
        #print(b.matrix)
        newBones.append(b)
    '''
    return rig

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
    f = open(fpath, "rb")
    slb = SLBFile(f)
    slb.load()
    
    name = path.basename(path.splitext(fpath)[0])
    # ADDING BONES
    bones = [((b['transform'][0:4], b['transform'][4:8],b['transform'][8:12],b['transform'][12:16]),b['ObjName']) for b in slb.bodies]
    rig = createBones(bones, slb.bodiesHierarchy, name)
    
    # ADDING MESH
    materials = []
    for material in slb.materials:
        tga_file = material['textureFileName']
        MyMat = MyMaterial(tga_file.replace('.tga', ''), path.join(fdir, tga_file.replace('.tga', '.png')))
        materials.append(MyMat)
        
    for materialID, current_surface in enumerate(slb.lods[0]['Surfaces']):
        verts = [(v['point'][0], v['point'][2], v['point'][1]) for v in current_surface['vertices']]
        faces = [s['indexes'] for s in current_surface['faces']]
        normals = [s['indexes'] for s in current_surface['normals']]
        #uvs = [uv['uv'] for uv in current_surface['uvs']]
        uvs = [(uv['uv'][0],1.0-uv['uv'][1]) for uv in current_surface['uvs']]
        
        
        faceMaterials = [materialID for i in range(0, len(faces))]
        verts = verts[0:len(uvs)]
        ob = createObject(name, verts, faces, uvs, faceMaterials, materials, normals )
        
        # ASSIGN VERTICES TO GROUPS
        for group in current_surface['groups']:
            grp_name = slb.bodies[group.bodyIndex]["ObjName"]
            ob.vertex_groups.new(grp_name)
            vxIds = [vxId for vxId in range(group.vertexIndex, group.vertexIndex+group.vertexCnt)]
            ob.vertex_groups[grp_name].add(vxIds, 1.0, 'REPLACE')
            
        #bpy.ops.object.parent_set(type='ARMATURE')
        #ob.parent_bone = bone
        ob.parent = rig
        ob.parent_type = 'ARMATURE'
        
main()
