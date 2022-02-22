# import all required libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera

startTime = datetime.now()  # get program start time

n = 0  # loop counter
i = 0  # data readings counter
counter = 10000  # image counter (start from 10000 for better naming scheme)
storage = 10000  # used storage space (headroom for script and csv file)

def create_csv(data_file):  # creating csv file
    with open(data_file, 'w') as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("RowNum", " Date/time", " Compass", " Compass(raw)", " Accelerometer", " Accelerometer(raw)",  " Gyro", " Gyro(raw)", " Orintation")  # write first line (data type)
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
    accel_raw = sense.get_accelerometer_raw()  # get accelerometer raw data
    gyro = sense.get_gyroscope()  # get gyriscope data
    gyro_raw = sense.get_gyroscope_raw()  # get raw gyroscope data
    orientation = sense.get_orientation()  # get orientation
    row = (i, datetime.now(), compass, compass_raw,  accel_raw, gyro, gyro_raw, orientation)  # assign data to row
    print("sensing data...")  # debug
    add_csv_data(data_file, row)  # write row to csv file


base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder / 'data.csv'  # set data.csv file name and location
sense = SenseHat()  # set up sense hat
camera = PiCamera()  # set up camera
camera.resolution = (1296, 972)  # set camera resolution
create_csv(data_file)  # create data.csv file
sense.set_imu_config(True, True, True)  # configure imu
print("program running...")  # debug
                  
# loop start
currentTime = datetime.now()  # get time before loop start
while currentTime < startTime + timedelta(minutes=175) and storage < 3000000000:  # run for 175 minutes (3 hours - 5 minutes => 175 minutes)
    n = n + 1  # increase loop counter by one
    print("loop count: ", n)  # debug
    read_data(data_file)  # collect data from all sensors

    if n % 30 == 0:  # run every 30 loops (60 seconds)
        camera.capture(f"{base_folder}/img_{counter}.jpg")  # capture camera and save the image
        print("took a picture")  # debug
        counter = counter + 1  # increase image counter by one

    sleep(2)  # pause one second before next cycle
    currentTime = datetime.now()  # update current time

print("Program ended")  # debug
