#importing necessary libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import time, sleep
from picamera import PiCamera
from orbit import ISS
from skyfield.api import load
from PIL import Image
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import os

startTime = datetime.now()  # get program start time

counter = 10000  # image counter (start from 10000 for better naming scheme)
i = 0  # readings counter
storage = 7400000  # used storage space (headroom for script, label.txt and tflite model)

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

model_file = base_folder/'particle.tflite' # set model directory
label_file = base_folder/'label.txt' # set label file directory

interpreter = make_interpreter(f"{model_file}")  # assign model to interpreter
interpreter.allocate_tensors()  # set up tensor cores
size = common.input_size(interpreter)  # resize image

currentTime = datetime.now()  # get current time before loop start
while (currentTime < startTime + timedelta(minutes=175) and storage < 3000000000):  # run for 175 minutes (3 hours - 5 minutes) or until storage is full
    camera.capture(f"{base_folder}/img_{counter}.jpg")  # capture camera and save the image
    print("took a picture")  # debug
    read_data(data_file)  # gather data

    image_file = base_folder/f'img_{counter}.jpg'  # set image directory
    image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
    common.set_input(interpreter, image)
    interpreter.invoke()
    classes = classify.get_classes(interpreter, top_k=1)
    labels = read_label_file(label_file)

    for c in classes:
        print("classifying image...")  # debug
        print(f'{labels.get(c.id, c.id)} {c.score:.5f}')  # debug
        if (f'{labels.get(c.id, c.id)}'  == 'particle' and float(f'{c.score:.5f}') >= 0.3):  # save only images with particles
            print("classified as particle, saving...")  # debug
            os.rename(image_file, base_folder/f'particle_{counter}.jpg')  # rename image to particle(number of picture).jpg
            image_size = os.path.getsize(base_folder/f'particle_{counter}.jpg')  # get image size
            storage = storage + image_size  # add image size to used storage
            print("saved image size: %d" % image_size)
            counter += 1  # increase image counter by one
        else:
            print("classified as a blank image, deleting...")  # debug
            os.remove(image_file)  # delete empty image

    currentTime = datetime.now()  # update current time
print("Program ended. Timed out or ran out of storage.")
