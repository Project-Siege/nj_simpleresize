bl_info = {
    "name": "Resize Images",
    "author": "Nomadic Jester",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Material > Resize Images",
    "description": "Resize images in material nodes",
    "category": "Material",
}

import bpy
import os
import subprocess
import sys
import importlib.util
from bpy.types import Panel, Operator
from bpy.props import IntProperty

# Function to install Pillow if not already installed
def install_pillow():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
    except subprocess.CalledProcessError as e:
        print("Pillow installation failed:", e)

# Check if Pillow is already installed
pillow_spec = importlib.util.find_spec("PIL")
if pillow_spec is None:
    # Pillow is not installed, so install it
    install_pillow()
else:
    print("Pillow is already installed.")

# Now you can import PIL modules and use them in your script
from PIL import Image

class ResizeImagesPanel(Panel):
    bl_label = "Resize Images"
    bl_idname = "MATERIAL_PT_resize_images"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.label(text="Preset Image Sizes:")
        layout.operator("image.set_preset_size", text="256x256").width = 256
        layout.operator("image.set_preset_size", text="512x512").width = 512
        layout.operator("image.set_preset_size", text="1024x1024").width = 1024

        layout.label(text="Custom Size:")
        row = layout.row()
        row.prop(scene, "custom_width")
        row.prop(scene, "custom_height")

        layout.operator("image.resize_images", text="Resize Images")

class SetPresetSizeOperator(Operator):
    bl_idname = "image.set_preset_size"
    bl_label = "Set Preset Size"
    bl_options = {'REGISTER', 'UNDO'}

    width: IntProperty(default=256)

    def execute(self, context):
        context.scene.custom_width = self.width
        context.scene.custom_height = self.width
        return {'FINISHED'}

class ResizeImagesOperator(Operator):
    bl_idname = "image.resize_images"
    bl_label = "Resize Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_object = context.active_object
        if selected_object:
            image_size = (context.scene.custom_width, context.scene.custom_height)
            self.resize_all_images(selected_object, image_size)
        return {'FINISHED'}

    def resize_all_images(self, obj, image_size):
        output_folder = bpy.path.abspath("//resized-images")
        os.makedirs(output_folder, exist_ok=True)

        for slot in obj.material_slots:
            material = slot.material
            if material:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        image = node.image
                        original_filepath = bpy.path.abspath(image.filepath)
                        copied_filepath = os.path.join(output_folder, os.path.basename(original_filepath))
                        
                        # Check if source and destination paths are the same
                        if original_filepath != copied_filepath:
                            shutil.copy(original_filepath, copied_filepath)
                            resized_image = self.resize_image(copied_filepath, image_size)
                            image.filepath = resized_image
                            self.update_object_texture(obj, image)
                            os.remove(original_filepath)

    def resize_image(self, image_path, size):
        img = Image.open(image_path)
        resized_img = img.resize(size, Image.BICUBIC)
        output_filepath = os.path.splitext(image_path)[0] + "_resized" + os.path.splitext(image_path)[1]
        resized_img.save(output_filepath)
        return output_filepath

    def update_object_texture(self, obj, image):
        for slot in obj.material_slots:
            material = slot.material
            if material:
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image == image:
                        node.image.reload()

def register():
    bpy.utils.register_class(ResizeImagesPanel)
    bpy.utils.register_class(SetPresetSizeOperator)
    bpy.utils.register_class(ResizeImagesOperator)
    bpy.types.Scene.custom_width = IntProperty(name="Width", default=256)
    bpy.types.Scene.custom_height = IntProperty(name="Height", default=256)

def unregister():
    bpy.utils.unregister_class(ResizeImagesPanel)
    bpy.utils.unregister_class(SetPresetSizeOperator)
    bpy.utils.unregister_class(ResizeImagesOperator)
    del bpy.types.Scene.custom_width
    del bpy.types.Scene.custom_height

if __name__ == "__main__":
    register()
