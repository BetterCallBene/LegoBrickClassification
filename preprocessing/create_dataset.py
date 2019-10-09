#!/usr/bin/env python
import os

def run_shell_script(command):
    try:
        os.system(command)
    except OSError as oe:
        print("Error while executing blender script")
        print(oe)
        raise

def get_blender_command(path_in, bg_images_path, images_per_brick, path_out):
    # path or reference to blender executable
    if sys.platform == "darwin":
        blender = "/Applications/Blender/blender.app/Contents/MacOS/blender"
    else:
        blender = "blender"

    bg = "-b='" + bg_images_path + "' " if bg_images_path else ""
    
    
    return (blender + " -b -P "
            + os.path.dirname(os.path.realpath(__file__))
            + "/render_brick.py -- "
            + "-i='" + path_in + "' "
            + bg
            + "-n=" + str(images_per_brick) + " "
            + "-s='" + path_out + "'")

def generate_dataset(dataset_in_path, bg_images_path, dataset_out_path, images_per_brick, except_list):
    """Generates a dataset of images using 3d models.

    A directory is created for each category and each category folder contains subdirectories for each individual brick.

    :param dataset_in_path: directory contains a set of .dat files
    :param bg_images_path: directory contains a set of images for background
    :param dataset_out_path: output path for generated images e.g. dataset/
    :param images_per_brick: number of images per brick
    :param except_list: list of categories in order to skip
    :return: Writes generated images to file
    # """
    
    

    # read all 3d files
    files = []
    for file in os.listdir(dataset_in_path):
        if file.endswith(".dat"):
            files.append(file)

    print(len(files))

    # # for each brick render IMAGES_PER_BRICk

    summary = dict()

    for i, file in enumerate(files):
        part_number, file_extension = os.path.splitext(file)
        print("processing file {} ({}/{})".format(part_number, i+1, len(files)))
        path_in = os.path.join(dataset_in_path, file)
        with open(path_in, 'r') as f:
            line = f.readline()
            # check whether file number is moved to another and skip if true
            if "~Moved to" in line:
                print("skip part: {}".format(line))
                continue
    #         # skip unimportant categories
            label = line[2:-1]
            if '~' in label:
                label = label.replace('~', '')
            if label.startswith('_'):
                label = label.replace('_', '')
            if label.startswith('='):
                label = label.replace('=', '')
            category = label.split(' ')[0]
            if category in except_list:
                print("skip part: {}".format(line))
                continue
        if category not in summary:
            summary[category] = list()
        summary[category].append((part_number, file))

    category_brick = "Brick"
    summary_brick = summary[category_brick]

    print ("Only {0}".format(category_brick))
    
    category_brick_dir = os.path.join(dataset_out_path, category_brick)

    
    elms = os.listdir(category_brick_dir)
    rest = [brick for brick in summary_brick if brick[0] not in elms]

    for part_number, file in rest:
        path_in = os.path.join(dataset_in_path, file)
        path_out = os.path.join(category_brick_dir, part_number)
        if not os.path.exists(path_out):
            os.makedirs(path_out)
        
# run blender python script to render images
        command = get_blender_command(path_in, bg_images_path, images_per_brick, path_out)
        run_shell_script(command)

if __name__ == "__main__":
    import sys, argparse
    argv = sys.argv[1:]

    usage_text = "Run as " + __file__ + " [options]"
    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "-i", "--input", dest="dataset_in", type=str, required=True,
        help="Input folder for all .dat files"
    )

    parser.add_argument(
        "-b", "--bg_images", dest="bg_images", type=str, required=False,
        help="Directory which holds the background images"
    )

    parser.add_argument(
        "-o", "--out_dataset", dest="dataset_out", type=str, required=False,
        default="results/dataset/",
        help="Output folder for generated images"
    )

    parser.add_argument(
        "-n", "--images", dest="images_per_brick", type=int, required=False,
        default=1,
        help="Number of generated images per brick"
    )

    args = parser.parse_args(argv)
    
    generate_dataset(args.dataset_in, args.bg_images, args.dataset_out, args.images_per_brick, ["Minifig", "Sticker", "Duplo", "Figure", "Pov-RAY"])

