from mapscraper import panoIDScrapy
import argparse
import ast
from setup import *
import sys

"""
setup should contain: 
    - save_dir: directory to save images to
    - loc_file: path to locations file to sample images from
    - census_shp_file: shapefile that contain the geometry of locations in loc_file
    - params: dictionary with basic image properties
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--Number", help="Number of images per census tract")
    parser.add_argument("-s", "--Split", help="Whether to split image collection")
    parser.add_argument("-i", "--Index", help="If split, index to start from")
    parser.add_argument("-p", "--NumPart", help="If split, number of parts")
    parser.add_argument("-t", "--ImageType", help="Type of image to collect: road, satellite, streetview")
    parser.add_argument("-kwargs", "--kwargs", help="Additional parameters kw1:arg1,kw2:arg2")

    args = parser.parse_args()
    if args.ImageType is None:
        print("Please specify type of image")
        sys.exit()
    else:
        imagetype = args.ImageType
    if args.kwargs is None:
        additional_params = {}
    else:
        additional_params = {}
        for i in args.kwargs.split(","):
            additional_params[i.split(":")[0]] = ast.literal_eval(i.split(":")[1])
    if args.Number is None:
        number = 10
    else:
        number = int(args.Number)
    if args.Split is None:
        split = True
    else:
        split = bool(int(args.Split))
    if args.Index is None:
        index = 0
    else:
        index = int(args.Index)
    if args.NumPart is None:
        numpart = 50
    else:
        numpart = int(args.numpart)

    panoid_scrapy = panoIDScrapy(census_file=loc_file, census_shp_file=census_shp_file,
                                 save_dir=save_dir, number=number,
                                 split=split, this_index=index, num_part=numpart)
    panoid_scrapy.start(image_type=imagetype, additional_params=additional_params)
