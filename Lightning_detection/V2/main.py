# importing necessary libraries
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
storage = 10000  # used storage space (headroom for script and csv file)
image_size = 0  # size of image
delete_counter = 0  #iamge counter used for deletion
spike = 0  # spike detection (set as not found)

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


def read_data(data_file, compass):  # data collection
    global i  # readings counter as a global variable
    t = load.timescale().now()  # get timescale
    position = ISS.at(t)  # get position from timescale
    location = position.subpoint()  # get location from position
    i = i + 1  # increase readings counter by one
    row = (i, datetime.now(), location, sense.get_compass_raw())  # assign data to row
    print("sensing data...")  # debug
    add_csv_data(data_file, row)  # write row to csv file

#some basic init
base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder / 'data.csv'  # set data.csv file name and location

sense = SenseHat() # set up sense hat
sense.set_imu_config(True, False, False)  # configure imu

camera = PiCamera()  # set up camera
camera.resolution = (1296, 972)  # set camera resolution

print("running...")  # debug
create_csv(data_file)  # create data.csv file

currentTime = datetime.now()  # get current time before loop start


while (currentTime < startTime + timedelta(minutes=175) and storage < 3000000000):  # run for 175 minutes (3 hours - 5 minutes) or until storage is full
    for k in range(10):  # run ten times (10 images)
        compass = sense.get_compass_raw()  # get data from magnetometer (compass)
        read_data(data_file, compass)  # gather data

        camera.capture(f"{base_folder}/img_{counter}.jpg")  # capture camera and save the image
        image_size = image_size + os.path.getsize(base_folder/f'img_{counter}.jpg')  # get image counter
        counter = counter + 1  # add one to image counter
        #print("took a picture")  # debug
        #print(image_size)  # debug

        sleep(1)  # wait one second

    if spike == 0:  # if spike is not detected
        for d in range(9):  # run ten times (10 images)
            delete_counter = (counter - d) - 1  # resovle number of images selected to be deleted
            os.remove(f"{base_folder}/img_{delete_counter}.jpg")  # remove unnecessary images
            print("removing images...")  # debug
            #print(delete_counter)  # debug

    if spike == 1:  # if spike is detected
        storage = storage + image_size  # add images size to storage counter
        print("saving images")  # debug

    #reset variables
    spike = 0
    image_size = 0

    currentTime = datetime.now()  # update current time

print("Program ended. Timed out or ran out of storage.")  # debug
