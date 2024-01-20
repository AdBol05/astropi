#* import all required libraries
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
from picamera import PiCamera
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
from exif import Image
import cv2
import math

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=9, seconds=30)  # run program for 177 minutes (3min headroom from the 3hr limit)

base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set temporary folder path
data_file = output_folder/'data.txt'  # set data.csv path
model_file = base_folder/'viewtype.tflite' # set model path
label_file = base_folder/'viewtype_labels.txt' # set label file path

img_counter = 1000  # image counter (start from 1000 for better naming scheme)
img_limit = 40  # max number of images
storage_txt = 125000000  # text file storage limit
storage_img = 125000000 # image storage limit

#* define functions
def average(list):
    return sum(list) / len(list)

def write_to_txt(filename, data):
    with open(filename, 'a') as f:
        f.write(data + '\n')
        print("Written data to txt file")

#* camera setup (set iamge resolution and frequency)
camera = PiCamera()
camera.resolution = (4056,3040)  # max 4056*3040

#* attempt to initialize coral TPU
coral = False
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

finally:
    print("Coral TPU initialized successfully")

#* final output message
print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print("#------------------------------------------------------------------------------------------------------#")