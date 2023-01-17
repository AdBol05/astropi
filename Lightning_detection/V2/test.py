
#* importing necessary libraries
from PIL import Image
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
from orbit import ISS
from skyfield.api import load
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import os

import threading, queue # hopefully multithreading (1:CSV data, 2:image collection)

#* define variables
startTime = datetime.now()  # get program start time
i = 0
time_limit = 5  # runtime limit in minutes

#* set up paths (resolve all paths and create file structure)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output';
temporary_folder = base_folder/'temp';
data_file = output_folder/'data.csv'  # set data.csv path
#? model_file = base_folder/'model.tflite' # set model directory
#? label_file = base_folder/'label.txt' # set label file directory
#? create output and temporary directories if they don't exist
if not os.path.exists(temporary_folder):
    print(f"Creating temporary directory in: {temporary_folder}")
    os.mkdir(temporary_folder)
if not os.path.exists(output_folder):
    os.mkdir(output_folder)
    print(f"Creating output directory in: {output_folder}")

#* define functions
def create_csv(data_file):  # creating csv file
    with open(data_file, 'w', buffering=1) as f:  # create csv file and set up logging
        print(f"Creating data.csv file in {data_file}")  # debug
        header = ("RowNum", "date", "latitude_deg", "longitude_deg", "elevation_km", "magnetometer_X", "magnetometer_Y", "magnetometer_Z")  # write first line (data type)
        csv.writer(f).writerow(header)  # write header to csv file


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    position = ISS.at(load.timescale().now()).subpoint()  # get position from timescale
    mag = sense.get_compass_raw()  # get magnetometer data
    data = (i, datetime.now(), position.latitude, position.longitude, position.elevation.km, mag.get("x"), mag.get("y"), mag.get("z"))  # assign data to row

    with open(data_file, 'a', buffering=1) as f:  # open csv file
        csv.writer(f).writerow(data)  # write data row to scv file
        print("Written data to .csv file")  # 175debug

    i += 1  # increase readings counter by one

def angle2exif(angle):  # convert raw coords angle to EXIF friendly format
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def capture(cam, cnt):  # take a picture and add metadata to it (cam -> camera, cnt -> image counter)
    coords = ISS.coordinates()  # get current ISS coordinates
    south, exif_lat = angle2exif(coords.latitude)  # convert coordinates to exif friendly format
    west, exif_long = angle2exif(coords.longitude)

    # add coordinates to image metadata
    cam.exif_tags['GPS.GPSLatitude'] = exif_lat
    cam.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    cam.exif_tags['GPS.GPSLongitude'] = exif_long
    cam.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    cam.capture(f"{temporary_folder}/img_{cnt:03d}.jpg")  # capture camera and save the image

    print(f"took a picture: {cnt}")  # debug

def move(name, cnt):
    os.replace(f"{temporary_folder}/img_{cnt}.jpg", f"{output_folder}/{name}_{cnt}.jpg")  # move image to output folder


#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (set iamge resolution and zoom)
camera = PiCamera()
camera.resolution = (1296, 972)
camera.zoom = (0.20, 0.155, 0.80, 0.845) #TODO: fix image crop

#* define thread functions
def get_data(startTime, storage_limit, data_file, time_limit):
    storage = 0
    counter = 0
    currentTime = datetime.now()  # get current time before loop start
    while (currentTime < startTime + timedelta(minutes=time_limit) and storage < storage_limit):
        if counter != 0:  # ignore for first iteration
            csv_size_prev = os.path.getsize(data_file)  # get size of data.csv file before data is written
            storage -= csv_size_prev  # subtract old data.csv file size from storage counter
    
        read_data(data_file)  # get data from all snsors and write to output file
        storage += os.path.getsize(data_file)  # add new data.csv file size of storage counter
        currentTime = datetime.now()  # get current time before loop start
        print(f"Read data from sensors, used data storage: {storage}")

def get_images(startTime, storage_limit, camera, counter, time_limit, sequence):
    storage = 0
    spike = 0
    currentTime = datetime.now()  # get current time before loop start
    while (currentTime < startTime + timedelta(minutes=time_limit) and storage < storage_limit):
        for k in range(sequence):
            capture(camera, counter)
            counter += 1  # add one to image counter
            #TODO: save images to output and add size to storage counter
            print(f"Took image: {counter}, used image storages: {storage}")

        if spike == 0:  # if spike is not detected
            print(f"#removing images: {counter - sequence + 1} - {counter - 1}")
            for d in range(sequence):  # run a couple times (save the only last image)
                delete_counter = (counter - d) - 1  # resovle number of images selected to be deleted
                if d != (sequence-1):  # delete all images except for the last one
                    os.remove(f"{temporary_folder}/img_{delete_counter}.jpg")  # remove unnecessary images
                else:  # save last image
                    print(f"#saving image: {delete_counter}") # debug
                    move("img", delete_counter)
                    storage += os.path.getsize(f"{output_folder}/img_{delete_counter}.jpg")  # add image size to used storage space

        if spike == 1:  # if spike is detected
            print("#saving all images")  # debug
            for d in range(sequence):  # save all images
                move_counter = (counter - d) - 1  # resovle number of images selected to be dmoved
                move("spike", move_counter)
                storage += os.path.getsize(f"{output_folder}/spike_{move_counter}.jpg")  # add image size to used storage space

#* initialization
create_csv(data_file)  # create data.csv file
print("starting threads")
#! THREADS RUN SYNCHRONOUSLY NOW FOR SOME REASON
threading.Thread(target = get_data, args = [startTime, 2500000, data_file, time_limit]).start()
threading.Thread(target = get_images, args = [startTime, 2997500000 , camera, 10000, time_limit, 10]).start()


print(f"#Program ended. All output files are located in {output_folder}")  # debug
print(f"#Time elapsed: {datetime.now() - startTime}")