
# coding: utf-8

# In[1]:


#get_ipython().system('export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt')


# In[2]:


#get_ipython().run_line_magic('matplotlib', 'inline')
from osgeo import gdal
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import rasterio as rio
import numpy as np
from matplotlib import pyplot as plt
import rasterio.plot
import os
from datetime import datetime as dt
from rasterio import Affine, MemoryFile
from rasterio.enums import Resampling
import numpy
scale=1


# In[42]:


# Validate the see if the clips can be used.
#get_ipython().run_line_magic('matplotlib', 'inline')
from os import environ
import sys
import io
from os.path import expanduser
import pprint
import s3fs
import boto3
import io
from re import match
#get_ipython().run_line_magic('matplotlib', 'inline')
import rasterio as rio

import earthpy as et
import earthpy.spatial as es
import earthpy.plot as ep
import numpy as np
import numpy
#get_ipython().run_line_magic('matplotlib', 'inline')
import rasterio as rio
from matplotlib import pyplot as plt
import rasterio.plot
import os
from datetime import datetime as dt
from rasterio.io import MemoryFile
import tempfile

sys.path.append("../model/robosat_pink/")
from robosat_pink.config import load_config
config_location= '/home/ubuntu/planet-snowcover/experiments/co-train.toml'
config = load_config(config_location)


p = pprint.PrettyPrinter()

fs = s3fs.S3FileSystem(session = boto3.Session(profile_name = config['dataset']['aws_profile']))

imagery_searchpath = config['dataset']['image_bucket']  + '/' +  config['dataset']['imagery_directory_regex']
print("Searching for imagery...({})".format(imagery_searchpath))
imagery_candidates = fs.ls(config['dataset']['image_bucket'])
#print("candidates:")
#p.pprint(imagery_candidates)
imagery_locs = [c for c in imagery_candidates if match(imagery_searchpath, c)]
print("result:")
p.pprint(imagery_locs)


# In[4]:


#get_ipython().system('export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt')


# In[ ]:


#Revised

#Now we got main root clips
#Now check that for each image, you can get the DEM clipped
import pandas as pd
import pyproj
from geopandas import GeoDataFrame
from shapely.geometry import shape,box
from rasterio.mask import mask
from rasterio.transform import from_origin
scale=1
#create the files with 5 babds
for link in imagery_locs:
    print(link)
    #sub_candidates = fs.ls(link)
    #print(sub_candidates)
    #dev_s3_client.list_objects(link) 
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')

    bucket=link.partition('/')[0] 
    my_bucket = s3.Bucket(bucket)
    for my_bucket_object in my_bucket.objects.filter(Prefix=link.partition('/')[2]):
        #print(my_bucket_object)
        print('{0}:{1}'.format(my_bucket.name, my_bucket_object.key))
        with rio.open('s3://{0}/{1}'.format(my_bucket.name, my_bucket_object.key)) as src:
            print("key",my_bucket_object.key)
            print(src.meta)
            # # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN
            planet_ndvi = es.normalized_diff(src.read(3), src.read(4))
            aug_pla_meta = src.profile
            # Change the count or number of bands from 4 to 5
            aug_pla_meta['count'] = 5
            # Change the data type to float rather than integer
            aug_pla_meta['dtype'] = "float64"
            aug_pla_meta
            
            #convert to float64
            #ndvi_64 = np.array(planet_ndvi, dtype=numpy.float64)
            t = src.transform
            # rescale the metadata
            transform = Affine(t.a * scale, t.b, t.c, t.d, t.e * scale, t.f)
            height = int(src.height / scale)
            width = int(src.width / scale)
            
            #clip the dem
            with rio.open('out.tiff') as origin:

                epsg4326_dem = origin.read(1)
                print('dem meta origin',origin.meta)

                print('planet origin',src.meta)
                #pf = src.read(1, masked=True)
                print(box(*src.bounds))
                
                try:
                    clipped_raster,clipped_transform = mask(origin,[box(*src.bounds)],crop=True,nodata= 0)
                except ValueError as err:
                     print('Handling run-time error:', err)
                        
                print('clipped transform',clipped_transform)
                clipped_meta = origin.meta.copy()
                clipped_meta.update({"driver": "GTiff",
                     "height": clipped_raster.shape[1],
                     "width": clipped_raster.shape[2],
                               "nodata": 0,
                     "transform": clipped_transform})
                print(src.meta,"ds")
                print(clipped_raster[0].shape)
                print(src.crs)
                print(src.meta)
                print(src.shape[1])
                print(src.shape[0])
                print("clipped")
                print(clipped_raster.shape[1])
                print(clipped_raster.shape[2])

                # type
                print(type(clipped_raster)) 

                #old 
                with rio.open("dem.masked1" + ".tif", "w", **clipped_meta) as dest:
                    dest.write(clipped_raster) 
                    
                    
                localname='dem.masked1.tif'
                #Second write is to do with resampling
                with rasterio.open(localname) as nf:
                    print(nf.profile)
                    print(nf.crs)
                    print(nf.meta)
                    dem_r = nf.read(1) # read the entire array
                    clipped_meta = nf.meta.copy()
                    # Resample it here to match the same as Planet
                    #profile = origin.profile
                    clipped_meta.update(transform=transform, driver='GTiff', height=height, width=width)
                    clipped_raster = nf.read(
                    out_shape=(origin.count, height, width),
                    resampling=Resampling.bilinear,
                    )
                    with rio.open("dem.masked2" + ".tif", "w", **clipped_meta) as dest:
                        dest.write(clipped_raster) 
                    # below works , but a better way

                    
                localname='dem.masked2.tif'    
                with rasterio.open(localname) as nf:
                    print(nf.profile)
                    print(nf.crs)
                    print(nf.meta)
                    dem_r = nf.read(1) # read the entire array
                    
                    #print(src.meta)
                    # # Load red and NIR bands - note all PlanetScope 4-band images have band order BGRN

                    aug_pla_meta = src.profile
                    # Change the count or number of bands from 4 to 6
                    aug_pla_meta['count'] = 6
                    # Change the data type to float rather than integer
                    aug_pla_meta['dtype'] = "float64"
                    aug_pla_meta
            
                    #convert to float64
                    dem_64 = np.array(dem_r, dtype=numpy.float64)
                    ndvi_64 = np.array(planet_ndvi , dtype=numpy.float64)
                    new_bucket = s3.Bucket('planet-snowcover-imagery-dem-ndvi')
                    temp_file = tempfile.TemporaryFile()
                    #with tempfile.NamedTemporaryFile() as tmpfile:
                    #tmpfile.write(data)
                    #with rasterio.open(tmpfile.name) as dataset:
                    #data_array = dataset.read()
            
                    with tempfile.NamedTemporaryFile() as tmpfile:
                        with rasterio.open(tmpfile.name,
                               'w', **aug_pla_meta) as dstr:
                            dstr.write_band(1, src.read(1))
                            dstr.write_band(2, src.read(2))
                            dstr.write_band(3, src.read(3))
                            dstr.write_band(4, src.read(4))
                            dstr.write_band(5, dem_64)
                            dstr.write_band(6, ndvi_64)
                        dstr.close()   
            
                        s3_client.upload_fileobj(tmpfile, new_bucket.name, my_bucket_object.key)  
                        # Write band calculations to a new raster file
                     
#    break


