# import all required libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
import os
import threading

startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=177)  # run program for 177 minutes (3min headroom from the 3hr limit)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
data_file = output_folder/'data.csv'  # set data.csv path

i = 0  # data readings counter
img_counter = 100000  # image counter (start from 10000 for better naming scheme)
storage_data = 32000000  # used storage space (CSV file)
storage_img = 2960000000 # used storage space (images)

def create_csv(data_file):  # creating csv file
    with open(data_file, 'w') as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("RowNum", "DateTime", "accX", "accY", "accZ")  # write first line (data type)
        writer.writerow(header)  # write header to csv file
        print(f"Creating data.csv file...\n path: {data_file}")  # debug


def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a') as f:  # open csv file
        writer = csv.writer(f)  # set up writer
        writer.writerow(data)  # write data row to csv file


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    i = i + 1  # increase readings counter by one
    acc = sense.get_accelerometer_raw()  # get raw accelerometer data
    data = (i, datetime.now(), round(acc.get("x"), 10), round(acc.get("y"), 10), round(acc.get("z"), 10))  # assign data to row
    add_csv_data(data_file, row)  # write row to csv file


create_csv()