# import all required libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
import os

startTime = datetime.now()  # get program start time

n = 0  # loop counter
i = 0  # data readings counter
counter = 10000  # image counter (start from 10000 for better naming scheme)
storage = 10000  # used storage space (headroom for script and csv file)

def create_csv(data_file):  # creating csv file
    with open(data_file, 'w') as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("RowNum", "Date/time", "Compass", "Compass(raw)", "Accelerometer", "Accelerometer(raw)",  "Gyro", "Gyro(raw)", "Orintation")  # write first line (data type)
        writer.writerow(header)  # write header to csv file
        print("Creating data.csv file...")  # debug


def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a') as f:  # open csv file
        writer = csv.writer(f)  # set up writer
        writer.writerow(data)  # write data row to csv file
        print("Writing data to .csv file...")  # debug


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    i = i + 1  # increase readings counter by one
    
    compass = sense.get_compass()  # get compass data
    compass_raw = sense.get_compass_raw()  # get raw compass data
    accel = sense.get_accelerometer()  # get accelerometer data
    accel_raw = sense.get_accelerometer_raw()  # get raw accelerometer data
    gyro = sense.get_gyroscope()  # get gyroscope data
    gyro_raw = sense.get_gyroscope_raw()  # get raw gyroscope data
    orientation = sense.get_orientation()  # get orientation
    
    row = (i, datetime.now(), compass, compass_raw,  accel_raw, gyro, gyro_raw, orientation)  # assign data to row
    
    print("sensing data...")  # debug
    add_csv_data(data_file, row)  # write row to csv file


