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
from PIL import Image
from orbit import ISS
from skyfield.api import load
import cv2
import math

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=9, seconds=50)  # run program for 177 minutes (3min headroom from the 3hr limit)

base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set temporary folder path
data_file = output_folder/'data.txt'  # set data.csv path
model_file = base_folder/'viewtype.tflite' # set model path
label_file = base_folder/'viewtype_labels.txt' # set label file path

img_counter = 1000  # image counter (start from 1000 for better naming scheme)
img_limit = 40  # max number of images
img_sequence = 4  # number of images to take in one loop iteration
storage_limit = 250000000 # image storage limit
storage_img = 0  # used image storage
storage_txt = 0  # used text storage

#* define functions
def average(list):
    return sum(list) / len(list)

def write_to_txt(filename, data):
    with open(filename, 'a') as f:
        f.write("{:.4f}".format(data) + '\n')
        print("Written data to txt file")

def img_save(counter):
    print("Saving images...")
    size = 0
    for i in range(img_sequence):  # loop over last images
        id = counter - (i - 1)  # resolve image number
        path = output_folder + '/img_' + id + '.jpg'  # resolve image path
        os.replace(f"{temporary_folder}/img_{id}.h264", path)  # move image to output folder
        size += os.path.getsize(path)  # add image size to counter
        print(f"saving to: {path}")  # debug

    return size  # return size of all moved file so it can be added to used storage

def img_delete(counter):
    print("Deleting images...")
    for i in range(img_sequence):  # loop over last images
        id = counter - (i - 1)  # resolve image number
        path = temporary_folder + '/img_' + id + '.jpg'  # resolve image path
        os.remove(path)  # delete image
        print(f"Removing: {path}")  # debug

def convert(angle):  # convert coordinates to degrees
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle


#* camera setup (set iamge resolution)
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
    coral = True
    print("Coral TPU initialized successfully")

except:
    e = sys.exc_info()  # get error message
    coral = False
    print(f"Failed initialize coral TPU")  # print error
    print("  Error: {}".format( e))  # print error details

#* main loop
while(datetime.now() < endTime and (storage_img + storage_txt) <= storage_limit):  # run until storage is full or time expires
    print("Capturing images...")
    for i in range(img_sequence):
        point = ISS().coordinates()  # get current coordinates
        south, exif_latitude = convert(point.latitude)  # convert ccords to EXIF-friendly format
        west, exif_longitude = convert(point.longitude)

        # Set image EXIF data
        camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
        camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
        camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
        camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

        camera.capture(f"{temporary_folder}/img_{img_counter}.jpg")  # capture camera and save the image

        print(img_counter)  # debug
        img_counter += 1  # increment image counter
        sleep(5)
    
    if coral:
        print("Classifying images...")
        classified = False  # save or delete images based on classifications

        #* Open image and convert it to coral-friendly format
        image = Image.open(f"{temporary_folder}/img_{img_counter}.jpg").convert('RGB').resize(size, Image.ANTIALIAS)  # open image

        #* Classify image
        common.set_input(interpreter, image)  # load interpreter and image to TPU
        interpreter.invoke()  # invoke interpreter

        classes = classify.get_classes(interpreter, top_k=1)  # get classes

        for c in classes:  # get score of all classes
            print(f"class ID: {c.id} class label: {labels.get(c.id, c.id)} image score: {float(f'{c.score:.5f}')}")  # debug
            if(f'{labels.get(c.id, c.id)}'  == 'usable' and float(f'{c.score:.5f}') >= 0.8):  # if classified as usable with accuracy higher than 0.8
                classified = True  # mark image as usable for distance calculation

    #TODO: calculate distance
    #? https://projects.raspberrypi.org/en/projects/astropi-iss-speed/3

    if (coral and classified and (img_counter + img_sequence) < img_limit) or (not coral and (img_counter + img_sequence) < img_limit):
        storage_img += img_save(img_counter)  # save images
    else:
        img_delete(img_counter)  # delete images

    sleep(30)

#* final output message
print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print("#------------------------------------------------------------------------------------------------------#")