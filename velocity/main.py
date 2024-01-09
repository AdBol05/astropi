#* import all required libraries
import csv
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from picamera import PiCamera
from sense_hat import SenseHat

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=177)  # run program for 177 minutes (3min headroom from the 3hr limit)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set temporary folder path
data_file = output_folder/'data.csv'  # set data.csv path
model_file = base_folder/'lightning.tflite' # set model path
label_file = base_folder/'labels.txt' # set label file path

img_counter = 100000  # image counter (start from 10000 for better naming scheme)
storage_data = 32000000  # used storage space (CSV file)
storage_img = 2960000000 # used storage space (images)

#* define functions
def create_csv(data_file):  # creating csv file
    with open(data_file, 'w') as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("DateTime", "accX", "accY", "accZ")  # write first line (data type)
        writer.writerow(header)  # write header to csv file
        print(f"Creating data.csv file...\n path: {data_file}")  # debug

def add_csv_data(data_file, data):  # appending data to csv file
    with open(data_file, 'a') as f:  # open csv file
        writer = csv.writer(f)  # set up writer
        writer.writerow(data)  # write data row to csv file

def read_data(data_file):  # data collection
    acc = sense.get_accelerometer_raw()  # get raw accelerometer data
    row = (datetime.now(), round(acc.get("x"), 10), round(acc.get("y"), 10), round(acc.get("z"), 10))  # assign data to row
    add_csv_data(data_file, row)  # write row to csv file

#* define thread functions
def get_data(startTime, endTime, storage_limit, data_file):  # data collection thread
    currentTime = datetime.now()  # get current time before loop start
    storage = 0  # data.csv file size counter
    print("Started data thread")  # debug
    while (currentTime < endTime and storage < storage_limit):  # run until storage or time runs out
        if storage != 0:  # ignore first iteration
            storage -= os.path.getsize(data_file)  # subtract old data.csv file size from storage counter

        read_data(data_file)  # get data from all sensors and write to output file
        storage += os.path.getsize(data_file)  # add new data.csv file size to storage counter
        currentTime = datetime.now()  # update time
        sleep(1)  # wait one second

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Data collection thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

def get_images(startTime, endTime, storage_limit, counter, out_dir, temp_dir, model, labels):  # image collection thread
    currentTime = datetime.now()  # get current time before loop start
    storage = 0;
    print("Started image thread")

    #TODO: image thread

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Image collection thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(False, False, True)  # enable accelerometer

#* camera setup (set iamge resolution and frequency)
camera = PiCamera()
camera.resolution = (1296, 972)  # max 4056*3040
camera.framerate = 30

#* initialization
print("starting threads")  # debug
# define two threads (one for image collection, and one for sensor reading)
thread1 = threading.Thread(target = get_data, args = [startTime, endTime, storage_data, data_file])
thread2 = threading.Thread(target = get_images, args = [startTime, endTime, storage_img, img_counter, output_folder, temporary_folder, model_file, label_file])

#* start threads
thread1.start()
thread2.start()

#* wait for threads to finish
thread1.join()
thread2.join()

#* final output message
print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print("#------------------------------------------------------------------------------------------------------#")