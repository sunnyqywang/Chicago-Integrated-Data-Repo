import argparse 
import calendar 
import datetime
import pandas as pd
# Chicago Data Portal uses Socrata API
from sodapy import Socrata
# Need a credentials.py file with a dictionary named cityofchicago 
# with the following keys: apitoken, username, pwd
from credentials import *

# The script will get entire months of data containing the start and end date
# A day of data (before covid) takes 2-3 minutes to download!

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--StartDate", help="StartDate")
    parser.add_argument("-e", "--EndDate", help="EndDate")
    parser.add_argument("-d", "--SaveDir", help="Save directory")
    
    args = parser.parse_args()

    start_date = args.StartDate
    end_date = args.EndDate
    if args.SaveDir is None:
        save_dir = "/home/jtl/Dropbox (MIT)/DOE_TSMS/00_Data/raw_data/mobility/"
    else:
        save_dir = args.SaveDir

    apitoken = cityofchicago["apitoken"]
    username = cityofchicago["username"]
    pwd = cityofchicago["pwd"]

    client = Socrata("data.cityofchicago.org", apitoken, username, pwd)
    # automatic timeout is 10s, increase to 2 hours
    client.timeout = 7200
    
    for y,m in [(i.year, i.month) for i in pd.period_range(start_date, end_date, freq="M")]:
        print("Downloading %d-%d" %(y,m))

        time = datetime.datetime.now()
        # slow
        # results = client.get("m6dm-c72p", where="date_extract_y(trip_start_timestamp) = " + str(y) +" AND date_extract_m(trip_start_timestamp)= " + str(m), content_type="csv", limit=2000)
        if m < 10:
            pad = '0'
        else:
            pad = ''
        (y1,m1) = calendar.nextmonth(year=y, month=m)
        if m1 < 10:
            pad1 = '0'
        else:
            pad1 = ''

        s = str(y)+'-'+pad+str(m)+'-01'
        e = str(y1)+'-'+pad1+str(m1)+'-01'

        d = calendar.monthrange(y,m)[1]

        results = client.get_all("m6dm-c72p", where="trip_start_timestamp >= \"" + s +"\" AND trip_start_timestamp < \"" + e + "\"",  content_type="csv")
        
        results = pd.DataFrame(results)
        results.columns = results.iloc[0]

        # the results have headers on each page therefore header rows are interleaved in the dataframe
        # filter these header rows out
        results = results[results['trip_id'] != 'trip_id']

        print("Number of Entries: %d " %(len(results)))
        print("Time Taken Download", datetime.datetime.now()-time)
        time = datetime.datetime.now()

        results.to_csv(save_dir+"chicago_tnc_"+str(y)+pad+str(m)+"01_"+str(y)+pad+str(m)+str(d)+".csv", index=False)
        print("Time Taken Write", datetime.datetime.now()-time)

