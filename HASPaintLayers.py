'''
Hirourk 
not.nice.primer@gmail.com

Created by Hirourk

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
bl_info = {
    "name": "HAS Paint Layers",
    "blender": (3, 1, 0),
    "category": "Paint",
    "version": (0, 8, 5),
    "description": "Layers for texture painting",
    "author": "Hirourk",
    "location": "View3D > Tool Shelf > Paint Layers",
    "warning": "Add-on is still in development",
    "doc_url": "https://hirourk.github.io/HASPaintLayersWiki/index.html"
}

import os
import bpy
import re
import shutil
from pathlib import Path
from bl_operators.presets import AddPresetBase
from bpy.props import CollectionProperty, StringProperty, IntProperty, PointerProperty, BoolProperty, FloatVectorProperty, FloatProperty, EnumProperty
import numpy as np
from bl_ui.utils import PresetPanel
from bpy.types import Panel, Operator, PropertyGroup, Menu, Scene, UIList
import bpy.utils.previews
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent, save_pre
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix,  Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
import blf
import struct
import zipfile
from xml.etree.ElementTree import Element, SubElement, ElementTree
import nodeitems_utils
import subprocess
import sys
import bmesh
from bpy_extras import view3d_utils
import gpu
from bgl import glEnable, glDisable, GL_BLEND, GL_DEPTH_TEST
import math
import tempfile
from gpu_extras.batch import batch_for_shader
from math import cos, sin, pi
import datetime
import mathutils
from contextlib import contextmanager
import uuid
import random
import webbrowser

###
### ENUMS
###

shader_node_categories = {
    "Shader": ["ShaderNodeBsdfDiffuse", "ShaderNodeBsdfPrincipled", "ShaderNodeEmission"],
    "Texture": ["ShaderNodeTexImage", "ShaderNodeTexNoise", "ShaderNodeTexChecker"],
    "Converter": ["ShaderNodeRGBToBW", "ShaderNodeMath", "ShaderNodeMixRGB"],
    "Input": ["ShaderNodeTexCoord", "ShaderNodeValue"],
    "Output": ["ShaderNodeOutputMaterial"]
}
BLEND_MODES = [
    ('MIX', 'Mix', 'Mix the layers'),
    ('PASS', 'Passthrough', 'Pass through'),
    (None),
    ('ADD', 'Add', 'Add the layers'),
    ('MULTIPLY', 'Multiply', 'Multiply the layers'),
    ('SUBTRACT', 'Subtract', 'Subtract the layers'),
    ('SCREEN', 'Screen', 'Screen the layers'),
    ('DIVIDE', 'Divide', 'Divide the layers'),
    (None),
    ('DIFFERENCE', 'Difference', 'Difference between the layers'),
    ('DARKEN', 'Darken', 'Darken the layers'),
    ('LIGHTEN', 'Lighten', 'Lighten the layers'),
    ('OVERLAY', 'Overlay', 'Overlay the layers'),
    ('DODGE', 'Dodge', 'Dodge the layers'),
    ('BURN', 'Burn', 'Burn the layers'),
    (None),
    ('HUE', 'Hue', 'Combine Hue of the layers'),
    ('SATURATION', 'Saturation', 'Combine Saturation of the layers'),
    ('VALUE', 'Value', 'Combine Value of the layers'),
    ('COLOR', 'Color', 'Combine Color of the layers'),
    ('SOFT_LIGHT', 'Soft Light', 'Soft light blending'),
    ('LINEAR_LIGHT', 'Linear Light', 'Linear light blending'),
    (None),
    ('COMBNRM', 'Combine Normal', 'Combine normal blending'),
]
TEXTURE_TYPE = [
    ('DIFFUSE', 'Diffuse', 'Texture as Diffuse'),
    ('METALLIC', 'Metallic', 'Texture as Metallic'),
    ('ROUGHNESS', 'Roughness', 'Texture as Roughness'),
    ('EMISSION', 'Emission', 'Texture as Emission'),
    ('ALPHA', 'Alpha', 'Texture as Alpha'),
    ('NORMAL', 'Normal', 'Texture as Normal'),
    ('HEIGHT', 'Height', 'Texture as Height'),
    ('AO', 'Ambient Occlusion', 'Texture as Ambient Occlusion'),
    ('CUSTOM', 'Custom', 'Custom texture'),
]
TEXTURE_FILTER = [
    ('Linear', 'Linear', ''),
    ('Closest', 'Closest', ''),
    ('Cubic', 'Cubic', ''),
    ('Smart', 'Smart', ''),
]
BAKE_TYPE = [
    ('AO', "Ambient Occlusion", ""),
    ('NORMAL',"Normal Map", ''),
    ('CURVATURE',"Curvature Map", ''),
    ('NRMOBJ',"Object Normal Map", ''),
    ('POSITION',"Object Position Map", ''),
    ('HEIGHT',"Height Map", ''),
    ('DIFFUSE', "Diffuse Map", ""),
    ('EMISSION', "Emission", ""),
]
SORT_COLORS = [
    ('PANEL_CLOSE', "", ""),
    ('SEQUENCE_COLOR_01', "", ""),
    ('SEQUENCE_COLOR_02', "", ""),
    ('SEQUENCE_COLOR_03', "", ""),
    ('SEQUENCE_COLOR_04', "", ""),
    ('SEQUENCE_COLOR_05', "", ""),
    ('SEQUENCE_COLOR_06', "", ""),
    ('SEQUENCE_COLOR_07', "", ""),
    ('SEQUENCE_COLOR_08', "", ""),
]
FOLDER_SORT_COLORS = [
    ('OUTLINER_COLLECTION', "", ""),
    ('COLLECTION_COLOR_01', "", ""),
    ('COLLECTION_COLOR_02', "", ""),
    ('COLLECTION_COLOR_03', "", ""),
    ('COLLECTION_COLOR_04', "", ""),
    ('COLLECTION_COLOR_05', "", ""),
    ('COLLECTION_COLOR_06', "", ""),
    ('COLLECTION_COLOR_07', "", ""),
    ('COLLECTION_COLOR_08', "", ""),
]
FILTERS = [
    ('PAINT', 'Paint Layer', 'ShaderNodeTexImage',"BRUSH_DATA",0),
    ('FILL', 'Fill Layer', 'ShaderNodeGroup',"IMAGE",0),
    (None),
    ('LEVELS', 'Levels', 'ShaderNodeGroup',"SEQ_HISTOGRAM",0),
    ('COLORRAMP', 'Color Ramp', 'ShaderNodeValToRGB',"COLORSET_10_VEC",0),
    ('CURVERGB', 'Curve', 'ShaderNodeRGBCurve',"NORMALIZE_FCURVES",0),
    ('HSV', 'HSV', 'ShaderNodeHueSaturation',"MOD_HUE_SATURATION",0),
    ('INVERT', 'Invert', 'ShaderNodeInvert',"MOD_MASK",0),
    ('GAMMA', 'Gamma', 'ShaderNodeGamma',"COLORSET_13_VEC",0),
    ('BRIGHTCONTRAST', 'Brightness Contrast', 'ShaderNodeBrightContrast',"COLORSET_10_VEC",0),
    (None),
    ('LIGHT', 'Light', 'ShaderNodeGroup',"SHADING_RENDERED",0),
    ('BLUR', 'Blur', 'ShaderNodeGroup',"PROP_OFF",0),
    ('SNAPSHOT', 'Snapshot', 'ShaderNodeGroup',"FCURVE_SNAPSHOT",0),
    (None),
    ('SEPARATERGB', 'Separate RGB', 'ShaderNodeSeparateRGB',"IMAGE_RGB_ALPHA",0),
    ('MASKCOLOR', 'Select Color', 'ShaderNodeGroup',"CLIPUV_DEHLT",0),
    ('MASKGEN', 'Mask Generator', 'ShaderNodeGroup',"NODE_TEXTURE",0),
    (None),
    ('MAPPING', 'Transform', 'ShaderNodeGroup',"UV",0),
    (None),
    ('CUSTOM', 'Custom Filter', 'ShaderNodeGroup',"NODETREE", 0),
]
MASKITEMS = [
    ('AO', "ShaderNodeAmbientOcclusion", "Color", 'ao_expand'),
    ('Curvature', "ShaderNodeAmbientOcclusion", "Color", 'curv_expand'),
    ('Position', "ShaderNodeTexCoord", "Generated", 'pos_expand'),
    ('Object Normal', "ShaderNodeNewGeometry", "Normal", 'objn_expand'),
]
###
### VERSIONS
###

version = bpy.app.version

is_pre_3_1 = (version[0] == 3 and version[1] < 1) or version[0] < 3

is_3_4_or_newer = (version[0] > 3) or (version[0] == 3 and version[1] >= 4)

is_4_0_or_newer = version[0] >= 4

is_4_2_or_newer = version[0] > 4 or (version[0] == 4 and version[1] >= 2)

operator_running = False

###
### PROPERTIES
###

preview_icons = {}
class UsedMaps(PropertyGroup):
    def update_shader(self, context):
        UpdateShader()
    Diffuse: BoolProperty(name="Diffuse", default= True, update = update_shader)
    Metallic: BoolProperty(name="Metallic", default= True, update = update_shader)
    Roughness: BoolProperty(name="Roughness", default= True, update = update_shader)
    Emission: BoolProperty(name="Emission", default= False, update = update_shader)
    Alpha: BoolProperty(name="Alpha", default= False, update = update_shader)
    Normal: BoolProperty(name="Normal", default= True, update = update_shader)
    Height: BoolProperty(name="Height", default= True, update = update_shader)
    AO: BoolProperty(name="Ambient Occlusion", default= False, update = update_shader)
    Custom: BoolProperty(name="Custom", default= False, update = update_shader)

class Brushes(PropertyGroup):
    def get_texture_types(self, context):
        return getusedmaps()
    def updatedvalues(self, context):
        self.color = (self.value,self.value,self.value,1.0)
        
    type: EnumProperty(
        name="Brush type",
        items = get_texture_types
    )
    color: FloatVectorProperty(
        name="Brush Color",
        description="Brush color",
        subtype='COLOR',
        size=4, 
        default=(0.5, 0.5, 0.5, 1.0),
        min=0.0,
        max=1.0,
    )
    value: FloatProperty(
        name="Brush value",
        description="Brush value",
        default=1.0, 
        min=0.0,
        max=1.0,
        update = updatedvalues
    )
    onechannel: BoolProperty()
    in_use: BoolProperty(default = True)
    texture: PointerProperty(
        name="Texture",
        type=bpy.types.Texture,
        description="Brush texture"
    )

class LayerReference(PropertyGroup):

    id: StringProperty()
    index: IntProperty()
    def get_layer(self):
        part = get_material_collection()

        for l in part.layers:
            if l.id == self.id:
                return l
        
        return None
 
class SocketReference(PropertyGroup):
    def updatesocket(self, context):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            if node:
                set_default(node, self.socket_name, self.default_value)
    default_value: FloatProperty(update= updatesocket, min = 0.0, max =1.0)
    node_name: StringProperty(name="Node Name")
    socket_name: StringProperty(name="Socket Name")
    node_tree_name: StringProperty(name="Node Tree Name")
    
    def get_socket(self):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            if node:
                return node.inputs[self.socket_name]
        return None
    def set_socket_reference(self, socket):
        if socket:
            self.node_tree_name = socket.node.id_data.name
            self.node_name = socket.node.name 
            self.socket_name = socket.name

class NodeReference(PropertyGroup):

    node_name: StringProperty(name="Node Name")
    node_tree_name: StringProperty(name="Node Tree Name")
    node_type: StringProperty(name="Node Type")
    
    def get_node(self):
        node_tree = bpy.data.node_groups.get(self.node_tree_name)
        if node_tree:
            node = node_tree.nodes.get(self.node_name)
            return node
        return None

    def set_node_reference(self, node):
        if node:

            self.node_tree_name = node.id_data.name
            self.node_name = node.name
            self.node_type = node.bl_idname 

class HistrogramReference(PropertyGroup):
    texture_name: StringProperty()
    histogram: StringProperty()
    
class LevelsProperty(PropertyGroup):

    def valupdate(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        if self.levels_node:
            ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(self.s_channel, -1)
            set_rgb_curve(self.levels_node.get_node(), self.val01, self.val02, self.val03, self.val04, self.val05, ind)
        self.suppress_update = False

    levels_node: PointerProperty(type=NodeReference)

    val01: FloatProperty(
        default=0.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val02: FloatProperty(
        default=0.5,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val03: FloatProperty(
        default=1.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val04: FloatProperty(
        default=0.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    val05: FloatProperty(
        default=1.0,
        min=0.0,
        max=1.0,
        update=valupdate
    )
    def channelswitch(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        node = self.levels_node.get_node()
        ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(self.s_channel, -1)
        if not ind == -1:
            curve = node.mapping.curves[ind]
            if not len(curve.points) == 2:
                while len(curve.points) < 5:
                    curve.points.new(0.5, 0.5)
                self.val01 = curve.points[1].location[0]
                self.val03 = curve.points[3].location[0]
                self.val02 = fraction_between(curve.points[2].location[0], self.val01, self.val03)
                self.val04 = curve.points[0].location[1]
                self.val05 = curve.points[4].location[1]
            else:
                self.val01 = 0.0
                self.val02 = 0.5
                self.val03 = 1.0
                self.val04 = 0.0
                self.val05 = 1.0
                set_rgb_curve(node, self.val01, self.val02, self.val03, self.val04, self.val05, ind)

        curve = node.mapping.curves[ind]  
        self.suppress_update = False
    s_channel: EnumProperty(
        name="Channel",
        items=[
            ('COL', 'Color', '', "EVENT_C",0),
            (None),
            ('R', 'R Channel', '',"EVENT_R",1),
            ('G', 'G Channel', '',"EVENT_G",2),
            ('B', 'B Channel', '',"EVENT_B",3),
        ],
        update=channelswitch,
    )
    expand: BoolProperty(default = False)
    expand_levels: BoolProperty(default = False)
    suppress_update: BoolProperty()

class ResourceProperty(PropertyGroup):
    def update(self, context):
        if self.suppress_update:
            return
        UpdateShader()
    def MappingUpdate(self, context):
        if self.suppress_update:
            return
        mapping = self.mapping_node.get_node()
        if mapping:
            set_default(mapping, "Location", (self.mapx,self.mapy,0.0))
            set_default(mapping, "Rotation", (0.0,0.0,self.maprot))
            set_default(mapping, "Scale", (self.mapscalex,self.mapscaley,1.0))
    suppress_update: BoolProperty()
    expand: BoolProperty(default = False)
    grayscale: BoolProperty(default = False)
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=update
    )
    mapping_node: PointerProperty(type=NodeReference)
    histogram: StringProperty()
    def default_value_socket_update(self, context):
        if self.suppress_update:
            return
        self.default_color = (self.default_value,self.default_value,self.default_value,self.default_value)

    def default_color_socket_update(self, context):
        if self.suppress_update:
            return
        if self.grayscale:
            self.suppress_update = True
            self.default_color = (self.default_color[0],self.default_color[0],self.default_color[0],1.0)
            self.suppress_update = False
        if self.default_color_socket.get_socket():
            self.default_color_socket.get_socket().default_value = self.default_color
        else:
            UpdateShader()
    default_color: FloatVectorProperty(
        name="Default Color",
        description="Default color",
        subtype='COLOR',
        size=4, 
        default=(0.5, 0.5, 0.5, 1.0),
        min=0.0,
        max=1.0,
        update=default_color_socket_update
    )
    default_color_socket: PointerProperty(type=SocketReference)

    default_value: FloatProperty(
        name="Default Value",
        default=0.5,
        min=0.0,
        max=1.0,
        update=default_value_socket_update
    )
    mapx: FloatProperty(
        name="Mapping Offset X",
        default=0,
        update=MappingUpdate,
        subtype='DISTANCE'
    )
    mapy: FloatProperty(
        name="Mapping Offset Y",
        default=0,
        update=MappingUpdate,
        subtype='DISTANCE',
    )
    mapscalex: FloatProperty(
        name="Mapping Scale X",
        default=1.0,
        update=MappingUpdate
    )
    mapscaley: FloatProperty(
        name="Mapping Scale Y",
        default=1.0,
        update=MappingUpdate
    )
    maprot: FloatProperty(
        name="Mapping Rotation",
        default=0,
        update=MappingUpdate,
        subtype='ANGLE'
    )

    repeat: EnumProperty(
        name="Repeat",
        items=[
            ('TILE', "Repeat XY", "Repeat Texture in All Directions"),
            ('X', "Repeat X", "Repeat Texture Horizontally"),
            ('Y', "Repeat Y", "Repeat Texture Vertically"),
            ('CLIP', "Clip", "Texture will be Clipped"),
        ],
        default="TILE",
        update=update
    )
    expand_mapping: BoolProperty(default = False)
    levels: PointerProperty(type=LevelsProperty)

class TextureMappedProperty(PropertyGroup):
    texture_type: EnumProperty(
        name="Type",
        items=[
            ('PAINT', "Paint Layer", ""),
            ('TEXTURE', "Texture", ""),
            ('PROC', "Procedural", ""),
        ],
        description="Texture use type",
        default="PAINT",
    )
    proc_node_type: EnumProperty(
        name="Type",
        items=[
            ('PAINT', "Paint Layer", ""),
            ('TEXTURE', "Texture", ""),
            ('PROC', "Procedural", ""),
        ],
        description="Texture use type",
        default="PAINT",
    ) 
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
    )
    mapping_x: FloatProperty(
        name="Offset X",
        default=0.0,
    )
    mapping_y: FloatProperty(
        name="Offset Y",
        default=0.0,
    )
    mapping_rotation: FloatProperty(
        name="Rotation",
        default=0.0,
    )
    mapping_scale_x: FloatProperty(
        name="Scale X",
        default=1.0,
    )
    mapping_scale_Y: FloatProperty(
        name="Scale Y",
        default=1.0,
    )

class MaskGeneratorProperty(PropertyGroup):
    def get_item(self,item):
        if item == "AO":
            return self.ao_resource
        elif item == "Curvature":
            return self.curv_resource
        elif item == "Position":
            return self.pos_resource
        elif item == "Object Normal":
            return self.objn_resource
        return None
    expand: BoolProperty(name="Expand", default=False)
    ao_resource: PointerProperty(type=ResourceProperty)
    curv_resource: PointerProperty(type=ResourceProperty)
    pos_resource: PointerProperty(type=ResourceProperty)
    objn_resource: PointerProperty(type=ResourceProperty)
    ao_expand: BoolProperty(name="AO",default = False)
    curv_expand: BoolProperty(name="Curvature",default = False)
    pos_expand: BoolProperty(name="Position",default = False)
    objn_expand: BoolProperty(name="Object Normal",default = False)

class FilterProperty(PropertyGroup):
    def resetinputs(self):
        self.socket_in = 0
        self.socket_out = 0
    def reset_filter_name(self, context):
        if self.suppress_update:
            return
        self.suppress_update = True
        self.resetinputs()
        self.node_name = ""
        self.resource.image = None

        if self.name == "LIGHT":
            for geds in get_material_collection().bake_maps:
                geds.type == "NRMOBJ"
                if geds.image:
                    self.resource.image = geds.image
        if self.name == "PAINT":
            if not self.resource.image:
                texture_name = f'.HAS_{self.id}_paint'
                ims = bpy.data.images.get(texture_name)
                if ims:
                    self.resource.image = ims
                else:
                    self.resource.image = newimage(texture_name)
        UpdateShader()

        self.suppress_update = False
    def reset_filter(self, context):
        
        self.suppress_update = True
        self.resetinputs()
        UpdateShader()
        self.suppress_update = False
    def reset_custom_filter(self, context):
        self.suppress_update = True
        self.node_name = ""
        self.resetinputs()
        if self.custom_node_tree_p and self.custom_node_tree_p.name.startswith("."):
            self.custom_node_tree_p = None
        UpdateShader()
        self.suppress_update = False
    def update_layer(self, context):
        if not self.suppress_update:
            layer_filter(get_layer_by_id(self.layer_in), multi = True)

    def valupdate(self, context):
        if self.suppress_update:
            return
        layer_filter(get_layer_by_id(self.layer_in))

    id: StringProperty(
        name="ID",
        default="empty"
    )

    name: StringProperty(
        name="Filter",
        default="",
        update=reset_filter_name
    )
    edit: BoolProperty(
        name="Settings",
        description="Toggle filter settings",
        default=False,
    )
    in_use: BoolProperty(
        name="Visibility",
        description="Toggle filter visibility",
        default=True,
        update=update_layer
    )
    node_name: StringProperty( 
        default="",
        name="Node",
        description="Name of the node",
    )
    mixnode: StringProperty()
    #custom_node_tree: StringProperty(update = reset_filter_name)
    custom_node_tree_p: PointerProperty(type=bpy.types.NodeTree, update = reset_custom_filter)
    layer_in: StringProperty(
        default="",
    )
    node: PointerProperty(type=NodeReference)
    displnode: PointerProperty(type=NodeReference)
    socket_in: IntProperty(
        default=0,
        name="Input",
        
    )
    socket_out: IntProperty(
        default=0,
        name="Input", 
    )

    image: PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=update_layer
    )
    resource: PointerProperty(type=ResourceProperty)
    maskgen: PointerProperty(type=MaskGeneratorProperty)
    editgrunge: BoolProperty(
        name="Grunge",
        description="Toggle Grunge settings",
        default=False,
    )
    blend_mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODES,
        description="Blend mode for mixing layers",
        default="MIX",
        update=reset_filter
    )
    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            sock.default_value = self.opacity
           
    opacity: FloatProperty(
        name="Opacity",
        description="Opacity of the layer",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_opacity
    )
    opacity_socket: PointerProperty(type=SocketReference)
    Unspval: FloatProperty(
        default=1.0,
        min=0.0,
        update=valupdate
    )
    connection_type: EnumProperty(
        name="Filter Type",
        items=[
            ('COLOR', 'Color', ''),
            ('ALPHA', 'Alpha', ''),
            ('UV', 'UV', ''),
        ],
    )
    def get_texture_types(self, context):
        return getusedmaps()
    affect_channels: EnumProperty(
        name="Channel",
        items=get_texture_types,
        description="Filter for channel",
        update=reset_filter
    )
    suppress_update: BoolProperty(default = False)

    levels: PointerProperty(type=LevelsProperty)
    
class LayerProperties(PropertyGroup):

    def update_layer(self, context):
        if self.layer_type =="PBR":
            create_pbr_nodegroup(self)
            return
        elif self.layer_type =="FOLDER":
            create_folder_nodegroup(self)
            return
        else:
            name = getlayergroupname(self)
            if name in bpy.data.node_groups:
                create_layer_node(self)
                return
        UpdateShader()

    def update_opacity(self, context):
        sock = self.opacity_socket.get_socket()
        if sock:
            sock.default_value = self.opacity

    def update_color(self, context):
        sock = self.color_socket.get_socket()
        if sock:
            sock.default_value = self.default_color

    def update_shader(self, context):
        if self.suppress_update:
            return
        UpdateShader()
    
    def texturetypechanged(self, context):
        if self.suppress_update:
            return

        if self.texture_type == "HEIGHT":
            suppress_update = True
            self.blend_mode = "ADD"
            suppress_update = False
        check_attach(self,context)
        UpdateShader()
    
    def get_node_groups(self, context):
        prefixes_to_check = ['DIFFUSE_Group', 'METALLIC_Group', 'ROUGHNESS_Group', 'EMISSION_Group', 'ALPHA_Group', 'NORMAL_Group', 'HEIGHT_Group']
        items = [(group.name, group.name, "") for group in bpy.data.node_groups if not any(group.name.startswith(prefix) for prefix in prefixes_to_check)]
        return items
    
    def get_texture_types(self, context):
        return getusedmaps()

    id: StringProperty(
        name="ID",
        default="empty"
    )
    blend_mode: EnumProperty(
        name="Blend Mode",
        items=BLEND_MODES,
        description="Blend mode for mixing layers",
        default="MIX",
        update=update_layer
    )
    texture_type: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        update=texturetypechanged
    )
    opacity: FloatProperty(
        name="Opacity",
        description="Opacity of the layer",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_opacity
    )
    #mask_value: PointerProperty(type=SocketReference)
    mask_value: BoolProperty(default = False, name = "MaskBase", update=update_layer)
    opacity_socket: PointerProperty(type=SocketReference)

    use_layer: BoolProperty(
        name="Use Layer",
        description="Toggle layer visibility",
        default=True,
        update=update_shader
    )
    collapse_box: BoolProperty(default = False, name = "Compact Layer")

    def update_on_image(self, context):
        if self.suppress_update:
            return
        UpdateShader()

    resource: PointerProperty(type=ResourceProperty)
    expand_filters: BoolProperty(default = True)
    expand_sublayers: BoolProperty(default = True)
    lock: BoolProperty(default = False)
    mask: BoolProperty()
    node_name: StringProperty(
        default="",
        name="Node",
        description="Name of the node",
    )
    def renamebuttonupdate(self, context):
        self.renamebutton = False
    layer_name: StringProperty(
        default="",
        name="Layer name",
        description="Layer Name",
        update = renamebuttonupdate
    )
    attachedto: StringProperty(
        default="",
        name="Attached To Layer",
    )
    filters: CollectionProperty(type=FilterProperty)
    
    filter_show: BoolProperty(
        name="ShowFilters",
        description="Toggle Filters Visibility",
        default=True,
    )
    index: IntProperty()

    sub_layers: CollectionProperty(type=LayerReference)

    layer_type: EnumProperty(
        name="Layer Type",
        items=[
            ('SIMPLE', "", ""),
            ('PBR', "", ""),
            ('FILL', "", ""),
            ('FOLDER', "", ""),
        ],
        default='SIMPLE',
    )
    sort_color: StringProperty(default = "PANEL_CLOSE")

    renamebutton: BoolProperty()
    suppress_update: BoolProperty()

class TextureTypeProp(PropertyGroup):
    def get_texture_types(self, context):
        tt = [ts for ts in TEXTURE_TYPE]
        tt.append(("EMPTY", "Empty", ""))
        return tt
    expand: BoolProperty(default = True)
    save_name: StringProperty(
        name="Save Name",
        default="Map",
        description="Name for saving texture",
    )

    type: EnumProperty(
        name="Alpha Type",
        items=[
            ('RGB', "RGB", ""),
            ('RGBA', "RGBA", ""),
            ('RGB_A', "RGB+A", ""),
            ('R_G_B_A', "R+G+B+A", ""),
            ('R', "R", ""),
        ],
        default='RGB',
    )
    RGB: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )
    RGBA: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )
    R: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )
    G: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )
    B: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )
    A: EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        default = 8
    )

class OtherProps(PropertyGroup):

    def update_layer(self, context):
        UpdateShader()

    image: PointerProperty(
        name="Image",
        type=bpy.types.Image
    )

    expand_area_MtlSettings: BoolProperty(
        name="Expand Material Settings",
    )
    expand_area_Actions: BoolProperty(
        name="Expand Actions",
    )
    expand_area_Saving: BoolProperty(
        name="Expand Saving",
    )
    expand_area_Materials: BoolProperty(
        name="Expand Materials",
    )
    expand_area_CreateLayer: BoolProperty(
        name="Create layer options",
    )
    expand_area_MaterialCollection: BoolProperty(
        name="Material collection",
    )
    expand_area_ProjectTexture: BoolProperty(
        name="Projection",
    )
    expand_area_QuickEdit: BoolProperty(
        name="QuickEdit",
    )
    expand_area_PaintTools: BoolProperty(
        name="Paint Tools",
    )
    expand_area_Bake: BoolProperty(
        name="Bake",
    )
    expand_area_DepthSelection: BoolProperty(
        name="Depth Selection",
    )
    expand_area_FolderHidePJ: BoolProperty(
        name="Hide folder",
    )
    expand_area_butlayers: BoolProperty(
        name="Layers",
        default = True
    )
    expand_area_butfile: BoolProperty(
        name="File",
        default = True
    )
    expand_area_buttools: BoolProperty(
        name="Tools",
        default = True
    )
    expand_area_butmtl: BoolProperty(
        name="Material",
        default = True
    )
    expand_area_Brushes: BoolProperty(
        name="Brushes",
    )
    expand_area_Prefs: BoolProperty(
        name="Preferences",
    )
    expand_area_DefaultMaterial: BoolProperty(
        name="Default Material",
    )
    bakemtl: PointerProperty(
        name="Bake Mtl",
        type=bpy.types.Material
    )
    save_path: StringProperty(
        name="Save Path",
        default="",
        description="Folder for texture export",
        subtype='DIR_PATH',
    )
    currentprefix: StringProperty(
        name="Prefix",
        default="",
        description="Prefix that will be used for exporting textures",
    )
    height_to_normal: BoolProperty(
        name="Bake height to normal",
        default=True,
    )
    invert_green_n: BoolProperty(
        name="Invert G channel for Normal",
        default=False,
    )
    layercombineactive: BoolProperty(
        name="LayerCombineActive",
        default=False,
    )
    toggle_save: BoolProperty(
        name="Save textures with file",
        default=True,
    )
    screen_capture_scale: FloatProperty(
        name="Screen capture scale",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Scale capture scale"
    )
    screen_grab_size_y: IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Height of the screen grab"
    )
    screen_grab_size_x: IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Width of the screen grab"
    )
    new_texture_type_name: StringProperty(name="Name", default="")
    new_texture_type_label: StringProperty(name="Label", default="")
    new_texture_type_description: StringProperty(name="Description", default="")
    tempsavingdir: StringProperty(
        name="Save Projection Image Directory",
        description="Directory for images used in projection",
        default=bpy.app.tempdir,
        subtype='DIR_PATH'
    )
    preview_mode: EnumProperty(
        name="Preview Mode",
        items=[
            ('COMBINED', "Combined", ""),
            (None),
            ('DIFFUSE', "Diffuse", ""),
            ('ROUGHNESS', "Roughness", ""),
            ('METALLIC', "Metallic", ""),
            ('HEIGH', "Heigh", ""),
            ('NORMAL', "Normal", ""),
        ],
        default='COMBINED',
        update=update_layer
    )

    preview_image: PointerProperty(
        name="Image",
        type=bpy.types.Image
    )
    fixed: BoolProperty()
    brushes: CollectionProperty(type=Brushes)
    brush_size: FloatProperty(default = 20.0)
    HistogramRefs: CollectionProperty(type=HistrogramReference)

    inbufferfilter: StringProperty()
    emptyprop: BoolProperty()
    exportprops: CollectionProperty(type=TextureTypeProp)
    usedids: StringProperty()
    search: StringProperty()

class DebugPlaneProps(PropertyGroup):
    depth_distance: FloatProperty(
        name="Depth Distance",
        description="Distance from the view for depth mask selection",
        default=3.0,
        min=0.1
    )
    show_plane: BoolProperty(
        name="Show Plane",
        description="Toggle plane visibility",
        default=False
    )
    plane_color: FloatVectorProperty(
        name="Plane Color",
        description="Color of the plane (RGBA)",
        subtype='COLOR',
        size=4,
        default=(0.0, 0.15, 0.22, 0.25),
        min=0.0,
        max=1.0
    )
    plane_size: FloatProperty(
        name="Plane Size",
        description="Size of the plane",
        default=1.0,
        min=0.1,
        max=10.0
    )

class BakeMapSettings(PropertyGroup):

    type: EnumProperty(
        name="Bake Type",
        items = BAKE_TYPE,
        default='AO',
        update=lambda self, context: self.update_layer_action(context)
    )
    image: PointerProperty(
        name="Image",
        type=bpy.types.Image, 
    )
    use_map: BoolProperty(name="Bake Map", default=True)
    aodist: FloatProperty(default = 1.0, min = 0.0, max = 100.0)
    heightdist: FloatProperty(default = 1.0, min = 0.0)
    heightoffset: FloatProperty(default = 0.0)
    subd: IntProperty(default = 0, min = 0, max = 6)
    smsubd: BoolProperty(default = False)
  
class ObjectsColProperty(PropertyGroup):
    def Upd(self, context):
        part = get_material_collection()
        if not self.obj:
            
            for i, m in enumerate(part.baking_props.high_poly_obj):
                if self.obj == m.obj:
                    part.baking_props.high_poly_obj.remove(i)
                    break
            for i, m in enumerate(part.baking_props.low_poly_obj):
                if self.obj == m.obj:
                    part.baking_props.low_poly_obj.remove(i)
                    break
        if self.suppress_update:
            return
        self.suppress_update = True

        for i, m in enumerate(part.baking_props.high_poly_obj):
            if not m.obj:
                part.baking_props.high_poly_obj.remove(i)
        for i, m in enumerate(part.baking_props.low_poly_obj):
            if not m.obj:
                part.baking_props.low_poly_obj.remove(i)
        
        seen_high = set()
        for i in reversed(range(len(part.baking_props.high_poly_obj))):
            obj = part.baking_props.high_poly_obj[i].obj
            if obj in seen_high:
                part.baking_props.high_poly_obj.remove(i)
            else:
                seen_high.add(obj)

        seen_low = set()
        for i in reversed(range(len(part.baking_props.low_poly_obj))):
            obj = part.baking_props.low_poly_obj[i].obj
            if obj in seen_low:
                part.baking_props.low_poly_obj.remove(i)
            else:
                seen_low.add(obj)
        
        part.baking_props.high_poly_obj.add()
        part.baking_props.low_poly_obj.add()

        self.suppress_update = False

    suppress_update: BoolProperty()
    obj: PointerProperty(type=bpy.types.Object, update = Upd)

class BakingProperties(PropertyGroup):
    def hidehp(self, context):
        for ob in self.gethpobjects(context):
            ob.hide_set(not self.visible_hp)
    def hidelp(self, context):
        for ob in self.getlpobjects(context):
            ob.hide_set(not self.visible_lp)
    def hidecage(self, context):
        if self.cage:
            self.cage.hide_set(not self.visible_cage)
    def gethpobjects(self,context):
        objs = []
        for ob in self.high_poly_obj:
            if ob.obj:
                objs.append(ob.obj)
        return objs
    def getlpobjects(self,context):
        objs = []
        for ob in self.low_poly_obj:
            if ob.obj:
                objs.append(ob.obj)
        return objs
    bake_image_sizeY: IntProperty(
        name="Bake Image Size",
        description="Size of the bake image for all maps",
        default=1024,
        min=16,
        max=8192
    )
    bake_image_sizeX: IntProperty(
        name="Bake Image Size",
        description="Size of the bake image for all maps",
        default=1024,
        min=16,
        max=8192
    )
    smooth_cage: BoolProperty(
        name="Smooth Cage",
        description="Make the cage smooth shaded",
        default=True,
        update=lambda self, context: create_or_update_cage(context)
    )
    expand_hp: BoolProperty()
    expand_lp: BoolProperty()
    visible_hp: BoolProperty(default = True, update = hidehp)
    visible_lp: BoolProperty(default = True, update = hidelp)
    visible_cage: BoolProperty(default = True, update = hidecage)
    high_poly_obj: CollectionProperty(
        name="High Poly Object",
        description="Select the high poly object",
        type=ObjectsColProperty,
    )
    low_poly_obj: CollectionProperty(
        name="Low Poly Object",
        description="Select the low poly object",
        type=ObjectsColProperty
    )
    use_cage: BoolProperty(
        name="Use Cage",
        description="Automatically create cage with depth offset",
        default=False,
        update=lambda self, context: create_or_update_cage(context)
    )
    cage: PointerProperty(type=bpy.types.Object)
    cage_depth: FloatProperty(
        name="Cage Depth",
        description="Depth offset for cage using displacement modifier",
        default=0.1,
        min=0.0,
        max=10.0,
        update=lambda self, context: update_cage_depth(context)
    )
    cage_color: FloatVectorProperty(
        name="Cage Color",
        description="Color of the cage material",
        subtype='COLOR',
        size=4, 
        default=(0.1, 0.5, 0.6, 0.08),
        min=0.0,
        max=1.0,
        update=lambda self, context: update_cage_material(context)
    )
    cage_alpha: FloatProperty(
        name="Cage Alpha",
        description="Alpha transparency of the cage material",
        default=0.2,
        min=0.0,
        max=1.0,
        update=lambda self, context: update_cage_material(context)
    )
    samples: IntProperty(
        name="Bake Samples",
        default=12,
        min=1,
        max=8192
    )

class HASMaterialProperties(PropertyGroup):
    def update_layer(self, context):
        UpdateShader()
    layers: CollectionProperty(type=LayerProperties)
    sublayers: CollectionProperty(type=LayerProperties)
    
    base_layers: CollectionProperty(type=LayerReference)

    material: PointerProperty(
        name="Material",
        type=bpy.types.Material
    )
    name: StringProperty(
        default="Set",
        name="Set name",
    )
    shader_type: EnumProperty(
        name="Shader Type",
        items=[
            ('PRINCIPLED', "Principled BSDF", "Use Principled BSDF shader", "SHADING_RENDERED", 0),
            ('UNLIT', "Unlit", "Use Unlit shader", "SHADING_SOLID", 1),
            ('Custom', "Custom", "Use Custom shader", "SHADING_TEXTURE", 2),
        ],
        default='PRINCIPLED',
        update=update_layer
    )
    uvs: StringProperty(
        default="",
        name="UVs",
        description="Name of the UVs attribute",
        update=update_layer
    )
    height_intensity: FloatProperty(
        name="Height instensity",
        default=1.0,
        update=update_layer
    )
    bake_maps: CollectionProperty(type=BakeMapSettings)

    baking_props: PointerProperty(type=BakingProperties)
    
    texture_sizeX: IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )
    texture_sizeY: IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )

    opacity_mode: EnumProperty(
        name="Opacity Mode",
        items=[
            ('OPAQUE', "Opaque", ""),
            ('BLEND', "Blend", ""),
            ('HASHED', "Hashed", ""),
            ('CLIP', "Clip", ""),    
        ],
        default='OPAQUE',
        update=update_layer
    )
    diffusealpha: BoolProperty(
        default=False,
        name="Diffuse Transparency",
        description="Use Diffuse alpha for opacity",
        update=update_layer
    )
    used_maps: PointerProperty(type=UsedMaps)

    def update_mtl_action(self, context):
        if self.mtl_actions == 'COMBINELAYERS':
            self.combine_layers(context)
        elif self.mtl_actions == 'RESIZEALL':
            self.resize_all(context)
        elif self.mtl_actions == 'DELETEALL':
            self.delete_all_layers(context)
        elif self.mtl_actions == 'FIXSCENE':
            self.fixscene(context)
    def combine_layers(self, context):

        bpy.ops.haspaint.combine_all_layers('INVOKE_DEFAULT')
    def resize_all(self, context):
        bpy.ops.haspaint.resize_layers('INVOKE_DEFAULT')
    def delete_all_layers(self, context):
        bpy.ops.haspaint.delete_layers('INVOKE_DEFAULT')
    def fixscene(self, context):
        bpy.ops.haspaint.setupscene('INVOKE_DEFAULT')
        
    mtl_actions: EnumProperty(
        name="Layer Action",
        items=[
            ('COMBINELAYERS', "Combine Layers", "Combine Layers","NODE_COMPOSITING",0),
            ('RESIZEALL', "Resize All Layers", "Resize All Layers","MOD_EDGESPLIT",1),
            (None),
            ('FIXSCENE', "Setup Scene", "Setup current scene","SCENE_DATA",3),
            (None),
            ('DELETEALL', "Delete All Layers", "Remove all layers","TRASH",2),
        ],
        default='COMBINELAYERS',
        update=lambda self, context: self.update_mtl_action(context)
    )
    addtofolder: StringProperty()
    selected_layer: StringProperty()
    selected_alpha: BoolProperty()
    InvertG: BoolProperty(default = False, update=update_layer)
    move_layer: IntProperty()
    node: StringProperty()
    texture_filtering: EnumProperty(
        name="Texture filtering",
        items= TEXTURE_FILTER,
        default='Cubic',
        update=update_layer
    )
    colorfix: BoolProperty(default = True, update = update_layer)
class ViewData(PropertyGroup):
    image_name: StringProperty()
    image_path: StringProperty()
    render_sizeX: IntProperty()
    render_sizeY: IntProperty()
    crop_startX: IntProperty()
    crop_startY: IntProperty()
    crop_endX: IntProperty()
    crop_endY: IntProperty()
    view: StringProperty()
    loc: FloatVectorProperty(
        name="Location",
        description="Location of the camera",
        default=(0.0, 0.0, 0.0),  
        size=3, 
        subtype='TRANSLATION'
    )
    rot: FloatVectorProperty(
        name="Rotation",
        description="Rotation of the camera",
        default=(0.0, 0.0, 0.0),
        size=3, 
        subtype='EULER'
    )
    ortho: BoolProperty(default=False)
    ortho_scale: FloatProperty()
    focal: FloatProperty()

###
### Presets
###

preset_folder = bpy.utils.user_resource('SCRIPTS',path=  "presets/haspresets/savedpresets", create=False)
if not os.path.exists(preset_folder):
    os.makedirs(preset_folder)
initial_file = os.path.join(preset_folder, "Packed.py")
try:
    if not os.path.isfile(initial_file):
        with open(initial_file, "w") as f:
            f.write("import bpy\n")
            f.write("scene = bpy.context.scene\n")
            f.write("op = bpy.context.scene.other_props.exportprops\n")

            f.write("scene.other_props.height_to_normal = True\n")
            f.write("scene.other_props.invert_green_n = False\n")
            f.write("op[0].type = 'RGB_A'\n")
            f.write("op[0].RGB = 'DIFFUSE'\n")
            f.write("op[0].R = 'METALLIC'\n")
            f.write("op[0].G = 'ROUGHNESS'\n")
            f.write("op[0].B = 'HEIGHT'\n")
            f.write("op[0].A = 'ALPHA'\n")
            f.write("op[0].save_name = '(mtl)_Diffuse'\n")
            f.write("op[1].type = 'R_G_B_A'\n")
            f.write("op[1].RGB = 'ROUGHNESS'\n")
            f.write("op[1].R = 'ROUGHNESS'\n")
            f.write("op[1].G = 'METALLIC'\n")
            f.write("op[1].B = 'AO'\n")
            f.write("op[1].A = 'EMPTY'\n")
            f.write("op[1].save_name = '(mtl)_RMO'\n")
            f.write("op[2].type = 'RGB'\n")
            f.write("op[2].RGB = 'NORMAL'\n")
            f.write("op[2].R = 'EMPTY'\n")
            f.write("op[2].G = 'EMPTY'\n")
            f.write("op[2].B = 'EMPTY'\n")
            f.write("op[2].A = 'EMPTY'\n")
            f.write("op[2].save_name = '(mtl)_Normal'\n")
except (OSError, PermissionError) as e:
    print(f"Failed to create or write to the file: {e}")
initial_file = os.path.join(preset_folder, "PBR.py")
try:
    if not os.path.isfile(initial_file):
        with open(initial_file, "w") as f:
            f.write("import bpy\n")
            f.write("scene = bpy.context.scene\n")
            f.write("op = bpy.context.scene.other_props.exportprops\n")

            f.write("scene.other_props.height_to_normal = True\n")
            f.write("scene.other_props.invert_green_n = False\n")
            f.write("op[0].type = 'RGB'\n")
            f.write("op[0].RGB = 'DIFFUSE'\n")
            f.write("op[0].R = 'METALLIC'\n")
            f.write("op[0].G = 'ROUGHNESS'\n")
            f.write("op[0].B = 'HEIGHT'\n")
            f.write("op[0].A = 'DIFFUSE'\n")
            f.write("op[0].save_name = '(mtl)_Diffuse'\n")
            f.write("op[1].type = 'R'\n")
            f.write("op[1].RGB = 'ROUGHNESS'\n")
            f.write("op[1].R = 'METALLIC'\n")
            f.write("op[1].G = 'ROUGHNESS'\n")
            f.write("op[1].B = 'EMPTY'\n")
            f.write("op[1].A = 'EMPTY'\n")
            f.write("op[1].save_name = '(mtl)_Roughness'\n")
            f.write("op[2].type = 'R'\n")
            f.write("op[2].RGB = 'METALLIC'\n")
            f.write("op[2].R = 'EMPTY'\n")
            f.write("op[2].G = 'EMPTY'\n")
            f.write("op[2].B = 'EMPTY'\n")
            f.write("op[2].A = 'EMPTY'\n")
            f.write("op[2].save_name = '(mtl)_Metallic'\n")
            f.write("op[3].type = 'RGB'\n")
            f.write("op[3].RGB = 'NORMAL'\n")
            f.write("op[3].R = 'EMPTY'\n")
            f.write("op[3].G = 'EMPTY'\n")
            f.write("op[3].B = 'EMPTY'\n")
            f.write("op[3].A = 'EMPTY'\n")
            f.write("op[3].save_name = '(mtl)_Normal'\n")
except (OSError, PermissionError) as e:
    print(f"Failed to create or write to the file: {e}")
initial_file = os.path.join(preset_folder, "ColorOnly.py")
try:
    if not os.path.isfile(initial_file):
        with open(initial_file, "w") as f:
            f.write("import bpy\n")
            f.write("scene = bpy.context.scene\n")
            f.write("op = bpy.context.scene.other_props.exportprops\n")

            f.write("scene.other_props.height_to_normal = True\n")
            f.write("scene.other_props.invert_green_n = False\n")
            f.write("op[0].type = 'RGB'\n")
            f.write("op[0].RGB = 'DIFFUSE'\n")
            f.write("op[0].R = 'EMPTY'\n")
            f.write("op[0].G = 'EMPTY'\n")
            f.write("op[0].B = 'EMPTY'\n")
            f.write("op[0].A = 'EMPTY'\n")
            f.write("op[0].save_name = '(mtl)_Color'\n")
except (OSError, PermissionError) as e:
    print(f"Failed to create or write to the file: {e}")
class OT_AddMyPreset(AddPresetBase, Operator):
    bl_idname = 'haspaint.add_preset'
    bl_label = 'Add A preset'
    preset_menu = 'PR_MT_HASPresets'
    bl_options = {'REGISTER', 'UNDO'}

    preset_defines = [
        'scene = bpy.context.scene',
        'op = bpy.context.scene.other_props.exportprops',
    ]

    preset_values = [
        'scene.other_props.height_to_normal',
        'scene.other_props.invert_green_n',
    ]

    preset_subdir = 'haspresets/savedpresets'

    def execute(self, context):
        self.preset_values = [
            'scene.other_props.height_to_normal',
            'scene.other_props.invert_green_n',
        ]

        for idx, item in enumerate(context.scene.other_props.exportprops):
            self.preset_values.extend([
                f'op[{idx}].type',
                f'op[{idx}].RGB',
                f'op[{idx}].R',
                f'op[{idx}].G',
                f'op[{idx}].B',
                f'op[{idx}].A',
                f'op[{idx}].save_name',
            ])
        return super().execute(context)
        
class PR_MT_HASPresets(Menu):
    bl_idname = 'PR_MT_HASPresets'
    bl_label = 'My Presets'
    preset_subdir = 'haspresets/savedpresets'
    preset_operator = 'haspaint.execute_preset_has'
    draw = Menu.draw_preset

class ExecutePreset(Operator):
    """Execute a preset"""
    bl_idname = "haspaint.execute_preset_has"
    bl_label = "Execute a Python Preset"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: StringProperty(
        subtype='FILE_PATH',
        options={'SKIP_SAVE'},
    )
    menu_idname: StringProperty(
        name="Menu ID Name",
        description="ID name of the menu this was called from",
        options={'SKIP_SAVE'},
    )

    def execute(self, context):
        from os.path import basename, splitext
        filepath = self.filepath

        preset_class = getattr(bpy.types, 'PR_MT_HASPresets')
        preset_class.bl_label = bpy.path.display_name(basename(filepath))

        ext = splitext(filepath)[1].lower()

        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "unknown filetype: %r" % ext)
            return {'CANCELLED'}

        if hasattr(preset_class, "reset_cb"):
            preset_class.reset_cb(context)

        with open(filepath, 'r') as file:
            lines = file.readlines()

        texture_props_lines = [line for line in lines if 'exportprops' in line]
        while len(context.scene.other_props.exportprops) > 0:
            context.scene.other_props.exportprops.remove(0)

        last_line = lines[-1]

        match = re.search(r'\[(\d+)\]', last_line)

        if match:
            number = int(match.group(1))

        for n in range(number+1):
            context.scene.other_props.exportprops.add()

        if ext == ".py":
            try:
                bpy.utils.execfile(filepath)
            except Exception as ex:
                self.report({'ERROR'}, "Failed to execute the preset: " + repr(ex))

        elif ext == ".xml":
            import rna_xml
            rna_xml.xml_file_run(context,
                                 filepath,
                                 preset_class.preset_xml_map)

        if hasattr(preset_class, "post_cb"):
            preset_class.post_cb(context)

        return {'FINISHED'}

class AddTextureTypeProp(Operator):
    bl_idname = "haspaint.add_texture_type_prop"
    bl_label = "Add Texture Type"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        context.scene.other_props.exportprops.add()
        return {'FINISHED'}

class TEXTURE_PT_file_browser_panel(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "HAS Export Textures"
    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        return (
            space_data.type == 'FILE_BROWSER' and
            space_data.params is not None and
            space_data.active_operator and
            space_data.active_operator.bl_idname == "HASPAINT_OT_export_textures"
        )

    def draw(self, context):
        layout = self.layout
        other_props = context.scene.other_props

        box = layout.box()

        row = box.row(align=True)
        row.menu("PR_MT_HASPresets", text="Template Presets", icon='COLLAPSEMENU')
        row.operator("haspaint.add_preset", text="", icon='ADD')
        row.operator("haspaint.add_preset", text="", icon='REMOVE').remove_active = True
        
        boxd = box.box()
        boxd.prop(other_props, "height_to_normal", text="Height to Normal")
        boxd.prop(other_props, "invert_green_n", text="Normal Invert G Channel")

        boxd = box.box()
        boxd.label(text="Allowed properties: (obj), (mtl), (file), (set)")
        row = boxd.row(align=True)
        row.label(text="Pack Images")
        for idx, item in enumerate(context.scene.other_props.exportprops):
            boxq = boxd.box()
            row = boxq.row(align=True)
            row.prop(item, 'expand', text = "", toggle = True, icon = "TRIA_DOWN" if item.expand else "TRIA_RIGHT")
            row.prop(item, "save_name", text="")
            row.operator("haspaint.remove_texture_type_prop", text="", icon='X').index = idx
            if item.expand:
                row = boxq.column(align=True)
                row.prop(item, "type", text="")
                if item.type == "RGB":
                    row.prop(item, "RGB", text="RGB")
                elif item.type == "RGBA":
                    row.prop(item, "RGBA", text="RGBA")
                elif item.type == "RGB_A":
                    row.prop(item, "RGB", text="RGB")
                    row.prop(item, "A", text="A")
                elif item.type == "R_G_B_A":
                    row.prop(item, "R", text="R")
                    row.prop(item, "G", text="G")
                    row.prop(item, "B", text="B")
                    row.prop(item, "A", text="A")
                elif item.type == "R":
                    row.prop(item, "R", text="R")
        box.operator("haspaint.add_texture_type_prop", text="Add Texture Type") 

###
### Other
###

class TextureSizeAddSubtract(Operator):
    bl_idname = "haspaint.texture_size_add_subtract"
    bl_label = "Add or subtract from texture size"
    bl_options = {'REGISTER', 'UNDO'}

    add: BoolProperty(name="AddSubtract", default=True)
    isbake: BoolProperty()
    
    def execute(self, context):
        part = get_material_collection()

        if self.isbake:
            size_x = part.baking_props.bake_image_sizeY
            size_y = part.baking_props.bake_image_sizeX
        else:
            size_x = part.texture_sizeX
            size_y = part.texture_sizeY

        if self.add:

            new_size_x = next_power_of_two(size_x + 1) if size_x else 2
            new_size_y = next_power_of_two(size_y + 1) if size_y else 2
        else:

            new_size_x = next_power_of_two(max(size_x - 1, 1))
            new_size_y = next_power_of_two(max(size_y - 1, 1))
            
            if new_size_x >= size_x:
                new_size_x = next_power_of_two(max(size_x // 2, 1))
            if new_size_y >= size_y:
                new_size_y = next_power_of_two(max(size_y // 2, 1))

        if self.isbake:

            part.baking_props.bake_image_sizeX = new_size_x
            part.baking_props.bake_image_sizeY = new_size_y
        else:
            part.texture_sizeX = new_size_x
            part.texture_sizeY = new_size_y

        return {'FINISHED'}

class SetupMaterial(Operator):
    bl_idname = "haspaint.setup_material"
    bl_label = "Setup Material"
    bl_options = {'REGISTER', 'UNDO'}
    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object:
            if active_object.active_material:
                mat = active_object.active_material
                mat.use_nodes = True
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                mat = bpy.data.materials.new(name=re.sub(r'[^A-Za-z0-9]', '', f"has{active_object.name}"))

                if active_object.material_slots:
                    active_material_index = active_object.active_material_index
                    active_material_slot = active_object.material_slots[active_material_index]
                    if active_material_slot.material is None:
                        active_material_slot.material = mat
                    else:
                        active_object.data.materials.append(mat)
                else:
                    active_object.data.materials.append(mat)
                mat.use_nodes = True

            part = bpy.context.scene.material_props.add()
            part.material = mat
            part.name = get_next_set_name()
            part.baking_props.high_poly_obj.add()
            part.baking_props.low_poly_obj.add()
        obj = active_object
        if not obj:
            return
        
        if not obj.material_slots:
            return
        
        material = obj.active_material
        if not material:
            return

        image_nodes = get_all_image_nodes_in_material(material)
        if image_nodes:
            part = get_material_collection()

            for node in image_nodes:
                layer_item = part.layers.add()
                layer_item.suppress_update = True
                layer_item.resource.suppress_update = True

                layer_item.resource.image = node.image

                layer_item.layer_name = newlayername()
                layer_item.id = shortid()
                part.base_layers.add().id = layer_item.id

                layer_item.suppress_update = False
                layer_item.resource.suppress_update = False

            bpy.ops.haspaint.select_texture()
            
            UpdateShader()

        return {'FINISHED'}
        return {'FINISHED'}

class HASRemoveMaterial(Operator):
    bl_idname = "haspaint.remove_material"
    bl_label = "Remove Material"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()
    def execute(self, context):
        context.scene.material_props.remove(self.index)
        return {'FINISHED'}

class WM_OT_OpenWebsite(Operator):
    bl_idname = "haspaint.open_website"
    bl_label = "Help"
    bl_description = "Open Documentation for HAS Paint Layers"
    link: StringProperty()
    def execute(self, context):
        webbrowser.open(self.link)
        return {'FINISHED'}

###
### Baking
###

class AddBakeMap(Operator):
    bl_idname = "haspaint.add_bake_map"
    bl_label = "Add Bake map"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        part = get_material_collection()
        baking_props = part.baking_props
        part.bake_maps.add()

        return {'FINISHED'}

class RemoveBakeMap(Operator):
    bl_idname = "haspaint.remove_bake_map"
    bl_label = "Remove Bake map"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        baking_props = part.baking_props
        part.bake_maps.remove(self.index)

        return {'FINISHED'}

class ExportTextures(Operator):
    bl_idname = "haspaint.export_textures"
    bl_label = "Export Textures"

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.exr;*.hdr",
        options={'HIDDEN'}
    )

    def execute(self, context):
        part = get_material_collection()
        if not part:
            return {'FINISHED'}
        elif not part.layers:
            return {'FINISHED'}
        directory = os.path.dirname(self.filepath)
        user_filename = os.path.basename(self.filepath)
        otps = context.scene.other_props
        otps.save_path = directory
        otps.currentprefix = user_filename

        basescene = bpy.context.window.scene
        usedtypes = getusedtypes()

        layers = get_layers(part.base_layers)

        mtlname = getmaterialgroupname(part)
        obj_name = bpy.context.active_object.name
        file_name = os.path.basename(bpy.data.filepath) if bpy.data.filepath else "untitled"
        set_name = part.name
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        if part.uvs:
            old_uv = plane.data.uv_layers[0]
            new_uv = plane.data.uv_layers.new(name=part.uvs)

        tree = material.node_tree
        if mtlname in bpy.data.node_groups:
            node_group = bpy.data.node_groups[mtlname]
        has_mtl = tree.nodes.new('ShaderNodeGroup')
        has_mtl.node_tree = node_group
        props = otps.exportprops
        if not otps.exportprops:

            pr = otps.exportprops.add()
            pr.type = 'RGB'
            pr.RGB = 'DIFFUSE'
            pr.save_name = '(mtl)_Color'
        if otps.exportprops:
            for textype in otps.exportprops:
                if textype.A:
                    alpha_name = gettexturelabel(textype.A)
                clear_socket_links(colorfix, 0)
                clear_socket_links(colorfix, 1)
                clear_socket_links(colorfix, 2)
                clear_socket_links(alphasocket.node, 0)
                alphafrom = None
                alphabake = False
                set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                alphasocket.default_value = 1.0
                if textype.type == "RGB":
                    type_name = gettexturelabel(textype.RGB)

                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    #has_mtl.inputs["Normal"].default_value = (0.0,0.0,0.0,0.0)

                    if type_name == 'Normal':
                        invnrmnode = create_node(tree,'ShaderNodeGroup', -200,-200, "cus", InvertNormalNode().name) if otps.invert_green_n else None

                        gamma = create_node(tree,'ShaderNodeGamma', -200,0, "", '')
                        set_default(gamma,1, 2.4)
                        tree.links.new(has_mtl.outputs[f'RawNormal'], gamma.inputs[0])
                        tree.links.new(gamma.outputs[0], colorfix.inputs[1])
                        if invnrmnode:
                            tree.links.new(gamma.outputs[0], invnrmnode.inputs['Normal'])
                            tree.links.new(invnrmnode.outputs['Normal'], colorfix.inputs[1])
                        #seprgb = create_node(tree,'ShaderNodeSeparateRGB', -600,0, "", "")
                        #nrmlznd = create_node(tree,'ShaderNodeVectorMath', -600,0, "op", "NORMALIZE")
                        if otps.height_to_normal:
                            subt = create_node(tree,'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
                            set_default(subt, 0, 1.0)
                            bump = create_node(tree,'ShaderNodeBump', -600,0, "", "")
                            set_default(bump, 0, part.height_intensity)
                            nrmnd = create_node(tree,'ShaderNodeNormalMap', -600,0, "", "")

                            scre = create_node(tree,'ShaderNodeMixRGB', -600,0, "mix", "SCREEN")
                            set_default(scre, 0, 1.0)

                            tree.links.new(has_mtl.outputs["Height"], bump.inputs[2])
                            tree.links.new(bump.outputs[0], subt.inputs[1])
                            tree.links.new(nrmnd.outputs[0], subt.inputs[2])
                            tree.links.new(subt.outputs[0], scre.inputs[1])
                            #tree.links.new(has_mtl.outputs[f'RawNormal'], scre.inputs[2])
                            tree.links.new(has_mtl.outputs[f'RawNormal'], gamma.inputs[0])
                            tree.links.new(gamma.outputs[0], scre.inputs[2])
                            if invnrmnode:
                                tree.links.new(gamma.outputs[0], invnrmnode.inputs['Normal'])
                                tree.links.new(invnrmnode.outputs['Normal'], scre.inputs[2])
                            emis = get_node_by_name(tree,"Emission")
                            if emis:
                                tree.links.new(scre.outputs[0], emis.inputs[0])

                elif textype.type == "RGBA":
                    type_name = gettexturelabel(textype.RGBA)
                    #mixs = get_node_by_name(tree,"Mix Shader")
                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], colorfix.inputs[2])
                    tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], alphasocket)
                    #tree.links.new(has_mtl.outputs[f'{type_name}Alpha'], alphasocket)
                    
                    #alphafrom = has_mtl.outputs[f'{type_name}Alpha']
                    #alphabake = False
                elif textype.type == "RGB_A":
                    type_name = gettexturelabel(textype.RGB)
                    #alpha_name = gettexturelabel(textype.A)

                    tree.links.new(has_mtl.outputs[f'{type_name}'], colorfix.inputs[1])
                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                    #tree.links.new(has_mtl.outputs[f'{alpha_name}'], alphasocket)
                    if alpha_name in has_mtl.outputs:
                        alphafrom = has_mtl.outputs[f'{alpha_name}']
                        alphabake = True
                elif textype.type == "R_G_B_A":
                    R = gettexturelabel(textype.R)
                    G = gettexturelabel(textype.G)
                    B = gettexturelabel(textype.B)
                    A = gettexturelabel(textype.A)
                    Combine = create_node(material.node_tree,'ShaderNodeCombineRGB', 50,300, "", "")
                    
                    tree.links.new(has_mtl.outputs[f'{R}'], Combine.inputs[0])
                    tree.links.new(has_mtl.outputs[f'{G}'], Combine.inputs[1])
                    tree.links.new(has_mtl.outputs[f'{B}'], Combine.inputs[2])
                    #tree.links.new(has_mtl.outputs[f'{A}'], alphasocket)

                    tree.links.new(Combine.outputs[0], colorfix.inputs[1])
                    if alpha_name in has_mtl.outputs:
                        alphafrom = has_mtl.outputs[f'{A}']
                        alphabake = True
                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))

                elif textype.type == "R":
                    
                    R = gettexturelabel(textype.R)
                    bw = create_node(material.node_tree,'ShaderNodeRGBToBW', 50,300, "", "")
                    
                    tree.links.new(has_mtl.outputs[f'{R}'], bw.inputs[0])
                    tree.links.new(bw.outputs[0], colorfix.inputs[1])

                    set_default(colorfix, 2, (1.0,1.0,1.0,1.0))
                    alphasocket.default_value = 1.0
                    alphabake = True
                image_name = generate_filename(textype.save_name, context, obj_name, mtlname, file_name, set_name)
                albake_image = None
                if alphabake and alphafrom:
                    saved_links = get_links(colorfix, 1)
                    tree.links.new(alphafrom, colorfix.inputs[1])
                    albake_image = bpy.data.images.new(f"{image_name}_alpha", part.texture_sizeX, part.texture_sizeY, alpha=True)
                    render_image(bake_scene, albake_image)  
                    set_links(saved_links,colorfix.inputs[1])
                    clear_socket_links(alphasocket.node, 0)
                bake_image = bpy.data.images.new(image_name, part.texture_sizeX, part.texture_sizeY, alpha=True)
                render_image(bake_scene, bake_image, alpha_bake = albake_image)    
                file_path = os.path.join(directory, bake_image.name + ".png")
                bake_image.filepath_raw = os.path.join(directory, basescene.other_props.currentprefix + bake_image.name + ".png")
                
                bake_image.save()

                bpy.data.images.remove(bake_image)
                if albake_image:
                    bpy.data.images.remove(albake_image)

        #cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene

        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class CollapseLayer(Operator):
    bl_idname = "haspaint.collapse_layer"
    bl_label = "Collapse layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')

    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        FoundLayer = part.layers[self.layer_index]
        suc = False
        bkimg = FoundLayer.resource.image
        if not bkimg:
            bkimg = create_bake_image(part.texture_sizeX,part.texture_sizeY, FoundLayer, suffix="")
        if bkimg:
            suc, bake_image = bake_layer(context, FoundLayer, basescene, bkimg)

        if suc:
            if bake_image:
                FoundLayer.resource.image = bkimg
                FoundLayer.filters.clear()
                FoundLayer.mask = False
                UpdateShader()
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
       
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CombineWithLayerBelowOperator(Operator):
    bl_idname = "haspaint.combine_with_layer_below"
    bl_label = "Combine with layer below"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    applyfilters: BoolProperty(default = True)
    applyfilters2: BoolProperty(default = False)

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if not layer:
            return
        if layer.attachedto:
            attl = get_layer_by_id(layer.attachedto)
            if attl:
                FoundLayer = get_layer_below(attl.sub_layers, layer.id)
        else:
            FoundLayer = get_layer_below(part.base_layers, layer.id)
        if not FoundLayer:
            layout.row().label(text=f"No Layer To Combine With")
            return 
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        layout.row().label(text=f"Combine current layer with {FoundLayer.layer_name}", icon='NODE_COMPOSITING')
        layout.row().label(text=f"Image {FoundLayer.resource.image.name}")
        layout.row().prop(self, "applyfilters", text="Apply Filters For Current layer", icon= "SHADERFX")
        layout.row().prop(self, "applyfilters2", text="Apply Filters For Layer Below", icon= "SHADERFX")
        
    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        index = -1
        CurrentLayer = part.layers[self.layer_index]
        layer = CurrentLayer
        attl=None
        if not layer:
            return
        if layer.attachedto:
            attl = get_layer_by_id(layer.attachedto)
            if attl:
                BelowLayer = get_layer_below(attl.sub_layers, layer.id)
        else:
            BelowLayer = get_layer_below(part.base_layers, layer.id)
    
        if not CurrentLayer or not BelowLayer:
            return {'CANCELLED'}
        if self.applyfilters:
            suc, bake_image = bake_layer(context, CurrentLayer, basescene, CurrentLayer.resource.image)

        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        tree, group_node = Add_layer(material, output_node, CurrentLayer)
        tree, below_group_node = Add_layer(material, output_node, BelowLayer)

        tree.links.new(below_group_node.outputs['Color'], group_node.inputs['Color'])
        tree.links.new(below_group_node.outputs['Alpha'], group_node.inputs['Alpha'])

        tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
        tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
        tree.links.new(group_node.outputs['Alpha'], alphasocket)

        render_image(bake_scene, BelowLayer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)
        bpy.context.window.scene = basescene

        if attl:
            remove_layer_ref(attl.sub_layers,CurrentLayer.id)
        else:
            remove_layer_ref(part.base_layers,CurrentLayer.id)

        UpdateShader()
        if suc:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
       
    def invoke(self, context, event):
        
        return context.window_manager.invoke_props_dialog(self)

class CombineAllLayersOperator(Operator):
    bl_idname = "haspaint.combine_all_layers"
    bl_label = "Combine All Layers"
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')

    def execute(self, context):
        bsmtl = hasmatnode()
        usdtypes = getusedtypes()
        basescene = bpy.context.window.scene
        part = get_material_collection()
        
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        group_node = material.node_tree.nodes.new('ShaderNodeGroup')
        group_node.node_tree = bsmtl
        imgs= []
        types= []

        tree = material.node_tree
        for type in usdtypes:
            nm = gettexturelabel(type)
            bake_image = bpy.data.images.new(nm, part.texture_sizeX, part.texture_sizeY, alpha=True)
            bake_image.alpha_mode = 'CHANNEL_PACKED'
            bake_image.colorspace_settings.name = 'sRGB'
            tree.links.new(group_node.outputs[f'{nm}'], colorfix.inputs[1])
            tree.links.new(group_node.outputs[f'{nm}Alpha'], colorfix.inputs[2])
            tree.links.new(group_node.outputs[f'{nm}Alpha'], alphasocket)

            render_image(bake_scene, bake_image)
            imgs.append(bake_image)
            types.append(type)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        part.base_layers.clear()
        
        for i, im in enumerate(imgs):
            layer_item = part.layers.add()
            layer_item.suppress_update = True
            layer_item.resource.suppress_update = True
            layer_item.resource.image = im
            layer_item.layer_name = newlayername()
            layer_item.id = shortid()

            part.base_layers.add().id = layer_item.id

            layer_item.suppress_update = False
            layer_item.resource.suppress_update = False
        SelectLayer(layer_item.id)

        UpdateShader()

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SnapshotLayer(Operator):
    bl_idname = "haspaint.snapshotlayer"
    bl_label = "Snapshot Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default = -1)
    filter_index: IntProperty(default = -1)
    addfilter: StringProperty()
    addfiltervalue: FloatProperty()
    def execute(self, context):

        part = get_material_collection()
        FoundLayer = part.layers[self.layer_index]
        suc = False
        if FoundLayer:
            if FoundLayer.filters:
                suc, bake_image = snapshot(context, FoundLayer, FoundLayer.filters[self.filter_index], adfilter = self.addfilter, adfilter_value = self.addfiltervalue)
                UpdateShader()

        if suc:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

def snapshot(context, FoundLayer, foundfilter, adfilter = "", adfilter_value = 0.0):
    part = get_material_collection()
    node_group = bpy.data.node_groups.get(f"{getlayergroupname(FoundLayer)}_filters")
    basescene = bpy.context.window.scene

    image_name = f"{foundfilter.id}_snapshot"

    bake_image = foundfilter.resource.image
    if not foundfilter.resource.image:
        bake_image = bpy.data.images.new(image_name, part.texture_sizeX, part.texture_sizeY, alpha=True)

    filter_node = get_node_by_name(node_group, foundfilter.node_name)
    output = get_node_by_name(node_group, "Group Output")

    bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

    node_group.links.new(filter_node.outputs['Pass'], output.inputs["Color"])
    node_group.links.new(filter_node.outputs['PassAlpha'], output.inputs["Alpha"])
    tree, group_node = Add_layer(material, output_node, FoundLayer)
    tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
    tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
    tree.links.new(group_node.outputs['Alpha'], alphasocket)

    render_image(bake_scene, bake_image, filter = adfilter, filter_value = adfilter_value)
    cleanup_bake_scene( bake_scene, material, plane)

    bpy.context.window.scene = basescene

    if True:
        foundfilter.resource.image = bake_image
    return True, bake_image
    
def BakeLayerToImage(self,context, layer):
    basescene = bpy.context.window.scene
    part = get_material_collection()
    bake_image = create_bake_image(part.texture_sizeX, part.texture_sizeY, layer, suffix=layer.resource.image.name)
    suc, bake_image = bake_layer(context, layer, basescene,bake_image)

    return bake_image

def bake_layer(context, layer, basescene, bake_image):

    FoundLayer = layer

    if FoundLayer:

        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)

        tree, group_node = Add_layer(material, output_node, FoundLayer)

        tree.links.new(group_node.outputs['Color'], colorfix.inputs[1])
        tree.links.new(group_node.outputs['Alpha'], colorfix.inputs[2])
        tree.links.new(group_node.outputs['Alpha'], alphasocket)

        render_image(bake_scene, bake_image)
        cleanup_bake_scene( bake_scene, material, plane)
        bpy.context.window.scene = basescene

        return True, bake_image
        
    else:
        return False, None

def setup_bake_scene(basescene):
    part = get_material_collection()

    new_scene = bpy.data.scenes.new("BakeScene")
    bpy.context.window.scene = new_scene
    material = bpy.data.materials.new(name="HASBakeMtlTemp")

    new_scene.render.resolution_y = part.texture_sizeX
    new_scene.render.resolution_x = part.texture_sizeY

    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    material.blend_method = 'BLEND'
    new_scene.render.film_transparent = True
    new_scene.view_layers["ViewLayer"].use_pass_combined = False
    new_scene.view_layers["ViewLayer"].use_pass_emit = True
    new_scene.view_settings.view_transform = 'Standard'
    new_scene.render.image_settings.color_mode = 'RGBA'
    new_scene.render.image_settings.color_depth = '16'
    new_scene.render.image_settings.compression = 0
    
    new_scene.render.engine = 'BLENDER_EEVEE_NEXT' if is_4_2_or_newer else 'BLENDER_EEVEE'
    new_scene.render.dither_intensity = 0
    new_scene.render.filter_size = 0

    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
        else:
            tree.nodes.remove(node)

    if 'output_node' not in locals():
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (200, 0)

    MixShader = tree.nodes.new('ShaderNodeMixShader')
    MixShader.location = (200, 0)
    MixRGB = create_node(tree,'ShaderNodeMixRGB', -200,0, "mix", 'DIVIDE')

    set_default(MixRGB, 0, 1.0)
    Transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
    Transparent.location = (200, 0)
    Emission = tree.nodes.new('ShaderNodeEmission')
    Emission.location = (200, 0)

    tree.links.new(MixRGB.outputs[0], Emission.inputs[0])
    tree.links.new(Transparent.outputs[0], MixShader.inputs[1])
    tree.links.new(Emission.outputs[0], MixShader.inputs[2])
    tree.links.new(MixShader.outputs[0], output_node.inputs[0])

    sftext = bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    sftext = bpy.context.object
    sftext.data.body = "Scene for offscreen operations. Just delete this scene if you stuck here"
    sftext.hide_render = True

    bpy.ops.object.camera_add(location=(0, 0, 2), rotation=(0, 0, 0))
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = 2  
    camera.location = (0, 0, 2)

    new_scene.camera = camera
    bpy.ops.mesh.primitive_plane_add(size=2)
    plane = bpy.context.active_object
    plane.name = "BakePlane"
    plane.data.materials.append(material)

    plane.scale.y = part.texture_sizeX / max(part.texture_sizeX, part.texture_sizeY)
    plane.scale.x = part.texture_sizeY / max(part.texture_sizeX, part.texture_sizeY)

    return new_scene, material, plane, output_node, MixRGB, MixShader.inputs[0], camera

def Add_layer(mat, output_node, layer):

    name = getlayergroupname(layer)

    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        if node_group:
            tree = mat.node_tree
            group_node = tree.nodes.new('ShaderNodeGroup')
            group_node.node_tree = node_group
            group_node.name = name
            group_node.location = (-300, 0)
            return tree, group_node

def create_bake_image(texture_sizeX,texture_sizeY, layer, suffix=""):

    image_name = f"BakeResult_{layer.name}{suffix}"
    bake_image = bpy.data.images.new(image_name, texture_sizeX, texture_sizeY, alpha=True)
    
    bake_image.alpha_mode = 'CHANNEL_PACKED'
    bake_image.colorspace_settings.name = 'sRGB'

    return bake_image

def render_image(scene, bake_image, filter = "", filter_value = 0.0, alpha_bake = None):
    
    bpy.context.window.scene = scene
    
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()

    render_layers = tree.nodes.new('CompositorNodeRLayers')
    render_layers.location = (-300, 0)
    if alpha_bake:
        alphaimage = tree.nodes.new('CompositorNodeImage')
        alphaimage.location = (0, 0)
        alphaimage.image = alpha_bake

    alpha_convert = tree.nodes.new('CompositorNodePremulKey')
    alpha_convert.location = (0, 0)
    alpha_convert.mapping = 'PREMUL_TO_STRAIGHT'
    
    colorspace = tree.nodes.new('CompositorNodeConvertColorSpace')
    colorspace.location = (0, 0)
    if is_4_0_or_newer:
        colorspace.from_color_space = 'Linear Rec.709'
    else:
        colorspace.from_color_space = 'Linear'
    colorspace.to_color_space = 'sRGB'

    gamma_node = tree.nodes.new(type='CompositorNodeGamma')
    
    set_default(gamma_node, 1, 1.0)
    gamma_node.location = (-600, 0)

    render_node = tree.nodes.new(type='CompositorNodeRLayers')
    render_node.location = (400, -200)
    filternode = None
    if filter == "BLUR":
        filternode = tree.nodes.new(type='CompositorNodeBlur')
        filternode.location = (400, -200) 
        filternode.size_y = int(filter_value*20)
        filternode.size_x = int(filter_value*20)

    viewer_node = tree.nodes.new(type='CompositorNodeViewer')
    viewer_node.location = (400, -200)
    links = bpy.context.scene.node_tree.links
    
    links.new(render_layers.outputs[0], alpha_convert.inputs[0])
    links.new(alpha_convert.outputs[0], colorspace.inputs[0])
    if alpha_bake:
        links.new(colorspace.outputs[0], viewer_node.inputs[0])
        links.new(alphaimage.outputs[0], viewer_node.inputs[1])
    else:
        links.new(colorspace.outputs[0], viewer_node.inputs[0])

    if filternode:
        links.new(colorspace.outputs[0], filternode.inputs['Image'])
        links.new(filternode.outputs['Image'], viewer_node.inputs[0])

    bpy.ops.render.render()

    render_result = bpy.data.images.get("Viewer Node")
    if render_result:
        bake_image.scale(render_result.size[0], render_result.size[1])
        
        bake_image.pixels = list(render_result.pixels)

def cleanup_bake_scene( new_scene, mat, plane):
    bpy.data.materials.remove(mat)
    bpy.data.objects.remove(plane)
    bpy.data.scenes.remove(new_scene)

class ResizeTexturePopup(Operator):
    """Resize the selected texture"""
    bl_idname = "haspaint.resize_texture"
    bl_label = "Resize Layer"
    bl_options = {'REGISTER'}

    layer_index: IntProperty(default=-1)

    new_width: IntProperty(name="New Width", default=1024, min=1)
    new_height: IntProperty(name="New Height", default=1024, min=1)

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        
        layout.prop(self, "new_width")
        layout.prop(self, "new_height")

    def execute(self, context):

        basescene = bpy.context.window.scene
        part = get_material_collection()

        layer = part.layers[self.layer_index]
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        bake_scene.render.resolution_x = self.new_width
        bake_scene.render.resolution_y = self.new_height
        tree = material.node_tree
        image_node = create_node(tree,'ShaderNodeTexImage', -600,0, "img", layer.resource.image)
        image_node.interpolation= part.texture_filtering
        tree.links.new(image_node.outputs[0], colorfix.inputs[1])
        tree.links.new(image_node.outputs[1], colorfix.inputs[2])
        tree.links.new(image_node.outputs[1], alphasocket)

        render_image(bake_scene, layer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        return {'FINISHED'}
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class ResizeAllLayersPopup(Operator):
    """Resize the selected texture"""
    bl_idname = "haspaint.resize_layers"
    bl_label = "Resize Layers"
    bl_options = {'REGISTER'}

    new_width: IntProperty(name="New Width", default=1024, min=1)
    new_height: IntProperty(name="New Height", default=1024, min=1)

    def draw(self, context):
        layout = self.layout
        
        layout.label(text="Warning: This operation cannot be undone.", icon='ERROR')
        
        layout.prop(self, "new_width")
        layout.prop(self, "new_height")

    def execute(self, context):
        basescene = bpy.context.window.scene
        part = get_material_collection()
        bake_scene, material, plane, output_node, colorfix, alphasocket, camera = setup_bake_scene(basescene)
        bake_scene.render.resolution_x = self.new_width
        bake_scene.render.resolution_y = self.new_height
        tree = material.node_tree

        for layer in part.layers:

            image_node = create_node(tree,'ShaderNodeTexImage', -600,0, "img", layer.resource.image)
            image_node.interpolation= part.texture_filtering
            tree.links.new(image_node.outputs[0], colorfix.inputs[1])
            tree.links.new(image_node.outputs[1], colorfix.inputs[2])
            tree.links.new(image_node.outputs[1], alphasocket)

            render_image(bake_scene, layer.resource.image)

        cleanup_bake_scene( bake_scene, material, plane)

        bpy.context.window.scene = basescene
        return {'FINISHED'}
    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)

class BAKING_OT_BakeTextures(Operator):
    bl_idname = "haspaint.bake_textures"
    bl_label = "Bake Textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        original_scene = context.scene
        low_poly = bpy.context.active_object
        high_poly = None
        part = get_material_collection()
        if not part.bake_maps:
            return {'CANCELLED'}

        if "Baking_Scene" not in bpy.data.scenes:
            baking_scene = bpy.data.scenes.new("Baking_Scene")
        else:
            baking_scene = bpy.data.scenes["Baking_Scene"]
        sel=[]
        baking_props = part.baking_props
        bpy.context.window.scene = baking_scene
        if baking_props.use_cage and baking_props.cage:
            bpy.context.scene.render.bake.cage_object = baking_props.cage
            baking_props.cage.hide_select = False
            baking_props.cage.hide_render = False
        if baking_props.gethpobjects(context):
            high_poly = combine_objects(baking_props.gethpobjects(context), apply_modifiers=True)
            high_poly.name = "HP"
            if high_poly:
                sel.append(high_poly)
        if baking_props.getlpobjects(context):
            low_poly = combine_objects(baking_props.getlpobjects(context), apply_modifiers=True)
        else:
            low_poly = combine_objects([low_poly], apply_modifiers=True)
        
        if low_poly:
            low_poly.name = "LP"
            sel.append(low_poly)

        if baking_scene.render.bake.cage_object:
            bpy.data.scenes["Baking_Scene"].collection.objects.link(baking_scene.render.bake.cage_object)
        bpy.context.scene.render.engine='CYCLES'
        bpy.context.scene.cycles.samples=part.baking_props.samples
        bpy.context.scene.render.bake.use_selected_to_active=True if high_poly else False
        bpy.context.scene.render.bake.use_cage=True if baking_props.use_cage else False

        bpy.ops.object.select_all(action='DESELECT')
        for obj in sel:
            obj.select_set(True)

        view_layer = baking_scene.view_layers[0]
        view_layer.objects.active = low_poly

        if low_poly.material_slots:
            low_poly.data.materials.clear()

        lpmtl = bpy.data.materials.new(name=f"LP_tmpbakemtl")
        low_poly.data.materials.append(lpmtl)
        lpmtl.use_nodes = True
        hpmtl = None
        if high_poly:
            if not len(high_poly.data.materials) ==0:
                hpmtl = high_poly.data.materials[0]
            else:
                hpmtl = bpy.data.materials.new(name=f"HP_tmpbakemtl")
                high_poly.data.materials.append(hpmtl)

        bakefrom = low_poly
        if high_poly:
            high_poly.select_set(True)
            bakefrom = high_poly
        bakefrommtl = bakefrom.data.materials[0]
        
        tmp_material = bpy.data.materials.new(name="HAS_TempCapture_Mtl")
        tmp_material.use_nodes = True
        tmp_nodes = tmp_material.node_tree.nodes
        if not high_poly:
            lpmtl = tmp_material
        links = tmp_material.node_tree.links
        gnr = None
        
        for bake_map in part.bake_maps:
            defaultbake = False
            for node in tmp_nodes:
                tmp_nodes.remove(node)
            if bake_map.use_map:

                if bake_map.type == "CURVATURE":

                    subsurf_modifier = bakefrom.modifiers.new(name="HASTempSubdivision", type='SUBSURF')
                    if not bake_map.smsubd:
                        subsurf_modifier.subdivision_type = 'SIMPLE'

                    subsurf_modifier.levels = 0
                    subsurf_modifier.render_levels = bake_map.subd

                    geom = tmp_nodes.new(type='ShaderNodeNewGeometry')
                    power = tmp_nodes.new(type='ShaderNodeMath')
                    power.operation = "POWER"

                    set_default(power, 1, 2.478)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')
                    links.new(geom.outputs["Pointiness"], power.inputs[0])
                    links.new(power.outputs[0], emission.inputs["Color"])
                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])
                elif bake_map.type == "AO":

                    aonode = tmp_nodes.new(type='ShaderNodeAmbientOcclusion')

                    set_default(aonode, "Distance", 50)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')     

                    links.new(aonode.outputs[0], emission.inputs[0])

                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])

                elif bake_map.type == "NRMOBJ":

                    geometry_node = tmp_nodes.new(type='ShaderNodeNewGeometry')
                    vector_math_add = tmp_nodes.new(type='ShaderNodeVectorMath')
                    vector_math_add.operation = 'MULTIPLY_ADD'
                    set_default(vector_math_add, 1, (0.5,0.5,0.5))
                    set_default(vector_math_add, 2, (0.5,0.5,0.5))
                    
                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')

                    links.new(geometry_node.outputs['Normal'], vector_math_add.inputs[0])

                    links.new(vector_math_add.outputs[0], material_output_node.inputs['Surface'])

                elif bake_map.type == "POSITION":

                    texcoord = tmp_nodes.new(type='ShaderNodeTexCoord')
                    seprgb = tmp_nodes.new(type='ShaderNodeSeparateRGB')
                    combrgb = tmp_nodes.new(type='ShaderNodeCombineRGB')
                    invert = tmp_nodes.new(type='ShaderNodeInvert')
                    gamma = tmp_nodes.new(type='ShaderNodeGamma')

                    set_default(gamma, 1, 2.2)
                    emission = tmp_nodes.new(type='ShaderNodeEmission')

                    material_output_node = tmp_nodes.new(type='ShaderNodeOutputMaterial')

                    links.new(texcoord.outputs[0], seprgb.inputs[0])

                    links.new(seprgb.outputs[0], combrgb.inputs[0])
                    links.new(seprgb.outputs[1], invert.inputs[1])
                    links.new(invert.outputs[0], combrgb.inputs[1])
                    links.new(seprgb.outputs[2], combrgb.inputs[2])

                    links.new(combrgb.outputs[0], gamma.inputs[0])
                    links.new(gamma.outputs[0], emission.inputs[0])

                    links.new(emission.outputs[0], material_output_node.inputs['Surface'])
        
                elif bake_map.type == "HEIGHT":
                    if high_poly:
                        bpy.ops.object.select_all(action='DESELECT')
                        high_poly.select_set(True)
                        bpy.context.view_layer.objects.active = high_poly

                        geo_nodes_mod = high_poly.modifiers.new(name="Height_GeometryNodes", type='NODES')
                        geo_nodes_mod.node_group = bpy.data.node_groups.new(name="HeightGeometryNodes", type='GeometryNodeTree')
                        nodes = geo_nodes_mod.node_group.nodes

                        for node in nodes:
                            nodes.remove(node)
                        for link in geo_nodes_mod.node_group.links:
                            geo_nodes_mod.node_group.links.remove(link)
                        gnlinks = geo_nodes_mod.node_group.links
                        input_node = nodes.new(type='NodeGroupInput')
                        output_node = nodes.new(type='NodeGroupOutput')
                        gnr = geo_nodes_mod.node_group
                        create_socket(geo_nodes_mod.node_group, 'Geometry', 'geom', True)
                        create_socket(geo_nodes_mod.node_group, 'Geometry', 'geom', False)
                        create_socket(geo_nodes_mod.node_group, 'Height', 'float', False)
                        object_info_node = nodes.new(type='GeometryNodeObjectInfo')
                        if baking_props.cage:
                            object_info_node.inputs['Object'].default_value = baking_props.cage
                        else:
                            object_info_node.inputs['Object'].default_value = low_poly

                        transfer = nodes.new(type='GeometryNodeAttributeTransfer' if not is_3_4_or_newer else "GeometryNodeSampleNearestSurface")
                        transfer.data_type = 'FLOAT_VECTOR' if is_3_4_or_newer else "FLOAT"
                        if not is_3_4_or_newer:
                            transfer.mapping = 'NEAREST_FACE_INTERPOLATED'

                        source = nodes.new(type='GeometryNodeInputPosition')
                        base = nodes.new(type='GeometryNodeInputPosition')

                        dist = nodes.new(type='ShaderNodeVectorMath')
                        dist.operation = 'DISTANCE'

                        maprange = nodes.new(type='ShaderNodeMapRange')
                    
                        set_default(maprange, 3, 1.0)
                        set_default(maprange, 4, 0.0)
                        set_default(maprange, 1, -bake_map.heightdist)
                        set_default(maprange, 2, bake_map.heightdist)

                        add = nodes.new(type='ShaderNodeMath')
                        add.operation = "ADD"
                        set_default(add, 1, bake_map.heightoffset)

                        for input_socket in output_node.inputs[1:-1]:
                            if input_socket.name == "Height":
                                geo_nodes_mod[input_socket.identifier + "_attribute_name"] = "Height"

                        gnlinks.new(input_node.outputs[0], output_node.inputs[0])
                        gnlinks.new(object_info_node.outputs['Geometry'], transfer.inputs[0])
                        gnlinks.new(source.outputs[0], transfer.inputs['Attribute' if not is_3_4_or_newer else "Value"])
                        
                        gnlinks.new(transfer.outputs['Value'], dist.inputs[0])
                        gnlinks.new(base.outputs[0], dist.inputs[1])

                        gnlinks.new(dist.outputs['Value'], add.inputs[0])
                        gnlinks.new(add.outputs[0], maprange.inputs[0])
                        gnlinks.new(maprange.outputs[0], output_node.inputs[1])

                        height_nodes = tmp_material.node_tree.nodes

                        attribute_node = height_nodes.new(type='ShaderNodeAttribute')
                        attribute_node.attribute_name = 'Height'
                        material_output_node = height_nodes.new(type='ShaderNodeOutputMaterial')

                        tmp_material.node_tree.links.new(attribute_node.outputs['Fac'], material_output_node.inputs['Surface'])
                        for obj in sel:
                            obj.select_set(True)
                        view_layer.objects.active = low_poly
                    else:
                        continue
                else:
                    defaultbake = True

                self.addimage(lpmtl, part, bake_map, baking_props)
                if not bake_map.type == "DIFFUSE":
                    bakefrom.data.materials[0] = tmp_material
                    baking_scene.render.bake.use_clear = True
                    baking_scene.cycles.bake_type = 'EMIT'
                if bake_map.type == "EMISSION":
                    bakefrom.data.materials[0] = bakefrommtl
                    baking_scene.render.bake.use_clear = True
                    baking_scene.cycles.bake_type = 'EMIT'
                    defaultbake = False
                try:
                    if not defaultbake:
                        bpy.ops.object.bake(type='EMIT')
                    else:
                        if bake_map.type == "DIFFUSE":
                            baking_scene.render.bake.use_pass_direct = False
                            baking_scene.render.bake.use_pass_indirect = False
                            baking_scene.cycles.bake_type = 'DIFFUSE'
                        bpy.ops.object.bake(type=bake_map.type, use_clear=True, margin=4, save_mode='INTERNAL')
                except RuntimeError as e:
                    self.report({'ERROR'}, f"Bake failed: {e}")
                bpy.ops.object.modifier_remove(modifier="HASTempSubdivision")
        if tmp_material == lpmtl and tmp_material.users == 0:
            bpy.data.materials.remove(tmp_material)
        else:
            if tmp_material and tmp_material.users == 0:
                bpy.data.materials.remove(tmp_material)
            if lpmtl and lpmtl.users == 0:
                bpy.data.materials.remove(lpmtl)
        if not tmp_material == hpmtl:
            if hpmtl and hpmtl.users == 0:
                bpy.data.materials.remove(hpmtl)
        if gnr and gnr.users == 0:
            bpy.data.node_groups.remove(gnr)
            
        remove_object(high_poly)
        remove_object(low_poly)

        bpy.data.scenes.remove(baking_scene)
        if baking_props.cage:
            baking_props.cage.hide_select = True
            baking_props.cage.hide_render = True
        bpy.context.window.scene = original_scene

        return {'FINISHED'}

    def addimage(self, mtl,part,bake_map,baking_props):
        image_name = f"{part.name.replace(' ', '')}_{getname(BAKE_TYPE, bake_map.type).replace(' ', '')}"
        bake_image = bpy.data.images.get(image_name)
        if not bake_image:
            bake_image = bpy.data.images.new(name=image_name, width=baking_props.bake_image_sizeY, height=baking_props.bake_image_sizeY)
            bake_image.generated_type = 'BLANK'
            bake_image.generated_color = (0.0, 0.0, 0.0, 1.0)
        else:
            bake_image.generated_type = 'BLANK'
            bake_image.generated_color = (0.0, 0.0, 0.0, 1.0)
            bake_image.user_clear()

            bpy.data.images[bake_image.name].scale( baking_props.bake_image_sizeY, baking_props.bake_image_sizeY )

            bake_image.pixels = [0.0] * (bake_image.size[0] * bake_image.size[1] * bake_image.channels)
            bake_image.pack()

        mtl.use_nodes = True
        nodes = mtl.node_tree.nodes
        texture_node = nodes.new('ShaderNodeTexImage')
        texture_node.image = bake_image
        bake_image.use_fake_user = True
        nodes.active = texture_node
        bake_map.image = bake_image
        
        return bake_image

def remove_object(obj):
    if obj and obj.name in bpy.data.objects:
        
        mesh = obj.data if obj.type == 'MESH' else None

        for collection in obj.users_collection:
            collection.objects.unlink(obj)

        bpy.data.objects.remove(obj, do_unlink=True)

        if mesh and mesh.users == 0:
            bpy.data.meshes.remove(mesh)

def combine_objects(objects, apply_modifiers=False):
    if not objects:
        return None

    copied_objects = []
    for obj in objects:
        if obj:
            
            new_mesh = obj.data.copy()
            new_obj = obj.copy()
            new_obj.data = new_mesh
            bpy.context.collection.objects.link(new_obj)
            
            if apply_modifiers:
                for modifier in new_obj.modifiers:
                    if modifier.show_viewport:  
                        bpy.context.view_layer.objects.active = new_obj
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                new_obj.modifiers.clear()
            else:
                new_obj.modifiers.clear()
            
            copied_objects.append(new_obj)

    bpy.ops.object.select_all(action='DESELECT')

    for obj in copied_objects:
        obj.select_set(True)

    if copied_objects:
        bpy.context.view_layer.objects.active = copied_objects[0]

    if bpy.ops.object.join.poll():
        bpy.ops.object.join()
    else:
        return None

    return bpy.context.object

def set_smooth_cage(cage, smooth):
    if cage:
        
        if cage:
            if "smooth" in cage.modifiers:
                mod = cage.modifiers["smooth"]
            else:
                mod = cage.modifiers.new(name="smooth", type='WEIGHTED_NORMAL')
            
            mod.weight = 1
            
            cage.data.use_auto_smooth = smooth

        cage.modifiers["smooth"].show_viewport = smooth
        cage.modifiers["smooth"].show_render = smooth

def create_or_update_cage(context):
    part = get_material_collection()
    baking_props = part.baking_props
    nm = get_cage_name()

    set_smooth_cage(baking_props.cage, baking_props.smooth_cage)

    curobj = context.view_layer.objects.active
    if not baking_props.use_cage:
        if baking_props.cage:
            bpy.data.objects.remove(baking_props.cage, do_unlink=True) 
        return
    if get_cage():
        return
    low_poly = None

    if baking_props.use_cage:
        low_poly = combine_objects(baking_props.getlpobjects(context), apply_modifiers=True)

    if not low_poly:
        return

    if baking_props.use_cage:
        
        cage = low_poly
        cage.name = nm
        cage.modifiers.new(name="Cage_Displace", type='DISPLACE')
        cage_material = bpy.data.materials.new(name="CageMaterial")
        cage_material.use_nodes = True
        cage_material.blend_method = 'BLEND'
        cage_material.diffuse_color = baking_props.cage_color
        nodes = cage_material.node_tree.nodes
        nodes.clear()
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')

        set_default(principled_node, 'Base Color', baking_props.cage_color)

        set_default(principled_node, 'Alpha', baking_props.cage_color[3])
        cage_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
        context.view_layer.objects.active = cage
        cage.update_tag()
        cage.data.materials.clear()
        cage.data.materials.append(cage_material)
        cage.modifiers['Cage_Displace'].strength = baking_props.cage_depth
        baking_props.cage = cage
        cage.hide_select = True
        cage.hide_render = True

        set_smooth_cage(cage, baking_props.smooth_cage)
            
        context.view_layer.objects.active = curobj

    context.view_layer.objects.active = curobj

def update_cage_depth(context):
    part = get_material_collection()
    baking_props = part.baking_props
    cage = baking_props.cage
    if cage:
        cage = bpy.data.objects[get_cage_name()]
        cage.modifiers['Cage_Displace'].strength = baking_props.cage_depth

def update_cage_material(context):
    part = get_material_collection()
    curobj = context.view_layer.objects.active
    baking_props = part.baking_props
    cage = baking_props.cage
    if cage:
        if cage.active_material:
            cage.active_material.use_nodes = True
            cage.active_material.blend_method = 'BLEND'
            cage.active_material.diffuse_color = baking_props.cage_color
            nodes = cage.active_material.node_tree.nodes
            nodes.clear()
            output_node = nodes.new(type='ShaderNodeOutputMaterial')
            principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')

            set_default(principled_node, 'Base Color', baking_props.cage_color)
            set_default(principled_node, 'Alpha', baking_props.cage_color[3])
            cage.active_material.node_tree.links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
            context.view_layer.objects.active = cage
            cage.update_tag()
            context.view_layer.objects.active = curobj

def get_cage_name():
    part = get_material_collection()
    if not part:
        return None
    return f"{part.name}_BakeCage"

def get_cage():
    nm = get_cage_name()
    if nm in bpy.data.objects:
        return bpy.data.objects[nm]
    return None
         
class BakeMapPref(Operator):
    bl_idname = "haspaint.bakemapprefs"
    bl_label = "Bake Preferences"
    bl_options = {'REGISTER', 'UNDO'}

    bake_type: StringProperty()

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        for bkmp in part.bake_maps: 

            if bkmp.type == self.bake_type:
                if self.bake_type == "CURVATURE":
                    layout.label(text = "Curvature")
                    layout.prop(bkmp, "subd", text="Subdivide",slider = True)
                    layout.prop(bkmp, "smsubd", text="Smooth Subdiv",toggle = True)
                if self.bake_type == "AO":
                    layout.label(text = "Ambient Occlusion")
                    layout.prop(bkmp, "aodist", text="AO Distance",slider = True)
                if self.bake_type == "HEIGHT":
                    layout.label(text = "Height")
                    layout.prop(bkmp, "heightdist", text="Height Distance")
                    layout.prop(bkmp, "heightoffset", text="Height Offset")
                    
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class GetFromSelected(Operator):
    bl_idname = "haspaint.get_from_selected"
    bl_label = "Make Group From Selected"
    bl_options = {'REGISTER', 'UNDO'}

    hp: BoolProperty(default = False)

    def execute(self, context):
        part = get_material_collection()
        expobj = []
        if self.hp:
            for ep in part.baking_props.high_poly_obj:
                if ep.obj:
                    expobj.append(ep.obj)
        else:
            for ep in part.baking_props.low_poly_obj:
                if ep.obj:
                    expobj.append(ep.obj)
                    
        for obj in context.selected_objects:
            if obj and obj.type == 'MESH':
                if not obj in expobj:
                    if self.hp:
                        part.baking_props.high_poly_obj.add().obj = obj 
                    else:
                        part.baking_props.low_poly_obj.add().obj = obj 
        return {'FINISHED'}

class RemoveAllBakeObjects(Operator):
    bl_idname = "haspaint.remove_all_bake_objects"
    bl_label = "Remove All Bake Objects"
    bl_options = {'REGISTER', 'UNDO'}

    hp: BoolProperty(default = False)

    def execute(self, context):
        part = get_material_collection()
        if self.hp:
            part.baking_props.high_poly_obj.clear()
            part.baking_props.high_poly_obj.add()
        else:
            part.baking_props.low_poly_obj.clear()
            part.baking_props.low_poly_obj.add()
    
        return {'FINISHED'}

###
### Image
###

class CustomNewImageOperator(Operator):
    bl_idname = "haspaint.custom_new"
    bl_label = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}

    fill: BoolProperty(default=False)

    def execute(self, context):
        part = get_material_collection()
        if not self.fill:
            new_image = bpy.data.images.new(
                name=newimagename(newlayername()),
                width=part.texture_sizeX,
                height=part.texture_sizeY,
                alpha= True,
                float_buffer= False,
                tiled=False
            )
            new_image.generated_type = 'BLANK'
            new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
            new_image.alpha_mode = 'CHANNEL_PACKED'
            new_image.colorspace_settings.name = 'sRGB'
        else:
            new_image = None
        part = get_material_collection()
        if not part:
            return {'CANCELLED'}
        layer_item = part.layers.add()
        layer_item.suppress_update = True
        layer_item.resource.suppress_update = True
        if not self.fill:
            layer_item.resource.image = new_image
        layer_item.layer_name = newlayername()
        layer_item.id = shortid()

        selectedisattached = part.layers[get_selected_layer_index()].attachedto
        
        part.base_layers.add().id = layer_item.id
        if selectedisattached:
            reassign_layer(part.base_layers, get_layer_by_id(selectedisattached).sub_layers, layer_item.id, parent = get_layer_by_id(selectedisattached))
        else:
            move_last_to_selected(part.base_layers)

        if self.fill:
            layer_item.layer_type = "FILL"
        self.report({'INFO'}, f"Texture '{self.name}' created.")
        layer_item.suppress_update = False
        layer_item.resource.suppress_update = False
        SelectLayer(layer_item.id)
        
        UpdateShader()
        return {'FINISHED'}

class CreatePBRLayer(Operator):
    bl_idname = "haspaint.create_pbr"
    bl_label = "PBR Layer"
    bl_options = {'REGISTER', 'UNDO'}

    color: FloatVectorProperty(name="Color", subtype='COLOR', size=4, default=(0.0, 0.0, 0.0, 0.0), min=0.0, max=1.0)
    alpha: BoolProperty(name="Alpha", default=True)
    float_buffer: BoolProperty(name="32-bit Float", default=False)
    tiled: BoolProperty(name="Tiled", default=False)
    generated_type: EnumProperty(
        name="Generated Type",
        items=[
            ('BLANK', 'Blank', ''),
            ('UV_GRID', 'UV Grid', ''),
            ('COLOR_GRID', 'Color Grid', '')
        ],
        default='BLANK'
    )
    
    def execute(self, context):

        part = get_material_collection()
        if not part:
            return {'CANCELLED'}
        layer_name = newlayername(pref= "PBR")
        image_name = newimagename(layer_name)
        
        xs = part.texture_sizeX
        ys = part.texture_sizeY

        new_image = bpy.data.images.new(
            name=image_name,
            width=xs,
            height=ys,
            alpha=self.alpha,
            float_buffer=self.float_buffer,
            tiled=self.tiled
        )
        new_image.generated_type = 'BLANK'
        new_image.generated_color = self.color
        
        new_image.alpha_mode = 'CHANNEL_PACKED'
        new_image.colorspace_settings.name = 'sRGB'

        if not part:
            return {'CANCELLED'}
        base_layer_item = part.layers.add()
        base_layer_item.suppress_update = True
        base_layer_item.resource.suppress_update = True
        base_layer_item.resource.image = new_image
        base_layer_item.layer_name = layer_name
        base_layer_item.layer_type = "PBR"
        base_layer_item.id = shortid()
        part.base_layers.add().id = base_layer_item.id
        base_layer_item.suppress_update = False
        base_layer_item.resource.suppress_update = False
        defcolor = {
            'DIFFUSE': ((0.5,0.5,0.5,1.0)),
            'ROUGHNESS': ((0.8,0.8,0.8,1.0)),
            'METALLIC': ((0.0,0.0,0.0,1.0)),
            'NORMAL': ((0.5,0.5,1.0,1.0)),
            'HEIGHT': ((0.5,0.5,0.5,1.0)),
            'ALPHA': ((1.0,1.0,1.0,1.0)),
            'EMISSION': ((0.0,0.0,0.0,1.0)),
            'AO': ((1.0,1.0,1.0,1.0)),
            'CUSTOM': ((0.0,0.0,0.0,1.0)),
        }
        for type in getusedmaps():
            layer_item = part.layers.add()
            layer_item.suppress_update = True
            layer_item.resource.suppress_update = True
            if type[0] == "DIFFUSE":
                layer_item.resource.image = new_image

            layer_item.resource.default_color = defcolor.get(type[0], ((0.0,0.0,0.0,1.0)))
            layer_item.resource.default_value = defcolor.get(type[0], ((0.0,0.0,0.0,1.0)))[0]
            layer_item.texture_type = type[0]
            layer_item.id = shortid()
            base_layer_item.sub_layers.add().id = layer_item.id
            layer_item.suppress_update = False
            layer_item.resource.suppress_update = False

        selectedisattached = part.layers[get_selected_layer_index()].attachedto
        
        if selectedisattached:
            reassign_layer(part.base_layers, get_layer_by_id(selectedisattached).sub_layers, base_layer_item.id, parent = get_layer_by_id(selectedisattached))
        else:
            move_last_to_selected(part.base_layers)
        SelectLayer(base_layer_item.id)
        
        UpdateShader()

        return {'FINISHED'}

class IsolateImage(Operator):
    bl_idname = "haspaint.isolate_image"
    bl_label = "Isolate Image"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()

    def execute(self, context):
        image = bpy.context.scene.other_props.preview_image

        if image and self.texture_name == image.name:
            bpy.context.scene.other_props.preview_image = None
            UpdateShader()
            return {'FINISHED'}
        else:
            image = bpy.data.images.get(self.texture_name, None)
            if image:
                bpy.context.scene.other_props.preview_image = image
                part = get_material_collection()
                material = bpy.context.active_object.active_material
                if not material:
                    return
                tree = material.node_tree
                
                if material is None:
                    return

                for node in tree.nodes:
                    if node.type == 'OUTPUT_MATERIAL':
                        output_node = node
                    else:
                        tree.nodes.remove(node)
                if 'output_node' not in locals():
                    output_node = tree.nodes.new('ShaderNodeOutputMaterial')
                    output_node.location = (600, 0)
                mtl_n = material.name

                image_node = create_image_node(tree, image)

                tree.links.new(image_node.outputs[0], output_node.inputs[0]) 
                return {'FINISHED'}
            else:
                self.report({'WARNING'}, "Invalid Image ")
                return {'CANCELLED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class CreateFolderOperator(Operator):
    bl_idname = "haspaint.create_folder"
    bl_label = "Folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        part = get_material_collection()
        if not part:
            return {'CANCELLED'}
        layer_item = part.layers.add()
        layer_item.suppress_update = True
        layer_item.layer_name = newlayername(pref= "Folder")
        layer_item.layer_type = "FOLDER"
        layer_item.id = shortid()
        layer_item.sort_color = 'OUTLINER_COLLECTION'
        part.base_layers.add().id = layer_item.id

        layer_item.suppress_update = False
        move_last_to_selected(part.base_layers)
        
        UpdateShader()
        return {'FINISHED'}

###
### Layer actions
###

class UncheckLayerOperator(Operator):
    bl_idname = "haspaint.uncheck_layer"
    bl_label = "Uncheck Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    def execute(self, context):

        layer = getlayer(self.layer_index)

        if layer:
            layer.use_layer = not layer.use_layer
            return {'FINISHED'}
        return {'FINISHED'}

class MoveLayerOperator(Operator):
    bl_idname = "haspaint.move_layer"
    bl_label = "Move Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])
    parent: IntProperty(default = -1)

    def execute(self, context):
        
        part = get_material_collection()
        index = self.layer_index
        if self.parent == -1:
            alt = False
            layers =part.base_layers
        else:
            alt= True
            layers = part.base_layers[self.parent].get_layer().sub_layers
        
        new_index = index + 1 if self.direction == 'UP' else index - 1

        if 0 <= new_index < len(layers):
            layers.move(index, new_index)
            UpdateShader()
        return {'FINISHED'}

class MoveFilterOperator(Operator):
    bl_idname = "haspaint.move_filter"
    bl_label = "Move Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    direction: EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])

    def execute(self, context):
        layer = getlayer(self.layer_index)
        filter = getfilter(self.layer_index, self.filter_index)
        ind = self.filter_index
        new_index = ind + 1 if self.direction == 'UP' else ind - 1
        if 0 <= new_index < len(layer.filters):
            layer.filters.move(ind, new_index)
            UpdateShader()
        return {'FINISHED'}

class SelectTextureOperator(Operator):
    bl_idname = "haspaint.select_texture"
    bl_label = "Select Texture"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()
    id: StringProperty()
    alpha: StringProperty(default = "Skip")
    def execute(self, context):
        part = get_material_collection()
        if self.texture_name:
            SelectTexture(self.texture_name)
            part.selected_layer = self.id
        elif self.id:
            SelectLayer(self.id)
        if self.alpha == "Set":
            part.selected_alpha = True
        if self.alpha == "Remove":
            part.selected_alpha = False
        
        return {'FINISHED'}
        
class SetStandardVT(Operator):
    bl_idname = "haspaint.setstandardvt"
    bl_label = "Set Standard View Transform"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene.view_settings.view_transform = 'Standard'
        return {'FINISHED'}

class SetupScene(Operator):
    bl_idname = "haspaint.setupscene"
    bl_label = "Setup Scene"
    bl_options = {'REGISTER', 'UNDO'}

    viewtransform: BoolProperty(name="Set View Transform to 'Standart'", default=True)

    mat: BoolProperty(name="Switch To Material Preview", default=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        
        bs = layout.box()
        bsr = bs.row()
        bsr.label(text= "Recommended for precise color output.")
        bsr.operator("haspaint.open_website", text="", icon="QUESTION")
        bs.prop(self, "viewtransform")
        
        bs = layout.box()
        bs.prop(self, "mat")

    def execute(self, context):

        if self.viewtransform:
            bpy.context.scene.view_settings.view_transform = 'Standard'
        if self.mat:
            bpy.context.space_data.shading.type = 'MATERIAL'
        bpy.context.scene.other_props.fixed = True
        return {'FINISHED'}

class SaveLayersOperators(Operator):
    bl_idname = "haspaint.save_layers"
    bl_label = "Save Layers"
    bl_description = "Save all textures"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        modified_images = [img for img in bpy.data.images if img.is_dirty]
        if modified_images:
            bpy.ops.image.save_all_modified()
        else:
            self.report({'INFO'}, "No images are modified.")
        return {'FINISHED'}

class DeleteLayersOperator(Operator):
    bl_idname = "haspaint.delete_layers"
    bl_label = "Delete layers"
    bl_description = "Delete layers from material"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Are you sure you want to delete all layers?")

    def execute(self, context):
        part = get_material_collection()
        part.base_layers.clear()
        part.layers.clear()
        UpdateShader()

        self.report({'INFO'}, "Layers deleted successfully.")
        return {'FINISHED'}

class AddLayerToFolderOperator(Operator):
    bl_idname = "haspaint.layer_to_folder"
    bl_label = "Add Layer To Folder"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()

        curlayer = part.layers[self.layer_index]

        folderlayer = getbyid(part.addtofolder)
        
        subls = get_layers(folderlayer.sub_layers)

        folditem = get_layer_in_list(part.base_layers, folderlayer.id)
        curitem = get_layer_in_list(part.base_layers, curlayer.id)
        
        contains = curlayer in subls
        if not contains:
            reassign_layer(part.base_layers, folderlayer.sub_layers, curlayer.id, parent = folderlayer)
            if folditem.index < curitem.index:
                folderlayer.sub_layers.move(len(folderlayer.sub_layers)-1,0)
        else:
            for i, l in enumerate(reversed(subls)):
                if curlayer==l:
                    reassign_layer(folderlayer.sub_layers, part.base_layers, curlayer.id)
                    part.base_layers.move(len(part.base_layers)-1,folditem.index)
                    break

        UpdateShader()
        return {'FINISHED'}

class StartAddToFolderOperator(Operator):
    bl_idname = "haspaint.startaddtofolder"
    bl_label = "Add Layer To Folder"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        if not part.addtofolder:
            part.addtofolder = part.layers[self.layer_index].id
        else:
            part.addtofolder = ''

        return {'FINISHED'}

class DuplicateLayerOperator(Operator):
    bl_idname = "haspaint.duplicate_layer"
    bl_label = "Duplicate Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        
        for i, l in enumerate(get_layers(part.base_layers)):
            if i==self.layer_index:
                nwl = part.layers.add()

                col_copy(l, nwl)
                nwlf = part.base_layers.add()
                nwlf.id = nwl.id

                UpdateShader()
                return {'FINISHED'}
        return {'CANCELLED'}
    
def copy_layer(layer, to_layer):
    l = to_layer
    l.opacity = layer.opacity
    l.image = layer.resource.image
    l.blend_mode = layer.blend_mode
    l.texture_type = layer.texture_type

    properties = ["name",
    "node_name",
    "layer_name",
    "in_use",
    'custom_node_tree_p',
    'socket_in',
    'socket_out',
    'image',
    'blend_mode',
    'opacity',
    'default_color',
    ]

    for filter in layer.filters:
        fil = l.filters.add()
        for prop in properties:
            try:
                
                setattr(fil, prop, getattr(filter, prop))

            except AttributeError:
                continue
    original_image = layer.resource.image
    
    new_image = original_image.copy()
    to_layer.resource.image = new_image

class OpenImageOperator(Operator):
    bl_idname = "haspaint.open_image_file"
    bl_label = "Open Image File"
    bl_description = "Open file browser to select an image"

    filepath: StringProperty(
        name="File Path",
        description="Path to the image file",
        maxlen=1024,
        subtype='FILE_PATH'
    )
    layer_index: IntProperty()
    def execute(self, context):
        get_material_collection().layers[self.layer_index].resource.image = bpy.data.images.load(self.filepath)
        
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class UnlinkImageOperator(Operator):
    bl_idname = "haspaint.unlinkimage"
    bl_label = "Unlink"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    def execute(self, context):

        layer = getlayer(self.layer_index)

        if layer:
            layer.resource.image = None
            return {'FINISHED'}
        return {'FINISHED'}

class SetUsedMaps(Operator):
    bl_idname = "haspaint.setusedmaps"
    bl_label = "Select used maps"
    bl_description = "Maps that will be used in material and layers"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):

        part = get_material_collection()
        layout = self.layout
        column = layout.column(align=True)
        column.prop(part.used_maps, "Diffuse", toggle=True)
        column.prop(part.used_maps, "Roughness", toggle=True)
        column.prop(part.used_maps, "Metallic", toggle=True)
        column.prop(part.used_maps, "Normal", toggle=True)
        column.prop(part.used_maps, "Height", toggle=True)
        column.prop(part.used_maps, "Emission", toggle=True)
        column.prop(part.used_maps, "Alpha", toggle=True)
        column.prop(part.used_maps, "AO", toggle=True)
        column.prop(part.used_maps, "Custom", toggle=True)

    def execute(self, context):
        return {'FINISHED'}

class RenameLayer(Operator):
    bl_idname = "haspaint.rename_layer"
    bl_label = "Rename Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    new_name: StringProperty(name="New Name", default="")

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

    def execute(self, context):
        layer = getlayer(self.layer_index)
        if layer and layer.resource.image:
            layer.resource.image.name = self.new_name
            self.report({'INFO'}, f"Layer renamed to '{self.new_name}'")
        else:
            self.report({'WARNING'}, "Layer or image not found")
        return {'FINISHED'}

    def invoke(self, context, event):
        layer = getlayer(self.layer_index)
        if layer:
            self.new_name = layer.resource.image.name
        return context.window_manager.invoke_props_dialog(self)

class RemoveLayer(Operator):
    bl_idname = "haspaint.remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    deletetexture: BoolProperty(default= True)

    def execute(self, context):
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:
            remove_references(layer)
            part.addtofolder = ""
            UpdateShader()
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class SetLayerData(Operator):
    bl_idname = "haspaint.setlayerfill"
    bl_label = "Set Layer Data"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty(default=-1)
    image_name: StringProperty()

    def draw(self, context):
        layout = self.layout
        if layer:
            layout.prop(foundsubl, "default_color", text = "Fill Color")

    def execute(self, context):

        UpdateShader()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SetSortColorOperator(Operator):
    bl_idname = "haspaint.set_color"
    bl_label = "Uncheck Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    color: StringProperty(default = "PANEL_CLOSE")
    def execute(self, context):
        layer = getlayer(self.layer_index)
        layer.sort_color = self.color
        return {'FINISHED'}

class OtherActionsOperator(Operator):
    bl_idname = "haspaint.otheractions"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        part = get_material_collection()
        if layer:
            if self.action == "ADDFILTER":
                fil = layer.filters.add()
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                UpdateShader()

            if self.action == "ADDPAINT":
                fil = layer.filters.add()
                fil.suppress_update = True
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                fil.name = 'PAINT'
                if not fil.resource.image:
                    texture_name = f'.HAS_{fil.id}_paint'
                    ims = bpy.data.images.get(texture_name)
                    if ims:
                        fil.resource.image = ims
                    else:
                        fil.resource.image = newimage(texture_name)
                fil.suppress_update = False
                UpdateShader()
            if self.action == "ADDFILL":
                fil = layer.filters.add()
                fil.suppress_update = True
                fil.id = shortid()
                fil.connection_type = "ALPHA" if part.selected_alpha else 'COLOR'
                fil.resource.grayscale = part.selected_alpha
                fil.name = 'FILL'
                fil.suppress_update = False
                UpdateShader()
            elif self.action == "DUPL":
                new_layer = part.layers.add()
                new_layer.suppress_update = True
                new_layer.id = shortid()
                nef = part.base_layers.add()
                nef.id = new_layer.id
                
                copy_layer(layer, new_layer)
                node_group = bpy.data.node_groups.get(f"{getlayergroupname(layer)}_filters")

                node_group_copy = node_group.copy()
                node_group_copy.name = f"{getlayergroupname(new_layer)}_filters"

                new_layer.layer_name = f"{layer.layer_name}_copy"

                new_layer.suppress_update = False
                UpdateShader()
            elif self.action == "ADDMASK":
                layer.mask = True
                UpdateShader()

            elif self.action == "REMOVEMASK":
                layer.mask = False
                for ind, filter in reversed(list(enumerate(layer.filters))):
                    if filter.connection_type == "ALPHA":
                        layer.filters.remove(ind)
                UpdateShader()
                
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)
    
class LayerActionPopup(Operator):
    bl_idname = "haspaint.layer_action"
    bl_label = "Layer Action"
    bl_options = {'REGISTER'}
    layer_index: IntProperty()
    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        if not part:
            return
        layer = part.layers[self.layer_index]
        if layer:
            
            rsb = layout.row()
            rsb.label(text = "Layer Action")
            rsb.label(icon = "GRIP")
            colcol = layout.column()
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.otheractions", text="Add Filter", icon = "SHADERFX", emboss = False)
            op.layer_index=self.layer_index
            op.action="ADDFILTER"
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.otheractions", text="Add Paint Layer", icon = "BRUSH_DATA", emboss = False)
            op.layer_index=self.layer_index
            op.action="ADDPAINT"
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.otheractions", text="Add Fill Layer", icon = "IMAGE", emboss = False)
            op.layer_index=self.layer_index
            op.action="ADDFILL"
            rvsbx = bx.row(align = True)
            rvsbx.alignment = 'LEFT'
            rvsbx.enabled = not layer.lock
            op = rvsbx.operator("haspaint.otheractions", text="Add Mask", icon = "CLIPUV_DEHLT", emboss = False)
            op.layer_index=self.layer_index
            op.action="ADDMASK"
            
            op = rvsbx.operator("haspaint.otheractions", text="Remove Mask", icon = "SNAP_FACE", emboss = False)
            op.layer_index=self.layer_index
            op.action="REMOVEMASK"
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            
            rowvs.prop(layer, "lock", text="Lock" if not layer.lock else"Unlock", icon = "DECORATE_LOCKED", emboss = False)
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.combine_with_layer_below", text="Combine with Layer Below", icon = "MOD_UVPROJECT", emboss = False)
            op.layer_index=self.layer_index
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.resize_texture", text="Resize Layer", icon = "MOD_EDGESPLIT", emboss = False)
            op.layer_index=self.layer_index
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.collapse_layer", text="Collapse Layer", icon = "IMPORT", emboss = False)
            op.layer_index=self.layer_index
            row = colcol.box().row(align = True)
            row.label(icon = layer.sort_color, text = "Color Tag")
            row.enabled = not layer.lock
            if not layer.layer_type == "FOLDER":
                for c in SORT_COLORS:
                    select_op = row.operator("haspaint.set_color", text="", icon=c[0], emboss = False)
                    select_op.color = c[0]
                    select_op.layer_index = self.layer_index
            else:
                for c in FOLDER_SORT_COLORS:
                    select_op = row.operator("haspaint.set_color", text="", icon=c[0], emboss = False)
                    select_op.color = c[0]
                    select_op.layer_index = self.layer_index
             
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.otheractions", text="Duplicate Layer", icon = "DUPLICATE", emboss = False)
            op.layer_index=self.layer_index
            op.action="DUPL"
            if layer.resource.image:
                rowvs = bx.row()
                rowvs.alignment = 'LEFT'
                rowvs.enabled = not layer.lock
                op = rowvs.operator("haspaint.isolate_image", text="Isolate current layer image", icon = "IMAGE_REFERENCE", emboss = False)
                op.texture_name=layer.resource.image.name
                rowvs = bx.row()
                rowvs.alignment = 'LEFT'
                rowvs.enabled = not layer.lock
                op = rowvs.operator("haspaint.image_info_popup", text="Edit Image Properties", icon = "PROPERTIES", emboss = False)
                op.texture_name = layer.resource.image.name
            bx = colcol.box()
            rowvs = bx.row()
            rowvs.alignment = 'LEFT'
            rowvs.enabled = not layer.lock
            op = rowvs.operator("haspaint.remove_layer", text="Remove layer", icon = "TRASH", emboss = False)
            op.layer_index=self.layer_index

            resource = layer.resource
            cols = colcol.box().split(factor=0.5)
            box = cols.column()
            cols.enabled = not layer.lock
            if not resource.image:
                boxe = box.row()
                
                boxe.prop(resource, "default_color", text="")
                boxe.scale_y = 1.0
            if not resource.image: 
                box = box.row(align = True)
            box.template_ID(resource, "image")
            if not resource.image: 
                op = box.operator("haspaint.add_has_image", text="New Image", icon = "IMAGE_REFERENCE", emboss = True)
                op.layer_index=layer.index

            if resource.image: 
                box.template_ID_preview(resource, "image", rows=4, cols=6, hide_buttons = True)
            
            op = box.operator("haspaint.open_image_file", text="Open", icon = "FILE_FOLDER", emboss = True)
            op.layer_index = self.layer_index

            if resource.image: 
                draw_mapping_box(cols.column(), layer.resource)

    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

class SetFilterOperator(Operator):
    bl_idname = "haspaint.setfilter"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        filter = layer.filters[self.filter_index]
        filter.name = self.action
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class FilterSelectPopup(Operator):
    bl_idname = "haspaint.filter_select"
    bl_label = "Select Filter"
    bl_options = {'REGISTER'}
    layer_index: IntProperty()
    filter_index: IntProperty()
    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:
            
            rsb = layout.row()
            rsb.label(text = "Select Filter")
            rsb.label(icon = "GRIP")
            colcol = layout.column()
            bx = colcol.box()
            for filterenum in FILTERS:
                if not filterenum:
                    bx = colcol.box()
                    continue
                rowvs = bx.row()
                rowvs.alignment = 'LEFT'
                op = rowvs.operator("haspaint.setfilter",text=filterenum[1],icon=filterenum[3],emboss=False)
                op.layer_index=self.layer_index
                op.filter_index=self.filter_index
                op.action=filterenum[0]

    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)


class TypeSelectPopup(Operator):
    bl_idname = "haspaint.type_select"
    bl_label = "Map Type"
    bl_options = {'REGISTER'}
    layer_index: IntProperty()
    current: StringProperty()
    def draw(self, context):
        layout = self.layout
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        if layer:
            rsb = layout.row()
            rsb.label(text = "Texture type")
            rsb.label(icon = "GRIP")
            colcol = layout.column(align = True)
            bx = colcol
            for type in getusedmaps():
                if not type:
                    bx = colcol.box()
                    continue
                rowvs = bx.row()
                rowvs.alignment = 'LEFT'
                op = rowvs.operator("haspaint.settype",text=type[1],emboss=self.current == type[0], depress = self.current == type[0])
                op.layer_index=self.layer_index
                op.action=type[0]

    def execute(self, context):
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=150)

class SetTypeOperator(Operator):
    bl_idname = "haspaint.settype"
    bl_label = "Action"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    action: StringProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        layer.texture_type = self.action
        return {'FINISHED'}
    def invoke(self, context, event):
        close_panel(event)
        return self.execute(context)

class ImageInfoPopup(Operator):
    bl_idname = "haspaint.image_info_popup"
    bl_label = "Image Info"
    bl_options = {'REGISTER'}
    texture_name: StringProperty()

    def draw(self, context):
        layout = self.layout
        image = bpy.data.images.get(self.texture_name)

        if image:
            op = layout.row().operator("haspaint.save_image", text="Save", icon='FILE_TICK')
            op.image_name = self.texture_name
            column = layout.column()
            column.enabled = not image.is_dirty
            column.prop(image.colorspace_settings, "name")
            column.prop(image, "alpha_mode")
            column.prop(image, "use_generated_float", text = 'Use 32 bit depth')
            
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

def close_panel(event):
    x, y = event.mouse_x, event.mouse_y
    bpy.context.window.cursor_warp(10, 10)

    move_back = lambda: bpy.context.window.cursor_warp(x, y)
    bpy.app.timers.register(move_back, first_interval=0.001)

class CleanupData(Operator):
    bl_idname = "haspaint.cleanup"
    bl_label = "Cleanup HAS Data"
    bl_options = {'REGISTER', 'UNDO'}

    remove_all_has_data: BoolProperty(default = False)
    clear_unused_blocks: BoolProperty(default = True)

    def draw(self, context):
        layout = self.layout

        rsb = layout.column()

        rsbr = rsb.row()
        rsbr.prop(self, "clear_unused_blocks", text = "Clear Unused HAS Data", icon = 'FAKE_USER_ON')
        rsbr.enabled = not self.remove_all_has_data
        rsbr = rsb.row()
        rsbr.prop(self, "remove_all_has_data", text = "Remove All HAS Data", icon = 'TRASH')
        sda = ""
        if self.clear_unused_blocks:
            sda = "Clear Unused HAS Data"
        if self.remove_all_has_data:
            sda = "Remove All HAS Data"
        if sda:
            bsrs = rsb.box().column(align = True)
            bsrs.label(icon = 'ERROR', text = f"Will {sda}!")
            bsrs.label(text = "including textures, node groups and materials")
            bsrs = rsb.box().column(align = True)
            bsrs.label(text = "Affects only data blocks that start with")
            bsrs.label(text = "'.HAS_' or 'HASM'")
    def execute(self, context):
        if self.clear_unused_blocks or self.remove_all_has_data:
            if self.clear_unused_blocks:
                clear_unused_layers()
            for ng in bpy.data.node_groups:
                if ng.name.startswith(".HAS_"):
                    if ng.users == 0 or self.remove_all_has_data:
                        bpy.data.node_groups.remove(ng)
            for img in bpy.data.images:
                if img.name.startswith(".HAS_"):
                    if img.users == 0 or self.remove_all_has_data:
                        bpy.data.images.remove(img)
            if self.remove_all_has_data:
                curscene = bpy.context.scene
                mtlprops = curscene.material_props
                while len(mtlprops) > 0:
                    mtlprops.remove(0)
            
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class SaveImageOperator(bpy.types.Operator):
    bl_idname = "haspaint.save_image"
    bl_label = "Save Image"
    bl_description = "Save the active image"

    image_name: StringProperty()

    def execute(self, context):
        try:
            image = bpy.data.images.get(self.image_name)
            if image:
                image.pack()
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save image: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class AddHASImage(Operator):
    bl_idname = "haspaint.add_has_image"
    bl_label = "Add HAS Image"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()

    def execute(self, context):
        part = get_material_collection()
        layer = getlayer(self.layer_index)

        new_image = bpy.data.images.new(
            name=newimagename(layer.name),
            width=part.texture_sizeX,
            height=part.texture_sizeY,
            alpha= True,
            float_buffer= False,
            tiled=False
        )
        new_image.generated_type = 'BLANK'
        new_image.generated_color = (0.0, 0.0, 0.0, 0.0)
        new_image.alpha_mode = 'CHANNEL_PACKED'
        new_image.colorspace_settings.name = 'sRGB'
        layer.resource.image = new_image
        return {'FINISHED'}

###
### Filter
###

class RemoveTextureTypeProp(Operator):
    bl_idname = "haspaint.remove_texture_type_prop"
    bl_label = "Remove Texture Type"
    bl_options = {'REGISTER', 'UNDO'}
    index: IntProperty()

    def execute(self, context):
        context.scene.other_props.exportprops.remove(self.index)

        return {'FINISHED'}

class RemoveFilter(Operator):
    bl_idname = "haspaint.remove_layer_filter"
    bl_label = "Remove Layer Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                layer.filters.remove(ind)
                UpdateShader()
                return {'FINISHED'}

class ShowHideFilter(Operator):
    bl_idname = "haspaint.showhidefilter"
    bl_label = "Remove Layer Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    compfilter: BoolProperty()

    def execute(self, context):
        part = get_material_collection()

        layer = part.layers[self.layer_index]

        filters = layer.filters

        for ind, filter in enumerate(filters):
            
            if ind == self.filter_index:
               
                filter.in_use = not filter.in_use
                
                UpdateShader()
                return {'FINISHED'}
        return {'CANCELLED'}

class ActivateTab(Operator):
    bl_idname = "haspaint.activate_tab"
    bl_label = "Tab"
    bl_options = {'REGISTER', 'UNDO'}

    activate_tab: IntProperty()

    def execute(self, context):
        
        context.scene.other_props.expand_area_QuickEdit = False
        context.scene.other_props.expand_area_DepthSelection = False
        context.scene.other_props.expand_area_PaintTools = False
        context.scene.other_props.expand_area_Bake = False
        if self.activate_tab == 0:
            context.scene.other_props.expand_area_QuickEdit = True
        if self.activate_tab == 1:
            context.scene.other_props.expand_area_DepthSelection = True
        if self.activate_tab == 2:
            context.scene.other_props.expand_area_PaintTools = True
        if self.activate_tab == 3:
            context.scene.other_props.expand_area_Bake = True
        return {'FINISHED'}

class AddFilter(Operator):
    bl_idname = "haspaint.add_layer_filter"
    bl_label = "Add Filter"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    type: StringProperty()

    def execute(self, context):
        part = get_material_collection()
        layer = part.layers[self.layer_index]
        fil = layer.filters.add()
        fil.suppress_update = True
        fil.id = shortid()
        fil.name = self.type
        fil.connection_type = "ALPHA"
        if self.type == "PAINT":
            
            if not fil.resource.image:
                texture_name = f'.HAS_{fil.id}_paint'
                ims = bpy.data.images.get(texture_name)
                if ims:
                    fil.resource.image = ims
                else:
                    fil.resource.image = newimage(texture_name)
        fil.resource.grayscale = True
        
        fil.suppress_update = False

        UpdateShader()
        return {'FINISHED'}

class AddMaskGenBlock(Operator):
    bl_idname = "haspaint.addmaskgenblock"
    bl_label = "Add Mask Generator Block"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()

    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                filter.maskgen.add()
                UpdateShader()
                return {'FINISHED'}

class RemoveMaskGenBlock(Operator):
    bl_idname = "haspaint.removemaskgenblock"
    bl_label = "Add Mask Generator Block"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    mask_index: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                filter.maskgen.remove(self.mask_index)
                UpdateShader()
                return {'FINISHED'}                

class FilterChangeInOut(Operator):
    bl_idname = "haspaint.filter_inout"
    bl_label = "Change Filter Input/Output"
    bl_options = {'REGISTER', 'UNDO'}

    layer_index: IntProperty()
    filter_index: IntProperty()
    inpout: BoolProperty()
    inputind: IntProperty()
    def execute(self, context):
        layer = getlayer(self.layer_index)
        for ind, filter in enumerate(layer.filters):
            if ind == self.filter_index:
                if self.inpout:
                    filter.socket_in=self.inputind
                else:
                    filter.socket_out=self.inputind
                UpdateShader()
                return {'FINISHED'}

class UpdateHist(Operator):
    bl_idname = "haspaint.update_hist"
    bl_label = "Update Histogram"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: StringProperty()

    def execute(self, context):
        set_histogram(self.texture_name, get_image_histogram(self.texture_name, num_bins=20, sample_rate=0.01))
        update_hist_display(self.texture_name)
        return {'FINISHED'}

###
### UI
###

class HAS_PT_LayersPanel(bpy.types.Panel):
    bl_label = "HAS Paint Layers"
    bl_idname = "HAS_PT_LayersPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    bl_category = 'HAS Paint Layers'

    def draw(self, context):
                
        layout = self.layout

        butcol = layout.row()
        butcol.prop(context.scene.other_props, "expand_area_butfile", text="", icon="FILE_BLEND")
        butcol.prop(context.scene.other_props, "expand_area_butmtl", text="", icon="NODE_MATERIAL")
        butcol.prop(context.scene.other_props, "expand_area_buttools", text="", icon="TOOL_SETTINGS")
        butcol.prop(context.scene.other_props, "expand_area_butlayers", text="", icon="RENDERLAYERS")
        butcol.label(text="")
        
        op = butcol.operator("haspaint.open_website", text="", icon="QUESTION")
        op.link = "https://hirourk.github.io/HASPaintLayersWiki/index.html"
        boxw = layout
        if bpy.context.active_object:

            part = get_material_collection()
            if context.scene.other_props.expand_area_butfile:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_Actions", text="File", icon="FILE_BLEND", emboss = False)
                
                if context.scene.other_props.expand_area_Actions:
                    boxs = box.box()
                    row = boxs.row(align=False)
                    
                    row.operator("haspaint.save_layers", text="Save All Textures", icon = "FILE_TICK")
                    row.prop(context.scene.other_props, "toggle_save", text = f"Auto Save Textures", icon = "CHECKBOX_HLT" if context.scene.other_props.toggle_save else "CHECKBOX_DEHLT")
                    row = boxs.row(align=False)

                    rowb = boxs.box()
                    rowb.scale_y = 2.0
                    rowb.operator("haspaint.export_textures", text="Export Textures", icon = "EXPORT")
                    row = rowb.row(align=False)

                    row.operator("haspaint.export_to_ora", text="Export Layers", icon='EXPORT')
                    row.operator("haspaint.import_from_ora", text="Import Layers", icon='IMPORT')

                    row = box.row(align=False)
                    box = box.box()
                    row.box().operator("haspaint.cleanup", text="Cleanup HAS Data", icon='FAKE_USER_OFF', emboss = False)
                    rowl = box.row(align=True)
                    rowl.prop(context.scene.other_props, "expand_area_MaterialCollection", text="HAS Set collection", icon="MATERIAL", emboss = False)
                    
                    if context.scene.other_props.expand_area_MaterialCollection:
                        box.label(text = "Registered Materials")
                        rowl = box.row(align=True)
                        
                        rowl.label(text = "Set names")
                        rowl.label(text = "Materials")
                        for i, p in enumerate(context.scene.material_props):
                            rowl = box.row(align=True)
                            rowl.prop(p, "name", text="")
                            rowl.prop(p, "material", text="")
                            rowl.operator("haspaint.remove_material", text="", icon='REMOVE').index = i
                            
            if not bpy.context.active_object or not bpy.context.active_object.type == 'MESH':
                return
            
            if not bpy.context.active_object.data.materials or not check_mtl_used():
                box = layout.box()
                box.operator("haspaint.setup_material", text="Setup material", icon="ADD", emboss = False)
                return
            
            if context.scene.other_props.expand_area_butmtl:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_MtlSettings", text="Material", icon="NODE_MATERIAL", emboss = False)
                if context.scene.other_props.expand_area_MtlSettings:
                    
                    rowd = box.column()
                    row1 = rowd.row()
                    row1.label(text= "Material Set Name")
                    row1.prop(part, "name", text="")
                    row1 = rowd.row()
                    row1.label(text= "Select Maps")
                    row1.operator("haspaint.setusedmaps", text="Maps", icon='COLLAPSEMENU')

                    row1 = rowd.row()
                    row1.label(text= "Shader Type")
                    row1.prop(part, "shader_type", text="")
                    row1 = rowd.row()
                    row1.label(text= "Texture filtering")
                    row1.prop(part, "texture_filtering", text="")
                    row1 = rowd.row()
                    row1.label(text= "UV Channel")
                    row1.prop(part, "uvs", text="")
                    row1 = rowd.row()
                    row1.label(text= "Height Intensity")
                    row1.prop(part, "height_intensity", text="")
                    row1 = rowd.row()
                    row1.label(text= "Transparency Mode")
                    row1.prop(part, "opacity_mode", text="")
                    row1 = rowd.row()
                    row1.label(text= "Alpha")
                    row1.prop(part, "diffusealpha", text="Use Diffuse Alpha", toggle = True)
                    row1 = rowd.row()
                    row1.label(text= "Invert G in Normal")
                    row1.prop(part, "InvertG", text="")
                    # row1 = rowd.row()
                    # row1.label(text= "Fix")
                    # row1.prop(part, "colorfix", text="")
                    
                    row = box.row(align=False)
                    row.label(text="Texture size")
                    txl = row.operator("haspaint.texture_size_add_subtract", text="", icon='ADD')
                    txl.add = True
                    txl.isbake = False
                    txl = row.operator("haspaint.texture_size_add_subtract", text="", icon='REMOVE')
                    txl.add = False
                    txl.isbake = False
                    row.prop(part, "texture_sizeX", text="X")
                    row.prop(part, "texture_sizeY", text="Y")
                    box = box.box()
                    box.prop(context.scene.other_props, "expand_area_DefaultMaterial", text="Default Material Values", icon="PROPERTIES", emboss = False)
                    if context.scene.other_props.expand_area_DefaultMaterial:
                        node = get_node_by_name(bpy.context.active_object.active_material.node_tree, part.node)

                        if node:
                            colsq = box.column(align=False)
                            for ind, input_socket in enumerate(node.inputs):
                                colsqrow=colsq.row(align = True)
                                if input_socket.type == "RGBA":
                                    colsqrow.label(text = input_socket.name)
                                    colsqrow.prop(input_socket, "default_value", text="")
            
            if context.scene.other_props.expand_area_buttools:
                box = boxw.box()
                box.prop(context.scene.other_props, "expand_area_ProjectTexture", text="Tools", icon="TOOL_SETTINGS", emboss = False)
                if context.scene.other_props.expand_area_ProjectTexture:
                    rws = box.row()
                    op = rws.operator("haspaint.activate_tab", text="Quick Edit", icon="OUTLINER_OB_IMAGE", emboss = context.scene.other_props.expand_area_QuickEdit)
                    op.activate_tab = 0
                    
                    op = rws.operator("haspaint.activate_tab", text="Masking", icon="MOD_MASK", emboss = context.scene.other_props.expand_area_DepthSelection)
                    op.activate_tab = 1
                    
                    op = rws.operator("haspaint.activate_tab", text="Paint Tools", icon="BRUSH_DATA", emboss = context.scene.other_props.expand_area_PaintTools)
                    op.activate_tab = 2
                    
                    op = rws.operator("haspaint.activate_tab", text="Bake", icon="OUTLINER_OB_VOLUME", emboss = context.scene.other_props.expand_area_Bake)
                    op.activate_tab = 3

                    if context.scene.other_props.expand_area_QuickEdit:
                        boxs = box.box()
                        rowq = boxs.row(align=False)

                        if not context.scene.view_settings.view_transform == "Standard":
                        
                            rowqs = boxs.row(align=False)
                            spl = rowqs.split(factor = 0.8)
                            spl.column().label(text = f"{context.scene.view_settings.view_transform} Will Cause Issues With Colors")
                            spl.alert = True
                            spl.column().operator("haspaint.setstandardvt", text="Fix", icon='ERROR')
                            
                        if bpy.context.preferences.filepaths.image_editor:
                            global operator_running
                            rowq.alert = operator_running
                            rowq.operator('haspaint.crop_tool', text="Select region for quick edit", icon="OBJECT_DATAMODE")
                            
                            rowq.prop(context.scene.other_props, "screen_capture_scale", text="Capture scale")
                            rowq.operator('haspaint.setquefolder', text="", icon="FILE_FOLDER")

                            for index, vd in enumerate(context.scene.view_data):

                                rowq = box.row()

                                op = rowq.operator('haspaint.snap_to_view', text="", icon = "SCREEN_BACK")
                                op.index = index
                                op = rowq.operator(ProjectApply.bl_idname, text="", icon = "IMPORT")
                                op.index = index
                                op = rowq.operator(ProjectOpen.bl_idname, text=vd.image_name, icon = "FILE_IMAGE")
                                op.index = index
                                op = rowq.operator(ProjectRemove.bl_idname, text="", icon = "PANEL_CLOSE")
                                op.index = index
                        else:
                            rowq.label(text="External Image Editor Path:")
                            rowq.prop(context.preferences.filepaths, "image_editor", text="")

                    if context.scene.other_props.expand_area_DepthSelection:
                        boxs = box.box()
                        boxs.label(text="Mask by depth")
                        bxsplit = boxs.split(factor=0.5)
                        rowq = bxsplit.column(align=True)
                        rowq.prop(context.scene.debugplane_props, "plane_size", text="Size")
                        rowq.prop(context.scene.debugplane_props, "plane_color", text="")

                        rowq = bxsplit.column(align=True)
                        rowqrs = rowq.row(align =True)
                        rowqrs.operator("haspaint.depth_mask_operator", text="Select By Depth", icon = "CLIPUV_DEHLT")
                        rowqrs.prop(context.scene.debugplane_props, "depth_distance", text = "Depth")

                        rowq.operator("haspaint.adjust_depth_distance_operator", text="Adjust Depth", icon = "ARROW_LEFTRIGHT")
                    
                    if context.scene.other_props.expand_area_PaintTools:
                        boxs = box.box()
                        boxs.label(text = "Paint By")

                        row = boxs.row(align=False)
                        row.operator("haspaint.paint_by_selection", text="Face", icon="SNAP_FACE").mode = 'POLYGON'
                        row.operator("haspaint.paint_by_selection", text="UV", icon="UV_DATA").mode = 'UV_ISLAND'
                        row.operator("haspaint.paint_by_selection", text="Part", icon="SNAP_VOLUME").mode = 'PART'

                    if context.scene.other_props.expand_area_Bake:
                        boxs = box.box()
                        baking_props = part.baking_props
                        colboxs = boxs.column(align = True)
                        boxe = colboxs.box()
                        brow = boxe.row(align = True)
                        brow.prop(baking_props, "visible_hp", text="", icon = 'HIDE_OFF' if baking_props.visible_hp else "HIDE_ON", emboss = False)
                        brow.prop(baking_props, "expand_hp", text=f"High ({len(baking_props.high_poly_obj)-1})", icon="MESH_UVSPHERE", emboss = False)
                        
                        orp = brow.operator("haspaint.remove_all_bake_objects", text="", icon='TRASH', emboss = False)
                        orp.hp = True

                        if baking_props.expand_hp:
                            colbox = boxe.column(align = True)
                            for ob in baking_props.high_poly_obj:
                                colbox.prop(ob, "obj", text ="")
                            if len(baking_props.high_poly_obj)==0:
                                colbox.label(text = "Empty collection")

                        boxe = colboxs.box()
                        brow = boxe.row(align = True)
                        brow.prop(baking_props, "visible_lp", text="", icon = 'HIDE_OFF' if baking_props.visible_lp else "HIDE_ON", emboss = False)
                        brow.prop(baking_props, "expand_lp", text=f"Low ({len(baking_props.low_poly_obj)-1})", icon="MESH_ICOSPHERE", emboss = False)
                        
                        orp = brow.operator("haspaint.remove_all_bake_objects", text="", icon='TRASH', emboss = False)
                        orp.hp = False
                        if baking_props.expand_lp:
                            colbox = boxe.column(align = True)
                            for ob in baking_props.low_poly_obj:
                                colbox.prop(ob, "obj", text ="")
                        if baking_props.high_poly_obj or baking_props.low_poly_obj:
                            
                            hps = baking_props.gethpobjects(context)
                            lps = baking_props.getlpobjects(context)
                            for eg in lps:
                                if eg:
                                    if eg in hps:
                                        boxe = colboxs.box()
                                        boxe.label(text = "Duplicate object found, collections should have unique objects")
                                        break

                            rowg1 = colboxs.box()
                            rowg = rowg1.row(align = True)
                            
                            rowg.prop(baking_props, "visible_cage", text="", icon = 'HIDE_OFF' if baking_props.visible_cage else "HIDE_ON", emboss = False)
                            rowg.prop(baking_props, "use_cage", text="Cage", icon="CUBE", emboss = baking_props.use_cage)
                            
                            if baking_props.use_cage:
                                rowg.prop(baking_props, "smooth_cage", text="Smooth Cage", icon="META_PLANE" if baking_props.smooth_cage else "MESH_PLANE")
                                rowg = rowg1.row()
                                rowg.prop(baking_props, "cage_depth", text="Offset")
                                rowg.prop(baking_props, "cage_color", text="")
                                
                        boxs = boxs.box()
                        rowt = boxs.row(align=False)
                        rowt.label(text="Size")
                        txb = rowt.operator("haspaint.texture_size_add_subtract", text="", icon='ADD')
                        txb.add = True
                        txb.isbake = True
                        txb = rowt.operator("haspaint.texture_size_add_subtract", text="", icon='REMOVE')
                        txb.add = False
                        txb.isbake = True
                        rowt.prop(baking_props, "bake_image_sizeY", text="")
                        rowt.prop(baking_props, "bake_image_sizeX", text="")
                        rowt = boxs.row(align=False)
                        rowt.label(text="Settings")
                        rowt.prop(baking_props, "samples", text="Samples")

                        rowt = boxs.row(align=False)
                        rowt.label(text="Maps")
                        rowt.operator("haspaint.add_bake_map", text="", icon="ADD")

                        for ind, bake_map in enumerate(part.bake_maps):

                            box2 = boxs.row()
                            box2.prop(bake_map, "use_map", text='', icon="SHADING_RENDERED" if bake_map.use_map else "SHADING_WIRE", icon_only = True)

                            if bake_map.type == "HEIGHT" or bake_map.type == "DIFFUSE":
                                if not baking_props.high_poly_obj:
                                    box2.label(text = "No Bake Source Selected",icon = "ERROR")
                            if bake_map.image:
                                slct = bpy.context.scene.other_props.preview_image == bake_map.image
                                    
                                isolate = box2.operator("haspaint.isolate_image", text="", icon = "IMAGE_REFERENCE", depress = slct)
                                isolate.texture_name= bake_map.image.name
                            bpr = box2.operator("haspaint.bakemapprefs", text="",icon = "TOOL_SETTINGS")
                            bpr.bake_type = bake_map.type
                            box2.prop(bake_map, "type", text="")
                            
                            box2.template_ID(bake_map, "image", open="image.open", text ="")
                            box2.operator("haspaint.remove_bake_map", text="", icon="REMOVE").index = ind
                        
                        rowt = boxs.row(align=False)
                        rowt.enabled = True if part.bake_maps else False
                        rowt.scale_y = 2.0
                        rowt.operator("haspaint.bake_textures", text = "Bake", icon = "OUTLINER_OB_VOLUME")

            if context.scene.other_props.expand_area_butlayers:
                rowl = layout.row(align=False)
                box = rowl.box()
                row = box.row(align=False)
                nimg=row.operator("haspaint.custom_new", text="", icon='BRUSH_DATA', emboss = False)
                nimg.fill = False
                box = rowl.box()
                row = box.row(align=False)
                nimg = row.operator("haspaint.custom_new", text="", icon='IMAGE', emboss = False)
                nimg.fill = True

                box = rowl.box()
                row = box.row(align=False)
                row.operator("haspaint.create_pbr", text="", icon='NODE_MATERIAL', emboss = False)

                box = rowl.box()
                row = box.row(align=False)
                row.operator("haspaint.create_folder", text="", icon='FILE_FOLDER', emboss = False)

                rowl.label(text="")
                box = rowl.box()
                row = box.row(align=False)
                row.prop(context.scene.other_props, "preview_mode", text="", icon='SHADING_RENDERED',icon_only=True, emboss = False)
                box = rowl.box()
                row = box.row(align=False)
                row.prop(part, "mtl_actions", text="", icon='COLLAPSEMENU',icon_only=True, emboss = False)
                
                part = get_material_collection()
                if not part:
                    return
                masks = []
                group_box = None
                if not context.scene.other_props.fixed:
                    rowqs = layout.row()
                    rowqs.alert = True
                    rowqs.operator("haspaint.setupscene", text="Setup Scene", icon='SCENE_DATA')
                    rowqs.scale_y = 2.0
                rowqs = layout.row()
                
                for templayer in reversed(part.base_layers):
                    rowl = layout.row()
                    layer = templayer.get_layer()
                    if layer:
                        layerbox(self, context, rowl, part.base_layers, masks, templayer.index, None)

def layerbox(self, context, layout, layers, masks, index, parent):
    part = get_material_collection()

    layer = layers[index].get_layer()
    alt = True
    if layer.layer_type == "FOLDER":
        row, fold = folderbox(self, context, layout, layer, masks, layer.index)
        if not fold:
            for subl in reversed(layer.sub_layers):
                layerbox(self, context, row, layer.sub_layers, masks, subl.index, layer)
        return
    if layer.collapse_box:
        compactlinelayerbox(self, context, layout, layers, masks, index)
        return
        
    box = layout.box()
    
    selected, selectedalpha, selnm, sameimg = is_selected(layer)

    if can_be_added_to(layer):
        lrfld = getbyid(part.addtofolder)
        if lrfld:
            split = box.split(factor=0.06)
        
            conts = layer in get_layers(getbyid(part.addtofolder).sub_layers)

            adf = split.operator("haspaint.layer_to_folder", text="", icon='PANEL_CLOSE'if conts else "ADD")
            adf.layer_index = layer.index
            box = split

    if selected and not selectedalpha:
        ics = 'SNAP_FACE'
    else:
        ics = 'SHADING_BBOX'
    if alt:
        ics = "SNAP_FACE" if selected else "SHADING_BBOX"
    
    msp = 0.25 if not alt else 0.2
    
    split = box.split(factor= msp)
    
    imsplit = split
    spim = imsplit.row(align = False)
    left_column = spim.column().row(align = False)
    left_column.scale_y = 3.2 if not alt else 2.0
    rw = left_column.row()
    rw.enabled = not layer.lock
    resources = layer.resource

    if resources.image:
        if resources.image.preview:
            rw.template_icon(resources.image.preview.icon_id, scale=1.0 if not alt else 1.0)
        else:
            rw.prop(resources, "default_color", text="",emboss  = False)
    else:
        rw.prop(resources, "default_color", text="")
    csr = left_column.column(align = True)
    if layer.lock:
        csr.prop(layer, "lock", text="", icon = "DECORATE_UNLOCKED", emboss = True,invert_checkbox=True)
    else:
        select_op = csr.operator("haspaint.select_texture", text="", icon=ics, depress = selected and not selectedalpha)
        select_op.texture_name = layer.resource.image.name if layer.resource.image else ""
        select_op.id = layer.id
        select_op.alpha= "Remove"

    right_column = split.column()
    right_column.enabled = not layer.lock
    row = right_column.row(align=False)

    uncheck_button = row.operator("haspaint.uncheck_layer", text="", icon='HIDE_OFF' if layer.use_layer else 'HIDE_ON', emboss = False)
    uncheck_button.layer_index = layer.index

    act = row.operator("haspaint.layer_action", text="", icon='COLLAPSEMENU', emboss = False)
    act.layer_index = layer.index

    row.label(icon = "BLANK1")

    if layer.renamebutton:
        row.prop(layer, "layer_name", text="")
    else:
        row.prop(layer, "renamebutton", text=f' {layer.layer_name} ', emboss = False)

    row.prop(layer, "collapse_box", text="", icon = 'RADIOBUT_OFF' if layer.sort_color == "PANEL_CLOSE" else layer.sort_color, emboss = False)

    row = right_column.row(align=True)

    if layer.layer_type == "PBR":
        if layer.mask:
            rowfe = row.row()
            select_op = rowfe.operator("haspaint.select_texture", text="", icon='CLIPUV_DEHLT', depress = selected and selectedalpha)
            select_op.texture_name = ""
            select_op.id = layer.id
            select_op.alpha= "Set"
            if selectedalpha:
                #if layer.mask_value.get_socket():
                #    rowfe.prop(layer.mask_value, "default_value", text="", slider = True)
                rowfe.prop(layer, "mask_value", text="White Mask" if layer.mask_value else "Black Mask", icon = 'SNAP_FACE'  if layer.mask_value else 'COLORSET_16_VEC')
                addpaint = rowfe.operator("haspaint.add_layer_filter", text="Add Paint", icon='BRUSH_DATA')
                addpaint.layer_index = layer.index
                addpaint.type = "PAINT"
        if not selectedalpha:
            if layer.layer_type == "PBR" or layer.layer_type == "FOLDER":
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_sublayers", text="", icon = "RENDERLAYERS")
            if layer.filters:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_filters", text="", icon = "SHADERFX")
            for foundsubl in get_layers(layer.sub_layers):
                if foundsubl:
                    select_op = row.operator("haspaint.uncheck_layer", text=f"{getlabel(foundsubl.texture_type)}", emboss = foundsubl.use_layer)
                    select_op.layer_index = foundsubl.index

        move_up = row.operator("haspaint.move_layer", text="", icon='TRIA_UP', emboss = not alt)
        move_up.layer_index = index

        move_up.direction = 'UP'
    else:
        if alt:
            if layer.mask:
                rowfe = row.row()
                select_op = rowfe.operator("haspaint.select_texture", text="", icon='CLIPUV_DEHLT', depress = selected and selectedalpha)
                select_op.texture_name = ""
                select_op.id = layer.id
                select_op.alpha= "Set"
                if selectedalpha:
                    #if layer.mask_value.get_socket():
                    #    rowfe.prop(layer.mask_value, "default_value", text="", slider = True)
                    rowfe.prop(layer, "mask_value", text="White Mask" if layer.mask_value else "Black Mask", icon = 'SNAP_FACE'  if layer.mask_value else 'COLORSET_16_VEC')
                    addpaint = rowfe.operator("haspaint.add_layer_filter", text="Add Paint", icon='BRUSH_DATA')
                    addpaint.layer_index = layer.index
                    addpaint.type = "PAINT"
            if not selectedalpha:
                if layer.layer_type == "PBR" or layer.layer_type == "FOLDER":
                    rowfe = row.row()
                    rowfe.enabled = selected
                    rowfe.prop(layer, "expand_sublayers", text="", icon = "RENDERLAYERS")
                if layer.filters:
                    rowfe = row.row()
                    rowfe.enabled = selected
                    rowfe.prop(layer, "expand_filters", text="", icon = "SHADERFX")
                typeselect = row.operator("haspaint.type_select", text=getlabel(layer.texture_type), emboss = False)
                typeselect.layer_index = layer.index
                typeselect.current = layer.texture_type
                
        if not selectedalpha:
            row.prop(layer, "blend_mode", text="", emboss = not alt)

            row.prop(layer, "opacity", text="Opacity" if not alt else "", emboss = not alt)

        move_up = row.operator("haspaint.move_layer", text="", icon='TRIA_UP', emboss = not alt)
        move_up.layer_index = index
        move_up.parent = parent.index if parent else -1
        move_up.direction = 'UP'
        if not alt:
            row = right_column.row(align=True)

            if masks:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_sublayers", text="", icon = "RENDERLAYERS")
            if layer.filters:
                rowfe = row.row()
                rowfe.enabled = selected
                rowfe.prop(layer, "expand_filters", text="", icon = "SHADERFX")

            if not selectedalpha:
                row.prop(layer, "texture_type", text="", emboss = not alt)

    move_down = row.operator("haspaint.move_layer", text="", icon='TRIA_DOWN', emboss = not alt)
    move_down.layer_index = index
    move_up.parent = parent.index if parent else -1
    move_down.direction = 'DOWN'

    if layer.expand_sublayers:
        if layer.layer_type== "PBR": 
            if selected:
                for foundsubl in get_layers(layer.sub_layers):
                    if foundsubl.use_layer:
                        rowbox = right_column.box()
                        compactlayerbox(self, context, rowbox, foundsubl, None,selected, layer)

    sel = False
    contalpha = False
    contcol = False
    if layer.expand_filters:
        for f in layer.filters:
            if f.resource.image:
                if f.resource.image.name == context.scene.selected_texture:
                    sel = True
            if f.connection_type == 'ALPHA':
                contalpha = True
            elif f.connection_type == 'COLOR':
                contcol = True
        if selectedalpha:        
            if not contalpha:
                return right_column
        else:        
            if not contcol:
                return right_column
        if layer.filters:
            if selected or sel:
                rowbox = right_column.column(align = True)
                for findex, filter in enumerate(reversed(layer.filters)):

                    if selectedalpha:
                        if not filter.connection_type == 'ALPHA':
                            continue
                    else:
                        if not filter.connection_type == 'COLOR':
                            continue
                    findex = len(layer.filters) - 1 - findex
                    uifilter(self, context, layer, filter, findex,rowbox,layer.index)

    return right_column

def compactlinelayerbox(self, context, layout, layers, masks, index):
    part = get_material_collection()
    layer = layers[index].get_layer()
    alt = True

    selnm= ""
    selected = layer.id == part.selected_layer
    selectedalpha = False
    if selected:
        selectedalpha = part.selected_alpha
    if layer.resource.image:
        selnm = layer.resource.image.name
        if not selectedalpha:
            selected = context.scene.selected_texture == layer.resource.image.name
            
    row = layout.box().row(align= True)
    if selected and not selectedalpha:
        ics = 'SNAP_FACE'
    else:
        ics = 'SHADING_BBOX'
    if alt:
        ics = 'BLANK1'

    select_op = row.operator("haspaint.select_texture", text="", icon=ics, depress = selected and not selectedalpha)
    select_op.texture_name = selnm
    select_op.id = layer.id
    select_op.alpha= "Remove"

    uncheck_button = row.operator("haspaint.uncheck_layer", text="", icon='HIDE_OFF' if layer.use_layer else 'HIDE_ON')
    uncheck_button.layer_index = layer.index

    row.prop(layer, "blend_mode", text="", emboss = False)
    row.prop(layer, "texture_type", text="", emboss = False)

    opas = row.operator("haspaint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss = False)
    opas.layer_index = layer.index
    if layer.sort_color == "PANEL_CLOSE":
        if layer.renamebutton:
            row.prop(layer, "layer_name", text="")
        else:
            row.prop(layer, "renamebutton", text=layer.layer_name, emboss = False)
    else:
        if layer.renamebutton:
            row.prop(layer, "layer_name", text="")
        else:
            row.prop(layer, "renamebutton", text=layer.layer_name, emboss = False)
    
    move_up = row.operator("haspaint.move_layer", text="", icon='TRIA_UP')
    move_up.layer_index = layer.index
    move_up.direction = 'UP'

    move_down = row.operator("haspaint.move_layer", text="", icon='TRIA_DOWN')
    move_down.layer_index = layer.index
    move_down.direction = 'DOWN'
    row.prop(layer, "collapse_box", text="", icon = 'RADIOBUT_OFF' if layer.sort_color == "PANEL_CLOSE" else layer.sort_color, emboss = False)

def folderbox(self, context, layout, layer, masks, index):
    part = get_material_collection()
    if layer.lock:
        layout.prop(layer, "lock", text="", icon = "DECORATE_UNLOCKED", emboss = False)
    box = layout.box()
    box.enabled = not layer.lock
    row = box.row(align = True)

    selected, selectedalpha, selnm, sameimg= is_selected(layer)
    select_op = row.operator("haspaint.select_texture", text="", icon="SNAP_FACE" if selected else "SHADING_BBOX", depress = selected)
    select_op.texture_name = selnm
    select_op.id = layer.id
    select_op.alpha= "Remove"
    if layer.mask:
        select_op = row.operator("haspaint.select_texture", text="", icon='CLIPUV_DEHLT', depress = selected and selectedalpha)
        select_op.texture_name = selnm
        select_op.id = layer.id
        select_op.alpha= "Set"
    row.prop(layer, "collapse_box", text="",icon = layer.sort_color, invert_checkbox = True, emboss = not layer.collapse_box)
    adf=row.operator("haspaint.startaddtofolder", text="", icon='PLUS', depress = True if part.addtofolder == layer.id else False, emboss = True if part.addtofolder == layer.id else False)
    adf.layer_index = layer.index

    uncheck_button = row.operator("haspaint.uncheck_layer", text="", icon='HIDE_OFF' if layer.use_layer else 'HIDE_ON', emboss = False)
    uncheck_button.layer_index = index
    act = row.operator("haspaint.layer_action", text="", icon='COLLAPSEMENU', emboss = False)
    act.layer_index = layer.index
    
    if layer.filters:
        rowfe = row.row()
        rowfe.enabled = selected
        rowfe.prop(layer, "expand_filters", text="", icon = "SHADERFX")
    
    row.label(icon = "BLANK1")
    if layer.renamebutton:
        row.prop(layer, "layer_name", text="")
    else:
        row.prop(layer, "renamebutton", text=f' {layer.layer_name} ', emboss = False)
    
    row.prop(layer, "blend_mode", text="", emboss = False)

    opas = row.operator("haspaint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss = False)
    opas.layer_index = layer.index

    move_up = row.operator("haspaint.move_layer", text="", icon='TRIA_UP', emboss = False)
    move_up.layer_index = index
    move_up.direction = 'UP'

    move_down = row.operator("haspaint.move_layer", text="", icon='TRIA_DOWN', emboss = False)
    move_down.layer_index = index
    move_down.direction = 'DOWN'
    right_column = box
    sel = False
    contalpha = False
    contcol = False
    if layer.expand_filters and not layer.collapse_box:
        for f in layer.filters:
            if f.resource.image:
                if f.resource.image.name == context.scene.selected_texture:
                    sel = True
            if f.connection_type == 'ALPHA':
                contalpha = True
            elif f.connection_type == 'COLOR':
                contcol = True
        if selectedalpha:        
            if not contalpha:
                return box, layer.collapse_box
        else:        
            if not contcol:
                return box, layer.collapse_box
        if layer.filters:
            if selected or sel:
                rowbox = right_column.column(align = True)
                for findex, filter in enumerate(reversed(layer.filters)):
                    if selectedalpha:
                        if not filter.connection_type == 'ALPHA':
                            continue
                    else:
                        if not filter.connection_type == 'COLOR':
                            continue
                    findex = len(layer.filters) - 1 - findex
                    uifilter(self, context, layer, filter, findex,rowbox,layer.index)

    return box, layer.collapse_box

def compactlayerbox(self, context,layout, layer, masks, allselected, baselayer):

    split = layout
    selected = False
    if layer.resource.image:
        selected = context.scene.selected_texture == layer.resource.image.name

    split = split.split(factor=0.2)
    middle_column = split.column()
    
    row = middle_column.row(align=True)

    row.label(text = getlabel(layer.texture_type))
    rsg = layout.row(align=True)
    
    if not layer.resource.image:
        if layer.texture_type == "DIFFUSE" or layer.texture_type == "EMISSION" or layer.texture_type == "CUSTOM" or layer.texture_type == "NORMAL":
            rsg.prop(layer.resource, "default_color", text="",emboss  = True)
        else:
            rsg.prop(layer.resource, "default_value", text="",emboss  = True, slider = True)

    rsg.prop(layer.resource, "image", text="")
    if not layer.resource.image:
        
        op = rsg.operator("haspaint.open_image_file", text="", icon = "FILE_FOLDER", emboss = True)
        op.layer_index=layer.index
    if layer.resource.image:
        rsg = layout.column(align=True)
        draw_mapping_box(rsg, layer.resource)
    row.scale_y = 1.0

    right_column = split.column(align = True)
    
    row = right_column.row(align=False)

    row.prop(layer, "blend_mode", text="", emboss = False)

    opas = row.operator("haspaint.opacity_controller", text=f"{round(layer.opacity*100)/100}", emboss = False)
    opas.layer_index = layer.index

    if layer.filters:
        rowbox = layout.column(align=True)
        for findex, filter in enumerate(reversed(layer.filters)):
            
            findex = len(layer.filters) - 1 - findex
            uifilter(self, context, layer, filter, findex,rowbox,layer.index)

def uifilter(self, context, layer, filter, index, rowbox, lindex):
    rowbox= rowbox.box()
    row = rowbox.row(align = True)
    if filter.name == 'PAINT':
        if filter.resource.image:
            slct = context.scene.selected_texture == filter.resource.image.name
            select_op = row.operator("haspaint.select_texture", text="", icon='SNAP_FACE' if slct else 'SHADING_BBOX', depress = True if slct else False)
            select_op.texture_name = filter.resource.image.name
            select_op.id = layer.id
            select_op.alpha= "Skip"
    hid = row.operator("haspaint.showhidefilter", text="", icon="HIDE_OFF" if filter.in_use else "HIDE_ON", emboss=False)
    hid.layer_index = lindex
    hid.filter_index = index
    hid.compfilter = False

    row.prop(filter, "edit", text="", icon="TRIA_DOWN" if filter.edit else "TRIA_RIGHT", emboss=False)

    filter_value = next((item for item in FILTERS if item and item[0] == filter.name), None)
    if filter_value:
        op = row.operator("haspaint.filter_select", text=filter_value[1], icon=filter_value[3], emboss=False)
    else:
        op = row.operator("haspaint.filter_select", text="Select Filter", icon='BLANK1', emboss=False)
    op.layer_index = lindex
    op.filter_index = index
 
    if filter.name == 'CUSTOM' and filter.custom_node_tree_p and not filter.edit:
        row.prop_search(filter, "custom_node_tree_p", bpy.data, "node_groups", text = "")
        #row.prop(filter, "custom_node_tree", text="", emboss=False)
    otp = context.scene.other_props

    move_up = row.operator("haspaint.move_filter", text="", icon='TRIA_UP', emboss=False)
    move_up.layer_index = lindex
    move_up.filter_index = index
    move_up.direction = 'UP'
    move_down = row.operator("haspaint.move_filter", text="", icon='TRIA_DOWN', emboss=False)
    move_down.layer_index = lindex
    move_down.filter_index = index
    move_down.direction = 'DOWN'

    remove_filter = row.operator("haspaint.remove_layer_filter", text="", icon='TRASH', emboss=False)
    remove_filter.layer_index = lindex
    remove_filter.filter_index = index

    socket_ui_mapping = {
        'VALUE': 'value',
        'RGBA': 'color',
        'VECTOR': 'vector',
    }
    ignoreinputs = False
    
    if filter.edit:
        if filter.name == 'CUSTOM':
            rowbox.prop_search(filter, "custom_node_tree_p", bpy.data, "node_groups", text = "")
            alt = True
        else:
            alt = False
        row = row.row(align=True)
        node_group = bpy.data.node_groups.get(f"{getlayergroupname(layer)}_filters")

        if node_group:
            
            node = node_group.nodes.get(filter.node_name)
            opr = rowbox.column()
            
            rowsgefs = opr.row()
            rowsgefs.prop(filter, "blend_mode", text='', emboss = False)
            rowsgefs.prop(filter, "opacity", text="Opacity", emboss = False, slider = True)
            rowsge = opr.row(align = True)
            if layer.layer_type == "FOLDER" or layer.layer_type == "PBR" :
                rowsge.prop(filter, "affect_channels", text='', emboss = False)

            if node:
                if filter.name == 'COLORRAMP':
                    rowbox.box().template_color_ramp(node, "color_ramp", expand=False)
                elif filter.name == 'SEPARATERGB':
                    alt = True
                elif filter.name == 'LEVELS':
                    drawlevels(filter.levels, rowbox, histogram_source = layer.resource.image.name if layer.resource.image else None, skipexpand = True)
                    
                elif filter.name == 'CURVERGB':
                    rowbox.box().template_curve_mapping(node, "mapping", type='COLOR', levels=False)

                elif filter.name == 'MASKCOLOR':
                    ros = rowbox.row(align=True)
                    if bpy.context.scene.other_props.preview_image:
                        ros.alert= True

                    if filter.resource.image:
                        isolate = ros.operator("haspaint.isolate_image", text="Preview", icon="IMAGE_REFERENCE" if filter.in_use else "FILE_IMAGE")
                        isolate.texture_name= filter.resource.image.name
                    ros.template_ID(filter.resource, "image", open="image.open", text ="ID Map")

                elif filter.name == 'PAINT':
                    ros = rowbox.row(align=False)
                    ignoreinputs = True
                    islt = False
                    if bpy.context.scene.other_props.preview_image == filter.resource.image:
                        islt = True
                    if filter.resource.image:
                        slct = context.scene.selected_texture == filter.resource.image.name
                        select_op = ros.operator("haspaint.select_texture", text="", icon='SNAP_FACE' if slct else 'SHADING_BBOX', depress = True if slct else False)
                        select_op.texture_name = filter.resource.image.name
                        select_op.id = layer.id
                        select_op.alpha= "Skip"
                        isolate = ros.operator("haspaint.isolate_image", text="", icon="IMAGE_REFERENCE" if filter.in_use else "FILE_IMAGE", depress = islt)
                        isolate.texture_name= filter.resource.image.name

                elif filter.name == 'FILL':
                    ros = rowbox.column(align=False)
                    ignoreinputs = True
                    islt = False
                    if bpy.context.scene.other_props.preview_image == filter.resource.image:
                        islt = True

                    if filter.resource.image:
                        ros.template_ID_preview(filter.resource, "image", open="image.open", rows=4, cols=6, hide_buttons = False)
                    else:
                        ros.template_ID(filter.resource, "image", open="image.open")
                    if not filter.resource.image:
                        rs = ros.row()
                        rs.scale_y = 2.0
                        rs.prop(filter.resource, "default_value" if filter.connection_type == "ALPHA" else "default_color", text="", slider = True)
                    if filter.resource.image:
                        draw_mapping_box(rowbox, filter.resource)
                elif filter.name == 'MASKGEN':
                    ignoreinputs = True
                    ros = rowbox.box() if filter.maskgen.expand else rowbox
                    ros1 = ros.row()
                    ros1.prop(filter.maskgen, "expand", text="Grunge", icon="DISCLOSURE_TRI_DOWN" if filter.maskgen.expand else "DISCLOSURE_TRI_RIGHT", emboss = False)
                    
                    if filter.maskgen.expand:
                        rowcol = ros.column()

                        row1 = rowcol.row()
                        if filter.resource.image:
                            texture = bpy.data.images.get(filter.resource.image.name)
                            if texture and texture.preview:
                                icon_id = texture.preview.icon_id
                                row1.template_icon(icon_id, scale=2.0)
                        else:
                            row1.label(text = "Choose Image")

                        row1.template_ID(filter.resource, "image", open="image.open", text ="")
                        if filter.resource.image:
                            rowcol.prop(filter.resource, "expand_mapping", text="Mapping", icon="TEXTURE", emboss = False)
                            box = rowcol.column()
                            if filter.resource.expand_mapping:
                                
                                rwbs = box.row()
                                rwbs.label(icon = "MOD_EDGESPLIT")
                                rwbs.prop(filter.resource, "repeat", text="")
                                bws = box.row(align = True)
                                bws.label(text = "Offset")
                                bws = box.row(align = True)
                                bws.prop(filter.resource, "mapx", text="X")
                                bws.prop(filter.resource, "mapy", text="Y")
                                bws = box.row(align = True)
                                bws.label(text = "Scale")
                                bws = box.row(align = True)
                                bws.prop(filter.resource, "mapscalex", text="")
                                bws.prop(filter.resource, "mapscaley", text="")
                                bws = box.row(align = True)
                                bws.label(text = "Rotate")
                                bws.prop(filter.resource, "maprot", text="")

                            box.prop(filter.resource.levels, "expand", text="Levels", icon="SEQ_HISTOGRAM", emboss = False)
                        
                            if filter.resource.levels.expand:
                                rowcol = rowcol.box()
                                nodein = filter.resource.levels.levels_node.get_node()
                                if nodein:
                                    drawlevels(filter.resource.levels, rowcol, histogram_source = filter.resource.image.name, skipexpand = True)
                    
                    for itm in MASKITEMS:
                        maskitem = filter.maskgen.get_item(itm[0]) 
                        cols = rowbox.column(align = True)
                        if maskitem:
                            bros = cols.box() if getattr(filter.maskgen, itm[3], None) else cols
                            bros.prop(filter.maskgen, itm[3],text =f"{itm[0]} Static" if maskitem.image else f"{itm[0]} Realtime", toggle = True, emboss = False, icon="DISCLOSURE_TRI_DOWN" if getattr(filter.maskgen, itm[3], None) else "DISCLOSURE_TRI_RIGHT",)
                            if getattr(filter.maskgen, itm[3], None):
                                brosrow = bros.row()
                                brosrow.label(text= "" if maskitem.image else "Optionally Choose Baked Map")
                                brosrow.template_ID(maskitem, "image", open="image.open", text ="")
                                nodein = maskitem.levels.levels_node.get_node()
                                if nodein:
                                    drawlevels(maskitem.levels, bros, histogram_source = maskitem.image.name if maskitem.image else "", skipexpand = True,compact = True)

                elif filter.name == "LIGHT":
                    filnd = filter.displnode.get_node()
                    if filnd:
                        rowbox.prop(filnd.outputs[0], "default_value", text = "")
                    if not filter.resource.image:
                        rowbox.label(text="Create Object Normal Map before applying or exporting")
                    rowbox.template_ID(filter.resource, "image", text ="Object Normal Map")
                
                if not ignoreinputs:
                    uiinputs(rowbox,node,layer, index, filter, lindex, alt)
      
        if filter.name == 'SNAPSHOT' or filter.name == 'BLUR':
            rosb = rowbox.box()
            ros = rosb.row(align=True)
            op = ros.operator("haspaint.open_website", text="", icon="QUESTION")
            op.link = "https://hirourk.github.io/HASPaintLayersWiki/03Filters"
            if filter.name == 'BLUR':
                bi = ros.operator("haspaint.snapshotlayer", text="Apply Blur", icon="OUTLINER_OB_IMAGE")
                bi.layer_index = lindex
                bi.filter_index = index
                ros.prop(filter, "Unspval", text ="Blur Size")
            else:
                bi = ros.operator("haspaint.snapshotlayer", text="Snapshot", icon="OUTLINER_OB_IMAGE")
                bi.layer_index = lindex
                bi.filter_index = index

            bi.layer_index=lindex
            bi.filter_index=index
            bi.addfilter = filter.name
            bi.addfiltervalue = filter.Unspval

def ui_common_inputs(layout, node):
    socket_ui_mapping = {
        'VALUE': 'value',
        'RGBA': 'color',
        'VECTOR': 'vector',
    }

    for ind, input_socket in enumerate(node.inputs):
        socket_type = input_socket.type
        socket_ui_type = socket_ui_mapping.get(socket_type)
        if socket_ui_type:
            socket_id = f"{input_socket.name}_{ind}"
            layout.prop(input_socket, "default_value", text=input_socket.name)

def uiinputs(rowbox,node, layer, index, filter,lindex, alt):
    socket_ui_mapping = {
        'VALUE': 'value',
        'RGBA': 'color',
        'VECTOR': 'vector',
    }
    if alt:
        split = rowbox.split(factor=0.75)
        col = split.column()
        colout = split.column()
    else:
        col = rowbox
    for ind, input_socket in enumerate(node.inputs):
        if not alt:
            if input_socket.is_linked:
                continue
        if input_socket.name == "Fac":
            return
        socket_type = input_socket.type
        socket_ui_type = socket_ui_mapping.get(socket_type)
        filtersockets(input_socket, socket_ui_mapping, col, ind, filter, layer, index, alt)
    if alt:
        for ind, input_socket in enumerate(node.outputs):
            socket_type = input_socket.type
            socket_ui_type = socket_ui_mapping.get(socket_type)
            filtersockets(input_socket, socket_ui_mapping, colout, ind, filter, layer, index, alt, inp = False)

def filtersockets(input_socket, socket_ui_mapping, col, ind, filter, layer, index, hide, inp = True):
    
    socket_type = input_socket.type
    socket_ui_type = socket_ui_mapping.get(socket_type)
    if socket_ui_type:

        socket_id = f"{input_socket.name}_{ind}"
        rowc = col.row(align=False)
        sc = filter.socket_in if inp else filter.socket_out
        rowc.enabled = not input_socket.is_linked
        if hide:
            cinput = rowc.operator("haspaint.filter_inout", text="", icon="RADIOBUT_ON" if sc == ind else "RADIOBUT_OFF", emboss=False)
            cinput.layer_index = layer.index
            cinput.filter_index = index
            cinput.inputind = ind
            
            cinput.inpout = inp
        
        rowc.prop(input_socket, "default_value", text=input_socket.name, slider = True)

def drawresource(layout, resource):
    box = layout.column()
    box.template_ID(resource, "image", new="", open='image.open')
    if resource.image: 
        if resource.image.preview:
            
            brr =box.row()
            
            brr.template_ID_preview(resource, "image", open="image.open", rows=4, cols=6, hide_buttons = True)
    else:
        boxe = box.row()
        boxe.prop(resource, "default_color", text="")
        boxe.scale_y = 1.0
    if resource.image: 
        box = box.column()
        box.prop(resource, "repeat", text="")
        bws = box.row()
        bws.prop(resource, "mapx", text="Offset X")
        bws.prop(resource, "mapy", text="Offset Y")
        bws = box.row()
        bws.prop(resource, "mapscalex", text="Scale X")
        bws.prop(resource, "mapscaley", text="Scale Y")
        bws = box.row()
        bws.prop(resource, "maprot", text="Rotate")

def drawlevels(levels, rowbox, histogram_source = "", skipexpand = False, compact = False):
    box = rowbox.row(align = True)
    
    histe = None
    if not skipexpand:
        box.prop(levels, "expand", text="Levels", icon="SEQ_HISTOGRAM", emboss = False)
        if not levels.expand:
            return

    otp = bpy.context.scene.other_props
    count = 70
    b = round(remap_value(levels.val01, 0.0, 1.0, 0.0, count-1))
    w = round(remap_value(levels.val03, 0.0, 1.0, 0.0, count-1))
    m = round(lerp(b, w,levels.val02))
    db = round(remap_value(levels.val04, 0.0, 1.0, 0.0, count-1))
    dw = round(remap_value(levels.val05, 0.0, 1.0, 0.0, count-1))
    inv = b>w
    ignoreinputs = True
    rowbox = rowbox.column(align = True)
    if compact:
        xsb = rowbox.box()
        drawlevels_vis_01(xsb,b,w,m, count = count)
        drawlevels_vis_02(xsb,db,dw, count = count)
    if compact:
        bx = rowbox.row(align = True)
    else:
        bx = rowbox.column(align = True)

    bx.prop(levels, "val01", text="Shadows", slider = True)
    bx.prop(levels, "val02", text="Midtones", slider = True)
    bx.prop(levels, "val03", text="Highlights", slider = True)

    if not compact:
        xsb = rowbox.box()
        if histogram_source:
            sdq = xsb.row()
            sdq.prop(levels, "s_channel", emboss = True, icon_only = True)
            sdq.prop(levels, "expand_levels", text="Histogram", icon="SEQ_HISTOGRAM", emboss = False)
            if levels.expand_levels:
                histe = sdq.operator("haspaint.update_hist", icon = 'FILE_REFRESH', text="", emboss = False)
                histe.texture_name = histogram_source
        drawlevels_vis_01(xsb,b,w,m, count = count)
        if levels.expand_levels:

            if histe:
                name = ".HAS_SceneProperties"
                if name in bpy.data.node_groups:
                    node_group = bpy.data.node_groups[name]
                    histnode = get_node_by_name(node_group, histogram_source)
                    if histnode:
                        wr = xsb.column(align = True)
                        wr.scale_y =0.3
                        wr.enabled = False
                        wr.template_curve_mapping(histnode, "mapping", type='COLOR', levels=False)
        drawlevels_vis_02(xsb,db,dw, count = count)

    if compact:
        bx = rowbox.row(align = True)
    else:
        bx = rowbox.column(align = True)
    bx.prop(levels, "val04", text="Black", slider = True)
    bx.prop(levels, "val05", text="White", slider = True)

def drawlevels_vis_01(layout, b , m , w, count = 70):
    otp = bpy.context.scene.other_props
    row = layout.row(align = True)
    row.scale_y = 0.3
    
    for p in range(count):
        icon = "BLANK1"
        if p == b:
            icon = 'DECORATE_ANIMATE'
        if p == m:
            icon = 'KEYFRAME'
        if p == w:
            icon = 'DECORATE_KEYFRAME'

        row.prop(otp, "emptyprop", icon_only = True, icon = icon, emboss = False)

def drawlevels_vis_02(layout, db, dw, count = 70):
    otp = bpy.context.scene.other_props

    row = layout.row(align = True)
    row.scale_y = 0.3
    for p in range(count):
        icon = "BLANK1"
        if p == db:
            icon = 'MARKER'
        if p == dw:
            icon = 'MARKER_HLT'
        row.prop(otp, "emptyprop", icon_only = True, icon = icon, emboss = False)

def draw_mapping_box(rowcol, resource):
    rowcol.prop(resource, "expand_mapping", text="Mapping", icon="TEXTURE", emboss = False)
    box = rowcol.column()
    if resource.expand_mapping:
        
        bws = box.row(align = True)
        bws.label(text = "Offset")
        bws = box.row(align = True)
        bws.prop(resource, "mapx", text="X")
        bws.prop(resource, "mapy", text="Y")
        bws = box.row(align = True)
        bws.label(text = "Scale")
        bws = box.row(align = True)
        bws.prop(resource, "mapscalex", text="")
        bws.prop(resource, "mapscaley", text="")
        bws = box.row(align = True)
        bws.label(text = "Rotate")
        bws.prop(resource, "maprot", text="")

class OpacityControlOperatorPOPUP(Operator):
    bl_idname = "haspaint.opacity_controller"
    bl_label = "Opacity"

    layer_index: IntProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        part = get_material_collection()

        layer = part.layers[self.layer_index]
        layout.prop(layer, "opacity", text="Layer Opacity", slider = True)

###
### NODES
###

def get_layers(base_layers):
    layers = []
    for bl in base_layers:
        l = bl.get_layer()
        if l:
            layers.append(bl.get_layer())

    return layers

def create_normal_blend_group():
    name = ".HAS_BlendNormals"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]

        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    
    create_socket(node_group, "Fac", 'float', True)
    create_socket(node_group, "Color1", 'color', True)
    create_socket(node_group, "Color2", 'color', True)

    create_socket(node_group, "Color", 'color', False)

    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    input_node.location = (-500, 0)
    output_node.location = (500, 0)
    math_nodeA = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeA.operation = 'ADD'
    math_nodeA.location = (0,0)
    math_nodeM = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeM.operation = 'MULTIPLY'
    math_nodeM.location = (-300,0)
    math_nodeN = node_group.nodes.new('ShaderNodeVectorMath')
    math_nodeN.operation = 'NORMALIZE'
    math_nodeN.location = (300,0)

    node_group.links.new(input_node.outputs['Color1'], math_nodeA.inputs[0])
    node_group.links.new(input_node.outputs['Color2'], math_nodeM.inputs[0])
    node_group.links.new(math_nodeM.outputs[0], math_nodeA.inputs[1])

    node_group.links.new(input_node.outputs['Fac'], math_nodeM.inputs[1])
    node_group.links.new(math_nodeA.outputs[0], math_nodeN.inputs[0])
    node_group.links.new(math_nodeN.outputs[0], output_node.inputs[0])

    return node_group

def mask_by_color_node(filter, layer):
    node_group = None
    name = f".HAS_SelectColor"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        return node_group
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    node_group.nodes.clear()
    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Sample", 'color', True)
    create_socket(node_group, "Output Color", 'color', True)
    create_socket(node_group, "Threshold", 'float', True)
    Note(node_group)
    
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    set_minmax(node_group, "Threshold", 0.0, 1.0)
    set_default(node_group, "Threshold", 0.1)
    set_default(node_group, "Output Color",(1.0,1.0,1.0,1.0))

    mix = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", 'MIX')
    set_default(mix, 1, (0.0,0.0,0.0,0.0))
    sepimg = create_node(node_group,'ShaderNodeSeparateRGB', -200,0, "", '')
    sepcol = create_node(node_group,'ShaderNodeSeparateRGB', -200,0, "", '')

    comparer = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')
    compareg = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')
    compareb = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'COMPARE')

    mult1 = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
    mult2 = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')

    blendalpha = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MINIMUM')

    links = node_group.links

    links.new(input_node.outputs["Color"],sepimg.inputs[0])
    links.new(input_node.outputs["Sample"],sepcol.inputs[0])

    links.new(sepimg.outputs[0],comparer.inputs[0])
    links.new(sepimg.outputs[1],compareg.inputs[0])
    links.new(sepimg.outputs[2],compareb.inputs[0])
    
    links.new(sepcol.outputs[0],comparer.inputs[1])
    links.new(sepcol.outputs[1],compareg.inputs[1])
    links.new(sepcol.outputs[2],compareb.inputs[1])

    links.new(input_node.outputs["Threshold"],comparer.inputs[2])
    links.new(input_node.outputs["Threshold"],compareg.inputs[2])
    links.new(input_node.outputs["Threshold"],compareb.inputs[2])

    links.new(comparer.outputs[0],mult1.inputs[0])
    links.new(compareg.outputs[0],mult1.inputs[1])
    links.new(mult1.outputs[0],mult2.inputs[0])
    links.new(compareb.outputs[0],mult2.inputs[1])

    links.new(mult2.outputs[0],blendalpha.inputs[0])

    links.new(input_node.outputs["Alpha"],blendalpha.inputs[1])

    links.new(blendalpha.outputs[0],mix.inputs[0])
    links.new(input_node.outputs["Output Color"],mix.inputs[2])

    links.new(mix.outputs[0],output_node.inputs["Color"])

    return node_group

def mask_gen_node(filter, layer, part):
    node_group = None
    name = getfiltergroupname(filter)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
    if not node_group:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)

    for node in  node_group.nodes:
        safe = False
        for itm in MASKITEMS:
            maskitem = filter.maskgen.get_item(itm) 
            if maskitem:
                if maskitem.levels.levels_node.get_node() == node:
                    safe = True
        if not safe:
            node_group.nodes.remove(node)

    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    links = node_group.links

    lastmaxconnection=input_node.outputs[0]
    
    lastmaxconnection = None
    filter.node_tree = node_group
    image_node = create_image_node(node_group, filter.resource.image, resource = filter.resource)
    
    levels_node = levels(node_group, image_node.outputs[0], filter.levels, id =filter.id)
    filter.node_name = levels_node.name
    filter.resource.levels.levels_node.set_node_reference(levels_node)
    #filter.resource.mapping_node.set_node_reference(mappingnode)

    blendalpha = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'SUBTRACT')
    prevao = None
    prevcurve = None
    prevpos = None
    prevobn = None
    for itm in MASKITEMS:
        maskitem = filter.maskgen.get_item(itm[0]) 
        if maskitem:
            if maskitem.image:
                masknode = create_image_node(node_group, maskitem.image)
                
                lastcol = masknode.outputs[0]
            else:
                masknode = create_node(node_group, itm[1], -600,0, "", "")
                if itm[0] == "Curvature":
                    masknode.inside = True

                lastcol = masknode.outputs[itm[2]]
            if itm[0] == "Position":
                Dot = create_node(node_group,'ShaderNodeVectorMath', -600,0, "op", "DOT_PRODUCT")
                set_default(Dot,1,(0.0,0.0,1.0))
                links.new(lastcol,Dot.inputs[0])
                lastcol = Dot.outputs["Value"]
            if itm[0] == "AO":
                prevao = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Curvature":
                prevcurve = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Position":
                prevpos = levels(node_group, lastcol, maskitem.levels).outputs[0]
            if itm[0] == "Object Normal":
                prevobn = levels(node_group, lastcol, maskitem.levels).outputs[0]
    if prevao and prevcurve and prevpos and prevobn:
        aocurve = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(aocurve,0,1.0)
        links.new(prevao,aocurve.inputs[1])
        links.new(prevcurve,aocurve.inputs[2])
        acpos = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(acpos,0,1.0)
        links.new(aocurve.outputs[0],acpos.inputs[1])
        links.new(prevpos,acpos.inputs[2])
        
        lastmix = create_node(node_group, 'ShaderNodeMixRGB', -600,0, "mix", "SUBTRACT")
        set_default(lastmix,0,1.0)
        links.new(levels_node.outputs[0],lastmix.inputs[1])
        links.new(acpos.outputs[0],lastmix.inputs[2])
        lastcol = lastmix.outputs[0]
        links.new(lastcol,output_node.inputs['Color'])
    return node_group

def getlayergroupname(layer):
    if layer:
        return f".HAS_{layer.id}_layer"
    return f"Undifined_layer"

def getfiltergroupname(filter):
    if filter:
        if filter.id:
            return f".HAS_{filter.id}_filter"
    return f"Undifined_filter"

def getmaterialgroupname(part):
    return f"HAS_{part.material.name}_Material"

def create_layer_node(layer, pbr = False):
    part = get_material_collection()
    name = getlayergroupname(layer)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    pth = layer.blend_mode== "PASS"

    active_filters = any_active_filter(layer.filters)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    Note(node_group)

    img = layer.resource.image
    links = node_group.links

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    lastconnection = None
    lastclipmaskconnection = None

    if img:
        image_node = create_image_node(node_group, img, resource = layer.resource)
        lastconnection = image_node.outputs[0]
        if layer.texture_type == "NORMAL" and layer.resource.image.colorspace_settings.name == "sRGB":
            gamma = create_node(node_group,'ShaderNodeGamma', -200,0, "", '')
            set_default(gamma,1, 0.454)
            lastconnection = gamma.outputs[0]
            links.new(image_node.outputs[0], gamma.inputs[0])
    math_node = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')

    initialmask = None
    if layer.mask:
        initialmask = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
        initialmask.name = "InitialMask"
        initialmask.inputs[0].name = "MaskValue"
        set_default(initialmask, 0, 1.0 if layer.mask_value else 0.0)
        set_default(initialmask, 1, 1.0)
        #layer.mask_value.set_socket_reference(initialmask.inputs[1])
    #else:
        #layer.mask_value.set_socket_reference(math_node.inputs[0])

    set_default(math_node, 0, 1.0)    
    set_default(math_node, 1, layer.opacity)
    math_node.inputs[1].name = 'OpSock'
    layer.opacity_socket.set_socket_reference(math_node.inputs[1])
    
    if layer.blend_mode == "COMBNRM":
        mix_node = create_node(node_group, 'ShaderNodeGroup' , -600,0, "cus", ".HAS_BlendNormals")
    else:
        if not pth:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", layer.blend_mode)
        else:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "MIX")

        mix_node.use_clamp = True
    
    mix_node.inputs[2].name = "ColSock"
    layer.resource.default_color_socket.set_socket_reference(mix_node.inputs["ColSock"])
    height_remap = None

    # if img:
    #     lastconnection = image_node.outputs[1]
    #     lastclipmaskconnection = image_node.outputs[0]

    if not img:
        set_default(mix_node, 'ColSock', layer.resource.default_color)

    if layer.texture_type == "HEIGHT" and img and layer.blend_mode == 'ADD':
        height_remap= create_node(node_group,'ShaderNodeMapRange', 0,0, "", "")
        height_remap.clamp = False
        set_default(height_remap, 3, -0.5)
        set_default(height_remap, 4, 0.5)
        
    if pth:
        lastconnection = input_node.outputs["Color"]
        lastclipmaskconnection = input_node.outputs["Alpha"]
    else:
        if img:
            if height_remap:
                links.new(image_node.outputs[0], height_remap.inputs[0])
                lastconnection = height_remap.outputs[0]
            else:
                if not lastconnection:
                    lastconnection = image_node.outputs[0]
            lastclipmaskconnection = image_node.outputs[1]
    if layer.mask:
        if initialmask and lastclipmaskconnection:
            links.new(lastclipmaskconnection, initialmask.inputs[1])
        if initialmask:
            lastclipmaskconnection = initialmask.outputs[0]
    if active_filters:
        filnode = create_node(node_group,'ShaderNodeGroup', -200,-200, "cus", layer_filter(layer).name)
        set_default(filnode, 'Color', layer.resource.default_color)
        set_default(filnode, 'Alpha', 1.0)
        if lastconnection:
            links.new(lastconnection, filnode.inputs['Color'])
        if lastclipmaskconnection:
            links.new(lastclipmaskconnection, filnode.inputs['Alpha']) 
        lastconnection = filnode.outputs["Color"]
        lastclipmaskconnection = filnode.outputs["Alpha"]
        layer.resource.default_color_socket.set_socket_reference(filnode.inputs["Color"])

    if not lastclipmaskconnection:
        if img:
            lastclipmaskconnection = image_node.outputs[1]

    links.new(input_node.outputs['Color'], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs['Color'])
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    if lastclipmaskconnection:

        links.new(lastclipmaskconnection, math_node.inputs[0])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    
    links.new(math_node.outputs[0], mix_node.inputs['Fac'])

    links.new(math_node.outputs[0], alphablend.inputs[1])
    links.new(input_node.outputs["Alpha"], alphablend.inputs[2])

    links.new(alphablend.outputs[0], output_node.inputs["Alpha"])

    return node_group

def simple_layer(name, image, opacity, blend_mode, default_color, mixmode = False, resource = None):
    part = get_material_collection()
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    pth = blend_mode== "PASS"

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    Note(node_group)

    img = image
    links = node_group.links

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    lastconnection = None
    lastclipmaskconnection = None

    if img:
        image_node = create_image_node(node_group, img, resource = resource)
    math_node = create_node(node_group,'ShaderNodeMath', -200,0, "op", 'MULTIPLY')
    math_node.name = 'Opacity'
    set_default(math_node, 0, 1.0)    
    set_default(math_node, 1, opacity)
    math_node.inputs[1].name = 'OpSock'

    if blend_mode == "COMBNRM":
        mix_node = create_node(node_group, 'ShaderNodeGroup' , -600,0, "cus", ".HAS_BlendNormals")
    else:
        if not pth:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", blend_mode)
        else:
            mix_node= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "MIX")

        mix_node.use_clamp = True
    mix_node.name = "Color"
    mix_node.inputs[2].name = "ColSock"

    if img:
        lastconnection = image_node.outputs[1]
        lastclipmaskconnection = image_node.outputs[0]
    else:
        set_default(mix_node, 'ColSock', default_color)

    if img:
        lastconnection = image_node.outputs[0]
        lastclipmaskconnection = image_node.outputs[1]
    if not lastclipmaskconnection:
        if img:
            lastclipmaskconnection = image_node.outputs[1]

    links.new(input_node.outputs['Color'], mix_node.inputs[1])
    links.new(mix_node.outputs[0], output_node.inputs['Color'])
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    if lastclipmaskconnection:
        links.new(lastclipmaskconnection, math_node.inputs[0])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)
    if lastconnection:
        links.new(lastconnection, mix_node.inputs[2])
    
    links.new(math_node.outputs[0], mix_node.inputs['Fac'])

    links.new(math_node.outputs[0], alphablend.inputs[1])
    links.new(input_node.outputs["Alpha"], alphablend.inputs[2])

    links.new(alphablend.outputs[0], output_node.inputs["Alpha"])

    return node_group

def layer_filter(layer, multi = False):
    if not layer:
        return None
    part = get_material_collection()

    name = f"{getlayergroupname(layer)}_filters"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        if layer.filters:
            clear_nodes(node_group, layer.filters)
        else:
            simple_clear_node(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    
    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)
    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)

    if not check_for_sockets(group_input.outputs, ["Color","Alpha"]) or not check_for_sockets(group_output.inputs, ["Color","Alpha"]):
        return node_group

    lastcolorconnection = group_input.outputs["Color"]
    lastalphaconnection = group_input.outputs["Alpha"]
    links = node_group.links

    if multi and check_socket(group_input.outputs, "Type"):
        count = -1
        for ch in getusedmaps():
            count = count+1
            type_switch_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", type_switch().name)
            type_switch_node.name = ch[0]
            if "Type" in group_input.outputs:
                links.new(group_input.outputs["Type"], type_switch_node.inputs['Type'])
            set_default(type_switch_node, "Compare", float(count))

    count = 0

    for channel in ["COLOR","ALPHA"]:
        lastconnection = group_input.outputs["Color"] if channel == "COLOR" else group_input.outputs["Alpha"]
        for filter in layer.filters:
            if not filter.name:
                continue
            if not channel == filter.connection_type:
                continue
            alphafiller = False
            ignoresetup = False
            ignoremix = False
            assignalpha = False
            templast = None
            filter.layer_in = layer.id
            if filter.in_use:
                count = count+1
                filternodename = None
                filternode = None
                
                if not filternodename:
                    filternodename = f"{getdescription(FILTERS, filter.name)}"
                Op = None
                optype = ''
                opacitymult= None
                blendfilter = None
                custominput= None
                custominputalpha= None
                if filter.name == 'MAPPING':
                    mappingnode = node_group.nodes.get(filter.node_name)
                    if not mappingnode:
                        mappingnode = create_node(node_group, 'ShaderNodeGroup' , -600,0, "cus", mapping().name)
                        filter.node_name = mappingnode.name
                    links.new(mappingnode.outputs[0],image_node.inputs[0])

                    continue
                elif filter.name == 'CUSTOM':
                    if not filter.custom_node_tree_p:
                        continue
                    Op = f"{filter.custom_node_tree_p.name}"
                    optype = 'cus'
                elif filter.name == "PAINT":

                    lrgroup = simple_layer(f'.HAS_{filter.id}_paint', filter.resource.image, filter.opacity, filter.blend_mode, (0.0,0.0,0.0,0.0), resource = filter.resource)
                    filternode = create_node(node_group, 'ShaderNodeGroup', -200,-200, "cus", lrgroup.name)
                    filter.node_name = filternode.name
                    links.new(lastconnection, filternode.inputs[0])
                    links.new(lastalphaconnection, filternode.inputs[1])
                    filter.opacity_socket.set_socket_reference(get_socket_from_name(lrgroup, "Opacity", "Opacity"))
                    templast = filternode.outputs[0]
                    lastconnection = filternode.outputs[0]
                    ignoresetup = True
                    ignoremix = True
                    lastalphaconnection = filternode.outputs[1]
                elif filter.name == "FILL":
                    lrgroup = simple_layer(f'.HAS_{filter.id}_fill', filter.resource.image, filter.opacity, filter.blend_mode, filter.resource.default_color, resource = filter.resource)
                    filternode = create_node(node_group, 'ShaderNodeGroup', -200,-200, "cus", lrgroup.name)
                    filter.node_name = filternode.name
                    links.new(lastconnection, filternode.inputs[0])
                    links.new(lastalphaconnection, filternode.inputs[1])
                    filter.resource.default_color_socket.set_socket_reference(get_socket_from_name(lrgroup, "Color", "ColSock"))
                    filter.opacity_socket.set_socket_reference(get_socket_from_name(lrgroup, "Opacity", "OpSock"))
                    templast = filternode.outputs[0]
                    
                    ignoresetup = True
                    ignoremix = True
                    assignalpha= False
                    lastalphaconnection = filternode.outputs[1]
                elif filter.name == "LEVELS":
                    filternode = levels(node_group, lastconnection, filter.levels, filter.id)
                    filternodename = filter.node_name
                    filter.node_name = filternode.name
                    templast = filternode.outputs["Color"]
                    ignoresetup = True
                elif filter.name == "MASKCOLOR":
                    Op = f"{mask_by_color_node(filter, layer).name}"
                    optype = 'cus'
                    image_node = create_image_node(node_group, filter.resource.image, resource = filter.resource)
                    filternode = node_group.nodes.get(filter.node_name)
                    if not filternode:
                        filternode = create_node(node_group, filternodename, -200,-200*count, optype, Op)
                    filter.node_name = filternode.name

                    custominput = image_node.outputs[0]
                    custominputalpha=image_node.outputs[1]
                elif filter.name == "MASKGEN":
                    Op = f"{mask_gen_node(filter, layer, part).name}"
                    optype = 'cus'
                elif filter.name == "LIGHT":
                    nqdd = light_node(filter)
                    Op = nqdd.name
                    
                    filter.displnode.set_node_reference(get_node_by_name(nqdd, "fs_LightNormal"))
                    optype = 'cus'
                    alphafiller= True
                elif filter.name == "BLUR":
                    Op = blur_node(filter).name
                    optype = 'cus'
                    assignalpha= True
                elif filter.name == "SNAPSHOT":
                    Op = snapshot_node(filter).name
                    optype = 'cus'
                    assignalpha= True
                    
                if filternodename:
                    
                    if not ignoresetup:
                        filternode = node_group.nodes.get(filter.node_name)
                        if filternode:
                            if filternode.type == 'GROUP' and not filternode.node_tree:
                                filternode = None
                        if not filternode:
                            filternode = create_node(node_group, filternodename, -200,-200*count, optype, Op)
                            filter.node_name = filternode.name
                            
                        else:
                            filternode.location = (-200,-200*count)

                        clear_node_socket_connections(filternode)

                        check_filter_sockets(filter, filternode)

                        if filternode.inputs:
                            if "Color" in filternode.inputs:
                                links.new(lastconnection, filternode.inputs["Color"])
                            else:
                                if filter.socket_in:
                                    links.new(lastconnection, filternode.inputs[filter.socket_in])
                                else:
                                    links.new(lastconnection, filternode.inputs[0])

                        if filternode.outputs:
                            if filter.socket_out:
                                templast = filternode.outputs[filter.socket_out]
                            else:
                                templast = filternode.outputs[0]
                        else:
                            continue
                    if not ignoremix:
                        
                        vldmode = "MIX" if filter.blend_mode == "PASS" or filter.blend_mode =="COMBNRM" else filter.blend_mode
                        blendfilter = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", vldmode)
                        blendfilter.inputs[0].default_value = filter.opacity
                        blendfilter.inputs[0].name = "Opacity"
                        
                        links.new(lastconnection, blendfilter.inputs[1])
                        links.new(templast, blendfilter.inputs[2])
                        if opacitymult:
                            links.new(opacitymult.outputs[0], blendfilter.inputs[0])
                        lastconnection = blendfilter.outputs[0]
                        
                        blendfilter.name = filter.id
                        filter.mixnode = blendfilter.name
                        filter.opacity_socket.set_socket_reference(blendfilter.inputs[0])
                    else:
                        lastconnection = filternode.outputs[0]
                if not filternode:
                    continue
                if channel == "COLOR" and alphafiller:
                    alpbl = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", "MIX")
                    set_default(alpbl, "Fac", filter.opacity)
                    set_default(alpbl, 2, (1.0,1.0,1.0,1.0))

                    links.new(lastalphaconnection, alpbl.inputs[1])
                    lastalphaconnection = alpbl.outputs[0]
               
                if channel == "COLOR":
                    lastcolorconnection = lastconnection   
                if assignalpha:
                    links.new(lastalphaconnection, filternode.inputs["Alpha"])
                    lastalphaconnection = filternode.outputs["Alpha"]
                if channel == "ALPHA":
                    lastalphaconnection = lastconnection

                if blendfilter:
                    ntypesw = get_node_by_name(node_group, filter.affect_channels)
                    if ntypesw:
                        opfis = create_node(node_group,'ShaderNodeMath', -200,0, "op", "MULTIPLY")
                        set_default(opfis, 1, filter.opacity)
                        links.new(ntypesw.outputs['Result'], opfis.inputs[0])
                        links.new(opfis.outputs[0], blendfilter.inputs[0])
                        opfis.name = f"{filter.id}_op"
                        opfis.inputs[1].name = 'opacity'
                        filter.opacity_socket.set_socket_reference(opfis.inputs[1])
                if custominput:
                    links.new(custominput, filternode.inputs["Color"])
                if custominputalpha:
                    links.new(custominputalpha, filternode.inputs["Alpha"])

    links.new(lastcolorconnection, group_output.inputs[0])
    links.new(lastalphaconnection, group_output.inputs[1])

    return node_group

def get_folder_nodegroup(folder_layer, pbr = False):
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    else:
        return create_pbr_nodegroup(folder_layer) if pbr else create_folder_nodegroup(folder_layer)
    
def create_folder_nodegroup(folder_layer, pbr = False):
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, folder_layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)

    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)
    
    links = node_group.links
    count = -1

    lastconnection = group_input.outputs['Color']

    prevnodes = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)
    
    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):

            if layer.use_layer and type==layer.texture_type:
                
                count = count+1
                
                l_group = create_layer_node(layer)
                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                if "Type" in layer_node.inputs:
                    links.new(group_input.outputs['Type'], layer_node.inputs['Type'])
                prev_node = layer_node
        
        if prev_node:
            prevnodes.append(prev_node)
    if prev_node:    
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
        links.new(prev_node.outputs['Alpha'], group_output.inputs['Alpha'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])
        links.new(group_input.outputs['Alpha'], group_output.inputs['Alpha'])
    prsef = None
    count = -1
    type_switch_node = None
    lastcol = None
    lastcolal = None
    for pren in prevnodes:
        count = count+1
        type_switch_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", type_switch().name)
        links.new(group_input.outputs["Type"], type_switch_node.inputs['Type'])
        set_default(type_switch_node, "Compare", float(count))
        links.new(pren.outputs["Color"], type_switch_node.inputs['Color'])
        links.new(pren.outputs["Alpha"], type_switch_node.inputs['Alpha'])
        if prsef:
            links.new(prsef.outputs["Color"], type_switch_node.inputs['PrevColor'])
            links.new(prsef.outputs["Alpha"], type_switch_node.inputs['PrevAlpha'])
        prsef = type_switch_node
    if type_switch_node:

        lastcol = type_switch_node.outputs["Color"]
        lastcolal = type_switch_node.outputs["Alpha"]
        folder_layerfinm = layer_filter(folder_layer, multi = True).name
        if folder_layerfinm:
            folder_layerfilnodegroup = create_node(node_group,'ShaderNodeGroup', -200,-200, "cus", folder_layerfinm)
            links.new(lastcol, folder_layerfilnodegroup.inputs['Color'])
            links.new(lastcolal, folder_layerfilnodegroup.inputs['Alpha'])
            links.new(group_input.outputs['Type'], folder_layerfilnodegroup.inputs['Type'])
            lastcol = folder_layerfilnodegroup.outputs["Color"]
            lastcolal = folder_layerfilnodegroup.outputs["Alpha"]

    mix = create_node(node_group,'ShaderNodeMixRGB', -200,-200, "mix", folder_layer.blend_mode)
    blenda = create_node(node_group,'ShaderNodeMixRGB', -200,-200, "mix", "SCREEN")
    set_default(blenda, 'Fac', 1.0)
    set_default(mix, 'Fac', folder_layer.opacity)
    folder_layer.opacity_socket.set_socket_reference(mix.inputs['Fac'])
    if lastcol:
        links.new(group_input.outputs['Color'], mix.inputs[1])
        links.new(lastcol, mix.inputs[2])
        links.new(group_input.outputs['Alpha'], blenda.inputs[1])
        links.new(lastcolal, blenda.inputs[2])

        links.new(lastcolal, mix.inputs[0])

        lastcol = mix.outputs[0]
        lastcolal = blenda.outputs[0]
        links.new(lastcol, group_output.inputs['Color'])
        links.new(lastcolal, group_output.inputs['Alpha'])

    return node_group

def create_pbr_nodegroup(folder_layer):
    part = get_material_collection()
    name = f"{getlayergroupname(folder_layer)}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes(node_group, folder_layer.filters)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Alpha", 'float', False)
    create_socket(node_group, "Type", 'float', True)

    Note(node_group)
    group_input = node_group.nodes.new(type='NodeGroupInput')
    group_input.location = (-500, 0)
    group_output = node_group.nodes.new(type='NodeGroupOutput')
    group_output.location = (500, 0)
    
    links = node_group.links
    
    lastconnection = group_input.outputs['Color']

    count = -1
    sockets = []
    alsockets = []
    lrs = get_layers(folder_layer.sub_layers)
    sourceimg = create_image_node(node_group, folder_layer.resource.image, resource = folder_layer.resource)
    mpng = get_node_by_name(node_group, "Mapping")
    srinm = sourceimg.outputs[1]
    folder_layerfinm = layer_filter(folder_layer, multi = True).name
    if folder_layerfinm:
        folder_layerfilnodegroup = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], folder_layerfilnodegroup.inputs["Type"])
        links.new(sourceimg.outputs[1], folder_layerfilnodegroup.inputs["Alpha"])
        srinm = folder_layerfilnodegroup.outputs["Alpha"]
    for type in getusedtypes():
        prev_node = None

        for index, layer in enumerate(lrs):
            filnodegroup = None
            if layer.use_layer and type==layer.texture_type:
                layer_node = None
                count = count+1

                if layer.filters:
                    finm = layer_filter(layer, multi = True).name
                    if finm:
                        filnodegroup = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", finm)
                image = None
                mixrgb = create_node(node_group,'ShaderNodeMixRGB', -200,count*-200, "mix", layer.blend_mode)
                opacitynode = create_node(node_group,'ShaderNodeMath', -200,count*-200, "op", "MULTIPLY")
                opacitynode.inputs[1].name = "OpSock"
                if layer.resource.image:
                    image = create_image_node(node_group, layer.resource.image, resource = layer.resource)         

                    links.new(image.outputs[0], mixrgb.inputs[2])

                set_default(mixrgb,2,layer.resource.default_color)
                set_default(mixrgb,0,1.0)
                set_default(opacitynode,1,layer.opacity)

                layer.resource.default_color_socket.set_socket_reference(mixrgb.inputs[2])
                layer.opacity_socket.set_socket_reference(opacitynode.inputs[1])
                
                layer_node = mixrgb

                if filnodegroup:
                    if image:
                        links.new(image.outputs['Color'], filnodegroup.inputs["Color"])
                    else:
                        set_default(filnodegroup,"Color", layer.resource.default_color)
                        set_default(filnodegroup,"Alpha", 1.0)
                        layer.resource.default_color_socket.set_socket_reference(filnodegroup.inputs["Color"])
                    links.new(filnodegroup.outputs['Color'], mixrgb.inputs[2])

                if layer_node:
                    links.new(prev_node.outputs['Color'] if prev_node else group_input.outputs['Color'], layer_node.inputs[1])
                    links.new(srinm if srinm else group_input.outputs['Alpha'], opacitynode.inputs[0])
                    links.new(opacitynode.outputs[0], mixrgb.inputs[0])
                    prev_node = layer_node
        if prev_node:
            sockets.append(prev_node.outputs['Color'])
    if prev_node:  
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])

    lastcol = blendin(node_group, sockets, group_input.outputs["Type"])
    lastcolal = blendin(node_group, alsockets, group_input.outputs["Type"])
    if folder_layerfinm:
        lastcolal =  folder_layerfilnodegroup.outputs["Alpha"]
        colfilt = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", folder_layerfinm)
        links.new(group_input.outputs["Type"], colfilt.inputs["Type"])
    if lastcol:
        if colfilt:
            links.new(lastcol, colfilt.inputs["Color"])
            lastcol = colfilt.outputs["Color"]
        links.new(lastcol, group_output.inputs['Color'])
        links.new(lastcolal, group_output.inputs['Alpha'])

    alphablend= create_node(node_group,'ShaderNodeMixRGB', 0,0, "mix", "SCREEN")
    set_default(alphablend,0,1.0)

    links.new(lastcolal, alphablend.inputs[2])
    links.new(group_input.outputs["Alpha"], alphablend.inputs[1])
    links.new(alphablend.outputs[0], group_output.inputs['Alpha'])
    return node_group

def clear_node_socket_connections(node):

    for input_socket in node.inputs:
        while input_socket.links:
            bpy.data.node_groups[node.id_data.name].links.remove(input_socket.links[0])

    for output_socket in node.outputs:
        while output_socket.links:
            bpy.data.node_groups[node.id_data.name].links.remove(output_socket.links[0])

def clear_nodes(node_group,filters):
    for node in node_group.nodes:
        safe = False
        # if node.type == 'GROUP' and node.node_tree:
        #     node_group.nodes.remove(node)
        #     continue
        for filter in filters:
            if filter.node_name == node.name:
                safe = True
            if filter.levels.levels_node.name == node.name:
                safe = True
        if not safe:
            node_group.nodes.remove(node)

def simple_clear_node(node_group):
    for node in  node_group.nodes:
        node_group.nodes.remove(node)

def clear_nodes_ignoring(node_group):
    for node in  node_group.nodes:
        if not node.name.startswith("fs_"):
            node_group.nodes.remove(node)

def create_node_sockets_from_string(node_group, input_sockets_string, output_sockets_string):

    socket_type_mapping = {
        'float': 'NodeSocketFloat',
        'color': 'NodeSocketColor',
        'vector': 'NodeSocketVector',
        'shader': 'NodeSocketShader',
    }

    def parse_socket_string(sockets_string):
        sockets = []
        socket_pairs = sockets_string.split(',')
        for socket_pair in socket_pairs:
            try:
                name = socket_pair.split('(')[0].strip('<> ').strip()
                socket_type_key = socket_pair.split('(')[1].split(')')[0].strip()
                sockets.append((name, socket_type_key.lower()))
            except IndexError:
                raise ValueError(f"Invalid socket format: {socket_pair}")
        return sockets

    def create_sockets(sockets, in_out):
        for name, socket_type_key in sockets:
            socket_type = socket_type_mapping.get(socket_type_key, 'NodeSocketColor')

            if is_4_0_or_newer:
                if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == in_out]:
                    node_group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
            else:
                if in_out == 'INPUT' and name not in node_group.inputs:
                    node_group.inputs.new(socket_type, name)
                elif in_out == 'OUTPUT' and name not in node_group.outputs:
                    node_group.outputs.new(socket_type, name)

    input_sockets = parse_socket_string(input_sockets_string)
    output_sockets = parse_socket_string(output_sockets_string)

    create_sockets(input_sockets, 'INPUT')
    create_sockets(output_sockets, 'OUTPUT')

def create_socket(node_group, name, socket_type_key, input):
    socket_type_mapping = {
        'float': 'NodeSocketFloat',
        'color': 'NodeSocketColor',
        'vector': 'NodeSocketVector',
        'shader': 'NodeSocketShader',
        'geom': 'NodeSocketGeometry',
    }
    if input:
        in_out = 'INPUT'
    else:
        in_out = 'OUTPUT'
    socket_type = socket_type_mapping.get(socket_type_key, 'NodeSocketColor')

    if is_4_0_or_newer:
        if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == in_out]:
            node_group.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    else:
        if in_out == 'INPUT' and name not in node_group.inputs:
            node_group.inputs.new(socket_type, name)
        elif in_out == 'OUTPUT' and name not in node_group.outputs:
            node_group.outputs.new(socket_type, name)

def set_default(node_group, name, value):
    if hasattr(node_group, 'interface') and hasattr(node_group.interface, 'items_tree'):
        for ind, item in enumerate(node_group.interface.items_tree):
            if item.item_type == 'SOCKET':
                if item.in_out == 'INPUT':
                    try:
                        if isinstance(name, int):
                            if name == ind:
                                item.default_value = value
                                return
                        elif isinstance(name, str):
                            if name == item.name:
                                item.default_value = value
                                return
                    except (KeyError, IndexError):
                        pass
    else:
        try:
            if isinstance(name, int):
                if name < len(node_group.inputs):
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "default_value"):
                        input_socket.default_value = value
            elif isinstance(name, str):
                if name in node_group.inputs:
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "default_value"):
                        input_socket.default_value = value
        except (KeyError, IndexError):
            pass

def set_minmax(node_group, name, min, max):

    if hasattr(node_group, 'interface'):
        try:
            if isinstance(name, int):
                node_group.interface.items_tree[name].min_value = min
                node_group.interface.items_tree[name].max_value = max
            elif isinstance(name, str):
                node_group.interface.items_tree[name].min_value = min
                node_group.interface.items_tree[name].max_value = max
        except (KeyError, IndexError):
            
            pass
    else:
        try:
            if isinstance(name, int):
                if name < len(node_group.inputs):
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "min_value"):
                        input_socket.min_value = min
                        input_socket.max_value = max
            elif isinstance(name, str):
                if name in node_group.inputs:
                    input_socket = node_group.inputs[name]
                    if hasattr(input_socket, "min_value"):
                        input_socket.min_value = min
                        input_socket.max_value = max
        except (KeyError, IndexError):
            pass

def create_node(node_group, nodename, locx, locy, mode, operation):
    if not nodename or nodename == "None":
        return
    node = node_group.nodes.new(nodename)

    if mode == "op":
        node.operation = operation
    elif mode == "img":
        node.image = operation
    elif mode == "mix":
        node.blend_type = operation
    elif mode == "cus":
        node.node_tree = bpy.data.node_groups.get(operation) 

    node.location.x = locx
    node.location.y = locy

    return node

def Note(node_group):
    note = node_group.nodes.new('NodeFrame')
    note.location = (-200, 400)
    note.label = "This node group is created and used by HAS Paint Layers"
    note.width = 600

def UnlitNode():
    part = get_material_collection()
    name = "HAS_Unlit"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_node_sockets_from_string(node_group, "<Color>(color), <Alpha>(float)","<Shader>(shader)")
    
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    set_default(node_group, "Alpha", 1.0)

    Note(node_group)

    fixtransp = create_node(node_group,'ShaderNodeMixRGB', 50,300, "mix", "MULTIPLY")
    set_default(fixtransp, 0, 1.0)
    emission = node_group.nodes.new('ShaderNodeEmission')
    emission.location = (50, 300)
    transparent = node_group.nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (50, 300)
    invert = node_group.nodes.new('ShaderNodeInvert')
    invert.location = (50, 300)
    addshader = node_group.nodes.new('ShaderNodeAddShader')
    addshader.location = (50, 300)

    tree_links = node_group.links
    if part.colorfix:
        tree_links.new(input_node.outputs["Color"], emission.inputs[0])
    else:
        tree_links.new(input_node.outputs["Color"], fixtransp.inputs[1])
        tree_links.new(input_node.outputs["Alpha"], fixtransp.inputs[2])
        tree_links.new(fixtransp.outputs[0], emission.inputs[0])
    
    tree_links.new(input_node.outputs["Alpha"], invert.inputs[1])
    tree_links.new(invert.outputs[0], transparent.inputs[0])

    tree_links.new(emission.outputs[0], addshader.inputs[0])
    tree_links.new(transparent.outputs[0], addshader.inputs[1]) 
    tree_links.new(addshader.outputs[0], output_node.inputs[0])
    return node_group

def SetupMtl(material,part):
    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    output_node = get_node_by_name(tree, "Material Output")
    if not output_node:
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (600, 0)
 
    shader_node = get_node_by_name(tree, "Principled BSDF")
    emit_node = get_node_by_name(tree, "HAS_Unlit")
    if part.shader_type == 'PRINCIPLED':
        if not shader_node:
            shader_node = tree.nodes.new('ShaderNodeBsdfPrincipled')
            shader_node.location = (output_node.location[0] -400,output_node.location[1])
        tree_links = tree.links

        tree_links.new(shader_node.outputs[0], output_node.inputs[0]) 

    elif part.shader_type == 'UNLIT':
        UnlitNode()
        if not emit_node:
            emit_node = create_node(tree, 'ShaderNodeGroup' , output_node.location[0] -200,output_node.location[1], "cus", UnlitNode().name)
            emit_node.name = "HAS_Unlit"
        tree_links = tree.links

        tree_links.new(emit_node.outputs[0], output_node.inputs[0]) 
        shader_node = emit_node

    return tree, shader_node, output_node

def UpdateShader():
    CheckForEmpty()
    fixorder()
    update_layer_index()
    create_normal_blend_group()
    matnode = hasmatnode()

    bpy.context.scene.other_props.layercombineactive = False
    part = get_material_collection()
    
    if part.shader_type == 'Custom':
        return 
    material = bpy.context.active_object.active_material
    
    if material is None:
        return
    mtl_n = material.name

    tree, shader_node, output_node = SetupMtl(material, part)
    material.blend_method = part.opacity_mode
    tree_links = material.node_tree.links
    group_node = get_node_by_name(tree, "HAS_Material_OO")

    if not group_node:
        group_node = tree.nodes.new('ShaderNodeGroup')
        group_node.location = shader_node.location - mathutils.Vector((300, 0))
        group_node.node_tree = matnode
        group_node.name = "HAS_Material_OO"
        group_node.label = "HAS_Material"
    part.node = group_node.name

    for input in group_node.inputs:
        input.hide = not input.hide
    for output in group_node.outputs:
        output.hide = not output.hide
    clear_socket_links(shader_node, "Alpha")
    if part.shader_type == 'PRINCIPLED':
        if bpy.context.scene.other_props.preview_mode == "COMBINED":
            for type in getusedmaps():
                nm = type[1]
                if nm:
                    if nm == "Diffuse":
                        tree_links.new(group_node.outputs[nm], shader_node.inputs["Base Color"])
                        
                        if part.diffusealpha:
                            tree_links.new(group_node.outputs['DiffuseAlpha'], shader_node.inputs["Alpha"])
                        elif typeexist("ALPHA"):
                            tree_links.new(group_node.outputs['Alpha'], shader_node.inputs["Alpha"])
                    elif nm == "Height":
                        tree_links.new(group_node.outputs['Normal'], shader_node.inputs["Normal"])
                    else:
                        if nm in shader_node.inputs:
                            tree_links.new(group_node.outputs[nm], shader_node.inputs[nm])
        else:
            for type in getusedmaps():
                if bpy.context.scene.other_props.preview_mode == type[0]:
                    material.blend_method = "OPAQUE"
                    tree_links.new(group_node.outputs[type[1]], output_node.inputs[0])
                if bpy.context.scene.other_props.preview_mode == "NORMAL":
                    tree_links.new(group_node.outputs["RawNormal"], output_node.inputs[0])
                    
    elif part.shader_type == 'UNLIT':
        tree_links.new(group_node.outputs['Diffuse'], shader_node.inputs["Color"])
        if part.diffusealpha:
            tree_links.new(group_node.outputs['DiffuseAlpha'], shader_node.inputs["Alpha"])
        elif typeexist("ALPHA"):
            tree_links.new(group_node.outputs['Alpha'], shader_node.inputs["Alpha"])

def typeexist(Name):
    for type in getusedtypes():
        if type == Name:
            return True
    return False

def getlayer(index):
    part = get_material_collection()
    return part.layers[index]

def getsublayer(index):
    part = get_material_collection()
    return part.sublayers[index]

def layersgroup(tex_type, name):
    
    part = get_material_collection()
    layers = get_layers(part.base_layers)
    group_name = getgroupname(tex_type[0], name)
    if group_name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[group_name]
        for nodei in  node_group.nodes:
            node_group.nodes.remove(nodei)    
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

    Note(node_group)
    group_output = node_group.nodes.new("NodeGroupOutput")
    group_output.location = (500, 0)
    group_input = node_group.nodes.new("NodeGroupInput")
    group_input.location = (-500, 0)

    create_node_sockets_from_string(node_group, "<Color>(color), <Alpha>(float)","<Color>(color), <Alpha>(float)")

    count = -1

    links = node_group.links
    for link in links:
        links.remove(link)
        
    prev_node = None

    for index, layer in enumerate(layers):
        fldrlrs = getusedtypesinlayers(get_layers(layer.sub_layers))

        if layer.layer_type =="FOLDER" or layer.layer_type =="PBR":
            if layer.use_layer and tex_type[0] in fldrlrs:
                count = count+1

                l_group = get_folder_nodegroup(layer, pbr = layer.layer_type =="PBR")

                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                else:
                    links.new(group_input.outputs['Color'], layer_node.inputs['Color'])
                    links.new(group_input.outputs['Alpha'], layer_node.inputs['Alpha'])
                
                set_default(layer_node, "Type", fldrlrs.index(tex_type[0]))
                prev_node = layer_node
        
        else:
            if layer.use_layer and tex_type[0]==layer.texture_type:

                count = count+1
                
                l_group = create_layer_node(layer)
                layer_node = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", l_group.name)

                if prev_node:
                    links.new(prev_node.outputs['Color'], layer_node.inputs['Color'])
                    links.new(prev_node.outputs['Alpha'], layer_node.inputs['Alpha'])
                else:
                    links.new(group_input.outputs['Color'], layer_node.inputs['Color'])
                    links.new(group_input.outputs['Alpha'], layer_node.inputs['Alpha'])
                prev_node = layer_node

    if prev_node:
        links.new(prev_node.outputs['Color'], group_output.inputs['Color'])
        links.new(prev_node.outputs['Alpha'], group_output.inputs['Alpha'])
        if part.InvertG:
            if tex_type[0] == "NORMAL":
                invnrmnode = create_node(node_group,'ShaderNodeGroup', -200,count*-200, "cus", InvertNormalNode().name)
                if invnrmnode:
                    links.new(prev_node.outputs['Color'], invnrmnode.inputs['Normal'])
                    links.new(invnrmnode.outputs['Normal'], group_output.inputs['Color'])
        if part.colorfix and tex_type[0] == "DIFFUSE" and part.diffusealpha and not part.shader_type == "UNLIT":
            Colfix = create_node(node_group,'ShaderNodeMixRGB', -200,0, "mix", 'DIVIDE')
            set_default(Colfix, 0, 1.0)
            links.new(prev_node.outputs['Color'], Colfix.inputs[1])
            links.new(prev_node.outputs['Alpha'], Colfix.inputs[2])
            links.new(Colfix.outputs[0], group_output.inputs['Color'])
    else:
        links.new(group_input.outputs['Color'], group_output.inputs['Color'])
        links.new(group_input.outputs['Alpha'], group_output.inputs['Alpha'])


    return node_group

def hasmatnode():
    part = get_material_collection()
    name = getmaterialgroupname(part)
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    links = node_group.links

    usedtypes = getusedtypes()
    Note(node_group)
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    hsocketout = None
    nrmsocketout = None
    for layer in part.layers:
        if layer.layer_type =="FOLDER":
            create_folder_nodegroup(layer)
        elif layer.layer_type =="PBR":
            create_pbr_nodegroup(layer)

    for indexgr, tex_type in enumerate(TEXTURE_TYPE):

        lgroup = layersgroup(tex_type, name)
        
        group_node = node_group.nodes.new('ShaderNodeGroup')
        group_node.node_tree = lgroup
        group_node.location = (0,-200*indexgr)
        type = tex_type[0]
        nm = tex_type[1]
        anm = f'{nm}Alpha'
        create_node_sockets_from_string(node_group, f"<{nm}>(color), <{anm}>(float)",f"<{nm}>(color), <{anm}>(float)")
        if not group_node.outputs or not group_node.inputs:
            continue
        links.new(group_node.outputs['Color'], output_node.inputs[nm])
        links.new(group_node.outputs['Alpha'], output_node.inputs[anm])
        links.new(input_node.outputs[nm], group_node.inputs['Color'])
        links.new(input_node.outputs[anm], group_node.inputs['Alpha'])

        if type == "ROUGHNESS":
            set_default(node_group, "Roughness", (0.9,0.9,0.9,1.0))
        if type == "HEIGHT":
            hsocketout = group_node.outputs['Color']
            set_default(node_group, "Height", (0.5,0.5,0.5,1.0))
        if type == "NORMAL":
            nrmsocketout = group_node.outputs['Color']
            set_default(node_group, "Normal", (0.5,0.5,1.0,1.0))
        if type == "DIFFUSE":
            set_default(node_group, "Diffuse", (0.0,0.0,0.0,1.0))
        if type == "ALPHA":
            set_default(node_group, "Alpha", (1.0,1.0,1.0,1.0))
        if not type == "DIFFUSE":
            set_default(node_group, anm, 1.0)

    create_socket(node_group, "RawNormal", 'Color', False)
    if nrmsocketout:
        links.new(nrmsocketout, output_node.inputs["RawNormal"])
    
    for type in getusedmaps():
        nm = type[1]
        anm = f'{nm}Alpha'
        if nm in output_node.inputs:
            if not input_node.outputs[nm].is_linked:
                links.new(input_node.outputs[nm], output_node.inputs[nm])
                links.new(input_node.outputs[anm], output_node.inputs[anm])
        
    if nrmsocketout or hsocketout:
        bump = node_group.nodes.new(type='ShaderNodeBump')
        set_default(bump, 0, part.height_intensity)
        bump.location = (500,-700)
        nrmap = node_group.nodes.new(type='ShaderNodeNormalMap')
        nrmap.location = (200,-500)
        if nrmsocketout:
            links.new(nrmsocketout, nrmap.inputs['Color'])
            links.new(nrmap.outputs[0], bump.inputs['Normal'])
        if hsocketout:
            links.new(hsocketout, bump.inputs['Height'])

        links.new(bump.outputs[0], output_node.inputs['Normal'])

    return node_group 

def update_layer_index():
    for ind, l in enumerate(get_material_collection().layers):
        l.index = ind
    for ind, l in enumerate(get_material_collection().sublayers):
        l.index = ind

def getfilter(layerindex, index):
    return get_material_collection().layers[layerindex].filters[index]

def check_mtl_used():
    mtlprops = bpy.context.scene.material_props
    for ind, prop in enumerate(mtlprops):
        if prop:
            if prop.material == bpy.context.active_object.active_material:
                return True
    return False 

def mapping():
    node_group = None
    name = '.HAS_Mapping'
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        return node_group
    if not node_group:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
        create_node_sockets_from_string(node_group, "<Offset X>(float),<Offset Y>(float),<Scale X>(float),<Scale Y>(float),<Rotation>(float)","<Mapping>(Vector)")
    links = node_group.links
    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    texcoord = create_node(node_group,'ShaderNodeTexCoord', -600,0, "", None)
    mapping = create_node(node_group,'ShaderNodeMapping', -600,0, "", None)

    combxyzl = create_node(node_group,'ShaderNodeCombineXYZ', -600,0, "", None)
    combxyzr = create_node(node_group,'ShaderNodeCombineXYZ', -600,0, "", None)
    combxyzs = create_node(node_group,'ShaderNodeCombineXYZ', -600,0, "", None)

    set_default(node_group, "Scale X", 1.0)

    set_default(node_group, "Scale Y", 1.0)

    links.new(input_node.outputs["Offset X"],combxyzl.inputs[0])
    links.new(input_node.outputs["Offset Y"],combxyzl.inputs[1])
    links.new(input_node.outputs["Scale X"],combxyzs.inputs[0])
    links.new(input_node.outputs["Scale Y"],combxyzs.inputs[1])
    links.new(input_node.outputs["Rotation"],combxyzr.inputs[2])

    links.new(combxyzl.outputs[0],mapping.inputs[1])
    links.new(combxyzr.outputs[0],mapping.inputs[2])
    links.new(combxyzs.outputs[0],mapping.inputs[3])

    links.new(combxyzl.outputs[0],mapping.inputs[1])
    links.new(combxyzr.outputs[0],mapping.inputs[2])
    links.new(combxyzs.outputs[0],mapping.inputs[3])

    links.new(texcoord.outputs["UV"],mapping.inputs[0])
    links.new(mapping.outputs[0],output_node.inputs[0])

    return node_group

def levels(node_group, colsoc, levelref, id = ""):

    curve = levelref.levels_node.get_node()
    if not curve:
        curve = create_node(node_group, 'ShaderNodeRGBCurve' , -600,0, "", "")
    if curve:
        ind = {"COL": 3, "R": 0, "G": 1, "B": 2, "A": 3, "LUM": 3}.get(levelref.s_channel, -1)
        set_rgb_curve(curve, levelref.val01, levelref.val02, levelref.val03, levelref.val04, levelref.val05, ind)
        links = node_group.links

        links.new(colsoc, curve.inputs[1])

        colsoc = curve.outputs[0]
        if id:
            curve.name = id
        levelref.levels_node.set_node_reference(curve)
        return curve
    return None

def InvertNormalNode():
    part = get_material_collection()
    name = ".HAS_InvertNormal"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Normal", 'color', True)
    create_socket(node_group, "Normal", 'color', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    Note(node_group)

    sep = create_node(node_group,'ShaderNodeSeparateRGB', 50,300, "", "")
    com = create_node(node_group,'ShaderNodeCombineRGB', 50,300, "", "")
    inv = create_node(node_group,'ShaderNodeInvert', 50,300, "", "")
    add = create_node(node_group,'ShaderNodeMath', 50,300, "op", "ADD")
    tree_links = node_group.links

    tree_links.new(input_node.outputs[0], sep.inputs[0])

    tree_links.new(sep.outputs[0], com.inputs[0])
    tree_links.new(sep.outputs[1], add.inputs[0])
    tree_links.new(add.outputs[0], inv.inputs[1])
    tree_links.new(inv.outputs[0], com.inputs[1])
    tree_links.new(sep.outputs[2], com.inputs[2])

    tree_links.new(com.outputs[0], output_node.inputs[0])

    return node_group

def set_rgb_curve(node, val1, val2, val3, val4, val5, index):
    if not node:
        return
    if node.type != 'CURVE_RGB':
        return

    curve = node.mapping.curves[index]  
    val2 = clamp(val2,0.001,0.999)

    while len(curve.points) > 5:
        curve.points.remove(curve.points[-1])  
    while len(curve.points) < 5:
        curve.points.new(0.5, 0.5)  
    for p in curve.points:
        p.handle_type = 'VECTOR'

    curve.points[1].location = (val1, val4) 
    curve.points[3].location = (val3, val5) 

    curve.points[0].location = (0.0 if val1 < val3 else 1.0, val4) 
    curve.points[4].location = (1.0 if val1 < val3 else 0.0, val5) 

    mid_x = lerp(val1, val3, 0.5)
    mid_y = lerp(val4, val5, val2)
    curve.points[2].location = (mid_x, mid_y)

    node.mapping.update()
    node.update()

def light_node(filter):
    part = get_material_collection()
    name = f".HAS_Light_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    create_socket(node_group, "Color", 'color', True)

    create_socket(node_group, "Attenuation", 'float', True)
    create_socket(node_group, "Glossiness", 'float', True)
    create_socket(node_group, "Level", 'float', True)
    create_socket(node_group, "Color", 'color', False)

    set_default(node_group,"Level",1.0)
    set_default(node_group,"Glossiness",1.0)
    set_default(node_group,"Attenuation",0.0)

    set_minmax(node_group, "Level", 0.0, 1.0)
    set_minmax(node_group, "Glossiness", 0.0, 200.0)
    set_minmax(node_group, "Attenuation", -1.0, 1.0)

    if hasattr(node_group, 'interface'):
        node_group.interface.items_tree["Attenuation"].subtype = 'FACTOR'
        node_group.interface.items_tree["Glossiness"].subtype = 'NONE'
        node_group.interface.items_tree["Level"].subtype = 'FACTOR'

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    Note(node_group)
    image = None
    if filter.resource.image:
        image = create_image_node(node_group, filter.resource.image)
        
        madd = create_node(node_group,'ShaderNodeVectorMath', 50,300, "op", "MULTIPLY_ADD")
        set_default(madd,1,(2.0,2.0,2.0))
        set_default(madd,2,(-1.0,-1.0,-1.0))

    geometry = create_node(node_group,'ShaderNodeNewGeometry', 50,300, "", "")
    normal = get_node_by_name(node_group, "fs_LightNormal")
    if not normal:
        normal = create_node(node_group,'ShaderNodeNormal', 50,300, "", "")
        normal.name = "fs_LightNormal"
    Rotate1 = create_node(node_group,'ShaderNodeVectorRotate', 50,300, "", "")

    Add = create_node(node_group,'ShaderNodeMath', 50,300, "op", "ADD")
    Mult1 = create_node(node_group,'ShaderNodeMath', 50,300, "op", "MULTIPLY")
    Mult2 = create_node(node_group,'ShaderNodeMath', 50,300, "op", "MULTIPLY")

    Mult1.use_clamp = True
    Mult2.use_clamp = True

    Rotate1.rotation_type = 'X_AXIS'
    
    tree_links = node_group.links

    tree_links.new(input_node.outputs["Attenuation"], Add.inputs[1])
    tree_links.new(input_node.outputs["Glossiness"], Mult1.inputs[1])
    tree_links.new(input_node.outputs["Level"], Mult2.inputs[1])
    if image:
        tree_links.new(image.outputs[0], madd.inputs[0])
        tree_links.new(madd.outputs[0], Rotate1.inputs[0])
    else:
        tree_links.new(geometry.outputs["Normal"], Rotate1.inputs[0])
    tree_links.new(Rotate1.outputs[0], normal.inputs[0])
    tree_links.new(normal.outputs[1], Add.inputs[0])

    tree_links.new(Add.outputs[0], Mult1.inputs[0])
    tree_links.new(Mult1.outputs[0], Mult2.inputs[0])
    tree_links.new(Mult2.outputs[0], output_node.inputs[0])

    return node_group

def blur_node(filter):
    name = f".HAS_Blur_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Pass", 'color', False)
    create_socket(node_group, "PassAlpha", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)
    image = create_image_node(node_group, filter.resource.image)
   
    tree_links = node_group.links

    tree_links.new(image.outputs[0], output_node.inputs[0])
    tree_links.new(image.outputs[1], output_node.inputs[1])
    tree_links.new(input_node.outputs["Color"], output_node.inputs["Pass"])
    tree_links.new(input_node.outputs["Alpha"], output_node.inputs["PassAlpha"])
    return node_group

def snapshot_node(filter):
    name = f".HAS_Snapshot_{filter.id}"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        clear_nodes_ignoring(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Pass", 'color', False)
    create_socket(node_group, "PassAlpha", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)
    image =  create_image_node(node_group, filter.resource.image)

    tree_links = node_group.links

    tree_links.new(image.outputs[0], output_node.inputs[0])
    tree_links.new(image.outputs[1], output_node.inputs[1])
    tree_links.new(input_node.outputs["Color"], output_node.inputs["Pass"])
    tree_links.new(input_node.outputs["Alpha"], output_node.inputs["PassAlpha"])
    return node_group

def getsocketconnection(node, socket_name):
    socket = node.inputs.get(socket_name)

    if socket.is_linked:
        link = socket.links[0]
        connected_socket = link.from_socket
        return connected_socket
    return None
            
def getgroupname(tex_type, mtl_name):
    res = f".HAS_{tex_type}_Group_{mtl_name}"
    return res

def newimage(texture_name):
    part = get_material_collection()
    if not part:
        return {'CANCELLED'}
   
    xs = part.texture_sizeX
    ys = part.texture_sizeY

    new_texture = bpy.data.textures.new(name=texture_name, type='IMAGE')
    new_image = bpy.data.images.new(texture_name, width=xs, height=ys, alpha=True)
    pixels = [0.0] * (4 * xs * ys)
    new_image.pixels = pixels
    new_texture.image = new_image
    return new_image

def blendin(node_group, sockets, value):
    links = node_group.links
    count = -1
    lastsock = None
    for socket in sockets:
        count = count +1
        mix= create_node(node_group,'ShaderNodeMixRGB', 0,-150*count, "mix", "MIX")
        compare = create_node(node_group,'ShaderNodeMath', -400,-150*count, "op", 'COMPARE')
        set_default(compare, 1, count)
        set_default(compare, 2, 0.1)

        links.new(value, compare.inputs[0])
        links.new(compare.outputs[0], mix.inputs[0])
        links.new(socket, mix.inputs[2])
        if lastsock:
            links.new(lastsock, mix.inputs[1])
        lastsock = mix.outputs[0]
    return lastsock

def getbyid(id):
    part = get_material_collection()
    for l in part.layers:
        if l.id == id:
            return l
    return None

def get_node_by_name(node_group, name):
    for node in node_group.nodes:
        if node.name == name:
            return node
    return None

def get_socket_from_name(node_group, name, socket):
    node = get_node_by_name(node_group, name)
    if node:
        if socket in node.inputs:
            return node.inputs[socket]
    return None

def get_image_nodes_recursive(node_tree, collected_nodes=None):
    if collected_nodes is None:
        collected_nodes = set()

    for node in node_tree.nodes:

        if node.type == 'TEX_IMAGE':

            if node.image is not None and any(node.outputs[i].is_linked for i in range(len(node.outputs))):
                collected_nodes.add(node)

        elif node.type == 'GROUP' and node.node_tree:
            get_image_nodes_recursive(node.node_tree, collected_nodes)

    return collected_nodes

def get_all_image_nodes_in_material(material):

    node_tree = material.node_tree

    image_nodes = get_image_nodes_recursive(node_tree)

    return list(image_nodes)

def clear_unused_layers():

    part = get_material_collection()
    ids=[]
    for layer in part.base_layers:
        ids.append(layer.id)
        for subl in layer.get_layer().sub_layers:
            ids.append(subl.id)

    for ind, layer in reversed(list(enumerate(part.layers))):
        if not layer.id in ids:
            part.layers.remove(ind)

def type_switch():
    name = f".HAS_TypeSwitch"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
        simple_clear_node(node_group)
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)

    create_socket(node_group, "Color", 'color', True)
    create_socket(node_group, "Alpha", 'float', True)
    create_socket(node_group, "PrevColor", 'color', True)
    create_socket(node_group, "PrevAlpha", 'float', True)
    create_socket(node_group, "Color", 'color', False)
    create_socket(node_group, "Alpha", 'float', False)

    create_socket(node_group, "Type", 'float', True)
    create_socket(node_group, "Compare", 'float', True)
    create_socket(node_group, "Result", 'float', False)

    input_node = node_group.nodes.new(type='NodeGroupInput')
    input_node.location = (-500, 0)
    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)
    
    Note(node_group)

    mix= create_node(node_group,'ShaderNodeMixRGB', 0,-150, "mix", "MIX")
    alphamix= create_node(node_group,'ShaderNodeMixRGB', 0,-150, "mix", "MIX")
    compare = create_node(node_group,'ShaderNodeMath', -400,-150, "op", 'COMPARE')

    set_default(compare, 2, 0.1)

    links = node_group.links

    links.new(input_node.outputs["Type"], compare.inputs[0])
    links.new(input_node.outputs["Compare"], compare.inputs[1])
    links.new(compare.outputs[0], mix.inputs[0])
    links.new(compare.outputs[0], alphamix.inputs[0])
    links.new(input_node.outputs["Color"], mix.inputs[2])
    links.new(input_node.outputs["Alpha"], alphamix.inputs[2])
    links.new(input_node.outputs["PrevColor"], mix.inputs[1])
    links.new(input_node.outputs["PrevAlpha"], alphamix.inputs[1])
    links.new(mix.outputs[0], output_node.inputs["Color"])
    links.new(alphamix.outputs[0], output_node.inputs["Alpha"])
    links.new(compare.outputs[0], output_node.inputs["Result"])
    return node_group

###
### QUICKEDIT
###

class SCREEN_OT_crop_tool(Operator):
    bl_idname = "haspaint.crop_tool"
    bl_label = "Crop Tool"
    bl_description = "Draw a box to crop a screenshot"
    bl_options = {'REGISTER', 'UNDO'}

    start_x: IntProperty()
    start_y: IntProperty()
    end_x: IntProperty()
    end_y: IntProperty()
    mouse_dragging: BoolProperty(default=False)
    operator_running: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        try:
            context.area.tag_redraw()

            if event.type == 'MOUSEMOVE':
                if self.mouse_dragging:
                    self.end_x = event.mouse_region_x
                    self.end_y = event.mouse_region_y

            elif event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    self.start_x = event.mouse_region_x
                    self.start_y = event.mouse_region_y
                    self.mouse_dragging = True
                elif event.value == 'RELEASE':
                    if self.mouse_dragging:
                        self.end_x = event.mouse_region_x
                        self.end_y = event.mouse_region_y
                        self.mouse_dragging = False

                        try:
                            self.take_screenshot_and_crop(context)
                        except Exception as e:
                            self.report({'ERROR'}, f"Screenshot failed: {str(e)}")
                            return {'CANCELLED'}

                        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                        context.area.tag_redraw()
                        self.operator_running = False
                        return {'FINISHED'}

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if self.mouse_dragging:
                    self.mouse_dragging = False
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.area.tag_redraw()
                self.operator_running = False
                return {'CANCELLED'}

            return {'RUNNING_MODAL'}
        
        except Exception as e:

            self.report({'ERROR'}, f"Modal error: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':

            if self.operator_running:
                self.report({'WARNING'}, "Operator is already running")
                return {'CANCELLED'}
            
            self.start_x = 0
            self.start_y = 0
            self.end_x = 0
            self.end_y = 0
            self.mouse_dragging = False
            
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            self.operator_running = True
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def draw_callback_px(self, context):
        if not self.mouse_dragging:
            return
        
        vertices = [
            (self.start_x, self.start_y),
            (self.start_x, self.end_y),
            (self.end_x, self.end_y),
            (self.end_x, self.start_y),
            (self.start_x, self.start_y)
        ]
        if is_4_0_or_newer:
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})

        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.5))  
        batch.draw(shader)

        size_x = abs(self.end_x - self.start_x)
        size_y = abs(self.end_y - self.start_y)
        size_text = f"Size: {size_x} x {size_y}"

        region_width, region_height = context.region.width, context.region.height
        text_pos_x = min(self.start_x, self.end_x) + 10
        text_pos_y = min(self.start_y, self.end_y) + 10

        font_id = 0 
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        if is_4_0_or_newer:
            blf.size(font_id, 20)
        else:
            blf.size(font_id, 20, 72)
        blf.position(font_id, text_pos_x, text_pos_y, 0)
        blf.draw(font_id, size_text)

    def is_operator_removed(self):
        try:
            _ = self.start_x
            return False
        except ReferenceError:
            return True

    def take_screenshot_and_crop(self, context):
        try:
            if self.start_x == self.end_x or self.start_y == self.end_y:
                self.report({'ERROR'}, "Region selected is too small")
                return {'CANCELLED'}   

            view_data = context.scene.view_data.add()
            region = context.region
            bpy.data.images['Render Result'].render_slots.active_index = 7
            region_3d = bpy.context.area.spaces.active.region_3d
            
            store_current_view(view_data, context)
        
            self.Render(context,view_data)
            
            filepath = bpy.data.filepath
            current_datetime = datetime.datetime.now().strftime("%H_%M_%S")
            folder = context.scene.other_props.tempsavingdir
            if bpy.data.is_saved:
                if bpy.app.tempdir ==context.scene.other_props.tempsavingdir:
                    folder = bpy.path.abspath("//HASCaptures/")

                    if not os.path.exists(folder):
                        os.makedirs(folder)
            filepath = os.path.join(folder, "has_sc_" + current_datetime)
            EXT = "png"
            filepath_final = filepath + "." + EXT
            i = 0
            while os.path.exists(bpy.path.abspath(filepath_final)):
                filepath_final = filepath + "_{:03d}.{:s}".format(i, EXT)
                i += 1

            view_data.image_name = name=bpy.path.basename(filepath_final)
            view_data.image_path = filepath_final

            render_result = bpy.data.images.get('Render Result')
            render_result.save_render(filepath_final)

            image_new = bpy.data.images.load(filepath_final)

            width = image_new.size[0]
            height = image_new.size[1]

            region_width = region.width
            region_height = region.height

            x_scale = context.scene.other_props.screen_capture_scale
            y_scale = context.scene.other_props.screen_capture_scale

            left = int(min(self.start_x, self.end_x) * x_scale)
            right = int(max(self.start_x, self.end_x) * x_scale)
            upper = int(min(self.start_y, self.end_y) * y_scale)
            lower = int(max(self.start_y, self.end_y) * y_scale)
            left = max(0, min(left, width))
            right = max(0, min(right, width))
            upper = max(0, min(upper, height))
            lower = max(0, min(lower, height))

            if left >= right:
                left, right = right, left

            if upper >= lower:
                upper, lower = lower, upper

            cropped_width = right - left
            cropped_height = lower - upper

            view_data.crop_startX= int(self.start_x * x_scale)
            view_data.crop_startY= int(self.start_y * x_scale)
            view_data.crop_endX= int(self.end_x * x_scale)
            view_data.crop_endY= int(self.end_y * x_scale)

            pixels = np.array(image_new.pixels[:]).reshape((height, width, 4)) 
            cropped_pixels = pixels[upper:lower, left:right, :]

            bpy.data.images.remove(image_new)

            cropped_image = bpy.data.images.new(
                name=bpy.path.basename(filepath_final),
                width=cropped_width,
                height=cropped_height,
                alpha=True 
            )

            cropped_image.pixels = cropped_pixels.flatten().tolist()

            cropped_image.filepath_raw = filepath_final
            cropped_image.file_format = 'PNG'

            cropped_image.save_render(filepath_final)

            check_views()
            bpy.data.images['Render Result'].render_slots.active_index = 0
            try:
                bpy.ops.image.external_edit(filepath=filepath_final)
            except RuntimeError as ex:
                self.report({'ERROR'}, str(ex))
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Screenshot error: {str(e)}")
            return {'CANCELLED'}
    def Render(self, context,view_data):
        render = context.scene.render
        
        region = context.region
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        bpy.context.scene.render.image_settings.color_depth = '8'
        bpy.context.scene.render.image_settings.compression = 0

        current_show_overlays = bpy.context.area.spaces.active.overlay.show_overlays
        bpy.context.area.spaces.active.overlay.show_overlays = False

        current_film_transparent = bpy.context.scene.render.film_transparent
        bpy.context.scene.render.film_transparent = True

        render.resolution_x = int(region.width * context.scene.other_props.screen_capture_scale)
        render.resolution_y = int(region.height * context.scene.other_props.screen_capture_scale)

        view_data.render_sizeX = render.resolution_x
        view_data.render_sizeY = render.resolution_y    

        render.resolution_percentage = 100
        bpy.ops.render.opengl()

        bpy.context.area.spaces.active.overlay.show_overlays = current_show_overlays
        bpy.context.scene.render.film_transparent = current_film_transparent
        
class ProjectApply(Operator):
    """Project edited image back onto the object"""
    bl_idname = "haspaint.has_project_apply"
    bl_label = "Project Apply"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        check_views()
        try:
            view_data = context.scene.view_data[self.index]
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}
            
        region_data = context.space_data.region_3d
        stored_view_matrix = (region_data.view_matrix.copy(), region_data.view_perspective)
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        prev_active = context.view_layer.objects.active
        prev_selected = context.selected_objects.copy()
        
        baseimage = bpy.data.images.get(view_data.image_name)

        if not baseimage:
            self.report({'ERROR'}, f"Image ({view_data.image_name}) not found")
            return {'CANCELLED'}

        start_x = view_data.crop_startX
        start_y = view_data.crop_startY
        end_x = view_data.crop_endX
        end_y = view_data.crop_endY

        img = bpy.data.images.load(view_data.image_path)

        if not img:
            self.report({'ERROR'}, f"Image ({view_data.image_path}) not found")
            return {'CANCELLED'}
        createdimage = create_image_with_overlay(view_data.render_sizeX, view_data.render_sizeY, img, end_x, end_y, start_x, start_y)
        if not createdimage:
            self.report({'ERROR'}, f"Image cannot be applied")
            return {'CANCELLED'}
            
        image_name = createdimage.name
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0))
        camera = context.object

        camera.data.lens = context.space_data.lens
        current_focal_length = camera.data.lens

        region_data.view_perspective = 'PERSP'

        bpy.context.scene.camera = camera
        
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active
        
        bpy.ops.paint.texture_paint_toggle()

        stored_view_str = view_data.view
        stored_view = eval(stored_view_str)

        apply_view_data_to_camera(view_data, camera)

        bpy.ops.paint.project_image(image=image_name)

        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.objects.remove(camera)

        bpy.data.images.remove(createdimage)
        bpy.data.images.remove(img)
        region_data.view_matrix, region_data.view_perspective = stored_view_matrix

        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active

        if prev_active.type == 'MESH':
            bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}

class ProjectRemove(Operator):
    """Remove the selected image from the project list"""
    bl_idname = "haspaint.project_remove"
    bl_label = "Remove Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        try:
            if context.scene.view_data[self.index].image_name:
                img = bpy.data.images.get(context.scene.view_data[self.index].image_name)
                if img:
                    if img.users == 0:
                        bpy.data.images.remove(img)
            context.scene.view_data.remove(self.index)
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}

        return {'FINISHED'}

class ProjectOpen(Operator):
    """Open the image in an external editor"""
    bl_idname = "haspaint.project_open"
    bl_label = "Open Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        try:
            image_name = context.scene.view_data[self.index].image_name
            filepath = context.scene.view_data[self.index].image_path
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}
        try:
            bpy.ops.image.external_edit(filepath=filepath)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))

        return {'FINISHED'}

class SnapToView(Operator):

    bl_idname = "haspaint.snap_to_view"
    bl_label = "Snap to view"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        load_stored_view(context.scene.view_data[self.index], context)
        
        return {'FINISHED'}

class SetQEFolder(Operator):
    bl_idname = "haspaint.setquefolder"
    bl_label = "Set Images Folder"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.exr;*.hdr",
        options={'HIDDEN'}
    )

    def execute(self, context):

        directory = os.path.dirname(self.filepath)
        user_filename = os.path.basename(self.filepath)

        context.scene.other_props.tempsavingdir = directory
        
        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ProjectBakeGet(Operator):
    """Edit a snapshot of the 3D Viewport in an external image editor"""
    bl_idname = "haspaint.projectbakeget"
    bl_label = "Project Edit"
    bl_options = {'REGISTER'}

    _proj_hack = [""]

    def execute(self, context):
        import os

        EXT = "png" 

        for image in bpy.data.images:
            image.tag = True
        obj = bpy.context.object

        if not obj.material_slots:
            return

        original_materials = [slot.material for slot in obj.material_slots]

        custom_material = bpy.data.materials.new(name="Custom_AO_Material")
        custom_material.use_nodes = True
        nodes = custom_material.node_tree.nodes
        links = custom_material.node_tree.links
        
        bpy.context.scene.eevee.gtao_quality = 1
        bpy.context.scene.eevee.use_gtao_bent_normals = False
        bpy.context.scene.eevee.use_gtao_bounce = False

        nodes.clear()

        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        ao_node = nodes.new(type='ShaderNodeAmbientOcclusion')
        fresnel_node = nodes.new(type='ShaderNodeFresnel')
        transparent_bsdf_node = nodes.new(type='ShaderNodeBsdfTransparent')
        add_shader_node = nodes.new(type='ShaderNodeAddShader')

        set_default(fresnel_node, 'IOR', 1.5)
        custom_material.blend_method = 'CLIP'  
        custom_material.show_transparent_back = False  

        output_node.location = (600, 0)
        add_shader_node.location = (400, 0)
        ao_node.location = (0, 0)
        fresnel_node.location = (0, -200)
        transparent_bsdf_node.location = (200, -200)

        links.new(ao_node.outputs['AO'], add_shader_node.inputs[0])
        links.new(fresnel_node.outputs['Fac'], transparent_bsdf_node.inputs['Color'])
        links.new(transparent_bsdf_node.outputs['BSDF'], add_shader_node.inputs[1])
        links.new(add_shader_node.outputs['Shader'], output_node.inputs['Surface'])
        custom_material.use_backface_culling = True

        for slot in obj.material_slots:
            slot.material = custom_material

        try:
            bpy.ops.paint.image_from_view()
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}

        for i, mat in enumerate(original_materials):
            obj.material_slots[i].material = mat

        image_new = None
        for image in bpy.data.images:
            if not image.tag:
                image_new = image
                break

        if not image_new:
            self.report({'ERROR'}, "Could not make new image")
            return {'CANCELLED'}

        filepath = os.path.basename(bpy.data.filepath)
        filepath = os.path.splitext(filepath)[0]

        if bpy.data.is_saved:
            filepath = "//" + filepath
        else:
            filepath = os.path.join(bpy.app.tempdir, "project_edit")

        obj = context.object

        if obj:
            filepath += "_" + bpy.path.clean_name(obj.name)

        filepath_final = filepath + "." + EXT
        i = 0

        while os.path.exists(bpy.path.abspath(filepath_final)):
            filepath_final = filepath + "{:03d}.{:s}".format(i, EXT)
            i += 1

        image_new.name = bpy.path.basename(filepath_final)
        ProjectBakeGet._proj_hack[0] = image_new.name

        image_new.filepath_raw = filepath_final
        image_new.file_format = 'PNG'
        image_new.save()

        filepath_final = bpy.path.abspath(filepath_final)

        image_name = ProjectBakeGet._proj_hack[0]
        image = bpy.data.images.get((image_name, None))
        if image is None:
            self.report({'ERROR'}, rpt_("Could not find image '{:s}'").format(image_name))
            return {'CANCELLED'}

        image.reload()
        fix_image_colors_by_alpha(image.name)
        bpy.ops.paint.project_image(image=image_name)
        
        bpy.data.materials.remove(custom_material)
        bpy.data.images.remove(image)

        return {'FINISHED'}

class ProjectBakeApply(Operator):
    """Project edited image back onto the object"""
    bl_idname = "haspaint.projectbakeapply"
    bl_label = "Project Apply"
    bl_options = {'REGISTER'}

    def execute(self, _context):
        image_name = ProjectBakeGet._proj_hack[0]
        image = bpy.data.images.get((image_name, None))
        if image is None:
            self.report({'ERROR'}, rpt_("Could not find image '{:s}'").format(image_name))
            return {'CANCELLED'}

        image.reload()
        bpy.ops.paint.project_image(image=image_name)

        return {'FINISHED'}

def check_views():
    view_data = bpy.context.scene.view_data
    for i in reversed(range(len(view_data))):
        if view_data[i].image_name not in bpy.data.images:
            view_data.remove(i)

def create_image_with_overlay(main_img_width, main_img_height, overlay_image, start_x, start_y, end_x, end_y):

    if start_x > end_x:
        start_x, end_x = end_x, start_x

    if start_y > end_y:
        start_y, end_y = end_y, start_y
        
    main_image = bpy.data.images.new("MainImage", width=main_img_width, height=main_img_height)

    overlay_width = overlay_image.size[0]
    overlay_height = overlay_image.size[1]
    
    offset_x = max(0, start_x)
    offset_y = max(0, start_y)
    end_x = min(end_x, main_img_width)
    end_y = min(end_y, main_img_height)

    main_pixels = np.zeros((main_img_height, main_img_width, 4), dtype=np.float32)
    overlay_pixels = np.array(overlay_image.pixels[:]).reshape((overlay_height, overlay_width, 4))

    for y in range(overlay_height):
        for x in range(overlay_width):
            target_x = offset_x + x
            target_y = offset_y + y
            if target_x < end_x and target_y < end_y:
                main_pixels[target_y, target_x, :] = overlay_pixels[y, x, :]

    main_pixels_flat = main_pixels.flatten()
    main_image.pixels = main_pixels_flat.tolist()
    main_image.update()
    
    return main_image

def load_stored_view(view_data, context):

    return True

def store_current_view(view_props, context):
    bpy.ops.object.mode_set(mode='OBJECT')
    prev_active = bpy.context.view_layer.objects.active
    
    space = context.area.spaces.active
    region = space.region_3d
    current_camera = bpy.context.scene.camera
    bpy.ops.object.camera_add()
    tempcamera = bpy.context.object 
    bpy.context.scene.camera = tempcamera
    ortho = not region.is_perspective
    
    if ortho:
        tempcamera.data.type = 'PERSP'
    else:
        tempcamera.data.type = 'ORTHO'
    region = bpy.context.space_data.region_3d
    old_lens = bpy.context.space_data.lens
    old_view_distance = region.view_distance

    new_lens = 50
    bpy.context.space_data.lens = new_lens
    if ortho:
        new_view_distance = old_view_distance * (new_lens / old_lens)
        region.view_distance = new_view_distance

    view_distance = region.view_distance
    lens = bpy.context.space_data.lens

    bpy.ops.view3d.camera_to_view()
    
    view_matrix = tempcamera.matrix_world
    view_props.loc = view_matrix.to_translation()
    view_props.rot = view_matrix.to_euler()

    if ortho:
        view_props.ortho = True

        view_props.ortho_scale = view_distance/(lens/76.5)

    view_props.focal = bpy.context.space_data.lens

    stored_view = (tempcamera.matrix_world.copy(), tempcamera.data.type)
    view_props.view = repr(stored_view)

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = area.spaces.active.region_3d
            if region.view_perspective == 'CAMERA':
                bpy.ops.view3d.view_camera()  

    bpy.data.objects.remove(tempcamera, do_unlink=True)
    bpy.context.view_layer.objects.active = prev_active
    region.view_distance = old_view_distance
    bpy.context.space_data.lens = old_lens
    bpy.context.scene.camera = current_camera

def apply_view_data_to_camera(view_data, camera):

    prev_active = bpy.context.view_layer.objects.active
    stored_view_str = view_data.view
    try:
        stored_view = eval(stored_view_str) 
    except (SyntaxError, NameError) as e:
        return

    camera.location = view_data.loc
    camera.rotation_euler = view_data.rot

    if view_data.ortho:

        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = view_data.ortho_scale/1.06
    else:
        camera.data.type = 'PERSP'
        camera.data.lens = view_data.focal/2.0  

    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = prev_active

def getusedmaps():
    types = []
    part = get_material_collection()
    if part:
        used = part.used_maps

        if used.Diffuse:
            types.append(('DIFFUSE', 'Diffuse', 'Texture as Diffuse'))
        if used.Roughness:
            types.append(('ROUGHNESS', 'Roughness', 'Texture as Roughness'))
        if used.Metallic:
            types.append(('METALLIC', 'Metallic', 'Texture as Metallic'))
        if used.Normal:
            types.append(('NORMAL', 'Normal', 'Texture as Normal'))
        if used.Height:
            types.append(('HEIGHT', 'Height', 'Texture as Height'))
        if used.Emission:
            types.append(('EMISSION', 'Emission', 'Texture as Emission'))
        if used.Alpha:
            types.append(('ALPHA', 'Alpha', 'Texture as Alpha'))
        if used.AO:
            types.append(('AO', 'Ambient Occlusion', 'Texture as Ambient Occlusion'))
        if used.Alpha:
            types.append(('CUSTOM', 'Custom', 'Custom texture'))

        return types
    return None

def getusedtypes():
    usedtypes = []
    part = get_material_collection()
    usedtypes = getusedtypesinlayers(part.layers)
    for layer in part.layers:
        newused = getusedtypesinlayers(get_layers(layer.sub_layers))
        for tp in newused:
            if not tp in usedtypes:
                usedtypes.append(tp)
    return usedtypes

def gettypeenum(intype):
    for type in TEXTURE_TYPE:
        if type[0] == intype:
            return type
    return []

def getlabel(find_type):

    texture_type_dict = {item[0]: item[1] for item in getusedmaps()}
    texture_label = texture_type_dict.get(find_type, "")
    return texture_label

def gettexturelabel(find_type):

    texture_type_dict = {item[0]: item[1] for item in TEXTURE_TYPE}
    texture_label = texture_type_dict.get(find_type, "")
    return texture_label

def getsublayers(layer):
    return get_layers(layer.sub_layers)

def fix_image_colors_by_alpha(image_name):
    image = bpy.data.images.get(image_name)

    if image is None:
        return
    if image.channels < 4:
        return

    pixels = np.array(image.pixels[:])  
    pixels = pixels.reshape((-1, 4)) 
    
    rgb = pixels[:, :3] 
    alpha = pixels[:, 3]

    rgb_corrected = np.where(alpha[:, None] > 0, rgb / alpha[:, None], rgb)
    rgb_corrected[alpha == 0] = [1.0, 1.0, 1.0]
    pixels[:, :3] = rgb_corrected
    
    image.pixels = pixels.flatten()
    
    image.update()

def create_image_node(node_group, img, resource = None):
    part = get_material_collection()
    links = node_group.links
    image_node = create_node(node_group,'ShaderNodeTexImage', -600,0, "img", img)
    
    image_node.interpolation= part.texture_filtering

    attribute = create_node(node_group,'ShaderNodeUVMap', -600,0, "", "")
    attribute.uv_map = part.uvs

    mapping = create_node(node_group,'ShaderNodeMapping', -600,0, "", "")
    if resource:
        set_default(mapping, "Location", (resource.mapx,resource.mapy,0.0))
        set_default(mapping, "Rotation", (0.0,0.0,resource.maprot))
        set_default(mapping, "Scale", (resource.mapscalex,resource.mapscaley,1.0))
        resource.mapping_node.set_node_reference(mapping)
    links.new(attribute.outputs[0],mapping.inputs[0])
    links.new(mapping.outputs[0],image_node.inputs[0])
    if part.uvs:
        attribute = create_node(node_group,'ShaderNodeAttribute', -600,0, "", "")
        attribute.attribute_name = part.uvs
        links.new(attribute.outputs[1],mapping.inputs[0])
    return image_node

###
### EXPORT
###

class ExportORALayersOperator(Operator):
    """Export current layers to ORA file"""
    bl_idname = "haspaint.export_to_ora"
    bl_label = "Export to ORA"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):

        if not self.filepath:
            self.report({'ERROR'}, "No file path specified.")
            return {'CANCELLED'}

        if not self.filepath.lower().endswith(".ora"):
            self.filepath += ".ora"

        ora_file = self.filepath

        part = get_material_collection() 
        layers = list(get_layers(part.base_layers))  
        layers.reverse() 

        save_dir = os.path.join(bpy.app.tempdir, "ora_temp")
        os.makedirs(save_dir, exist_ok=True)
        
        layer_files = []
        ora_layers = []
        
        for i, layer in enumerate(layers):
            if layer.resource.image:
                texture_name = BakeLayerToImage(self,context, layer).name
                self.report({'INFO'}, f"Processing Layer {i}: {texture_name}")
                
                image_name = f"layer_{i}.png"
                image_path = os.path.join(save_dir, image_name)
                layer.resource.image.filepath_raw = image_path
                layer.resource.image.file_format = 'PNG'
                layer.resource.image.save_render(image_path)
                
                ora_layer = {
                    "name": texture_name,
                    "src": f"data/{image_name}",
                    "opacity": str(layer.opacity),
                    "composite-op": "svg:src-over" 
                }

                ora_layers.append(ora_layer)
                layer_files.append(image_path)

                self.report({'INFO'}, f"Layer {i}: {texture_name} saved as {image_name}")

        stack = Element("image", {"w": str(layer.resource.image.size[0]), "h": str(layer.resource.image.size[1]), "xres": "96", "yres": "96"})
        root_stack = SubElement(stack, "stack", {"name": "root", "opacity": "1.0", "composite-op": "svg:src-over"})
        
        for ora_layer in ora_layers:
            SubElement(root_stack, "layer", ora_layer)

        stack_xml_path = os.path.join(save_dir, "stack.xml")
        ElementTree(stack).write(stack_xml_path, encoding='utf-8', xml_declaration=True)

        with zipfile.ZipFile(ora_file, 'w') as ora_zip:
            ora_zip.write(stack_xml_path, "stack.xml")
            for image_file in layer_files:
                ora_zip.write(image_file, os.path.join("data", os.path.basename(image_file)))

        for image_file in layer_files:
            os.remove(image_file)
        os.remove(stack_xml_path)
        os.rmdir(save_dir)

        self.report({'INFO'}, f"ORA file created: {ora_file}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ImportORALayersOperator(Operator):
    """Import ORA file as layers"""
    bl_idname = "haspaint.import_from_ora"
    bl_label = "Import ORA"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')

    filter_glob: StringProperty(
        default="*.ora",
        options={'HIDDEN'}
    )

    def execute(self, context):
        extract_dir = os.path.join(bpy.app.tempdir, "ora_import_temp")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(self.filepath, 'r') as ora_zip:
                ora_zip.extractall(extract_dir)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to extract ORA file: {e}")
            return {'CANCELLED'}

        stack_xml_path = os.path.join(extract_dir, 'stack.xml')
        if not os.path.exists(stack_xml_path):
            self.report({'ERROR'}, "stack.xml not found in the ORA file")
            return {'CANCELLED'}

        tree = ElementTree()
        try:
            tree.parse(stack_xml_path)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to parse stack.xml: {e}")
            return {'CANCELLED'}

        root = tree.getroot()

        canvas_width = int(root.attrib.get('w', 500))  
        canvas_height = int(root.attrib.get('h', 500))

        part = get_material_collection()
        layers = get_layers(part.base_layers)

        for i, layer_element in enumerate(root.findall(".//layer")):
            layer_name = layer_element.attrib.get('name', f"Unnamed Layer {i}")
            layer_src = layer_element.attrib.get('src')
            layer_x = int(layer_element.attrib.get('x', 0))
            layer_y = int(layer_element.attrib.get('y', 0))

            image_path = os.path.join(extract_dir, layer_src)
            if not os.path.exists(image_path):
                self.report({'ERROR'}, f"Layer image not found: {layer_src}")
                continue

            try:

                src_image = bpy.data.images.load(image_path)
                src_image.name = layer_name

                new_image = bpy.data.images.new(layer_name, width=canvas_width, height=canvas_height)

                new_image.pixels = [0.0] * (canvas_width * canvas_height * 4)

                self.copy_pixels_into_canvas(src_image, new_image, layer_x, layer_y)

                new_layer = layers.add()
                new_layer.resource.image = new_image
                new_layer.name = layer_name

            except Exception as e:
                self.report({'ERROR'}, f"Failed to add layer {layer_name}: {e}")
                continue
        try:
            for root_dir, dirs, files in os.walk(extract_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root_dir, name))
                for name in dirs:
                    os.rmdir(os.path.join(root_dir, name))
            os.rmdir(extract_dir)
        except Exception as e:
            self.report({'WARNING'}, f"Failed to clean up temporary files: {e}")

        return {'FINISHED'}
    def copy_pixels_into_canvas(self, src_image, canvas_image, offset_x, offset_y):
        """Copy src_image data into canvas_image at the given offset without resizing the original image."""
        if not src_image.has_data:
            src_image.reload()
        if not canvas_image.has_data:
            canvas_image.reload()

        src_pixels = list(src_image.pixels[:])
        canvas_pixels = list(canvas_image.pixels[:])

        src_width, src_height = src_image.size
        canvas_width, canvas_height = canvas_image.size

        for y in range(src_height):
            for x in range(src_width):
                canvas_x = x + offset_x
                canvas_y = (canvas_height - y - 1) - offset_y 

                if 0 <= canvas_x < canvas_width and 0 <= canvas_y < canvas_height:
                    src_index = ((src_height - y - 1) * src_width + x) * 4
                    canvas_index = (canvas_y * canvas_width + canvas_x) * 4

                    canvas_pixels[canvas_index:canvas_index + 4] = src_pixels[src_index:src_index + 4]

        canvas_image.pixels = canvas_pixels
        canvas_image.update()

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

###
### TOOLS
###

vertex_shader = '''
    uniform mat4 u_ViewProjectionMatrix;
    in vec3 position;

    void main()
    {
        gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0);
    }
'''

fragment_shader = '''
    uniform vec4 u_PlaneColor;
    out vec4 FragColor;

    void main()
    {
        FragColor = u_PlaneColor;
    }
'''

try:
    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
except Exception as e:
    shader = None

def create_plane_vertices(size):
    return [
        (-size, -size, 0.0), 
        (size, -size, 0.0),   
        (size, size, 0.0),    
        (-size, size, 0.0),   
    ]

plane_indices = [
    (0, 1, 2),  
    (0, 2, 3),  
]

def get_camera_view_matrix():
    rv3d = bpy.context.space_data.region_3d
    return rv3d.view_matrix.inverted()

def get_plane_world_positions(distance, size):
    view_matrix = get_camera_view_matrix()
    plane_offset = Vector((0, 0, -distance))
    plane_vertices = create_plane_vertices(size)
    return [
        tuple((view_matrix @ (Vector(v) + plane_offset)).to_3d())
        for v in plane_vertices
    ]

def draw_plane():
    try:
        scene = bpy.context.scene
        debugplane_props = getattr(scene, "debugplane_props", None)
        if not debugplane_props or not debugplane_props.show_plane:
            return  

        if shader is None:
            return

        transformed_vertices = get_plane_world_positions(
            debugplane_props.depth_distance,
            debugplane_props.plane_size
        )
        if len(transformed_vertices) < 3:
            return

        batch = batch_for_shader(shader, 'TRIS', {"position": transformed_vertices}, indices=plane_indices)
        if batch is None:
            return

        rv3d = bpy.context.space_data.region_3d
        view_projection_matrix = rv3d.perspective_matrix
        if view_projection_matrix is None:
            return

        with gpu.matrix.push_pop():
            gpu.matrix.load_projection_matrix(view_projection_matrix)
            gpu.state.depth_test_set('LESS')  

            shader.bind()
            shader.uniform_float("u_ViewProjectionMatrix", view_projection_matrix)
            shader.uniform_float("u_PlaneColor", debugplane_props.plane_color)
            batch.draw(shader)

            gpu.state.depth_test_set('NONE')  

    except Exception as e:
        print(f"Error while drawing plane: {e}")

class DepthMaskOperator(Operator):
    bl_idname = "haspaint.depth_mask_operator"
    bl_label = "Depth Mask Operator"

    def execute(self, context):
        scene = context.scene
        distance = scene.debugplane_props.depth_distance
        self.depth_mask_select(context, distance)
        return {'FINISHED'}

    def depth_mask_select(self, context, distance):
        view_3d = bpy.context.space_data.region_3d
        region = bpy.context.region
        rv3d = bpy.context.region_data

        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected")
            return

        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        for face in mesh.faces:
            face.select = False

        for face in mesh.faces:
            for vert in face.verts:
                vert_co_world = obj.matrix_world @ vert.co
                view_vector = view3d_utils.location_3d_to_region_2d(region, rv3d, vert_co_world)

                if view_vector:
                    depth = (view_3d.view_matrix @ vert_co_world).z
                    if abs(depth) < distance:
                        face.select = True
                        break
        bmesh.update_edit_mesh(obj.data)
        
        if context.object.mode != 'TEXTURE_PAINT':
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

class AdjustDepthDistanceOperator(Operator):
    bl_idname = "haspaint.adjust_depth_distance_operator"
    bl_label = "Adjust Depth Distance with Mouse Movement"

    initial_mouse_x: IntProperty()
    initial_distance: FloatProperty()

    _draw_handler = None  

    def modal(self, context, event):
        scene = context.scene

        if event.type == 'MOUSEMOVE':
            delta = event.mouse_x - self.initial_mouse_x
            scene.debugplane_props.depth_distance = self.initial_distance + delta * 0.01

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.ops.haspaint.depth_mask_operator()
            scene.debugplane_props.show_plane = False  
            self.remove_draw_handler()  
            return {'FINISHED'}

        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            scene.debugplane_props.show_plane = False  
            self.remove_draw_handler()  
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene
        self.initial_mouse_x = event.mouse_x
        self.initial_distance = scene.debugplane_props.depth_distance
        scene.debugplane_props.show_plane = True  
        
        self.add_draw_handler()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def add_draw_handler(self):
        
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_plane, (), 'WINDOW', 'POST_VIEW'
        )

    def remove_draw_handler(self):
        
        if self._draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
            self._draw_handler = None

class PaintSelectionOperator(Operator):
    bl_idname = "haspaint.paint_by_selection"
    bl_label = "Paint by Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: StringProperty(default='POLYGON')
    
    start_pos = None
    end_pos = None
    is_drawing = False

    def invoke(self, context, event):
        global operator_running

        if operator_running:
            self.report({'WARNING'}, "Operator is already running.")
            return {'CANCELLED'}

        self.start_pos = (event.mouse_region_x, event.mouse_region_y)
        self.end_pos = (event.mouse_region_x, event.mouse_region_y)
        self.is_drawing = False

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        operator_running = True  
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        global operator_running

        if event.type == 'MOUSEMOVE':
            if self.is_drawing:
                self.end_pos = (event.mouse_region_x, event.mouse_region_y)
                context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.start_pos = (event.mouse_region_x, event.mouse_region_y)
            self.is_drawing = True
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.end_pos = (event.mouse_region_x, event.mouse_region_y)
            self.is_drawing = False
            self.detect_and_paint(context)

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            operator_running = False  
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            operator_running = False  
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def detect_and_paint(self, context):
        if self.start_pos and self.end_pos:
            selection_box = self.get_selection_box()
            self.paint_selection(context, selection_box)
        else:
            self.report({'ERROR'}, "Selection coordinates are not set properly.")

    def get_selection_box(self):
        if self.start_pos and self.end_pos:
            min_x = min(self.start_pos[0], self.end_pos[0])
            max_x = max(self.start_pos[0], self.end_pos[0])
            min_y = min(self.start_pos[1], self.end_pos[1])
            max_y = max(self.start_pos[1], self.end_pos[1])
            return (min_x, max_x, min_y, max_y)
        else:
            return None

    def paint_selection(self, context, selection_box):
        initial_mode = context.active_object.mode

        if self.mode == 'POLYGON':
            self.paint_by_polygon(context, selection_box)
        elif self.mode == 'UV_ISLAND':
            self.paint_by_uv_island(context, selection_box)
        elif self.mode == 'PART':
            self.paint_by_object(context, selection_box)
        bpy.ops.object.mode_set(mode=initial_mode)

    def paint_by_polygon(self, context, selection_box):
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box

            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def paint_by_uv_island(self, context, selection_box):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box
            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.mesh.select_linked(delimit={'SEAM'})

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def paint_by_object(self, context, selection_box):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box
            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.mesh.select_linked(delimit={'NORMAL'})

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def apply_paint_to_selected_faces(self, context):
        obj = context.active_object

        if obj and obj.mode == 'OBJECT':  
            
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

            tool = bpy.context.workspace.tools.from_space_view3d_mode('PAINT_TEXTURE', create=False)
            fill_brush = None
            if tool:
                
                brush = bpy.context.tool_settings.image_paint.brush
                if brush:
                    
                    col = brush.color
                    fill_brush = bpy.data.brushes.get('Fill')
                    bpy.context.scene.tool_settings.image_paint.brush = fill_brush
                    
                    if fill_brush:
                        oldcol = fill_brush.color
                        fill_brush.color = col

            obj.data.use_paint_mask = True

            bpy.context.scene.tool_settings.image_paint.brush = bpy.data.brushes['Fill']

            bpy.ops.paint.image_paint(stroke=[{
                "name": "defaultStroke",
                "mouse": (0, 0),  
                "mouse_event": (0, 0),  
                "location": (0.0, 0.0, 0.0),  
                "pen_flip": False,
                "pressure": 1.0,
                "size": bpy.context.scene.tool_settings.unified_paint_settings.size,
                "time": 0.0,
                "is_start": True,
                "x_tilt": 0.0,  
                "y_tilt": 0.0,  
            }])
            if fill_brush:
                fill_brush.color = oldcol
            
            context.area.tag_redraw()

            operator_running = False  
            return {'FINISHED'}
        else:
            operator_running = False  
            self.report({'WARNING'}, "Active object is not a mesh or is not in object mode.")
            return {'CANCELLED'}

    def draw_callback_px(self, context, args):
        
        if not self.is_drawing or not self.start_pos or not self.end_pos or context is None or self is None:
            return

        min_x, max_x, min_y, max_y = self.get_selection_box()
        if min_x and max_x and min_y and max_y:
            vertices = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
                (min_x, min_y)
            ]
            
            shader = gpu.shader.from_builtin('UNIFORM_COLOR' if is_4_0_or_newer else '2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})

            shader.bind()
            shader.uniform_float("color", (1.0, 1.0, 1.0, 0.5))  
            batch.draw(shader)

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        operator_running = False
        return {'CANCELLED'}

###
### COMMON FUNCTIONS
###

def shortid():
    usedids = list(bpy.context.scene.other_props.usedids)
    while True:
        id = str(uuid.uuid4()).replace('-', '')[:6]
        if id not in usedids:
            usedids.append(id)
            bpy.context.scene.other_props.usedids = ''.join(usedids)
            return id

def newimagename(layer_name = ""):
    part = get_material_collection()
    if not part:
        return {'CANCELLED'}
    inlf = layer_name if layer_name else "Layer"
    base_name = f"{part.material.name}{inlf}"
    if bpy.data.images.get(base_name):
        number = 1
        while bpy.data.images.get(f"{base_name}_{number:02}"):
            number += 1
        image_name = f"{base_name}_{number:02}"
    else:
        image_name = base_name

    result = image_name.replace(' ', '')
    result = re.sub(r'[^A-Za-z0-9]', '', result)
    return result

def newlayername(pref = ""):
    part = get_material_collection()
    if not part:
        return {'CANCELLED'}
    base_name = f"{pref} Layer"
    if pref == "Folder":
        base_name = pref
    number = 1
    existing_layer_names = {l.layer_name for l in part.layers}

    while True:
        layer_name = f"{base_name} {number:02}"
        if layer_name not in existing_layer_names:
            break
        number += 1

    return layer_name

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def CheckForEmpty():
    part = get_material_collection()

    for index, layer in enumerate(part.layers):
        
        if layer.id == "empty":
            remove_by_id(layer.id)
            part.layers.remove(index)
    ids = get_all_ids_from_layers()

    for index, layer in enumerate(part.base_layers):
        if not layer.id in ids:
            part.base_layers.remove(index)
        if layer.get_layer():
            for si, sl in enumerate(get_layers(layer.get_layer().sub_layers)):
                if not sl.id in ids:
                    remove_by_id(sl.id)
                    sl.sub_layers.remove(si)
        else:
            part.base_layers.remove(index)

def remove_references(layer):
    part = get_material_collection()
    remove_by_id(layer.id)

def remove_by_id(id):
    part = get_material_collection()
    for i, l in enumerate(part.layers):
        for si, sl in enumerate(l.sub_layers):
            if sl.id == id:
                l.sub_layers.remove(i)
                break
    for i, l in enumerate(part.base_layers):
        if l.id == id:
            part.base_layers.remove(i)
            break
    for i, l in enumerate(part.layers):
        if l.id == id:
            part.layers.remove(i)
            break

def get_all_ids_from_layers():
    part = get_material_collection()
    ids = []
    for index, layer in enumerate(part.layers):
        ids.append(layer.id)
    return ids

def remove_layer_ref(layers, id):
    for i, l in enumerate(layers):
        if l.id == id:
            layers.remove(i)
            return
    
def fixorder():
    part = get_material_collection()

    update_layers_index(part.layers)
    update_layers_index(part.base_layers)
    for l in get_layers(part.base_layers):
        if l:
            update_layers_index(l.sub_layers)

def update_layers_index(layers):
    for index, layer in enumerate(layers):
        layer.index = index

def check_attach(self, context):
    part = get_material_collection()
    lastlayer = None
    for layer in get_layers(part.base_layers):

        if layer.texture_type == "MASK":
            if lastlayer:
                layer.attachedto = lastlayer.resource.image.name
        else:
            layer.attachedto = ""
            lastlayer = layer

def get_material_collection():

    curscene = bpy.context.scene

    target_view_layer = curscene.view_layers[0]
    active_object = target_view_layer.objects.active

    part= None
    mtlprops = curscene.material_props
    for ind, prop in enumerate(mtlprops):
        if prop:
            if prop.material == active_object.active_material:
                return prop
    return None

def check_material_collection():
    mtlprops = bpy.context.scene.material_props

    for ind in range(len(mtlprops) - 1, -1, -1):
        prop = mtlprops[ind]
        if prop:
            if not prop.material == bpy.context.active_object.active_material:
                if prop.material:
                    if prop.material.users ==1:
                        if 0 == len(prop.layers):
                            mtlprops.remove(ind)
                else:
                    if 0 == len(prop.layers):
                            mtlprops.remove(ind)

def getusedtypesinlayers(layers):
    usedtypes = []

    for type in getusedmaps():
        for layer in layers:
            if layer.texture_type == type[0]:
                
                usedtypes.append(type[0])

                break

    return usedtypes

def get_next_set_name():
    base_name = "Set"
    number = 1

    material_collection = bpy.context.scene.material_props

    existing_names = {mat.name for mat in material_collection}

    while f"{base_name}_{number:02}" in existing_names:
        number += 1

    return f"{base_name}_{number:02}"

def remap_value(value, in_min, in_max, out_min, out_max):
    return(((value - in_min) * (out_max - out_min)) / (in_max - in_min)) + out_min
    
def generate_filename(name_template, context, obj_name, mtl_name, file_name, set_name):
    values = {
        'obj': obj_name,
        'mtl': mtl_name,
        'file': file_name,
        'set': set_name,
     }
    
    pattern = re.compile(r'\((.*?)\)')
    
    def replace_match(match):
        key = match.group(1)
        return values.get(key, f'({key})')
    
    file_name = pattern.sub(replace_match, name_template)
    
    return file_name

def find_node_by_name(self, node_tree, name):
        for node in node_tree.nodes:
            if node.name == name:
                return node
            elif node.type == 'GROUP' and node.node_tree:
                found_node = self.find_node_by_name(node.node_tree, name)
                if found_node:
                    return found_node
        return None

def next_power_of_two(x):
    return 2**(x-1).bit_length()

def SelectTexture(texture_name):
    if not texture_name:
        texture_name = get_material_collection().layers[len(get_material_collection().layers)-1].image.name
    bpy.context.scene.selected_texture = texture_name
    texture = bpy.data.images.get(texture_name)
    if texture:
        bpy.context.scene.tool_settings.image_paint.canvas = texture
        if not texture.preview_ensure():
            texture.asset_generate_preview()
        if bpy.context.scene.tool_settings.image_paint.mode == 'MATERIAL':
            bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'                       

def SelectLayer(id):
    part = get_material_collection()
    layer = get_layer_by_id(id)
    part.selected_layer = id
    part.selected_alpha = False

    if layer.resource.image:
        SelectTexture(layer.resource.image.name)
        return
    bpy.context.scene.selected_texture = ""
    bpy.context.scene.tool_settings.image_paint.canvas = None

def lerp(a, b, t):
    return a + (b - a) * t

def can_be_added_to(layer):
    part = get_material_collection()
    if part.addtofolder and not layer.attachedto or layer.attachedto == part.addtofolder:
        return True
    return False

def fraction_between(value, min_val, max_val):
    if max_val == min_val:
        return 0
    return (value - min_val) / (max_val - min_val)

def get_layer_by_id(id):
    part = get_material_collection()
    for l in part.layers:
        if l.id == id:
            return l
    return None

def get_connected_nodes(node, visited=None):
    if visited is None:
        visited = set()

    visited.add(node)

    for output in node.outputs:
        if output.is_linked:
            for link in output.links:
                connected_node = link.to_node
                if connected_node not in visited:
                    get_connected_nodes(connected_node, visited)

    for input_ in node.inputs:
        if input_.is_linked:
            for link in input_.links:
                connected_node = link.from_node
                if connected_node not in visited:
                    get_connected_nodes(connected_node, visited)

    return visited

def reassign_layer(fromlist, tolist, id, parent = None):
    remove_layer_ref(fromlist, id)
    subl = tolist.add()
    subl.id = id
    get_layer_by_id(id).attachedto = parent.id if parent else ""

def get_links(node, socket):
    node_tree = node.id_data
    socket = node.inputs[socket]
    saved_links = [(link.from_node, link.from_socket) for link in socket.links]
    return saved_links

def set_links(saved_links, socket):
    for from_node, from_socket in saved_links:
        node_tree = from_node.id_data  
        node_tree.links.new(from_socket, socket)

def clear_socket_links(node, index):
    node_tree = node.id_data
    for link in node.inputs[index].links:
        node_tree.links.remove(link)

def get_layer_in_list(list, id):
    for item in list:
        if item.id == id:
            return item
    return None

def get_layer_below(inlist, id):
    lastind = -1
    for item in inlist:
        if item.id == id:
            
            foundlayer = inlist[lastind]
            part = get_material_collection()
            for layer in part.layers:
                if layer.id == foundlayer.id:

                    return layer
        lastind = item.index
    return None

def move_last_to_selected(inlist):
    part = get_material_collection()

    layer = get_layer_by_id(part.selected_layer)
    if layer:
        foundind= -1
        for i, ds in enumerate(inlist):
            if ds.id == layer.id:
                foundind = ds.index
        if not foundind == -1:
            inlist.move(len(inlist) - 1, foundind +1)
 
def get_selected_layer_index():
    part = get_material_collection()
    
    layer = get_layer_by_id(part.selected_layer)
    if layer:
        return layer.index

    selt = bpy.context.scene.selected_texture
    if selt:
        for layer in part.layers:
            if layer.resource.image:
                if selt == layer.resource.image.name:
                    return layer.index

    return -1

def is_selected(layer):
    part = get_material_collection()
    selnm= ""
    sameimg = False
    selected =False
    if part.selected_layer:
        selected = layer.id == part.selected_layer
    if layer.resource.image:
        selnm = layer.resource.image.name
        sameimg = bpy.context.scene.selected_texture == layer.resource.image.name
    selectedalpha = False
    if selected:
        selectedalpha = part.selected_alpha
    return selected, selectedalpha, selnm, sameimg

def get_image_histogram(image_name, num_bins=20, sample_rate=0.25):

    image = bpy.data.images.get(image_name)
    if image is None or not image.pixels:
        return ""
    
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape((height, width, 4))
    normalized_values = (pixels.flatten() * (num_bins - 1)).astype(int)
    histogram = np.bincount(normalized_values, minlength=num_bins)
    histogram = histogram / histogram.sum()
    
    return ','.join(map(str, histogram))

def any_active_filter(filters):
    if not filters:
        return False
    for filter in filters:
        if filter.in_use:
            return True
    return False

def parse_histogram_string(histogram_str):
    return [float(value) for value in histogram_str.split(',')]

def get_histogram(texture_name):
    for hist in bpy.context.scene.other_props.HistogramRefs:
        if hist.texture_name == texture_name:
            return hist.histogram
    return ""

def set_histogram(texture_name, histogram):
    for hist in bpy.context.scene.other_props.HistogramRefs:
        if hist.texture_name == texture_name:
            hist.histogram = histogram
            return
    hist = bpy.context.scene.other_props.HistogramRefs.add()
    hist.texture_name = texture_name
    hist.histogram = histogram
    
def update_hist_display(texture_name):
    name = ".HAS_SceneProperties"
    if name in bpy.data.node_groups:
        node_group = bpy.data.node_groups[name]
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    histrefs = bpy.context.scene.other_props.HistogramRefs

    for hist in histrefs:
        if hist.texture_name == texture_name:
            
            levelvis = get_node_by_name(node_group, texture_name)
            if not levelvis:
                levelvis = create_node(node_group, 'ShaderNodeFloatCurve' , -600,0, "", "")
                levelvis.name = hist.texture_name
            if levelvis:
                curve = levelvis.mapping.curves[0]
                for i, point in enumerate(parse_histogram_string(hist.histogram)):
                    if len(curve.points)>i:
                        curve.points[i].location = (i/19, point*1.0)
                    else:
                        curve.points.new(i/19, point*1.0)
                levelvis.mapping.update()

def check_socket(sockets, name):
    if name in sockets:
        
        return True
    return False

def check_for_sockets(sockets, names):
    for name in names:
        
        if not check_socket(sockets, name):
            return False
    return True

def get_custom_shader_groups():
    enum_items = []
    enum_items.append(('Empty', 'Empty', ''))
    for node_group in bpy.data.node_groups:
        if node_group.type == 'SHADER':
            group_name = node_group.name
            if not group_name.startswith("."):
                enum_items.append((group_name, group_name, "Custom Shader Group Node"))
    
    if not enum_items:
        enum_items.append(('NONE', 'None', 'No custom shader node groups found'))
    
    return enum_items

def check_filter_sockets(filter, filternode):
    if len(filternode.inputs)<=filter.socket_in:
        filter.socket_in = 0
    if len(filternode.outputs)<=filter.socket_out:
        filter.socket_out = 0

@contextmanager
def temporary_scene_settings(settings):
    
    original_settings = {}
    selected_objects = list(bpy.context.selected_objects)
    active_object = bpy.context.view_layer.objects.active

    for setting, value in settings.items():
        if setting == 'selected_objects':
            continue  
        path, attr = setting.rsplit(".", 1)
        obj = eval(path)
        original_settings[setting] = getattr(obj, attr)

    try:
        
        for setting, value in settings.items():
            if setting == 'selected_objects':
                
                bpy.ops.object.select_all(action='DESELECT')
                for obj in value:
                    obj.select_set(True)
                continue
            path, attr = setting.rsplit(".", 1)
            obj = eval(path)
            setattr(obj, attr, value)
        
        yield  
    finally:
        
        for setting, value in original_settings.items():
            path, attr = setting.rsplit(".", 1)
            obj = eval(path)
            setattr(obj, attr, value)
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            obj.select_set(True)
        
        bpy.context.view_layer.objects.active = active_object

@bpy.app.handlers.persistent
def save_modified_images(dummy):
    if bpy.context.scene.other_props.toggle_save:
        for image in bpy.data.images:
            if image.is_dirty:
                bpy.ops.image.save_all_modified()
                return

def getdescription(enumfrom, propfrom):
    for item in enumfrom:
        if item:
            if item[0] == propfrom:
                return item[2]
    return None

def getname(enumfrom, propfrom):
    for item in enumfrom:
        if item:
            if item[0] == propfrom:
                return item[1]
    return None
###
### Keys
###

class EraseBrush(Operator):
    bl_label = "Select erase brush"
    bl_idname = "haspaint.erase_brush"
    
    def execute(self, context):
        current_brush = context.tool_settings.image_paint.brush

        if current_brush and current_brush.blend == 'MIX':
            current_brush.blend = 'ERASE_ALPHA'
        else:
            current_brush.blend = 'MIX'
        return {'FINISHED'}

class LineStroke(Operator):
    bl_label = "Use Line Stroke"
    bl_idname = "haspaint.line_stroke"
    
    press: BoolProperty()

    def execute(self, context):
        current_brush = context.tool_settings.image_paint.brush

        if current_brush:
            if self.press:
                current_brush.stroke_method = 'LINE'
            else:
                current_brush.stroke_method = 'SPACE'
        return {'FINISHED'}

###
### REGISTER
###
classes = [
    DebugPlaneProps,
    
    SocketReference,
    NodeReference,
    HistrogramReference,
    LevelsProperty,
    ResourceProperty,
    Brushes,
    UsedMaps,
    LineStroke,
    TextureMappedProperty,
    UnlinkImageOperator,
    HAS_PT_LayersPanel,
    CleanupData,
    SaveImageOperator,
    SetFilterOperator,
    FilterSelectPopup,
    SetTypeOperator,
    WM_OT_OpenWebsite,
    OpenImageOperator,
    ObjectsColProperty,
    DuplicateLayerOperator,
    OtherActionsOperator,
    TypeSelectPopup,
    LayerActionPopup,
    ImageInfoPopup,
    CombineAllLayersOperator,
    SelectTextureOperator,
    MaskGeneratorProperty,
    GetFromSelected,
    RemoveAllBakeObjects,
    SetSortColorOperator,
    FilterProperty,

    BakeMapSettings,
    BakingProperties,
    LayerReference,
    AddHASImage,
    LayerProperties,
    MoveLayerOperator,
    UncheckLayerOperator,
    SaveLayersOperators,
    TextureTypeProp,
    OtherProps,
    ResizeAllLayersPopup,
    TextureSizeAddSubtract,
    DeleteLayersOperator,
    UpdateHist,
    OT_AddMyPreset,
    PR_MT_HASPresets,
    AddTextureTypeProp,
    RemoveTextureTypeProp,
    ExecutePreset,
    CombineWithLayerBelowOperator,
    HASMaterialProperties,
    CustomNewImageOperator,
    SetupMaterial,
    HASRemoveMaterial,
    ProjectApply,
    ProjectRemove,
    ProjectOpen,

    SCREEN_OT_crop_tool,
    ViewData,
    SnapToView,
    ExportORALayersOperator,
    ImportORALayersOperator,
    CollapseLayer,
    DepthMaskOperator,
    AdjustDepthDistanceOperator,
    TEXTURE_PT_file_browser_panel,
    PaintSelectionOperator,
    RemoveFilter,
    MoveFilterOperator,
    OpacityControlOperatorPOPUP,
    FilterChangeInOut,
    SetStandardVT,
    AddFilter,
    ShowHideFilter,
    IsolateImage,
    AddMaskGenBlock,
    RemoveMaskGenBlock,
    BAKING_OT_BakeTextures,
    AddBakeMap,
    RemoveBakeMap,
    RenameLayer,
    CreatePBRLayer,
    RemoveLayer,
    SetUsedMaps,
    SetupScene,
    ActivateTab,
    SetLayerData,
    SetQEFolder,
    ExportTextures,
    ResizeTexturePopup,

    EraseBrush,
    SnapshotLayer,
    ProjectBakeApply,
    ProjectBakeGet,
    BakeMapPref,
    AddLayerToFolderOperator,
    StartAddToFolderOperator,
    CreateFolderOperator,
]
def register_properties():
    bpy.types.Scene.paint_mode = EnumProperty(
        items=[
            ('POLYGON', 'By Polygon', 'Paint by individual polygons'),
            ('UV_ISLAND', 'By UV Island', 'Paint by UV islands'),
            ('PART', 'By Part', 'Paint by Separate Part')],
        name="Paint Mode",
        description="Choose the selection mode"
    )

def unregister_properties():
    del bpy.types.Scene.paint_mode

addon_keymaps = []

def register():
    for cls in classes:
            register_class(cls)
    register_properties()
    bpy.types.Scene.material_props = CollectionProperty(type=HASMaterialProperties)
    bpy.types.Scene.other_props = PointerProperty(type=OtherProps)
    bpy.types.Scene.debugplane_props = PointerProperty(type=DebugPlaneProps)

    presets_folder = bpy.utils.user_resource('SCRIPTS', create=True)

    has_presets = bpy.utils.user_resource('SCRIPTS', path= "presets/haspresets/savedpresets", create=False)
    
    bpy.types.Scene.has_presets = StringProperty(name="My Presets", default=has_presets)

    if not os.path.isdir(has_presets):
        os.makedirs(has_presets)

    if save_modified_images not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_modified_images)
    bpy.types.Scene.view_data = CollectionProperty(type=ViewData)
    
    bpy.types.Scene.selected_texture = StringProperty(name="Selected Texture")

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Image Paint', space_type='EMPTY')

    kmi = km.keymap_items.new("haspaint.erase_brush", 'E', 'PRESS', ctrl=False, shift=False)

    kmi_press = km.keymap_items.new("haspaint.line_stroke", 'W', 'PRESS', ctrl=False, shift=False)
    kmi_press.properties.press = True 

    kmi_release = km.keymap_items.new("haspaint.line_stroke", 'W', 'RELEASE', ctrl=False, shift=False)
    kmi_release.properties.press = False

    addon_keymaps.append(km)
    
def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.selected_texture
    del bpy.types.Scene.other_props
    del bpy.types.Scene.debugplane_props
    if save_modified_images in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_modified_images)

    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    # clear the list
    addon_keymaps.clear()

    del bpy.types.Scene.view_data
    unregister_properties()

if __name__ == "__main__":
    register()
