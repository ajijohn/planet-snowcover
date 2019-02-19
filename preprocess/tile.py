import argparse

import pandas as pd
import geopandas as gpd

import rasterio as rio
from mercantile import Tile, xy_bounds, bounds
from supermercado import burntiles

from raster_utils import reproject_raster

from rio_tiler.utils import tile_read

from os import path, makedirs

from functools import partial

import numpy as np
np.set_printoptions(suppress=True)

from concurrent import futures

def add_parser(subparser):
    parser = subparser.add_parser(
        "tile", help = "Tile images.",
        description="Produce GeoTIFF tiles containing all imagery information from source image or directory of source images. OSM/XYZ Format.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )


    parser.add_argument("output_dir", help="output directory. (AWS S3 and GCP GS compatible).")

    parser.add_argument("--cover",
                        help=".csv file containing x,y,z rows describing tiles to produce. (Default: completely cover an image)",
                        type=argparse.FileType('r'))

    parser.add_argument("--zoom", help="OSM zoom level for tiles", type=int)

    parser.add_argument("--indexes", help='band indices to include in tile.', nargs="+", type=int, default = [1,2,3,4])

    parser.add_argument("files", help="file or files to tile", nargs="+")

    parser.add_argument("--stats",
                        help = "Produces band-wise mean and std. dev statistics across tiles. ",
                        action = 'store_true')



    parser.set_defaults(func = main)

def _write_tile(tile, image, output_dir, tile_size = 512, bands = [1,2,3,4]):
    """
        extracts and writes tile from image into output_dir
    """
    tile_xy_bounds = xy_bounds(tile)
    tile_latlon_bounds = bounds(tile)
    data, mask = tile_read(image, tile_xy_bounds, tile_size, indexes=bands)
    bands, height, width = data.shape

    makedirs(path.join(output_dir, str(tile.z), str(tile.x)), exist_ok=True)
    tile_path = path.join(output_dir, str(tile.z), str(tile.x), "{}.{}".format(tile.y, "tif"))

    new_transform = rio.transform.from_bounds(*tile_latlon_bounds, width, height)

    profile = {
        'driver' : 'GTiff',
        'dtype' : data.dtype,
        'height' : height,
        'width' : width,
        'count' : bands,
        'crs' : {'init' : 'epsg:4326'},
        'transform' : new_transform
    }


    try:
        with rio.open(tile_path, 'w', **profile) as dst:
            for band in range(0, bands ):
                dst.write(data[band], band+1)
    except Exception as e:
        print(e)
        return tile, False

    return tile_path, True


def tile_image(imageFile, output_dir, zoom, cover=None, indexes = None):
    """
    Produce either A) all tiles covering <image> at <zoom> or B) all tiles in <cover> if <cover> is not None at <zoom> and place OSM directory structure in <imageFile>/Z/X/Y.png format inside output_dir.

    """
    from shapely.geometry import box
    from json import loads
    from supermercado import burntiles

    def __load_cover_tiles(coverfile):
        coverTiles = pd.read_csv(coverfile)
        if len(coverTiles.columns) != 3:
            raise Exception("cover file needs to have 3 columns (z, x, y)")

        return [Tile(z, x, y) for _, (z, x, y) in list(coverTiles.iterrows())]

    f = rio.open(imageFile)

    # check crs:
    if int(f.crs.to_dict()['init'].split(":")[1]) != 4326:
        print(f"invalid crs ({f.crs.to_dict()['init']}), reprojecting raster....")
        f.close()
        mf = rio.io.MemoryFile()
        reproject_raster(imageFile, 4326, mf)
        mf.seek(0)

        f = mf.open()

        print(f"reproject successful {f.crs.to_dict()}")

    bbox = box(f.bounds.left, f.bounds.bottom, f.bounds.right, f.bounds.top)
    bbox = loads(gpd.GeoSeries(bbox).to_json())['features'] # need geojson dict

    tiles = [Tile(z, x, y) for z, x, y in burntiles.burn(bbox, zoom)]


    covertiles = set()
    if cover is not None:
        covertiles = set(__load_cover_tiles(cover))
    tiles = set(tiles).intersection(covertiles)

    __TILER = partial(_write_tile, image = imageFile,
                     output_dir = output_dir, bands = indexes)

    with futures.ThreadPoolExecutor() as executor:
        responses = list(executor.map(__TILER, tiles))

    return(responses)


def compute_stats(tiles):
    """
    Single-band dataset-wide mean and std of tiles
    """

    bandcount = 0
    num_pixels = 0
    with rio.open(tiles[0]) as f:
        bandcount = f.count
        num_pixels = f.shape[0] * f.shape[1]

    num_pixels = num_pixels * len(tiles)



    running_N = np.zeros(bandcount)
    running_sum = np.zeros(bandcount)
    running_sos = np.zeros(bandcount)

    print(running_sos, bandcount)

    for file in tiles:
        with rio.open(file) as img:
            data = img.read()
            this_sum = data.sum(axis=(1,2))
            running_sum += this_sum
            running_sos += np.square(this_sum)


    mean = running_sum / num_pixels
    std = np.sqrt((running_sos / num_pixels) - (mean * mean))

    return(mean, std)



def main(args):
    all_tiles = []

    for image in args.files:
        fbase = path.splitext(path.basename(image))[0]
        image_output = path.join(args.output_dir, fbase)
        all_tiles.extend(tile_image(image, image_output, args.zoom, args.cover, args.indexes))

    if (args.stats):
        filenames, _ = list(zip(*all_tiles))

        mean, std = compute_stats(filenames)
        print(f"mean: {mean}\tstd: {std}")
