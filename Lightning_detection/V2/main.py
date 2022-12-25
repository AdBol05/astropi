# importing necessary libraries
from PIL import Image
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
from orbit import ISS
from skyfield.api import load
import os

#* define variables 
startTime = datetime.now()  # get program start time
counter = 10000  # image counter (start from 10000 for better naming scheme)
i = 0  # readings counter
storage = 10000  # used storage space (headroom for script and csv file)
image_size = 0  # size of image
delete_counter = 0  #iamge counter used for deletion
spike = 0  # spike detection (set as not found)

#* define functions
def create_csv(data_file):  # creating csv file
    with open(data_file, 'w', buffering=1) as f:  # create csv file and set up logging
        header = ("RowNum", "date", "coords-latitude(DMS)", "coords-longitude(DMS)", "coords-elevation(km)", "magnetometer-X", "magnetometer-Y", "magnetometer-Z")  # write first line (data type)
        csv.writer(f).writerow(header)  # write header to csv file
        print("Creating data.csv file...")  # debug


def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a', buffering=1) as f:  # open csv file
        csv.writer(f).writerow(data)  # write data row to scv file
        print("Writing data to .csv file...")  # debug


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    position = ISS.at(load.timescale().now()).subpoint()  # get position from timescale
    mag = sense.get_compass_raw()
    print("sensing data...")  # debug
    row = (i, datetime.now(), position.latitude.signed_dms(), position.longitude.signed_dms(), position.elevation.km, mag.get("x"), mag.get("y"), mag.get("z"))  # assign data to row   
    print(row)
    add_csv_data(data_file, row)  # write row to csv file
    i = i + 1  # increase readings counter by one

def angle2exif(angle):  # convert raw coords angle to EXIF friendly format
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def capture(cam, cnt):  # take a picture and add metadata to it
    cam.capture(f"{base_folder}/temp/img_{cnt}.jpg")  # capture camera and save the image
    image_size = image_size + os.path.getsize(base_folder/f'temp/img_{cnt}.jpg')  # get image counter

    # open last image and add metadata to it
    image = Image.open(f"{base_folder}/temp/img_{cnt}.jpg")
    image.save(f"{base_folder}/temp/img_{cnt}.jpg", exif=image.info["exif"], quality=100)

    print("took a picture")  # debug
    print(image_size)  # debug

#* set up paths
base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder / 'output/data.csv'  # set data.csv path
# create output and temp directories if they don't exist
if not os.path.exists(f"{base_folder}/temp"):
    os.mkdir(f"{base_folder}/temp")
if not os.path.exists(f"{base_folder}/output"):
    os.mkdir(f"{base_folder}/output")

#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (output resolution)
camera = PiCamera()
camera.resolution = (1296, 972)


#* initialization
print("running...")  # debug
create_csv(data_file)  # create data.csv file
currentTime = datetime.now()  # get current time before loop start


#* Main loop
while (currentTime < startTime + timedelta(minutes=175) and storage < 3000000000):  # run for 175 minutes (3 hours - 5 minutes) or until storage is full
    for k in range(10):  # run ten times (10 images)
        read_data(data_file)  # gather data
        capture(camera, counter)
        counter = counter + 1  # add one to image counter
        sleep(1)  # wait one second

    #* process images
    #! TODO: Spike detection + coral classification
    if spike == 0:  # if spike is not detected
        for d in range(9):  # run ten times (10 images)
            delete_counter = (counter - d) - 1  # resovle number of images selected to be deleted
            os.remove(f"{base_folder}/temp/img_{delete_counter}.jpg")  # remove unnecessary images
            print("removing images...")  # debug
            #print(delete_counter)  # debug

    if spike == 1:  # if spike is detected
        storage = storage + image_size  # add images size to storage counter
        print("saving images")  # debug

    #* reset variables
    spike = 0
    image_size = 0

    currentTime = datetime.now()  # update current time

print("Program ended. Timed out or ran out of storage.")  # debug