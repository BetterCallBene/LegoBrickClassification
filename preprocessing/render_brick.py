#!/usr/bin/env python
import bpy
import os
import numpy as np
import json
import random
import struct
import code

from mathutils import Euler

def hex2rgb(hex):
    int_tuple = struct.unpack("BBB", bytes.fromhex(hex))
    return [val/255 for val in int_tuple]

def render_brick(brick_file_path: str, n: int, render_folder: str, background_file_path: str):
    """Renders n images of a given .dat file

    :param brick_file_path: location of .dat file
    :param n: number of images to render
    :param render_folder: output directory
    :param background_file_path: path to list of background images
    :return: Saves generated images to render_folder
    """
    
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"), "r") as f:
        cfg = json.load(f)

    for obj in bpy.data.objects:
        obj.select_set(True)
        
    bpy.ops.object.delete(use_global=False)

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    
    cam = bpy.data.cameras.new('Cam01')
    cam_object = bpy.data.objects.new(name='Cam01', object_data=cam)
    bpy.context.collection.objects.link(cam_object)
    bpy.context.view_layer.objects.active = cam_object
    bpy.context.scene.camera = cam_object

    light = bpy.data.lights.new('sun_light', type='SUN')
    light.angle = np.pi/2
    light_object = bpy.data.objects.new(name='sun_light', object_data=light)
    light_object.location=(0, -1, 0)
    
    bpy.context.collection.objects.link(light_object)
    bpy.context.view_layer.objects.active = light_object

    bpy.ops.import_scene.importldraw(filepath=brick_file_path)
    bpy.data.objects.remove(bpy.data.objects["LegoGroundPlane"])

    cam_object.location = (0, -1, 0)
    cam_object.rotation_euler = Euler((np.pi/2, 0, 0), "XYZ")

    brick = [obj for obj in bpy.data.objects if obj.name.endswith(".dat")][0]
    
    if not os.path.exists(render_folder):
        os.mkdir(render_folder)

    #bpy.context.scene.render.engine = "BLENDER_EEVEE"
    rnd = bpy.data.scenes["Scene"].render
    rnd.resolution_x = cfg["width"]
    rnd.resolution_y = cfg["height"]
    rnd.resolution_percentage = 100

    bpy.context.scene.render.image_settings.file_format = "JPEG"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.quality = cfg["jpeg_compression"]

    # list of possible background images
    if background_file_path:
        images = []
        valid_ext = [".jpg", ".png"]
        for f in os.listdir(background_file_path):
            ext = os.path.splitext(f)[1]
            if ext.lower() in valid_ext:
                images.append(os.path.join(background_file_path, f))
    r = cfg["rotation_intervals"]

    for i in range(n):
        # brick settings
        brick_scale_factor = random.uniform(cfg['zoom_min'], cfg['zoom_max'])
        brick_rotx = random.choice([random.uniform(r['1_low'], r['1_high']), random.uniform(r['2_low'], r['2_high']),
                                    random.uniform(r['3_low'], r['3_high']), random.uniform(r['4_low'], r['4_high'])])
        brick_roty = random.choice([random.uniform(r['1_low'], r['1_high']), random.uniform(r['2_low'], r['2_high']),
                                    random.uniform(r['3_low'], r['3_high']), random.uniform(r['4_low'], r['4_high'])])
        brick_rotz = random.choice([random.uniform(r['1_low'], r['1_high']), random.uniform(r['2_low'], r['2_high']),
                                    random.uniform(r['3_low'], r['3_high']), random.uniform(r['4_low'], r['4_high'])])
        brick_posx = random.gauss(cfg['pos_mean'], cfg['pos_sigma'])
        brick_posz = random.gauss(cfg['pos_mean'], cfg['pos_sigma'])
        brick_posy = 0.0  # due to scaling
        
        brick.scale = (brick_scale_factor, brick_scale_factor, brick_scale_factor)
        brick.location = (brick_posx, brick_posy, brick_posz)
        brick.rotation_euler = (brick_rotx, brick_roty, brick_rotz)

        # set color
        color = hex2rgb(random.choice(cfg["color"]))
        color.append(1.0)
        color = tuple(color)

        bpy.data.materials["Material_4_c"].node_tree.nodes["Group"].inputs['Color'].default_value = color
        

        object_name = None
        if background_file_path:
            bg_image = random.choice(images)
            base=os.path.basename(bg_image)
            object_name=os.path.splitext(base)[0]
            bpy.ops.import_image.to_plane(shader='SHADELESS', files=[{'name':bg_image}])

            plane = bpy.data.objects[object_name]
            plane.location = (0, 1.0, 0)
            plane.scale = (1.4, 1.4, 1.0)
        else:
            bpy.ops.mesh.primitive_plane_add(size=2.0, calc_uvs=True, enter_editmode=False, align='WORLD', location=(0.0, 1.0, 0.0), rotation=(np.pi/2, 0.0, 0.0))
        
     
        file_name, file_extension = os.path.splitext(os.path.basename(brick_file_path))
        rnd.filepath = os.path.join(render_folder, "{0}_{1}.jpg".format(file_name, i))

        bpy.ops.render.render(write_still=True)

        if background_file_path:
            bpy.data.objects[object_name].select_set(True) # Blender 2.8x
            bpy.ops.object.delete() 
        else:
            bpy.data.objects["Plane"].select_set(True) # Blender 2.8x
            bpy.ops.object.delete() 

if __name__ == '__main__':

    # check whether script is opened in blender
    import sys, argparse
    if bpy.context.space_data:
        cwd = os.path.dirname(bpy.context.space_data.text.filepath)
    else:
        cwd = os.path.dirname(os.path.abspath(__file__))

    # get folder of script and add current working directory to path
    sys.path.append(cwd)


    # add python script arguments
    argv = sys.argv
    if "--" not in argv:
        argv = []
    else:
        argv = argv[argv.index("--") + 1:]  # get all after first --

    # when --help or no args are given
    usage_text = (
        "Run blender in background mode with this script on linux:"
        + " blender -b -P " + __file__ + "-- [options] "
        + "or with /Applications/Blender/blender.app/Contents/MacOS/blender -b -p " + __file__ + "-- [options]"
        + "on MacOS"
    )

    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument(
        "-i", "--input_file_path", dest="input", type=str, required=True, help="Input folder for 3d models"
    )

    parser.add_argument(
        "-b", "--background_files_path", dest="background", type=str, required=False, help="Input folder for "
                                                                                           "background images"
    )

    parser.add_argument(
        "-n", "--images_per_brick", dest="number", type=int, required=False, default=1, help="Number of bricks to "
                                                                                             "render"
    )

    parser.add_argument(
          "-s", "--save", dest="save", type=str, required=False, default="./", help="Output folder"
    )

    args = parser.parse_args(argv)
    if not argv:
        parser.print_help()
        sys.exit(-1)


    # finally render image(s)

    render_brick(args.input, args.number, args.save, args.background)

