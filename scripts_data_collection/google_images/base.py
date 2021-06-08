# # -*- coding: utf-8 -*-
# Copyright (C) 2019-2020, xiaohu <zhangxh@mit.edu>
# Distributed under the GPL license, see LICENSE.txt

import os
import requests
import time
import sys
import csv
import shutil

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class GeneralScrapy:
    """
    Methods to overwrite:
        _start()
        _valid()
    """
    
    def __init__(self):
        self._change_encoding = False
        self._wait_time = 1
        self.proxy = None

        self._create_folder('data')

    def start(self, image_type, additional_params={}):
        start_time = time.time()
        self._start(image_type, additional_params=additional_params)
        end_time = time.time()
        print('Time: {}s'.format(end_time - start_time))
        pass

    def _start(self):
        # need override
        pass
    
    def _create_folder(self, folder_name):
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        return True

    def _get_url(self, url, params={},
                 data={}, method="GET", store=True, 
                 _digest=False):
        self.current_url = url
        #print('Get {}'.format(url))

        html_page = self._get_page_content(url, params, data, method)

        if html_page == '':
            print(url, ' didn\'t pass validation')
            sys.exit()

        if _digest:
            self._digest_page(html_page)
        
        return html_page


    def _get_page_content(self, this_url,
                          params={}, data={},
                          method="GET", 
                          _valid_func=None):

        valid_error = 0
        if not _valid_func:
            _valid_func = self._valid
            
        success = False
        while True:
            try:
                if 'check_url' in data.keys():
                    metadata = requests.request(
                        method, data['check_url'],
                        params=params, 
                        timeout=5, verify=False, 
                        stream=True)
                    metadata = metadata.json()
                    if metadata["status"] != "OK":
                        break
                    
                html_page = requests.request(
                    method, this_url,
                    params=params, 
                    timeout=5, verify=False, 
                    stream=True)

                time.sleep(self._wait_time)
                if self._change_encoding:
                    html_page.encoding = self._page_encoding

                if _valid_func(html_page):
                    success = True
                    break
                
                valid_error += 1
                if valid_error == 50:
                    return ''
                print('not valid', data['census_tract_id'])
                  
            except Exception as e:
                print(e)
                time.sleep(self._wait_time)
                
        if success:                
            return html_page
        else:
            return None
        

    def _store_image(self, subfolder, image_id, html_page):
        with open(self._output_folder+subfolder+image_id+".jpg", "wb") as f:
            html_page.raw.decode_content = True
            shutil.copyfileobj(html_page.raw, f)
                
    def _valid(self, html_page):
        # needs override
        return True

