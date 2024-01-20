#* import all required libraries
import os
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from picamera import PiCamera
from sense_hat import SenseHat
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import cv2

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=9, seconds=30)  # run program for 177 minutes (3min headroom from the 3hr limit)

base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set temporary folder path
data_file_img = output_folder/'data_img.txt'  # set data.csv path
data_file_gps = output_folder/'data_gps.txt'  # set data.csv path
model_file = base_folder/'viewtype.tflite' # set model path
label_file = base_folder/'viewtype_labels.txt' # set label file path

img_counter = 100  # image counter (start from 10000 for better naming scheme)
img_limit = 40  # max number of images
storage_data = 125000000  # text file storage limit
storage_img = 125000000 # image storage limit

#* define functions
def average(list):
    return sum(list) / len(list)

def write_to_txt(filename, data):
    with open(filename, 'a') as f:
        f.write(data + '\n')

#* define thread functions
def gps_thread(startTime, endTime, storage_limit, data_file):  # data collection thread
    storage = 0  # data.csv file size counter
    print("Started data thread")  # debug
    while (datetime.now() < endTime and storage < storage_limit):  # run until storage or time runs out
        for i in range():
            print("reading gps...")

            #TODO: gps thread
        
        storage += os.path.getsize(data_file)  # add new data.csv file size to storage counter
        sleep(30)  # wait 30 seconds

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"GPS thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

def img_thread(startTime, endTime, storage_limit, counter, out_dir, temp_dir, model_file, label_file, data_file):  # image collection thread
    storage_img = 0  # used image storage
    storage_txt = 0  # used text storage
    print("Started image thread")  # debug

    try:  # attempt to to initialize coral TPU
        print("Initializing coral TPU")  # debug
        interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
        interpreter.allocate_tensors()  # set up TPU
        size = common.input_size(interpreter)  # get preffered input image size
        labels = read_label_file(label_file)  # get labels from label file

    except:
        e = sys.exc_info()  # get error message
        print(f"Failed initialize coral TPU")  # print error
        print("  Error: {}".format( e))  # print error details

    #TODO: image thread

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Image thread exited, storage used: {round((storage_img + storage_txt)/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(False, False, True)  # enable accelerometer

#* camera setup (set iamge resolution and frequency)
camera = PiCamera()
camera.resolution = (1296, 972)  # max 4056*3040

#* initialization
print("starting threads")  # debug
# define two threads (one for image collection, and one for sensor reading)
thread1 = threading.Thread(target = gps_thread, args = [startTime, endTime, storage_data, data_file_gps, data_file_gps])
thread2 = threading.Thread(target = img_thread, args = [startTime, endTime, storage_img, img_counter, output_folder, temporary_folder, model_file, label_file, data_file_img])

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