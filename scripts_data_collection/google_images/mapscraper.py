from base import GeneralScrapy
import json
import csv
import random
import requests
from shapely.geometry import Point
import geopandas as gpd
import setup

class panoIDScrapy(GeneralScrapy):
    
    streetview_url = 'https://maps.googleapis.com/maps/api/streetview'
    metadata_url = 'https://maps.googleapis.com/maps/api/streetview/metadata'
    static_url = 'https://maps.googleapis.com/maps/api/staticmap'
    
    params = setup.params
    
    def __init__(self, census_file, census_shp_file, save_dir, number=1, 
                 split=False, this_index=0, num_part=10):
        """

        @param census_file: path to census tract information file to collect images from
        @param census_shp_file: shapefile to sample points from
        @param save_dir: path to save image
        @param number: # images per census tract
        @param split: whether to split the entries in census_file during collection
        @param this_index: if split which part to start from
        @param num_part: if split, # parts
        """
        
        self._change_encoding = False
        self._wait_time = 0.1
        self.proxy = None

        # output folder
        self._create_folder(save_dir)
        self._output_folder = save_dir
        
        # location file with long(x) and lat(y) coords
        self.census_shp = gpd.read_file(census_shp_file)
        self.census_shp['COUNTYFP10'] = self.census_shp['COUNTYFP10'].astype(int)
        self.census_shp['TRACTCE10'] = self.census_shp['TRACTCE10'].astype(int)
        
        self.census_file = census_file
        
        self.num_part = num_part
        self.this_index = this_index
        self.split = split
        
        self.num_per_tract = number
        self.queried_ids = []
        
    def get_loc_from_census(self):
        """

        :return: a list of (census tract id, polygon) tuples from the census file
        """

        data = []
        with open(self.census_file) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                polygon = self.census_shp[(self.census_shp['COUNTYFP10']==int(row['county_fips'])) &
                                     (self.census_shp['TRACTCE10']==int(row['tract_fips']))]
                
                if len(polygon) != 1:
                    print("Fail to get state %s county %s tract %s" % 
                          (row['state_fips'], row['county_fips'], row['tract_fips']))
                    continue
                else:
                    polygon = polygon.iloc[0].geometry
                    polyid = str(row['state_fips'])+"_"+str(row['county_fips'])+"_"+str(row['tract_fips'])
                    
                
                data.append((polyid, polygon))
                
        return data

    def sample_census_tract(self, polyid, polygon):
        """

        :param polyid:
        :param polygon:
        :return: sampled point inside the polygon
        """

        point = None
        minx, miny, maxx, maxy = polygon.bounds
        while point is None:
            pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
            if polygon.contains(pnt):
                point = (pnt.x, pnt.y, polyid)
                
        return point
    
    def _start(self, image_type, additional_params={}):

        params = self.params.copy()

        if image_type == 'streetview':
            this_url = self.streetview_url  
            params["fov"] = 120
            params["location"] = "{},{}"
        elif image_type == 'satellite':
            this_url = self.static_url
            params['maptype'] = 'satellite'
            params["center"] = "{},{}"
        elif image_type == 'road':
            this_url = self.static_url
            params['maptype'] = 'roadmap'
            params["center"] = "{},{}"
        
        params.update(additional_params)

        self.loc_ids = self.get_loc_from_census()
        len_part = len(self.loc_ids) // self.num_part
        i = self.this_index
        if self.split:
            self.loc_ids = self.loc_ids[(len_part * i):(len_part * (i+1))]
        
        
        for (polyid, polygon) in self.loc_ids:
            i = 0     
            failed = 0
            while i < self.num_per_tract:
                point = self.sample_census_tract(polyid, polygon)
                this_params = params.copy()
                if image_type == 'streetview':
                    data = {'check_url':self.metadata_url}
                    this_params['location'] = this_params['location'].format(point[1], point[0])
                else:
                    data = {}
                    this_params['center'] = this_params['center'].format(point[1], point[0])
                    
                data['census_tract_id'] = point[2]
                data['image_id'] = str(i)
                
                if point[2] in self.queried_ids:
                    continue
                html_page = self._get_url(this_url, params=this_params, 
                                          data=data)
                if html_page:
                    self._store_image(subfolder=image_type+"/",
                                      image_id=data['census_tract_id']+"_"+data['image_id'], 
                                      html_page=html_page)
                    i += 1
                else:
                    failed += 1
                    print(this_params['location'])
                    
                if failed > 10:
                    print(point[2], 'not valid, obtained', i, 'images')
                    break
                    
    def _valid(self, html_page):
        """

        :param html_page:
        :return: True/False
        """
        
        try:
            if html_page == '{}':
                return True
            if (type(html_page) == requests.models.Response) & (html_page.status_code == 200):
                return True
            if html_page.status_code in [400, 404]:
                return False
            
            data = json.loads(html_page)
            if 'Data' in data:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False
        
        return True
