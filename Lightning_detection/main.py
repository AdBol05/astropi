#importing necessary libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import time, sleep
from picamera import PiCamera
from orbit import ISS
from skyfield.api import load

startTime = datetime.now()  # get program start time

counter = 10000  # image counter (start from 10000 for better naming scheme)
i = 0  # readings counter
storage = 7400000  # used storage space (headroom for script, label.txt and tflite model)

vals_x = []
vals_y = []
vals_z = []
spike = False

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
        #camera.capture(f"{base_folder}/img_{counter}.jpg")  # capture camera and save the image
        counter += 1
        compass = sense.get_compass_raw()
        vals_x.append(abs(float("{x}".format(**compass))))
        vals_y.append(abs(float("{y}".format(**compass))))
        vals_z.append(abs(float("{z}".format(**compass))))
        sleep(1)

    avrg_x = sum(vals_x) / len(vals_x)
    absmax_x = (max(vals_x) + 10) - avrg_x
    avrg_y = sum(vals_y) / len(vals_y)
    absmax_y = (max(vals_y) + 10) - avrg_y
    avrg_z = sum(vals_z) / len(vals_z)
    absmax_z = (max(vals_z) + 10) - avrg_z

    for j in range(len(vals_x)):
        if i != 0:
            if abs(vals_x[j] - vals_x[j - 1]) > absmax_x:
                print("spike detected")
                spike = True
            if abs(vals_y[j] - vals_y[j - 1]) > absmax_y:
                print("spike detected")
                spike = True
            if abs(vals_z[j] - vals_z[j - 1]) > absmax_z:
                print("spike detected")
                spike = True
            else:
                spike = False

    print(vals_x)
    print(vals_y)
    print(vals_z)

    # reset all values
    vals_x.clear()
    vals_y.clear()
    vals_z.clear()
    spike = False

    currentTime = datetime.now()  # update current time
print("Program ended. Timed out or ran out of storage.")
