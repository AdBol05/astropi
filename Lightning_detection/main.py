#importing necessary libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import time, sleep
from picamera import PiCamera
from orbit import ISS
from skyfield.api import load
import os

startTime = datetime.now()  # get program start time

counter = 10000  # image counter (start from 10000 for better naming scheme)
i = 0  # readings counter
storage = 7400000  # used storage space (headroom for script and csv file)
image_size = 0
delete_counter = 0

vals_x = []  # value list from magnetometer (x axis)
vals_y = []  # y axis
vals_z = []  # z axis
spike = 0  # detected spike

def create_csv(data_file):  # creating csv file
    with open(data_file, 'w', buffering=1) as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("RowNum", "date", "coordinates", "magnetometer")  # write first line (data type)
        writer.writerow(header)  # write header to csv file
        print("Creating data.csv file...")  # debug


def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a', buffering=1) as f:  # open csv file
        writer = csv.writer(f)  # set up writer
        writer.writerow(data)  # write data row to scv file
        print("Writing data to .csv file...")  # debug


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    t = load.timescale().now()  # get timescale
    position = ISS.at(t)  # get position from timescale
    location = position.subpoint()  # get position from timescale
    i = i + 1  # increase readings counter by one
    row = (i, datetime.now(), location, sense.get_compass_raw())  # assign data to row
    print("sensing data...")  # debug
    add_csv_data(data_file, row)  # write row to csv file


base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder / 'data.csv'  # set data.csv file name and location
sense = SenseHat() # set up sense hat
camera = PiCamera()  # set up camera
sense.set_imu_config(True, False, False)  # configure imu
camera.resolution = (1296, 972)  # set camera resolution
print("running...")  # debug
create_csv(data_file)  # create data.csv file

currentTime = datetime.now()  # get current time before loop start
while (currentTime < startTime + timedelta(minutes=175) and storage < 3000000000):  # run for 175 minutes (3 hours - 5 minutes) or until storage is full
    read_data(data_file)  # gather data
    for k in range(10):
        camera.capture(f"{base_folder}/img_{counter}.jpg")  # capture camera and save the image
        image_size = image_size + os.path.getsize(base_folder/f'img_{counter}.jpg')  #get image counter
        counter = counter + 1  # add one to image counter
        compass = sense.get_compass_raw()  # get data from magnetometer (compass)
        vals_x.append(abs(float("{x}".format(**compass))))  # assign data from magnetometer (x axis) to list vals_x
        vals_y.append(abs(float("{y}".format(**compass))))  # assign data from magnetometer (y axis) to list vals_y
        vals_z.append(abs(float("{z}".format(**compass))))  # assign data from magnetometer (z axis) to list vals_z
        sleep(1)  # wait one second

    avrg_x = sum(vals_x) / len(vals_x)  # get average value
    absmax_x = (max(vals_x) + 10) - avrg_x  # get max value plus deviation
    avrg_y = sum(vals_y) / len(vals_y)
    absmax_y = (max(vals_y) + 10) - avrg_y
    avrg_z = sum(vals_z) / len(vals_z)
    absmax_z = (max(vals_z) + 10) - avrg_z

    for j in range(len(vals_x)):  # compare each pair in list
        if i != 0:
            if (abs(vals_x[j] - vals_x[j - 1]) > absmax_x) or (abs(vals_y[j] - vals_y[j - 1]) > absmax_y) or (abs(vals_z[j] - vals_z[j - 1]) > absmax_z):  # if detected large difference between on values next to each other
                print("spike detected")  # debug
                spike = 1
            else:
                spike = 0

    print(delete_counter)  # debug

    if spike == 0:
        for d in range(10):  # run ten times (10 images)
            delete_counter = (counter - d) - 1
            os.remove(f"{base_folder}/img_{delete_counter}.jpg")  #remove unnecessary images
            print("removing images...")  # debug
            print(delete_counter)  # debug
    else:
        storage = storage + image_size  # add images size to storage counter
        print("saving images")  #debug

    # debug
    print(vals_x)
    print(vals_y)
    print(vals_z)

    # reset all values
    vals_x.clear()
    vals_y.clear()
    vals_z.clear()
    spike = 0
    image_size = 0

    currentTime = datetime.now()  # update current time
print("Program ended. Timed out or ran out of storage.")  #debug