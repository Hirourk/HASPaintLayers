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
    "version": (0, 4, 5),
    "description": "Layers for texture painting",
    "author": "Hirourk",
    "location": "View3D > Tool Shelf > Paint Layers",
    "warning": "",
    "doc_url": ""
}

import os
import bpy
import re
import shutil
from pathlib import Path
from bl_operators.presets import AddPresetBase
from bpy.props import CollectionProperty, StringProperty, IntProperty, PointerProperty, BoolProperty, FloatVectorProperty, FloatProperty
import numpy as np
from bl_ui.utils import PresetPanel
from bpy.types import Panel, Operator, PropertyGroup, Menu, Scene, UIList
import bpy.utils.previews
from bpy.utils import register_class, unregister_class
from bpy.app.handlers import persistent, save_pre
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix,  Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
import blf
import requests

GITHUB_API_URL = "https://github.com/Hirourk/HASPaintLayers/releases/latest"
CURRENT_VERSION = "1.0.0"

BLEND_MODES = [
    ('MIX', 'Mix', 'Mix the layers'),
    ('ADD', 'Add', 'Add the layers'),
    ('MULTIPLY', 'Multiply', 'Multiply the layers'),
    ('SUBTRACT', 'Subtract', 'Subtract the layers'),
    ('SCREEN', 'Screen', 'Screen the layers'),
    ('DIVIDE', 'Divide', 'Divide the layers'),
    ('DIFFERENCE', 'Difference', 'Difference between the layers'),
    ('DARKEN', 'Darken', 'Darken the layers'),
    ('LIGHTEN', 'Lighten', 'Lighten the layers'),
    ('OVERLAY', 'Overlay', 'Overlay the layers'),
    ('DODGE', 'Dodge', 'Dodge the layers'),
    ('BURN', 'Burn', 'Burn the layers'),
    ('HUE', 'Hue', 'Combine Hue of the layers'),
    ('SATURATION', 'Saturation', 'Combine Saturation of the layers'),
    ('VALUE', 'Value', 'Combine Value of the layers'),
    ('COLOR', 'Color', 'Combine Color of the layers'),
    ('SOFT_LIGHT', 'Soft Light', 'Soft light blending'),
    ('LINEAR_LIGHT', 'Linear Light', 'Linear light blending'),
]
TEXTURE_TYPE = [
    ('DIFFUSE', 'Diffuse', 'Texture as Diffuse'),
    ('METALLIC', 'Metallic', 'Texture as Metallic'),
    ('ROUGHNESS', 'Roughness', 'Texture as Roughness'),
    ('EMISSION', 'Emission', 'Texture as Emission'),
    ('ALPHA', 'Alpha', 'Texture as Alpha'),
    ('NORMAL', 'Normal', 'Texture as Normal'),
    ('HEIGHT', 'Height', 'Texture as Height'),
    ('ADJUSTHSV', 'Adjust HSV', 'Layer for HSV adjustment'),
    ('COLORRAMP', 'Adjust Color ramp', 'Layer for Color ramp adjustment'),
    ('MASK', 'Adjust Mask', 'Layer for Masking'),
    ('CUSTOM', 'Custom node', 'Layer for Custom node'),
    #('FOLDER', 'Folder', 'Folder for layers'),
]
USE_TEXTURE_TYPE = [
    ('DEFAULT', 'Default', ''),
    ('HEIGHT', 'Height', ''),
    ('NORMAL', 'Normal', ''),
    ('ADJUST', 'Adjust', ''),
    #('FOLDER', 'Folder', ''),
]
TEXTURE_FILTER = [
    ('Linear', 'Linear', ''),
    ('Closest', 'Closest', ''),
    ('Cubic', 'Cubic', ''),
    ('Smart', 'Smart', ''),
]
TEXTURE_PROPERTIES = {
    'DIFFUSE': (0, USE_TEXTURE_TYPE[0], True, "Base Color", ""),
    'METALLIC': (6, USE_TEXTURE_TYPE[0], True, "Metallic", ""),
    'ROUGHNESS': (9, USE_TEXTURE_TYPE[0], True, "Roughness", ""),
    'EMISSION': (19, USE_TEXTURE_TYPE[0], True, "Emission", "Emission Color"),
    'ALPHA': (21, USE_TEXTURE_TYPE[0], True, "Alpha", ""),
    'NORMAL': (22, USE_TEXTURE_TYPE[2], True, "Normal", ""),
    'HEIGHT': (22, USE_TEXTURE_TYPE[1], True, "Height", ""),
    'ADJUSTHSV': (-1, USE_TEXTURE_TYPE[3], False, "", ""),
    'COLORRAMP': (-1, USE_TEXTURE_TYPE[3], False, "", ""),
    'MASK': (-1, USE_TEXTURE_TYPE[3], False, "", ""),
    'CUSTOM': (-1, USE_TEXTURE_TYPE[3], False, "", ""),
    #'FOLDER': (-1, USE_TEXTURE_TYPE[4], False),
}
# Get Blender version
version = bpy.app.version
# Define version flags
is_pre_3_1 = version[0] == 3 and version[1] < 1
is_3_5_or_newer = version[0] == 3 and version[1] >= 5
is_4_0_or_newer = version[0] >= 4



class LayerProperties(bpy.types.PropertyGroup):

    # Update function for cn_input
    def update_layer_input(self, context):
        # Clamp the value of cn_input
        node_group = bpy.data.node_groups.get(self.custom_node)
        if node_group:
            if is_4_0_or_newer:
                max_inputs = len([sock for sock in node_group.interface.items_tree if sock.in_out == 'INPUT']) - 1
                if self.cn_input < 0:
                    self.cn_input = 0
                elif self.cn_input > max_inputs:
                    self.cn_input = max_inputs
            else:
                max_inputs = len(node_group.inputs)-1
                if self.cn_input < 0:
                    self.cn_input = 0
                elif self.cn_input > max_inputs:
                    self.cn_input = max_inputs
        UpdateShader()

    def update_layer_output(self, context):
        # Clamp the value of cn_input
        node_group = bpy.data.node_groups.get(self.custom_node)
        if node_group:
            if is_4_0_or_newer:
                max_outputs = len([sock for sock in node_group.interface.items_tree if sock.in_out == 'OUTPUT']) - 1
                if self.cn_output < 0:
                    self.cn_output = 0
                elif self.cn_output > max_outputs:
                    self.cn_output = max_outputs
            else:
                max_outputs = len(node_group.outputs)-1
                if self.cn_output < 0:
                    self.cn_output = 0
                elif self.cn_output > max_outputs:
                    self.cn_output = max_outputs
        UpdateShader()
    def update_layer_action(self, context):
        if self.currentlayer_actions == 'EDIT':
            self.perform_action_one(context)
        elif self.currentlayer_actions == 'COMBINEDOWN':
            self.perform_action_two(context)

    def perform_action_one(self, context):
        setup_composite_scene(self.image)

    def perform_action_two(self, context):
        part = get_material_collection(None)
        for i, l in enumerate(part.layers):
            if l==self:
                bpy.ops.texturelayer.combine_textures_func(layer=i)
                break

    def update_layer(self, context):
        UpdateShader()
    def get_node_groups(self, context):
        prefixes_to_check = ['DIFFUSE_Group', 'METALLIC_Group', 'ROUGHNESS_Group', 'EMISSION_Group', 'ALPHA_Group', 'NORMAL_Group', 'HEIGHT_Group']
        items = [(group.name, group.name, "") for group in bpy.data.node_groups if not any(group.name.startswith(prefix) for prefix in prefixes_to_check)]
        return items
    def get_texture_types(self, context):
        items = [(t_type[0], t_type[1], t_type[2]) for t_type in TEXTURE_TYPE]
        return items
    blend_mode: bpy.props.EnumProperty(
        name="Blend Mode",
        items=BLEND_MODES,
        description="Blend mode for mixing layers",
        default="MIX",
        update=update_layer
    )
    texture_type: bpy.props.EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
        #default="DIFFUSE",
        update=update_layer
    )
    opacity: bpy.props.FloatProperty(
        name="Opacity",
        description="Opacity of the layer",
        default=1.0,
        min=0.0,
        max=1.0,
        update=update_layer
    )

    use_layer: bpy.props.BoolProperty(
        name="Use Layer",
        description="Toggle layer visibility",
        default=True,
        update=update_layer
    )
    currentlayer_actions: bpy.props.EnumProperty(
        name="Layer Action",
        items=[
            #('EDIT', "Edit externally", "Edit current texture in external editor"),
            ('COMBINEDOWN', "Combine with layer below", "Combine with layer below"),
        ],
        default='COMBINEDOWN',
        update=lambda self, context: self.update_layer_action(context)
    )
    def update_on_image(self, context):
        CheckForEmpty()
        UpdateShader()

    image: bpy.props.PointerProperty(
        name="Image",
        type=bpy.types.Image,
        update=update_on_image
    )

    node_group_name: bpy.props.StringProperty(
        default="",
        name="Node group name",
    )
    node_name: bpy.props.StringProperty(
        default="",
        name="Node",
        description="Name of the node"
    )
    custom_node: bpy.props.EnumProperty(
        items=get_node_groups,
        name="Node",
        update=update_layer
    )
    cn_input: bpy.props.IntProperty(
        default=0,
        name="Input",
        update=update_layer_input,
    )
    cn_output: bpy.props.IntProperty(
        default=0,
        name="Output",
        update=update_layer_output,
    )
    cn_type: bpy.props.EnumProperty(
        name="Use",
        items=[
            ('COLOR', "Color", "Used for color output in Texture node"),
            ('UV', "UV", "Used for vector input for Texture node"),
            #('ALPHA', "Alpha", "Used for alpha output in Texture node"),
        ],
        default='COLOR',
        update=update_layer
    )
    hue: bpy.props.FloatProperty(
        name="Hue",
        default=0.5,
        min=0.0,
        max=1.0,
        update=update_layer
    )
    saturation: bpy.props.FloatProperty(
        name="saturation",
        default=1.0,
        min=0.0,
        max=2.0,
        update=update_layer
    )
    value: bpy.props.FloatProperty(
        name="value",
        default=1.0,
        min=0.0,
        max=2.0,
        update=update_layer
    )


def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))
    
# Function to update the texture previews
def update_texture_previews(self, context):
    enum_items = []
    part = get_material_collection(None)
    for layer in part.layers:
        if layer.image:
            texture = bpy.data.images.get(layer.image.name)
            if texture:
                texture.preview_ensure()
                icon_id = texture.preview.icon_id
                enum_items.append((layer.name, layer.name, 'Description for ' + layer.name, icon_id))
    
    return enum_items

class OtherProps(PropertyGroup):

    def update_layer(self, context):
        UpdateShader()
    def update_savepath(self, context):
        print (f"{self.save_path}")
    image: bpy.props.PointerProperty(
        name="Image",
        type=bpy.types.Image
    )
    texture_filtering: bpy.props.EnumProperty(
        name="Texture filtering",
        items= TEXTURE_FILTER,
        default='Linear',
        update=update_layer
    )
    expand_area_MtlSettings: bpy.props.BoolProperty(
        name="Expand Material Settings",
    )
    expand_area_Actions: bpy.props.BoolProperty(
        name="Expand Actions",
    )
    expand_area_Saving: bpy.props.BoolProperty(
        name="Expand Saving",
    )
    expand_area_Materials: bpy.props.BoolProperty(
        name="Expand Materials",
    )
    expand_area_CreateLayer: bpy.props.BoolProperty(
        name="Create layer options",
    )
    expand_area_MaterialCollection: bpy.props.BoolProperty(
        name="Material collection",
    )
    expand_area_ProjectTexture: bpy.props.BoolProperty(
        name="Projection",
    )
    bakemtl: bpy.props.PointerProperty(
        name="Bake Mtl",
        type=bpy.types.Material
    )
    save_path: bpy.props.StringProperty(
        name="Save Path",
        default="",
        description="Folder for texture export",
        subtype='DIR_PATH',
        update=update_savepath
    )
    height_to_normal: bpy.props.BoolProperty(
        name="Bake height to normal",
        default=True,
    )
    invert_green_n: bpy.props.BoolProperty(
        name="Invert G channel for Normal",
        default=False,
    )
    layercombineactive: bpy.props.BoolProperty(
        name="LayerCombineActive",
        default=False,
    )
    toggle_save: bpy.props.BoolProperty(
        name="Save textures with file",
        default=True,
    )
    screen_capture_scale: bpy.props.FloatProperty(
        name="Screen capture scale",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Scale capture scale"
    )
    screen_grab_size_y: bpy.props.IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Height of the screen grab"
    )
    screen_grab_size_x: bpy.props.IntProperty(
        name="Screen Grab Size Y",
        default=1024,
        min=1,
        description="Width of the screen grab"
    )
    new_texture_type_name: bpy.props.StringProperty(name="Name", default="")
    new_texture_type_label: bpy.props.StringProperty(name="Label", default="")
    new_texture_type_description: bpy.props.StringProperty(name="Description", default="")

def CheckForEmpty():
    part = get_material_collection(None)
    layer_prop = part.layers
    for index, layer in enumerate(layer_prop):
        if not layer.image:
            layer_prop.remove(index)
            #print(f"LayerDeleted {index}")

bpy.types.Scene.selected_texture = bpy.props.StringProperty(name="Selected Texture")

class HASMaterialProperties(PropertyGroup):
    def update_layer(self, context):
        UpdateShader()
    layers: CollectionProperty(type=LayerProperties)
    material: bpy.props.PointerProperty(
        name="Material",
        type=bpy.types.Material
    )
    name: bpy.props.StringProperty(
        default="Set",
        name="Set name",
    )
    shader_type: bpy.props.EnumProperty(
        name="Shader Type",
        items=[
            ('PRINCIPLED', "Principled BSDF", "Use Principled BSDF shader"),
            ('UNLIT', "Unlit", "Use Unlit shader"),
            ('Custom', "Custom", "Use Custom shader"),
        ],
        default='PRINCIPLED',
        update=update_layer
    )
    uvs: bpy.props.StringProperty(
        default="",
        name="UVs",
        description="Name of the UVs attribute",
        update=update_layer
    )
    height_intensity: bpy.props.FloatProperty(
        name="Height instensity",
        default=1.0,
        update=update_layer
    )
class TextureTypeProp(PropertyGroup):
    def get_texture_types(self, context):
        items = []
        for t_type in TEXTURE_TYPE:
            if TEXTURE_PROPERTIES[t_type[0]][2]:
                items.append(t_type)
        return items
    texture_type: bpy.props.EnumProperty(
        name="Texture type",
        items=get_texture_types,
        description="Texture use type",
    )
    use_type: bpy.props.BoolProperty(
        name="Use texture type",
        default=True
    )
    use_alpha: bpy.props.EnumProperty(
        name="Alpha Type",
        items=[
            ('COMBINED', "Combined", "Alpha is combined with texture"),
            ('SEPARATE', "Separate", "Alpha is exported separately"),
            ('NOALPHA', "No Alpha", "Alpha is ignored"),
        ],
        default='COMBINED',
    )
    save_name: bpy.props.StringProperty(
        name="Save Name",
        default="Dif",
        description="Name for saving texture",
    )

class UncheckLayerOperator(bpy.types.Operator):
    bl_idname = "texturelayer.uncheck_layer"
    bl_label = "Uncheck Layer"

    texture_name: bpy.props.StringProperty()

    def execute(self, context):
        part = get_material_collection(None)
        if self.texture_name:
            for layer in part.layers:
                if layer.image:
                    if layer.image.name == self.texture_name:
                        layer.use_layer = not layer.use_layer
                        return {'FINISHED'}
                        break
class CustomNewImageOperator(bpy.types.Operator):
    """Custom Operator to Create a New Image"""
    bl_idname = "image.custom_new"
    bl_label = "New image"
    
    name: bpy.props.StringProperty(name="Name", default="Untitled")
    width: bpy.props.IntProperty(name="Width", default=1024, min=1, max=16384)
    height: bpy.props.IntProperty(name="Height", default=1024, min=1, max=16384)
    color: bpy.props.FloatVectorProperty(name="Color", subtype='COLOR', size=4, default=(0.0, 0.0, 0.0, 1.0), min=0.0, max=1.0)
    alpha: bpy.props.BoolProperty(name="Alpha", default=True)
    float_buffer: bpy.props.BoolProperty(name="32-bit Float", default=False)
    tiled: bpy.props.BoolProperty(name="Tiled", default=False)
    generated_type: bpy.props.EnumProperty(
        name="Generated Type",
        items=[
            ('BLANK', 'Blank', ''),
            ('UV_GRID', 'UV Grid', ''),
            ('COLOR_GRID', 'Color Grid', '')
        ],
        default='BLANK'
    )
    
    def execute(self, context):
        # Create the new image with the specified properties
        new_image = bpy.data.images.new(
            name=self.name,
            width=self.width,
            height=self.height,
            alpha=self.alpha,
            float_buffer=self.float_buffer,
            tiled=self.tiled
        )
        
        # Set the initial color and type if the image type is BLANK
        if self.generated_type == 'BLANK':
            new_image.generated_type = 'BLANK'
            new_image.generated_color = self.color
        elif self.generated_type == 'UV_GRID':
            new_image.generated_type = 'UV_GRID'
        elif self.generated_type == 'COLOR_GRID':
            new_image.generated_type = 'COLOR_GRID'
        
        # Store blend mode for the texture
        part = get_material_collection(None)
        if not part:
            return {'CANCELLED'}
        layer_item = part.layers.add()
        layer_item.blend_mode = 'MIX'
        layer_item.opacity = 1.0
        layer_item.image = new_image

        self.report({'INFO'}, f"Texture '{self.name}' created.")
        bpy.ops.texturelayer.select_texture()
        check_material_collection()
        UpdateShader()
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CreateTextureOperator(Operator):
    bl_idname = "texturelayer.create_texture"
    bl_label = "Create Texture"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Generate a unique layer name
        
        base_name = "Layer"
        number = 1
        while bpy.data.images.get(f"{base_name}_{number:02}"):
            number += 1
        texture_name = f"{base_name}_{number:02}"
        part = get_material_collection(None)
        if not part:
            return {'CANCELLED'}

        xs = context.scene.texture_sizeX
        ys = context.scene.texture_sizeY

        # Ensure that the retrieved values are integers
        assert isinstance(xs, int), f"Expected int, got {type(xs)}"
        assert isinstance(ys, int), f"Expected int, got {type(ys)}"
        new_texture = bpy.data.textures.new(name=texture_name, type='IMAGE')
        new_image = bpy.data.images.new(texture_name, width=xs, height=ys, alpha=True)
        pixels = [0.0] * (4 * xs * ys)
        new_image.pixels = pixels
        new_texture.image = new_image



        # Store blend mode for the texture
        layer = part.layers.add()
        layer.blend_mode = 'MIX'
        layer.opacity = 1.0
        layer.image = new_image
        self.report({'INFO'}, f"Texture '{texture_name}' created.")

        # Call the function to update shader with new layer
        bpy.ops.texturelayer.select_texture()
        check_material_collection()
        UpdateShader()
        return {'FINISHED'}

def get_material_collection(scene):

    curscene = bpy.context.scene
    if scene:
        curscene = scene

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

class CreateLayerFromTextureOperator(Operator):
    bl_idname = "texturelayer.create_layer_from_texture"
    bl_label = "Create layer from texture"
    bl_options = {'REGISTER', 'UNDO'}

    copy: bpy.props.BoolProperty(name="Copy Texture", default=False)

    def execute(self, context):
        # Access the selected texture from OtherProps
        selected_texture = context.scene.other_props.image
        if selected_texture:
            if self.copy:
                # Create a copy of the selected texture's image
                new_image = selected_texture.copy()
                new_image.name = selected_texture.name + "_copy"
                texture_name = new_image.name
            else:
                # Use the existing texture's image
                new_image = selected_texture
                texture_name = selected_texture.name

            # Store blend mode for the texture
            part = get_material_collection(None)
            if not part:
                return {'CANCELLED'}

            layer_item = part.layers.add()
            layer_item.name = texture_name
            layer_item.blend_mode = 'MIX'
            layer_item.opacity = 1.0
            layer_item.image = new_image 

            self.report({'INFO'}, f"Layer '{texture_name}' created with the selected texture.")
            bpy.ops.texturelayer.select_texture()
            # Call the function to update shader with new layer
            check_material_collection()
            UpdateShader()

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No texture selected.")
            return {'CANCELLED'}

class CombineTextures(Operator):
    bl_idname = "texturelayer.combine_textures"
    bl_label = "Combine textures"

    def execute(self, context):
        bpy.ops.texturelayer.combine_textures_func(layer= -1)
        return {'FINISHED'}

def getusedtypes():
    usedtypes = []
    part = get_material_collection(None)
    if part:
        for layer in part.layers:
            if layer.texture_type in TEXTURE_PROPERTIES:
                prop = TEXTURE_PROPERTIES[layer.texture_type]
                if prop[2]:
                    if layer.use_layer:
                        if not layer.texture_type in usedtypes:
                            usedtypes.append(layer.texture_type)
            else:
                if not layer.texture_type in usedtypes:
                    usedtypes.append(layer.texture_type)
    return usedtypes
def get_next_set_name():
    base_name = "Set"
    number = 1

    # Get the material collection from the scene
    material_collection = bpy.context.scene.material_props

    # Check existing material names in the collection
    existing_names = {mat.name for mat in material_collection}

    # Generate a new name that doesn't exist in the collection
    while f"{base_name}_{number:02}" in existing_names:
        number += 1

    return f"{base_name}_{number:02}"

def generate_filename(name_template, context, obj_name, mtl_name, file_name, set_name):
    values = {
        'obj': obj_name,
        'mtl': mtl_name,
        'file': file_name,
        'set': set_name,
     }
    # Regular expression to find placeholders in the format (e.g., (obj_name))
    pattern = re.compile(r'\((.*?)\)')
    
    # Function to replace matched placeholders
    def replace_match(match):
        key = match.group(1)
        return values.get(key, f'({key})')
    
    # Replace placeholders in the prefix_template
    file_name = pattern.sub(replace_match, name_template)
    
    return file_name
def oops(self, context, infos):
    self.layout.label(text=infos)
class CombineTexturesFunc(Operator):
    bl_idname = "texturelayer.combine_textures_func"
    bl_label = "Combine layers"
    bl_options = {'REGISTER', 'UNDO'}

    layer: bpy.props.IntProperty(default = -1)

    def execute(self, context):
        layer = None
        basescene = bpy.context.window.scene
        part = get_material_collection(basescene)

        for i, l in enumerate(part.layers):
            if i==self.layer:
                layer = l
                break
        layer_below = None
        indsdeselected = []
        save_path = basescene.other_props.save_path
        layer_prop = part.layers
        if layer:
            #print("Custom layer selected")
            for ind, layer_s in enumerate(layer_prop):
                if layer == layer_s:
                    layer_below = layer_prop[clamp(ind-1,0,ind)]
                    if not layer_below.texture_type == layer_s.texture_type:
                        prop = TEXTURE_PROPERTIES[layer_s.texture_type]
                        if prop[2]:
                            layer_s.texture_type = layer_below.texture_type
            if not layer_below or layer_below==layer:
                return {'CANCELLED'}
            for ind, layer_s in enumerate(layer_prop):
                if layer_s == layer_below or layer_s ==layer:
                    layer_s.use_layer=True
                else:
                    if layer_s.use_layer:
                        indsdeselected.append(ind)
                        layer_s.use_layer=False
        elif not save_path or not os.path.exists(save_path):
            info_text = f"No valid path is specified"
            bpy.context.window_manager.popup_menu(lambda self, context: oops(self, context, info_text), title="Error", icon='ERROR')
            return {'CANCELLED'}
        else:
            basescene.other_props.layercombineactive = False
        UpdateShader()

        obj_name = bpy.context.active_object.name
        mtl_name = part.material
        file_name = os.path.basename(bpy.data.filepath) if bpy.data.filepath else "untitled"
        set_name = part.name


        
        usedtypes = getusedtypes()
        for s in usedtypes:
            print(s)
            
        hn_combine = 'NORMAL' in usedtypes and 'HEIGHT' in usedtypes and basescene.other_props.height_to_normal

        nrm_baked = False

        for inds, tex_type in enumerate(usedtypes):
            # Create a new scene
            if nrm_baked and basescene.other_props.height_to_normal:
                if tex_type=='HEIGHT':
                    continue

            new_scene = bpy.data.scenes.new("BakeScene")
            bpy.context.window.scene = new_scene

            mat = bpy.data.materials.new(name="HASBakeMtlTemp")
            bpy.context.scene.other_props.bakemtl = mat
            heights = part.height_intensity
            invertg = basescene.other_props.invert_green_n
            # Add a new object
            sftext = bpy.ops.object.text_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            sftext = bpy.context.object
            sftext.data.body = "Scene for offscreen operations. Just delete this scene if you stuck here"    

            bpy.ops.mesh.primitive_plane_add(size=2)
            plane = bpy.context.active_object
            plane.name = "BakePlane"
            # Assign the selected material to the plane
            plane.data.materials.append(mat)

            base_image = None
            alpha_image = None

            prop = None
            propn= None
            nsavename= "NORMAL"
            for ind, prope in enumerate(basescene.texture_types_props):
                if prope.texture_type==tex_type:
                    #print(f"baking {prope.texture_type}")
                    prop = prope
                if prope.texture_type=="NORMAL":
                    propn = prope
                    nsavename = propn.save_name

            

            outs = ['Result', 'Alpha']

            if not layer:
                if prop:
                    texture_name = f'{prop.save_name}'
                    if prop.use_alpha =="COMBINED" or prop.use_alpha =="SEPARATE":
                        outs = ['Result', 'Alpha']
                    if prop.use_alpha =="NOALPHA":
                        outs = ['Result']
                    usealpha = prop.use_alpha
                    
                else:
                    texture_name = f'{tex_type}'

                    if tex_type=='HEIGHT' or tex_type=='NORMAL':
                        usealpha = "NOALPHA"
                        outs = ['Result']
                    else:
                        usealpha = "COMBINED"
                        outs = ['Result', 'Alpha']
            else:
                texture_name = f'{tex_type}'
                usealpha = "COMBINED"
                


            tex_name = texture_name
            for currentoutput in outs:
                currentname = f"{tex_type}_Group_{part.material.name}"
                texture_name = generate_filename(tex_name, context, obj_name, part.material.name, file_name, set_name)
                if not layer_below:
                    if hn_combine and tex_type=='NORMAL':
                        CreateBakeNormalsMaterial(f'HEIGHT_Group_{part.material.name}', currentoutput, currentname, heights, invertg, part)
                        nrm_baked = True

                    elif tex_type=='HEIGHT' and basescene.other_props.height_to_normal:
                        CreateBakeNormalsMaterial(f'HEIGHT_Group_{part.material.name}', currentoutput, None, heights, invertg, part)
                        if basescene.other_props.height_to_normal:
                            if tex_type== "HEIGHT":
                                texture_name = generate_filename(nsavename, context, obj_name, mtl_name, file_name, set_name)
                        nrm_baked = True

                    elif tex_type=='NORMAL':
                        CreateBakeNormalsMaterial(None, currentoutput, 'NORMAL_Group_{mtl_name}', heights, invertg, part)

                    else:
                        CreateBakeMaterial(currentname,currentoutput, usealpha)
                    if tex_type=='HEIGHT':
                        if not basescene.other_props.height_to_normal:
                            basescene.other_props.layercombineactive = not usealpha =="NOALPHA" or usealpha =="SEPARATE"
                            print(basescene.other_props.layercombineactive)
                            create_scene_prop_node_group(basescene)


                    
                else:
                    basescene.other_props.layercombineactive = True
                    create_scene_prop_node_group(basescene)
                    CreateBakeMaterial(currentname, currentoutput, "COMBINED")

                # Create a new image to bake to
                bakeimagename = f"{texture_name}{currentoutput}"
                if layer_below:
                    bakeimagename = f"{layer_below.image.name}"
                    layer_below.image.name = f"{layer_below.image.name}_{currentoutput}_old"
                bake_image = bpy.data.images.new(bakeimagename, basescene.texture_sizeX, basescene.texture_sizeY, alpha=True)
                print(bake_image.name)
                if currentoutput =='Result':
                    base_image = bake_image
                elif currentoutput =='Alpha':
                    alpha_image = bake_image

                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # Set the bake settings
                bpy.context.scene.cycles.samples = 1
                bpy.context.scene.cycles.use_denoising = False
                bpy.context.scene.render.engine = 'CYCLES'


                
                # Select the plane object
                bpy.context.view_layer.objects.active = plane
                plane.select_set(True)

                image_texture_node = nodes.new(type='ShaderNodeTexImage')
                image_texture_node.image = bake_image
                # Set the active image texture node for baking
                mat.node_tree.nodes.active = image_texture_node
                
                
                # Bake the texture
                if nrm_baked:
                    bpy.ops.object.bake(type='NORMAL')
                else:
                    bpy.ops.object.bake(type='EMIT')
            bpy.context.window_manager.popup_menu(lambda self, context: oops(self, context, f"Done {inds+1}/{len(usedtypes)}"), title="Baking", icon='SHADING_RENDERED')    
            
            # Ensure the base image has an alpha channel
            if base_image.channels < 4:
                base_image.use_alpha = True
                base_image.alpha_mode = 'STRAIGHT'
                new_pixels = []
                for i in range(0, len(base_image.pixels), 3):
                    new_pixels.extend(base_image.pixels[i:i+3])
                    new_pixels.append(1.0)  # Default alpha value
                base_image.pixels = new_pixels
            if base_image and alpha_image and not usealpha =="SEPARATE":
                # Get the pixels of the base and alpha images
                base_pixels = list(base_image.pixels)
                alpha_pixels = list(alpha_image.pixels)

                # Combine the alpha channel
                for i in range(0, len(base_pixels), 4):
                    base_pixels[i + 3] = alpha_pixels[i]  # Assuming the alpha image is a grayscale image
                base_image.pixels = base_pixels

            if base_image:
                base_image.update()

                if not layer_below:

                    if base_image:
                        if save_path and os.path.exists(save_path):

                            file_path = os.path.join(save_path, texture_name + ".png")
                            base_image.filepath_raw = os.path.join(save_path, texture_name + ".png")
                            try:
                                base_image.save()
                                #print(f"Texture '{texture_name}' saved to '{file_path}'")
                            except Exception as e:
                                print(f"Error saving texture '{texture_name}': {e}")
                        else:
                            info_text = f"The specified path '{save_path}' is invalid or does not exist"
                            bpy.context.window_manager.popup_menu(lambda self, context: oops(self, context, info_text), title="Error", icon='ERROR')

                    else:
                        print(f"Texture '{texture_name}' not found")
            
            if alpha_image and usealpha =="SEPARATE":
                alpha_image.update()

                if not layer_below:

                    if alpha_image:
                        if save_path and os.path.exists(save_path):

                            file_path = os.path.join(save_path, texture_name + "_a.png")
                            alpha_image.filepath_raw = os.path.join(save_path, texture_name + "_a.png")
                            try:
                                alpha_image.save()
                            except Exception as e:
                                print(f"Error saving texture '{texture_name}': {e}")
                        else:
                            info_text = f"The specified path '{save_path}' is invalid or does not exist"
                            bpy.context.window_manager.popup_menu(lambda self, context: oops(self, context, info_text), title="Error", icon='ERROR')

                    else:
                        print(f"Texture '{texture_name}' not found")
            cleanup = True 
            if cleanup:        
                bpy.data.materials.remove(mat)
                if alpha_image and not usealpha =="SEPARATE":
                    bpy.data.images.remove(alpha_image)
                bpy.data.objects.remove(plane)
                bpy.data.scenes.remove(new_scene)
            

        if layer_below:
            layer_below.image = base_image 
            layer.image = None
        for ind in indsdeselected:
            layer_prop[ind].use_layer = True
        
        UpdateShader()
        return {'FINISHED'}

def CreateBakeMaterial(node_group_name, node_group_output, fixcolor):

    material = bpy.context.scene.other_props.bakemtl

    node_group = bpy.data.node_groups[node_group_name]
    
    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    tree_links = tree.links
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
        else:
            tree.nodes.remove(node)

    if 'output_node' not in locals():
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (200, 0)
    
    group_node = tree.nodes.new('ShaderNodeGroup')
    group_node.node_tree = node_group
    group_node.name = node_group_name
    group_node.location = (-300, 0)
    if node_group_output=='Result':
        mix = tree.nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'DIVIDE'
        mix.location = (-250,-30)
        mix.inputs['Fac'].default_value = 1
        mix.inputs['Fac'].default_value = 1

        math =tree.nodes.new('ShaderNodeMath')
        math.operation = 'MULTIPLY'
        math.use_clamp = True
        math.location = (-300, 0)
        if fixcolor =="COMBINED":
            tree_links.new(group_node.outputs['Result'], mix.inputs[1])
            tree_links.new(group_node.outputs['Alpha'], math.inputs[0])
            tree_links.new(group_node.outputs['Alpha'], math.inputs[1])
            tree_links.new(math.outputs[0], mix.inputs[2])
            tree_links.new(mix.outputs[0], output_node.inputs[0])
        if fixcolor =="NOALPHA" or fixcolor =="SEPARATE":
            #tree_links.new(group_node.outputs['Result'], mix.inputs[1])
            tree_links.new(group_node.outputs['Result'], output_node.inputs[0])
    else:
        math =tree.nodes.new('ShaderNodeMath')
        math.operation = 'MULTIPLY'
        math.use_clamp = True
        math.location = (-300, 0)
        tree_links.new(group_node.outputs['Alpha'], math.inputs[0])
        tree_links.new(group_node.outputs['Alpha'], math.inputs[1])
        tree_links.new(math.outputs[0], output_node.inputs[0])

def CreateBakeNormalsMaterial(Hnode_group_name, node_group_output, Nnode_group_name, heights, invertg, part):

    material = bpy.context.scene.other_props.bakemtl
    if Hnode_group_name:
        if bpy.data.node_groups[Hnode_group_name]:
            hnode_group = bpy.data.node_groups[Hnode_group_name]
    if Nnode_group_name:
        if bpy.data.node_groups[Nnode_group_name]:
            nnode_group = bpy.data.node_groups[Nnode_group_name]

    if material.use_nodes is False:
        material.use_nodes = True

    tree = material.node_tree
    tree_links = tree.links
    for node in tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            output_node = node
        else:
            tree.nodes.remove(node)
    alternative= True

    if 'output_node' not in locals():
        output_node = tree.nodes.new('ShaderNodeOutputMaterial')
        output_node.location = (200, 0)

    if Hnode_group_name and hnode_group:
        hgroup_node = tree.nodes.new('ShaderNodeGroup')
        hgroup_node.node_tree = hnode_group
        hgroup_node.name = Hnode_group_name
        hgroup_node.location = (-300, 0)
    if Nnode_group_name and nnode_group:
        ngroup_node = tree.nodes.new('ShaderNodeGroup')
        ngroup_node.node_tree = nnode_group
        ngroup_node.name = Nnode_group_name
        ngroup_node.location = (-300, 300)

    if node_group_output=='Result':
        if alternative:
            shader_node = tree.nodes.new('ShaderNodeBsdfDiffuse')
            shader_node.location = (50, 300)

            nrm_map_node = tree.nodes.new('ShaderNodeNormalMap')
            nrm_map_node.space = 'OBJECT'

            bump_node = tree.nodes.new('ShaderNodeBump')
            bump_node.inputs[0].default_value = part.height_intensity

            if Hnode_group_name and hnode_group:
                tree_links.new(hgroup_node.outputs['Result'], bump_node.inputs["Height"])
            if Nnode_group_name and nnode_group:
                tree_links.new(ngroup_node.outputs['Result'], nrm_map_node.inputs[1])

            math_multG = tree.nodes.new('ShaderNodeVectorMath')
            math_multG.operation = 'MULTIPLY'
            
            if invertg:
                math_multG.inputs[1].default_value = (1.0,-1.0,1.0)
            else:
                math_multG.inputs[1].default_value = (1.0,1.0,1.0)

            tree_links.new(nrm_map_node.outputs[0], bump_node.inputs['Normal'])
            tree_links.new(bump_node.outputs[0], math_multG.inputs[0])
            tree_links.new(math_multG.outputs[0], shader_node.inputs['Normal'])
            tree_links.new(shader_node.outputs[0], output_node.inputs[0])

        else:
                
            nrm_map_node = tree.nodes.new('ShaderNodeNormalMap')
            nrm_map_node.space = 'OBJECT'

            bump_node = tree.nodes.new('ShaderNodeBump')
            bump_node.inputs[0].default_value = part.height_intensity

            math_add = tree.nodes.new('ShaderNodeVectorMath')
            math_add.operation = 'ADD'
            math_add.inputs[1].default_value = (1.0,1.0,1.0)

            math_multG = tree.nodes.new('ShaderNodeVectorMath')
            math_multG.operation = 'MULTIPLY'
            if invertg:
                math_multG.inputs[1].default_value = (1.0,-1.0,1.0)
            else:
                math_multG.inputs[1].default_value = (1.0,1.0,1.0)

            math_mult = tree.nodes.new('ShaderNodeVectorMath')
            math_mult.operation = 'MULTIPLY'
            math_mult.inputs[1].default_value = (0.5,0.5,0.5)

            if Hnode_group_name and hnode_group:
                tree_links.new(hgroup_node.outputs['Result'], bump_node.inputs["Height"])
            if Nnode_group_name and nnode_group:
                tree_links.new(ngroup_node.outputs['Result'], nrm_map_node.inputs[1])

            tree_links.new(nrm_map_node.outputs[0], bump_node.inputs['Normal'])

            tree_links.new(bump_node.outputs[0], math_multG.inputs[0])
            tree_links.new(math_multG.outputs[0], math_add.inputs[0])
            tree_links.new(math_add.outputs[0], math_mult.inputs[0])
            tree_links.new(math_mult.outputs[0], output_node.inputs[0])

    else:
        mathc =tree.nodes.new('ShaderNodeMath')
        mathc.operation = 'MAXIMUM'
        mathc.inputs[0].default_value = 0
        mathc.inputs[1].default_value = 0
        mathc.use_clamp = True
        mathc.location = (-300, 0)

        mathm =tree.nodes.new('ShaderNodeMath')
        mathm.operation = 'MULTIPLY'
        mathm.use_clamp = True
        mathm.location = (-300, 0)

        if Hnode_group_name and hnode_group:
            tree_links.new(hgroup_node.outputs['Alpha'], mathc.inputs[0])
        if Nnode_group_name and nnode_group:
            tree_links.new(ngroup_node.outputs['Alpha'], mathc.inputs[1])

        tree_links.new(mathc.outputs[0], mathm.inputs[0])
        tree_links.new(mathc.outputs[0], mathm.inputs[1])
        tree_links.new(mathm.outputs[0], output_node.inputs[0])

def check_mtl_used():
    mtlprops = bpy.context.scene.material_props
    for ind, prop in enumerate(mtlprops):
        if prop:
            if prop.material == bpy.context.active_object.active_material:
                return True
    return False 
# Operator to save all layers/textures to a blend file
class SaveLayersOperators(bpy.types.Operator):
    bl_idname = "texturelayer.save_layers"
    bl_label = "Save Layers"
    bl_description = "Save all layers/textures to a blend file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        modified_images = [img for img in bpy.data.images if img.is_dirty]
        if modified_images:
            bpy.ops.image.save_all_modified()
        else:
            self.report({'INFO'}, "No images are modified.")
        return {'FINISHED'}

class SaveLayersCurrentOperators(bpy.types.Operator):
    bl_idname = "texturelayer.save_layers_current"
    bl_label = "Save Layers"
    bl_description = "Save all layers/textures to a blend file"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        layers = get_material_collection(None).layers
        modified_images= []
        for l in layers:
            if l.image.is_dirty:
                modified_images.append(l.image)
        if modified_images:
            bpy.ops.image.save_all_modified()
        else:
            self.report({'INFO'}, "No images are modified.")
        return {'FINISHED'}
class LoadLayersOperator(bpy.types.Operator):
    bl_idname = "texturelayer.load_layers"
    bl_label = "Load layers"
    bl_description = "Load layers from material"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        LoadLayersFromMaterial()
        return {'FINISHED'}

class DeleteLayersOperator(bpy.types.Operator):
    bl_idname = "texturelayer.delete_layers"
    bl_label = "Delete layers"
    bl_description = "Delete layers from material"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        part = get_material_collection(None)
        layer_prop = part.layers
        
        while len(layer_prop) > 0:
            layer_prop.remove(0)
        return {'FINISHED'}

def next_power_of_two(x):
    return 2**(x-1).bit_length()

class TextureSizeAddSubtract(Operator):
    bl_idname = "texturelayer.texture_size_add_subtract"
    bl_label = "Add or subtract from texture size"
    bl_options = {'REGISTER', 'UNDO'}

    add: bpy.props.BoolProperty(name="AddSubtract", default=True)

    def execute(self, context):
        size_x = context.scene.texture_sizeX
        size_y = context.scene.texture_sizeY

        if self.add:
            # Increase to next power of two
            context.scene.texture_sizeX = next_power_of_two(size_x + 1) if size_x else 2
            context.scene.texture_sizeY = next_power_of_two(size_y + 1) if size_y else 2
        else:
            # Decrease to next lower power of two, but ensure it doesn't go below 1
            new_size_x = next_power_of_two(max(size_x - 1, 1))
            new_size_y = next_power_of_two(max(size_y - 1, 1))
            
            # Ensure we don't round up to the current value
            if new_size_x >= size_x:
                new_size_x = next_power_of_two(max(size_x // 2, 1))
            if new_size_y >= size_y:
                new_size_y = next_power_of_two(max(size_y // 2, 1))
            
            context.scene.texture_sizeX = new_size_x
            context.scene.texture_sizeY = new_size_y
        return {'FINISHED'}

class TextureGrabSizeAddSubtract(Operator):
    bl_idname = "texturelayer.texture_grab_size_add_subtract"
    bl_label = "Add or subtract from texture grab size"
    bl_options = {'REGISTER', 'UNDO'}

    add: bpy.props.BoolProperty(name="AddSubtract", default=True)

    def execute(self, context):
        size_x = context.scene.other_props.screen_grab_size_x
        size_y = context.scene.other_props.screen_grab_size_y
        if self.add:
            # Increase to next power of two
            context.scene.other_props.screen_grab_size_x = next_power_of_two(size_x + 1) if size_x else 2
            context.scene.other_props.screen_grab_size_y = next_power_of_two(size_y + 1) if size_y else 2
        else:
            # Decrease to next lower power of two, but ensure it doesn't go below 1
            new_size_x = next_power_of_two(max(size_x - 1, 1))
            new_size_y = next_power_of_two(max(size_y - 1, 1))
            
            # Ensure we don't round up to the current value
            if new_size_x >= size_x:
                new_size_x = next_power_of_two(max(size_x // 2, 1))
            if new_size_y >= size_y:
                new_size_y = next_power_of_two(max(size_y // 2, 1))
            
            context.scene.other_props.screen_grab_size_x = new_size_x
            context.scene.other_props.screen_grab_size_y = new_size_y
        return {'FINISHED'}
def find_node_by_name(self, node_tree, name):
        for node in node_tree.nodes:
            if node.name == name:
                return node
            elif node.type == 'GROUP' and node.node_tree:
                found_node = self.find_node_by_name(node.node_tree, name)
                if found_node:
                    return found_node
        return None

class OT_AddMyPreset(AddPresetBase, Operator):
    bl_idname = 'my.add_preset'
    bl_label = 'Add A preset'
    preset_menu = 'MT_MyPresets'

    # Common variable used for all preset values
    preset_defines = [
        'scene = bpy.context.scene'
    ]

    # Properties to store in the preset
    preset_values = [
        'scene.other_props.height_to_normal',
        'scene.other_props.invert_green_n',
    ]

    # Directory to store the presets
    preset_subdir = 'haspresets/savepres'

    def execute(self, context):
        self.preset_values = [
            'scene.other_props.height_to_normal',
            'scene.other_props.invert_green_n',
        ]

        for idx, item in enumerate(context.scene.texture_types_props):
            self.preset_values.extend([
                f'scene.texture_types_props[{idx}].texture_type',
                f'scene.texture_types_props[{idx}].use_type',
                f'scene.texture_types_props[{idx}].use_alpha',
                f'scene.texture_types_props[{idx}].save_name',
            ])
        return super().execute(context)

class MT_MyPresets(Menu):
    bl_idname = 'MT_MyPresets'
    bl_label = 'My Presets'
    preset_subdir = 'haspresets/savepres'
    preset_operator = 'script.execute_preset_has'
    draw = Menu.draw_preset

class ExecutePreset(Operator):
    """Execute a preset"""
    bl_idname = "script.execute_preset_has"
    bl_label = "Execute a Python Preset"

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

        preset_class = getattr(bpy.types, 'MT_MyPresets')
        preset_class.bl_label = bpy.path.display_name(basename(filepath))

        ext = splitext(filepath)[1].lower()

        if ext not in {".py", ".xml"}:
            self.report({'ERROR'}, "unknown filetype: %r" % ext)
            return {'CANCELLED'}

        if hasattr(preset_class, "reset_cb"):
            preset_class.reset_cb(context)
        # Extract and execute texture_types_props lines
        with open(filepath, 'r') as file:
            lines = file.readlines()

        texture_props_lines = [line for line in lines if 'texture_types_props' in line]
        while len(context.scene.texture_types_props) > 0:
            context.scene.texture_types_props.remove(0)
        # Get the last line
        last_line = lines[-1]

        # Extract the number within square brackets
        match = re.search(r'\[(\d+)\]', last_line)

        if match:
            number = int(match.group(1))

        for n in range(number+1):
            context.scene.texture_types_props.add()

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

# Operator to add a new item to the collection
class AddTextureTypeProp(Operator):
    bl_idname = "scene.add_texture_type_prop"
    bl_label = "Add Texture Type"

    def execute(self, context):
        context.scene.texture_types_props.add()
        return {'FINISHED'}
# Operator to add a new item to the collection
class SetupMaterial(Operator):
    bl_idname = "scene.setup_material"
    bl_label = "Setup Material"

    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object:
            if active_object.active_material:
                mat = active_object.active_material
                mat.use_nodes = True
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
                mat = bpy.data.materials.new(name="HASMaterial")

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
        return {'FINISHED'}

class HASRemoveMaterial(Operator):
    bl_idname = "scene.remove_material"
    bl_label = "Remove Material"

    index: bpy.props.IntProperty()
    def execute(self, context):
        context.scene.material_props.remove(self.index)
        return {'FINISHED'}
# Operator to remove an item from the collection
class RemoveTextureTypeProp(Operator):
    bl_idname = "scene.remove_texture_type_prop"
    bl_label = "Remove Texture Type"

    index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.texture_types_props.remove(self.index)

        return {'FINISHED'}
class HAS_PT_LayersPanel(bpy.types.Panel):
    bl_label = "Paint Layers"
    bl_idname = "HAS_PT_LayersPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Paint Layers'

    def draw(self, context):
                
        layout = self.layout

        box = layout.box()
        
        if bpy.context.active_object:

            part = get_material_collection(None)
            box.operator("wm.check_for_updates", text="Check for updates", icon = "FILE_TICK")
            

            box.prop(context.scene.other_props, "expand_area_Actions", text="File", icon="TRIA_DOWN" if context.scene.other_props.expand_area_Actions else "TRIA_RIGHT", emboss = False)

            if context.scene.other_props.expand_area_Actions:
                boxs = box.box()
                row = boxs.row(align=False)
                row.operator("texturelayer.save_layers", text="Save All Textures", icon = "FILE_TICK")
                row.operator("texturelayer.delete_layers", text="Delete all layers", icon = "TRASH")
                row = boxs.row(align=False)
                row.prop(context.scene.other_props, "toggle_save", text = f"Auto Save Textures", icon = "CHECKBOX_HLT" if context.scene.other_props.toggle_save else "CHECKBOX_DEHLT")
                row = box.row(align=False)
                box = box.box()
                rowl = box.row(align=True)
                rowl.prop(context.scene.other_props, "expand_area_MaterialCollection", text="Set collection", icon="TRIA_DOWN" if context.scene.other_props.expand_area_MaterialCollection else "TRIA_RIGHT", emboss = False)
                
                if context.scene.other_props.expand_area_MaterialCollection:
                    rowl = box.row(align=True)
                    rowl.label(text = "Set names")
                    rowl.label(text = "Materials")
                    for i, p in enumerate(context.scene.material_props):
                        rowl = box.row(align=True)
                        rowl.prop(p, "name", text="")
                        rowl.prop(p, "material", text="")
                        rowl.operator("scene.remove_material", text="", icon='REMOVE').index = i

                box = row.box()
                row = box.row(align=True)

                row.operator("texturelayer.combine_textures", text="Export Textures", icon = "EXPORT")
                #row.operator("texturelayer.combine_textures", text="Settings")
                #row.label(text="Save path")
                row.prop(context.scene.other_props, "save_path", text="")

                row = box.row(align=False)
                row.prop(context.scene.other_props, "expand_area_Saving", text="Settings", icon="TRIA_DOWN" if context.scene.other_props.expand_area_Saving else "TRIA_RIGHT", emboss = False)
                if context.scene.other_props.expand_area_Saving:
                    row = box.row(align=True)
                    row.menu(MT_MyPresets.bl_idname, text=MT_MyPresets.bl_label, icon='COLLAPSEMENU')
                    row.operator(OT_AddMyPreset.bl_idname, text="", icon='ADD')
                    row.operator(OT_AddMyPreset.bl_idname, text="", icon='REMOVE').remove_active = True

                    boxd = box.box()
                    boxd.prop(context.scene.other_props, "height_to_normal")
                    boxd.prop(context.scene.other_props, "invert_green_n")

                    boxd = box.box()
                    boxd.label(text="Allowed properties (obj), (mtl), (file), (set)")
                    row = boxd.row(align=True)
                    row.label(text="Texture type")
                    row.label(text="Save name")
                    for idx, item in enumerate(context.scene.texture_types_props):
                        boxq = boxd.box()
                        row = boxq.row(align=True)
                        row.prop(item, "texture_type", text="")
                        row.prop(item, "save_name", text="")
                        row.operator("scene.remove_texture_type_prop", text="", icon='X').index = idx
                        row = boxq.row(align=True)
                        row.prop(item, "use_alpha", text="Alpha")



                    box.operator("scene.add_texture_type_prop", text="Add Texture Type") 

            #row = layout.row(align=True)
            if not bpy.context.active_object or not bpy.context.active_object.type == 'MESH':
                return
            if not bpy.context.active_object.data.materials or not check_mtl_used():
                box = layout.box()
                box.operator("scene.setup_material", text="Setup material", icon="ADD", emboss = False)
                return

            box = layout.box()
            box.prop(context.scene.other_props, "expand_area_MtlSettings", text="Material settings", icon="TRIA_DOWN" if context.scene.other_props.expand_area_MtlSettings else "TRIA_RIGHT", emboss = False)
            if context.scene.other_props.expand_area_MtlSettings:

                rowd = box.row(align=False)
                box.prop(part, "name", text="Set Name")
                box.prop(part, "shader_type", text="Shader Type")
                box.prop(context.scene.other_props, "texture_filtering", text="Texture filtering")
                box.prop(part, "uvs", text="UV")
                box.prop(part, "height_intensity", text="Height Intensity")

                row = box.row(align=False)
                row.label(text="Texture size")
                row.operator("texturelayer.texture_size_add_subtract", text="", icon='ADD').add = True
                row.operator("texturelayer.texture_size_add_subtract", text="", icon='REMOVE').add = False
                row.prop(context.scene, "texture_sizeX", text="X")
                row.prop(context.scene, "texture_sizeY", text="Y")
            box = layout.box()
            box.prop(context.scene.other_props, "expand_area_ProjectTexture", text="Tools", icon="TRIA_DOWN" if context.scene.other_props.expand_area_ProjectTexture else "TRIA_RIGHT", emboss = False)
            if context.scene.other_props.expand_area_ProjectTexture:
                rowq = box.row(align=False)
                if bpy.context.preferences.filepaths.image_editor:

                    global operator_running
                    rowq.alert = operator_running
                    rowq.operator('screen.crop_tool', text="Select region for quick edit", icon="OBJECT_DATAMODE")
                    
                    rowq.prop(context.scene.other_props, "screen_capture_scale", text="Capture scale")

                    for index, vd in enumerate(context.scene.view_data):

                        rowq = box.row()

                        op = rowq.operator('scene.snap_to_view', text="", icon = "SCREEN_BACK")
                        op.index = index
                        op = rowq.operator(ProjectApply.bl_idname, text="", icon = "IMPORT")
                        op.index = index
                        op = rowq.operator(ProjectOpen.bl_idname, text=vd.image_name, icon = "IMAGE")
                        op.index = index
                        op = rowq.operator(ProjectRemove.bl_idname, text="", icon = "PANEL_CLOSE")
                        op.index = index
                else:
                    # If external editor path is not set, show a path specifier
                    rowq.label(text="External Image Editor Path:")
                    rowq.prop(bpy.context.preferences.filepaths, "image_editor", text="")
            rowl = layout.row(align=False)
            box = rowl.box()
            row = box.row(align=False)
            row.operator("texturelayer.create_texture", text="", icon='ADD')
            box = rowl.box()
            row = box.row(align=False)
            row.operator("image.custom_new", text="", icon='IMAGE')

            box = rowl.box()
            row = box.row(align=False)
            row.prop(context.scene.other_props, "expand_area_CreateLayer", text="", icon="LOOP_BACK" if context.scene.other_props.expand_area_CreateLayer else "OUTLINER_OB_IMAGE")
            if context.scene.other_props.expand_area_CreateLayer:

                row.operator("texturelayer.create_layer_from_texture", text="", icon='IMPORT').copy = False
                row.template_ID(context.scene.other_props, "image", open="image.open")
            folder = None
            
            part = get_material_collection(None)
            if not part:
                return

            for layer in reversed(part.layers):
                
                if layer and layer.image:
                    if layer.texture_type in TEXTURE_PROPERTIES:
                        layer_texturetype = TEXTURE_PROPERTIES[layer.texture_type]
                    else:
                        layer_texturetype = "DIFFUSE"
                    islayer_adjust = not layer_texturetype[2]
                    if folder:
                        box = folder
                    else:
                        box = layout.box()

                    split = box.split(factor=0.2)

                    left_column = split.column()

                    if not islayer_adjust:

                        texture = bpy.data.images.get(layer.image.name)
                        if texture and texture.preview:
                            
                            icon_id = texture.preview.icon_id
                            left_column.template_icon(icon_id, scale=3.3)

                        else:
                            left_column.operator("texturelayer.select_texture", text="",icon='OUTLINER_OB_IMAGE', emboss = False)
                            left_column.enabled = False
                            left_column.scale_y = 3.0
                    else:
                        left_column.operator("texturelayer.select_texture", text="",icon='CLIPUV_DEHLT', emboss = False)
                        left_column.enabled = False
                        left_column.scale_y = 3.0


                    split = split.split(factor=0.08)
                    middle_column = split.column()
                    

                    row = middle_column.row(align=True)


                    if context.scene.selected_texture == layer.image.name:
                        row.alert = True
                    select_op = row.operator("texturelayer.select_texture", text="", icon='SNAP_FACE' if context.scene.selected_texture == layer.image.name else 'SHADING_BBOX')
                    select_op.texture_name = layer.image.name
                    row.scale_y = 3.2

                    right_column = split.column()

                    row = right_column.row(align=False)

                    uncheck_button = row.operator("texturelayer.uncheck_layer", text="", icon='HIDE_OFF' if layer.use_layer else 'HIDE_ON')
                    uncheck_button.texture_name = layer.image.name

                    row.prop(layer, "currentlayer_actions", text="", icon='COLLAPSEMENU',icon_only=True)
                    
                    row.prop(layer, "image", text="")
                    row = right_column.row(align=True)
                    
                    if layer.texture_type=='ADJUSTHSV':

                        row.prop(layer, "hue", text="Hue")
                        row.prop(layer, "saturation", text="Saturation")
                        row.prop(layer, "value", text="Value")
                    elif layer.texture_type=='COLORRAMP':
                        node_group = bpy.data.node_groups.get(layer.node_group_name)
                        if node_group:
                            node = node_group.nodes.get(layer.node_name)
                            if node:
                                row.box().template_color_ramp(node, "color_ramp", expand=False)
                    elif layer.texture_type=='CUSTOM':
                        rowbox = row.box()
                        rowc = rowbox.row(align=True)
                        rowc.prop(layer, "custom_node")
                        rowc.prop(layer, "cn_input")
                        rowc = rowbox.row(align=True)
                        rowc.prop(layer, "cn_type")
                        rowc.prop(layer, "cn_output")
                        
                        node_group = bpy.data.node_groups.get(layer.node_group_name)
                        if node_group:
                            node = node_group.nodes.get(layer.node_name)
                            if node:
                                # Define mapping of socket types to UI elements
                                socket_ui_mapping = {
                                    'VALUE': 'value',
                                    'RGBA': 'color',
                                    'VECTOR': 'vector',
                                    'BOOLEAN': 'checkbox',
                                    'STRING': 'text'
                                }
                                
                                # Iterate over input sockets and create UI elements
                                for ind, input_socket in enumerate(node.inputs):
                                    socket_type = input_socket.type
                                    socket_ui_type = socket_ui_mapping.get(socket_type)
                                    if socket_ui_type:
                                        # Create a unique identifier for the socket
                                        socket_id = f"{input_socket.name}_{ind}"
                                        rowc = rowbox.row(align=False)
                                        if layer.cn_input==ind:
                                            rowc.label(text="", icon='IPO_EASE_IN_OUT')
                                        
                                        if socket_ui_type == 'checkbox':
                                            rowc.prop(input_socket, "default_value", text=input_socket.name)
                                        else:
                                            rowc.prop(input_socket, "default_value", text=input_socket.name)
                    elif layer.texture_type=='FOLDER':
                        row.prop(layer, "cn_input", text="Layers below")
                        row = right_column.row(align=False)
                        folder = row.box()


                    else:

                        row.prop(layer, "blend_mode", text="")

                        row.prop(layer, "opacity", text="Opacity")
                    
                    move_up = row.operator("texturelayer.move_layer", text="", icon='TRIA_UP')
                    move_up.layer_name = layer.image.name
                    move_up.direction = 'UP'

                    row = right_column.row(align=True)

                    row.prop(layer, "texture_type", text="")

                    move_down = row.operator("texturelayer.move_layer", text="", icon='TRIA_DOWN')
                    move_down.layer_name = layer.image.name
                    move_down.direction = 'DOWN'

class MoveLayerOperator(bpy.types.Operator):
    bl_idname = "texturelayer.move_layer"
    bl_label = "Move Layer"
    bl_options = {'REGISTER', 'UNDO'}

    layer_name: bpy.props.StringProperty()
    direction: bpy.props.EnumProperty(items=[('UP', 'Up', ''), ('DOWN', 'Down', '')])

    def execute(self, context):
        part = get_material_collection(None)
        layers = part.layers
        index = [layer.image.name for layer in layers].index(self.layer_name)
        new_index = index + 1 if self.direction == 'UP' else index - 1

        if 0 <= new_index < len(layers):
            layers.move(index, new_index)
            UpdateShader()
        return {'FINISHED'}

class SelectTextureOperator(bpy.types.Operator):
    bl_idname = "texturelayer.select_texture"
    bl_label = "Select Texture"
    bl_options = {'REGISTER', 'UNDO'}

    texture_name: bpy.props.StringProperty()

    def execute(self, context):
        if not self.texture_name:
            self.texture_name = get_material_collection(context.scene).layers[len(get_material_collection(context.scene).layers)-1].image.name
        context.scene.selected_texture = self.texture_name
        texture = bpy.data.images.get(self.texture_name)
        #print(f"Panel image assigned {bpy.data.images.get(self.texture_name).name}")
        if texture:
            context.scene.tool_settings.image_paint.canvas = texture
            if not texture.preview_ensure():
                texture.asset_generate_preview()
            if bpy.context.scene.tool_settings.image_paint.mode == 'MATERIAL':
                bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'                       

            self.report({'INFO'}, f"Texture '{self.texture_name}' set as current texture.")
        else:
            self.report({'WARNING'}, f"Texture '{self.texture_name}' not found or has no image.")
        return {'FINISHED'}

@bpy.app.handlers.persistent
def save_modified_images(dummy):
    if bpy.context.scene.other_props.toggle_save:
        for image in bpy.data.images:
            if image.is_dirty:
                bpy.ops.image.save_all_modified()
                return

def create_normal_blend_group():

    if f"BlendNormals" in bpy.data.node_groups:
        node_group = bpy.data.node_groups[f"BlendNormals"]

        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name="BlendNormals")

    input_socket_names = ['Fac', 'Normal A', 'Normal B']
    for name in input_socket_names:
        if is_4_0_or_newer:
            if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == 'INPUT']:
                socket_type = 'NodeSocketFloat' if name == 'Fac' else 'NodeSocketColor'
                node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=socket_type)
        else:
            if name not in node_group.inputs:
                if name =='Fac':
                    node_group.inputs.new('NodeSocketFloat', name)
                else:
                    node_group.inputs.new('NodeSocketColor', name)

    output_socket_names = ['Result']
    for name in output_socket_names:
        if is_4_0_or_newer:
            if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == 'OUTPUT']:
                node_group.interface.new_socket(name=name, in_out='OUTPUT', socket_type='NodeSocketColor')
        else:
            if name not in node_group.outputs:
                node_group.outputs.new('NodeSocketColor', name)

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

    node_group.links.new(input_node.outputs['Normal A'], math_nodeA.inputs[0])
    node_group.links.new(input_node.outputs['Normal B'], math_nodeM.inputs[0])
    node_group.links.new(math_nodeM.outputs[0], math_nodeA.inputs[1])

    node_group.links.new(input_node.outputs['Fac'], math_nodeM.inputs[1])
    node_group.links.new(math_nodeA.outputs[0], math_nodeN.inputs[0])
    node_group.links.new(math_nodeN.outputs[0], output_node.inputs[0])


    return node_group

def create_scene_prop_node_group(scene):

    if f"HASSceneProperties" in bpy.data.node_groups:
        node_group = bpy.data.node_groups[f"HASSceneProperties"]

        node_group.nodes.clear()
    else:
        node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name="HASSceneProperties")

    output_socket_names =  ['BakingActive','LayerCombineActiveH']
    for name in output_socket_names:
        if is_4_0_or_newer:
            if name not in [sock.name for sock in node_group.interface.items_tree if sock.in_out == 'OUTPUT']:
                node_group.interface.new_socket(name=name, in_out='OUTPUT', socket_type='NodeSocketFloat')
        else:
            if name not in node_group.outputs:
                node_group.outputs.new('NodeSocketFloat', name)
    
    layercombine = scene.other_props.layercombineactive

    layercombinev = 0.0
    if layercombine:
        layercombinev =0.0
    else:
        layercombinev =0.5

    output_node = node_group.nodes.new(type='NodeGroupOutput')
    output_node.location = (500, 0)

    LayerCombineActive = node_group.nodes.new('ShaderNodeMath')
    LayerCombineActive.operation = 'ADD'
    LayerCombineActive.location = (0,0)
    LayerCombineActive.inputs[0].default_value =0.0
    LayerCombineActive.inputs[1].default_value = layercombinev
    
    node_group.links.new(LayerCombineActive.outputs[0], output_node.inputs['LayerCombineActiveH'])
    return node_group

def UpdateShader():

    create_normal_blend_group()
    bpy.context.scene.other_props.layercombineactive = False
    part = get_material_collection(None)
    hasprop_node = create_scene_prop_node_group(bpy.context.scene)
    customnodesetup = part.shader_type == 'Custom'
    nnode = None
    hnode = None
    if not customnodesetup:
        
        material = bpy.context.active_object.active_material
        if material is None:
            return

        mtl_n = material.name
        if material.use_nodes is False:
            material.use_nodes = True

        tree = material.node_tree

        for node in tree.nodes:
            if node.type == 'OUTPUT_MATERIAL':
                output_node = node
            else:
                tree.nodes.remove(node)

        if 'output_node' not in locals():
            output_node = tree.nodes.new('ShaderNodeOutputMaterial')
            output_node.location = (600, 0)

        shader_node = None
        if part.shader_type == 'PRINCIPLED':
            shader_node = tree.nodes.new('ShaderNodeBsdfPrincipled')
            shader_node.location = (50, 300)
            bump_node = tree.nodes.new('ShaderNodeBump')  
            bump_node.location = (-125, -200)
            bump_node.inputs[0].default_value = part.height_intensity
            tree_links = tree.links
            if is_4_0_or_newer:
                connect_to = 5
            else:
                connect_to = 22
            tree_links.new(bump_node.outputs[0], shader_node.inputs[connect_to])  

    usedtypes = getusedtypes()
        
    for indexgr, tex_type in enumerate(TEXTURE_TYPE):

        if tex_type[0] in usedtypes:
            is_nrm = tex_type[0]== 'NORMAL'
            is_h = tex_type[0]== 'HEIGHT'
            
            is_adjust = tex_type[0]== 'ADJUSTHSV'

            group_name = f"{tex_type[0]}_Group_{mtl_n}"
            
            if group_name in bpy.data.node_groups:
                node_group = bpy.data.node_groups[group_name]
                for nodei in  node_group.nodes:
                    if not nodei.type =="VALTORGB" and not nodei.type =="GROUP":
                        node_group.nodes.remove(nodei)
                    else:
                        used= False
                        for index, layer in enumerate(part.layers):
                            
                            if layer.node_name == nodei.name:
                                #print(f"Node '{nodei.name}' already exist")
                                used = True
                        if not used:
                                #print(f"Node '{nodei.name}' removed")
                                node_group.nodes.remove(nodei)    

            else:
                node_group = bpy.data.node_groups.new(type="ShaderNodeTree", name=group_name)

            hasprop_nodegroup = node_group.nodes.new("ShaderNodeGroup")
            hasprop_nodegroup.node_tree = hasprop_node
            hasprop_nodegroup.location = (-800, 0)

            group_output = node_group.nodes.new("NodeGroupOutput")
            group_output.location = (500, 0)
            if is_4_0_or_newer:
                if 'Result' not in node_group.interface.items_tree:
                    node_group.interface.new_socket(name='Result', in_out='OUTPUT', socket_type='NodeSocketColor')
                if 'Alpha' not in node_group.interface.items_tree:
                    node_group.interface.new_socket(name='Alpha', in_out='OUTPUT', socket_type='NodeSocketFloat')
                if 'Normal' not in node_group.interface.items_tree:
                    if is_nrm:
                        node_group.interface.new_socket(name='Normal', in_out='OUTPUT', socket_type='NodeSocketColor')
            else:
                while node_group.outputs:
                    node_group.outputs.remove(node_group.outputs[0])
                node_group.outputs.new('NodeSocketColor', 'Result')
                node_group.outputs.new('NodeSocketFloat', 'Alpha')
                if is_nrm:
                    node_group.outputs.new('NodeSocketVector', 'Normal')
            attribute_node = None
            if part.uvs:
                attribute_node = node_group.nodes.new('ShaderNodeAttribute')
                attribute_node.attribute_name = part.uvs
                attribute_node.location = (-1000, -300)

            count = -1
            prev_mix_node = None
            prev_mathA_node = None
            links = node_group.links
            for link in links:
                links.remove(link)
            layer_prop = part.layers
            for index, layer in enumerate(layer_prop):
                adjust_layers = []
                addadjust = False
                for ind in range(len(layer_prop)):
                    if ind>index:
                        if layer_prop[ind].texture_type == 'ADJUSTHSV' or layer_prop[ind].texture_type == 'COLORRAMP' or layer_prop[ind].texture_type == 'MASK' or layer_prop[ind].texture_type == 'CUSTOM':
                            if layer_prop[ind].use_layer:
                                adjust_layers.append(layer_prop[ind])
                                addadjust = True
                        else:
                            break

                if layer.use_layer and tex_type[0]==layer.texture_type and layer.image:

                    count = count+1

                    image_node = node_group.nodes.new('ShaderNodeTexImage')
                    image_node.image = layer.image

                    image_node.location = (-600, -count * 300)
                    if is_h:
                        if bpy.context.scene.other_props.texture_filtering=='Linear':
                            image_node.interpolation= 'Cubic'
                        else:
                            image_node.interpolation= bpy.context.scene.other_props.texture_filtering
                    else:
                        image_node.interpolation= bpy.context.scene.other_props.texture_filtering

                    math_node = node_group.nodes.new('ShaderNodeMath')
                    math_node.operation = 'MULTIPLY'
                    math_node.location = (-200, -count * 300)

                    mathA_node = node_group.nodes.new('ShaderNodeMath')
                    mathA_node.operation = 'MAXIMUM'
                    mathA_node.location = (-250, (-count * 300)-30)

                    colorfixA_node = node_group.nodes.new('ShaderNodeMath')
                    colorfixA_node.operation = 'POWER'
                    colorfixA_node.inputs[1].default_value = 2.0
                    colorfixA_node.location = (-250, (-count * 300)-70)

                    math_node.inputs[1].default_value = layer.opacity
                    if addadjust:
                        adjust_nodes=[]
                        for indx, s_layer in enumerate(adjust_layers):
                            if s_layer.texture_type =='ADJUSTHSV':
                                hsv_node = node_group.nodes.new('ShaderNodeHueSaturation')
                                hsv_node.location = (-300, -count * 300 + (indx*20))
                                adjust_nodes.append(hsv_node)
                            if s_layer.texture_type =='COLORRAMP':
                                rgb_ramp_node = None
                                for node in node_group.nodes:
                                    if node.name == s_layer.node_name and node.type == "ShaderNodeValToRGB" :
                                        rgb_ramp_node = node
                                if not rgb_ramp_node:
                                    rgb_ramp_node = node_group.nodes.new('ShaderNodeValToRGB')
                                rgb_ramp_node.location = (-300, -count * 300 + (indx*20)-50)
                                adjust_nodes.append(rgb_ramp_node)
                                s_layer.node_name = rgb_ramp_node.name
                                s_layer.node_group_name = group_name
                            if s_layer.texture_type =='MASK':
                                mix_node = node_group.nodes.new('ShaderNodeMixRGB')
                                mix_node.location = (-300, -count * 300 + (indx*20)-50)
                                mix_node.inputs[2].default_value = (0.0, 0.0, 0.0, 0.0)
                                adjust_nodes.append(mix_node)
                            if s_layer.texture_type =='CUSTOM':
                                custom_node = None
                                for node in node_group.nodes:
                                    if node.type == 'GROUP'and node.node_tree == bpy.data.node_groups.get(s_layer.custom_node):
                                        
                                        if node.name == s_layer.node_name:
                                            custom_node = node

                                        
                                if not custom_node:
                                    custom_node = node_group.nodes.new(type='ShaderNodeGroup')
                                    custom_node.node_tree = bpy.data.node_groups.get(s_layer.custom_node)
                                custom_node.location = (-300, -count * 300 + (indx*20)-50)
                                adjust_nodes.append(custom_node)
                                s_layer.node_name = custom_node.name
                                s_layer.node_group_name = group_name


                    if is_nrm:
                        group_node = node_group.nodes.new(type='ShaderNodeGroup')
                        group_node.node_tree = bpy.data.node_groups.get("BlendNormals")  
                        group_node.location = (0, -count * 300)
                    else:
                        mix_node = node_group.nodes.new('ShaderNodeMixRGB')
                        mix_node.location = (0, -count * 300)
                        mix_node.blend_type = layer.blend_mode
                    if attribute_node:
                        link = links.new(attribute_node.outputs[1], image_node.inputs[0])
                    links = node_group.links
                    if is_nrm:
                        link = links.new(image_node.outputs['Alpha'], math_node.inputs[0])
                        link = links.new(math_node.outputs[0], group_node.inputs['Fac'])
                        link = links.new(image_node.outputs['Alpha'], mathA_node.inputs[1])
                        link = links.new(image_node.outputs[0], group_node.inputs['Normal B'])
                    else:
                        link = links.new(image_node.outputs['Alpha'], colorfixA_node.inputs[0])
                        link = links.new(colorfixA_node.outputs[0], math_node.inputs[0])
                        link = links.new(image_node.outputs['Alpha'], mathA_node.inputs[1])
                        link = links.new(math_node.outputs[0], mix_node.inputs['Fac'])

                        if addadjust:
                            last_adjust_output = image_node.outputs[0]
                            last_adjust_output_uv = image_node.outputs[0]
                            if attribute_node:
                                last_adjust_output_uv = attribute_node.outputs[0]
                            firstuv = True
                            iscoloradjust = False
                            for indx, s_layer in enumerate(adjust_layers):
                                if s_layer.texture_type =='ADJUSTHSV':

                                    link = links.new(last_adjust_output, adjust_nodes[indx].inputs[4])
                                    last_adjust_output = adjust_nodes[indx].outputs[0]
                                    link = links.new(adjust_nodes[indx].outputs[0], mix_node.inputs[2])
                                    adjust_nodes[indx].inputs['Hue'].default_value = s_layer.hue
                                    adjust_nodes[indx].inputs['Saturation'].default_value = s_layer.saturation
                                    adjust_nodes[indx].inputs['Value'].default_value = s_layer.value
                                    mask_node = node_group.nodes.new('ShaderNodeTexImage')
                                    mask_node.location = (-300, -count * 300 + (indx*20)-50)
                                    mask_node.image = s_layer.image
                                    mask_node_invert = node_group.nodes.new('ShaderNodeInvert')
                                    mask_node_invert.location = (-300, -count * 300 + (indx*20)-50)
                                    link = links.new(mask_node.outputs[0], mask_node_invert.inputs[1])
                                    link = links.new(mask_node_invert.outputs[0], adjust_nodes[indx].inputs[3])
                                    iscoloradjust=True

                                if s_layer.texture_type =='COLORRAMP':
                                    link = links.new(last_adjust_output, adjust_nodes[indx].inputs[0])
                                    last_adjust_output = adjust_nodes[indx].outputs[0]
                                    link = links.new(adjust_nodes[indx].outputs[0], mix_node.inputs[2])
                                    iscoloradjust=True
                                if s_layer.texture_type =='CUSTOM':
                                    if s_layer.cn_type =='COLOR':
                                        link = links.new(last_adjust_output, adjust_nodes[indx].inputs[s_layer.cn_input])
                                        last_adjust_output = adjust_nodes[indx].outputs[s_layer.cn_output]
                                        link = links.new(adjust_nodes[indx].outputs[s_layer.cn_output], mix_node.inputs[2])
                                        iscoloradjust=True
                                    elif s_layer.cn_type =='UV':
                                        if not firstuv:
                                            link = links.new(last_adjust_output_uv, adjust_nodes[indx].inputs[s_layer.cn_input])
                                        firstuv = False
                                        last_adjust_output_uv = adjust_nodes[indx].outputs[s_layer.cn_output]
                                        link = links.new(adjust_nodes[indx].outputs[s_layer.cn_output], image_node.inputs[0])
                                        adjust_nodes[indx].location = (-1000, -count * 300 + (indx*20)-50)

                            if not iscoloradjust:
                                link = links.new(image_node.outputs[0], mix_node.inputs[2])

                            last_adjust_output = image_node.outputs[1]
                            for indx, s_layer in enumerate(adjust_layers):
                                if s_layer.texture_type =='MASK':    
                                    
                                    mask_node = node_group.nodes.new('ShaderNodeTexImage')
                                    mask_node.location = (-300, -count * 300 + (indx*20)-50)
                                    mask_node.image = s_layer.image
                                    
                                    link = links.new(last_adjust_output, adjust_nodes[indx].inputs[1])
                                    link = links.new(mask_node.outputs[0], adjust_nodes[indx].inputs['Fac'])
                                    last_adjust_output = adjust_nodes[indx].outputs[0]
                                    link = links.new(adjust_nodes[indx].outputs[0], math_node.inputs[0])
                        else:

                            link = links.new(image_node.outputs[0], mix_node.inputs[2])

                    if prev_mix_node:
                        if is_nrm:
                            link = links.new(prev_mix_node.outputs[0], group_node.inputs['Normal A'])
                        else:
                            link = links.new(prev_mix_node.outputs[0], mix_node.inputs[1])
                    else:
                        # If it's the first iteration, set Fac to 0
                        if is_nrm:
                            group_node.inputs['Normal A'].default_value = (0.50196, 0.50196, 1.0, 1.0)
                        elif is_h:
                            hasprop_nodegroup

                            mix_node.inputs['Fac'].default_value = 1
                            links.new(hasprop_nodegroup.outputs['LayerCombineActiveH'], mix_node.inputs[1])

                            #mix_node.inputs[1].default_value = (0.5, 0.5, 0.5, 1.0)
                        else:
                            mix_node.inputs['Fac'].default_value = 0
                            mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 0.0)

                    if prev_mathA_node:
                        link = links.new(prev_mathA_node.outputs[0], mathA_node.inputs[0])
                    else:
                        mathA_node.inputs[0].default_value = 0
                    

                    if is_nrm:
                        prev_mix_node = group_node
                    else:
                        prev_mix_node = mix_node
                    prev_mathA_node = mathA_node

            # Link the last mix node to the group output
            if prev_mix_node:
                if is_nrm:
                    nrm_node = node_group.nodes.new('ShaderNodeNormalMap')
                    nrm_node.location = (200, 0)
                    links.new(prev_mix_node.outputs[0], nrm_node.inputs[1])
                    links.new(prev_mix_node.outputs[0], group_output.inputs['Result'])
                    links.new(nrm_node.outputs[0], group_output.inputs['Normal'])
                    links.new(prev_mathA_node.outputs[0], group_output.inputs['Alpha'])
                else:
                    links.new(prev_mix_node.outputs[0], group_output.inputs['Result'])
                    links.new(prev_mathA_node.outputs[0], group_output.inputs['Alpha'])
            if not customnodesetup:

                if group_name in tree.nodes:
                    group_node = tree.nodes[group_name]
                else:
                    group_node = tree.nodes.new('ShaderNodeGroup')
                    group_node.node_tree = node_group
                    group_node.name = group_name
                    group_node.location = (-300, (-100 * indexgr)+300)

                tree_links = tree.links  
                if shader_node:
                    if tex_type[0] in TEXTURE_PROPERTIES:
                        
                        prop = TEXTURE_PROPERTIES[tex_type[0]]

                        if is_nrm:
                            tree_links.new(group_node.outputs['Normal'], bump_node.inputs['Normal'])
                        elif is_h:
                            tree_links.new(group_node.outputs['Result'], bump_node.inputs['Height'])
                        else:
                            if prop[3] in shader_node.inputs:
                                tree_links.new(group_node.outputs['Result'], shader_node.inputs[prop[3]])
                            elif prop[4] in shader_node.inputs:
                                tree_links.new(group_node.outputs['Result'], shader_node.inputs[prop[4]])
                                
                        tree_links.new(shader_node.outputs[0], output_node.inputs[0])
                else:
                    if tex_type[0] == "DIFFUSE":
                        tree_links.new(group_node.outputs[0], output_node.inputs[0])

class ViewData(bpy.types.PropertyGroup):
    image_name: StringProperty()
    image_path: StringProperty()
    render_sizeX: IntProperty()
    render_sizeY: IntProperty()
    crop_startX: IntProperty()
    crop_startY: IntProperty()
    crop_endX: IntProperty()
    crop_endY: IntProperty()
    view: bpy.props.StringProperty()
    orthoscale: FloatProperty()
    
operator_running = False
class SCREEN_OT_crop_tool(bpy.types.Operator):
    bl_idname = "screen.crop_tool"
    bl_label = "Crop Tool"
    bl_description = "Draw a box to crop a screenshot"
    bl_options = {'REGISTER', 'UNDO'}

    start_x: bpy.props.IntProperty()
    start_y: bpy.props.IntProperty()
    end_x: bpy.props.IntProperty()
    end_y: bpy.props.IntProperty()
    mouse_dragging: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        global operator_running
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

                    # Take screenshot and crop
                    self.take_screenshot_and_crop(context)
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    context.area.tag_redraw()
                    operator_running = False
                    return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            if self.mouse_dragging:
                self.mouse_dragging = False
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            context.area.tag_redraw()
            operator_running = False
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        global operator_running
        if context.area.type == 'VIEW_3D':
            # Check if operator is already running
            if operator_running:
                self.report({'WARNING'}, "Operator is already running")
                return {'CANCELLED'}
            
            self.start_x = 0
            self.start_y = 0
            self.end_x = 0
            self.end_y = 0
            self.mouse_dragging = False
            
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            operator_running = True
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def draw_callback_px(self, context):
        if not self.mouse_dragging:
            return
        
        # Draw the square
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
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.5))  # White color with some transparency
        batch.draw(shader)

        # Calculate and draw the size info text
        size_x = abs(self.end_x - self.start_x)
        size_y = abs(self.end_y - self.start_y)
        size_text = f"Size: {size_x} x {size_y}"

        # Position the text in the viewport
        region_width, region_height = context.region.width, context.region.height
        text_pos_x = min(self.start_x, self.end_x) + 10
        text_pos_y = min(self.start_y, self.end_y) + 10

        # Set text color (white in this case)
        

        # Draw the text using Blender's built-in font drawing (blf)
        font_id = 0  # Default font
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
        EXT = "png"

        if self.start_x == self.end_x or self.start_y == self.end_y:
            self.report({'ERROR'}, "Region selected is too small")
            return {'CANCELLED'}   


        render = context.scene.render
        region = context.region

        render.resolution_x = int(region.width * context.scene.other_props.screen_capture_scale)
        render.resolution_y = int(region.height * context.scene.other_props.screen_capture_scale)

        view_data = context.scene.view_data.add()
        view_data.render_sizeX = render.resolution_x
        view_data.render_sizeY = render.resolution_y

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                if area == bpy.context.area:
                    # Save current state of overlays in the active 3D viewport
                    current_show_overlays = area.spaces.active.overlay.show_overlays
                    # Turn off overlays in the active 3D viewport
                    area.spaces.active.overlay.show_overlays = False

        # Save current state of Film transparent in render properties
        current_film_transparent = bpy.context.scene.render.film_transparent

        # Set Film transparent to true in render properties
        bpy.context.scene.render.film_transparent = True



        render.resolution_percentage = 100
        bpy.ops.render.opengl()
        store_current_view(view_data, context)
        area.spaces.active.overlay.show_overlays = current_show_overlays
        bpy.context.scene.render.film_transparent = current_film_transparent
        filepath = bpy.data.filepath
        if bpy.data.is_saved:
            filepath = "//" + os.path.splitext(os.path.basename(filepath))[0]
        else:
            filepath = os.path.join(bpy.app.tempdir, "HAS_edit")

        obj = context.object
        tex = context.scene.selected_texture
        if obj:
            filepath += "_" + bpy.path.clean_name(obj.name)
        if tex:
            filepath += "_" + bpy.path.clean_name(tex)
        filepath_final = filepath + "." + EXT
        i = 0

        # Ensure unique file name
        while os.path.exists(bpy.path.abspath(filepath_final)):
            filepath_final = filepath + "{:03d}.{:s}".format(i, EXT)
            i += 1

        view_data.image_name = name=bpy.path.basename(filepath_final)
        view_data.image_path = filepath_final
        render_result = bpy.data.images.get('Render Result')
        render_result.save_render(filepath_final)

        image_new = bpy.data.images.load(filepath_final)

        # Image dimensions
        width = image_new.size[0]
        height = image_new.size[1]

        # Get the region dimensions
        region_width = region.width
        region_height = region.height

        # Calculate scale factors
        x_scale = context.scene.other_props.screen_capture_scale #width / region_width
        y_scale = context.scene.other_props.screen_capture_scale #height / region_height

        # Calculate crop coordinates in render space
        left = int(min(self.start_x, self.end_x) * x_scale)
        right = int(max(self.start_x, self.end_x) * x_scale)
        upper = int(min(self.start_y, self.end_y) * y_scale)
        lower = int(max(self.start_y, self.end_y) * y_scale)

        # Crop within image bounds
        left = max(0, min(left, width))
        right = max(0, min(right, width))
        upper = max(0, min(upper, height))
        lower = max(0, min(lower, height))

        if left >= right or upper >= lower:
            self.report({'ERROR'}, f"Invalid crop dimensions_{left}_{right}_{upper}_{lower}_ with image size {width}x{height}")
            return {'CANCELLED'}

        cropped_width = right - left
        cropped_height = lower - upper

        view_data.crop_startX= int(self.start_x * x_scale)
        view_data.crop_startY= int(self.start_y * x_scale)
        view_data.crop_endX= int(self.end_x * x_scale)
        view_data.crop_endY= int(self.end_y * x_scale)


        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        if region_3d.view_perspective == 'ORTHO':
                            view_data.orthoscale = region_3d.view_distance
        pixels = list(image_new.pixels)
        cropped_pixels = []
        for y in range(upper, lower):
            for x in range(left, right):
                index = (y * width + x) * 4
                cropped_pixels.extend(pixels[index:index + 4])
        bpy.data.images.remove(image_new)
        cropped_image = bpy.data.images.new(name=bpy.path.basename(filepath_final), width=cropped_width, height=cropped_height)
        cropped_image.pixels = cropped_pixels
        cropped_image.filepath_raw = filepath_final
        cropped_image.file_format = 'PNG'
        cropped_image.save_render(filepath_final)
        
        print(cropped_image.name)

        
        check_views()
        # Optionally open in external editor
        try:
            bpy.ops.image.external_edit(filepath=filepath_final)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))
        
        return {'FINISHED'}

class ProjectApply(Operator):
    """Project edited image back onto the object"""
    bl_idname = "image.has_project_apply"
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
        
        # Switch to Object mode if not already
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        prev_active = context.view_layer.objects.active
        prev_selected = context.selected_objects.copy()
        
        #image_name = view_data.image_name
        #expand_left, expand_right, expand_up, expand_down
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
        new_focal_length = current_focal_length / 2.0
        load_stored_view(context.scene.view_data[self.index], context)

        # Set the camera as active
        bpy.context.scene.camera = camera
        
        # Ensure the previous active object is selected and active
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active
        # Align the view to the camera

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.region_3d.view_perspective = 'PERSP'

        bpy.ops.view3d.camera_to_view()
        # Switch to Texture Paint mode
        bpy.ops.paint.texture_paint_toggle()
        stored_view_str = view_data.view
        stored_view = eval(stored_view_str)  # Convert string back to tuple
        ortho_zoom_level = view_data.orthoscale

        if 'ORTHO' in stored_view:
            camera.data.lens = 3000  # Example adjustment based on zoom level
            forward_vector = camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
            print("Forward Vector:", forward_vector)
            camera.location += forward_vector * ortho_zoom_level * 120.0  # Example movement based on zoom level
            camera.data.clip_start = 5  # Example clip start adjustment
            camera.data.clip_end = ortho_zoom_level * 2.1  # Example clip end adjustment
            bpy.context.view_layer.update()
        else:
            camera.data.lens = new_focal_length  # Set perspective lens



        # Project the image
        bpy.ops.paint.project_image(image=image_name)

        # Switch back to Object mode to remove the camera
        bpy.ops.object.mode_set(mode='OBJECT')

        # Delete the temporary camera
        bpy.data.objects.remove(camera)

        bpy.data.images.remove(createdimage)
        bpy.data.images.remove(img)
        region_data.view_matrix, region_data.view_perspective = stored_view_matrix
        # Restore previous selection and active object
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active

        # Switch back to Texture Paint mode if needed
        if prev_active.type == 'MESH':
            bpy.ops.paint.texture_paint_toggle()
        print("Image apply Finished")
        return {'FINISHED'}

class ProjectRemove(Operator):
    """Remove the selected image from the project list"""
    bl_idname = "image.project_remove"
    bl_label = "Remove Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="Image Index", default=0)

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
    bl_idname = "image.project_open"
    bl_label = "Open Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="Image Index", default=0)

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

def expand_image(image_obj, expand_left, expand_right, expand_up, expand_down):
    # Get image dimensions
    width = image_obj.size[0]
    height = image_obj.size[1]
    
    # Calculate new dimensions
    new_width = width + expand_left + expand_right
    new_height = height + expand_up + expand_down
    
    # Create a new image with the expanded size
    new_image = bpy.data.images.new(image_obj.name + "_expanded", width=new_width, height=new_height)
    
    # Fill the new image with transparent black pixels
    pixels = [0.0] * (new_width * new_height * 4)  # RGBA values
    
    # Copy original image pixels into the appropriate positions of the new image
    original_pixels = image_obj.pixels[:]
    
    for y in range(height):
        for x in range(width):
            # Calculate indices for original and new image
            original_index = (y * width + x) * 4
            new_index = ((y + expand_down) * new_width + (x + expand_left)) * 4
            
            # Copy RGBA values
            for c in range(4):
                pixels[new_index + c] = original_pixels[original_index + c]
    
    # Assign pixels to the new image
    new_image.pixels = pixels
    
    return new_image
def check_views():
    # Get the view_data collection
    view_data = bpy.context.scene.view_data
    
    # Loop through the view_data in reverse order by index
    for i in reversed(range(len(view_data))):
        # Check if the image exists in bpy.data.images
        if view_data[i].image_name not in bpy.data.images:
            # Remove the view_data if the image does not exist
            view_data.remove(i)

def check_external_editor():
    # Check if external editor is set
    if not bpy.context.preferences.filepaths.image_editor:
        # If not set, prompt user to set external image editor path
        bpy.ops.preferences.edit()
        bpy.context.preferences.active_section = 'File Paths'
        bpy.context.preferences.filepaths.image_editor = "path_to_your_external_editor"

def create_image_with_overlay(main_img_width, main_img_height, overlay_image, start_x, start_y, end_x, end_y):
    # Switch start_x and end_x if start_x is greater than end_x
    if start_x > end_x:
        start_x, end_x = end_x, start_x

    # Switch start_y and end_y if start_y is greater than end_y
    if start_y > end_y:
        start_y, end_y = end_y, start_y
        
    #    return overlay_image
    #print("Invalid coordinates: start_x should be <= end_x and start_y should be <= end_y.")
    main_image = bpy.data.images.new("MainImage", width=main_img_width, height=main_img_height)

    overlay_width = overlay_image.size[0]
    overlay_height = overlay_image.size[1]
    
    # Adjust offsets to ensure within bounds
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

def store_current_view(view_props, context):
    region_data = context.space_data.region_3d
    stored_view = (region_data.view_matrix.copy(), region_data.view_perspective)
    view_props.view = repr(stored_view)  # Store tuple as a string

def load_stored_view(view_props, context):
    stored_view_str = view_props.view
    
    if not stored_view_str:
        return False
    
    stored_view = eval(stored_view_str)  # Convert string back to tuple
    region_data = context.space_data.region_3d
    region_data.view_matrix = stored_view[0]
    region_data.view_perspective = stored_view[1]
    return True

class SnapToView(Operator):

    bl_idname = "scene.snap_to_view"
    bl_label = "Snap to view"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty(name="Image Index", default=0)

    def execute(self, context):

        view_props=context.scene.view_data[self.index]

        stored_view_str = view_props.view
        
        if not stored_view_str:
            return {'CANCELLED'}

        stored_view = eval(stored_view_str)  # Convert string back to tuple
        region_data = context.space_data.region_3d
        region_data.view_matrix = stored_view[0]
        region_data.view_perspective = stored_view[1]
        return {'FINISHED'}
def check_for_updates():
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data.get("tag_name")
        download_url = data.get("html_url")
        
        if latest_version and download_url:
            if latest_version != CURRENT_VERSION:
                show_update_message(latest_version, download_url)
            else:
                print("You are using the latest version.")
        else:
            print("Invalid update information.")
            
    except requests.RequestException as e:
        print(f"Error checking for updates: {e}")

def show_update_message(latest_version, download_url):
    def draw(self, context):
        self.layout.label(text=f"Update available: {latest_version}")
        self.layout.operator("wm.url_open", text="Download Update").url = download_url
    
    bpy.context.window_manager.popup_menu(draw, title="Update Available", icon='INFO')

# Add a UI button to check for updates
class CheckForUpdatesOperator(bpy.types.Operator):
    bl_idname = "wm.check_for_updates"
    bl_label = "Check for Updates"

    def execute(self, context):
        check_for_updates()
        return {'FINISHED'}

preview_collections = {}

classes = [
    HAS_PT_LayersPanel,
    CreateTextureOperator,
    MoveLayerOperator,
    SelectTextureOperator,
    LayerProperties,
    UncheckLayerOperator,
    SaveLayersOperators,
    OtherProps,
    TextureTypeProp,
    CreateLayerFromTextureOperator,
    TextureSizeAddSubtract,
    DeleteLayersOperator,
    CombineTextures,
    OT_AddMyPreset,
    MT_MyPresets,
    AddTextureTypeProp,
    RemoveTextureTypeProp,
    ExecutePreset,
    CombineTexturesFunc,
    HASMaterialProperties,
    CustomNewImageOperator,
    SetupMaterial,
    HASRemoveMaterial,
    SaveLayersCurrentOperators,
    ProjectApply,
    ProjectRemove,
    ProjectOpen,
    TextureGrabSizeAddSubtract,
    SCREEN_OT_crop_tool,
    ViewData,
    SnapToView,
    CheckForUpdatesOperator,
]


def register():
    for cls in classes:
            register_class(cls)

    bpy.types.Scene.material_props = CollectionProperty(type=HASMaterialProperties)
    #bpy.types.Scene.layer_prop = bpy.props.CollectionProperty(type=LayerProperties)
    bpy.types.Scene.texture_types_props = bpy.props.CollectionProperty(type=TextureTypeProp)
    bpy.types.Scene.other_props = bpy.props.PointerProperty(type=OtherProps)

    bpy.types.Scene.texture_sizeX = bpy.props.IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )
    bpy.types.Scene.texture_sizeY = bpy.props.IntProperty(
        name="Texture Size",
        description="Size of the new texture",
        default=1024,
        min=1,
        max=8192
    )
    bpy.types.Scene.active_collection_index = IntProperty(name="Active Collection Index", default=0)
     
    presets_folder = bpy.utils.user_resource('SCRIPTS', create=True)
    my_bundled_presets = os.path.join(os.path.dirname(__file__), "presets") 
    my_presets = os.path.join(presets_folder, 'haspresets','savepres')
    bpy.types.Scene.my_presets =my_presets

    if not os.path.isdir(my_presets):
        os.makedirs(my_presets)

        files = os.listdir(my_bundled_presets)

        for f in files:
            shutil.copy2(os.path.join(my_bundled_presets, f), my_presets)

    if save_modified_images not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_modified_images)
        print("Save modified images handler registered.")
    bpy.types.Scene.view_data = CollectionProperty(type=ViewData)


    

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    preview_collections.clear()
    #del bpy.types.Scene.layer_prop
    del bpy.types.Scene.texture_sizeX
    del bpy.types.Scene.texture_sizeY
    del bpy.types.Scene.selected_texture
    del bpy.types.Scene.other_props
    if save_modified_images in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_modified_images)
        print("Save modified images handler unregistered.")

    del bpy.types.Scene.view_data
    

if __name__ == "__main__":
    register()
