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
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import os

#* define variables
startTime = datetime.now()  # get program start time
counter = 10000  # image counter (start from 10000 for better naming scheme)
i = 0  # readings counter
storage = 10000  # used storage space (headroom for script)
max_storage = 3000000000  #TODO find ou the exact storage limit
delete_counter = 0  #iamge counter used for deletion
spike = 0  # spike detection (set as not found)

#* set up paths (resolve all paths and create file structure)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output';
temporary_folder = base_folder/'temp';
data_file = output_folder/'data.csv'  # set data.csv path
# model_file = base_folder/'model.tflite' # set model directory
# label_file = base_folder/'label.txt' # set label file directory
# create output and temporary directories if they don't exist
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
        header = ("RowNum", "date", "coords_latitude_deg", "coords_longitude_deg", "coords_elevation_km", "magnetometer_X", "magnetometer_Y", "magnetometer_Z")  # write first line (data type)
        csv.writer(f).writerow(header)  # write header to csv file

def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a', buffering=1) as f:  # open csv file
        csv.writer(f).writerow(data)  # write data row to scv file
        print("Writing data to .csv file...")  # debug

def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    position = ISS.at(load.timescale().now()).subpoint()  # get position from timescale
    mag = sense.get_compass_raw()  # get magnetometer data

    print(f"reading data... used storage: {storage}/{max_storage}")  # debug
    row = (i, datetime.now(), position.latitude, position.longitude, position.elevation.km, mag.get("x"), mag.get("y"), mag.get("z"))  # assign data to row

    #print(row)
    add_csv_data(data_file, row)  # write row to csv file
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

#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (set iamge resolution and zoom)
camera = PiCamera()
camera.resolution = (1296, 972)
camera.zoom = (0.20, 0.155, 0.80, 0.845) #! TODO: fix image crop

#* coral setup
#! TODO: train and implement coral
"""
interpreter = make_interpreter(f"{model_file}")  # assign model to interpreter
interpreter.allocate_tensors()  # set up TPU
size = common.input_size(interpreter)  # resize image
""" 

#* initialization
create_csv(data_file)  # create data.csv file
currentTime = datetime.now()  # get current time before loop start

#* Main loop
while (currentTime < startTime + timedelta(minutes=175) and storage < max_storage):  # run for 175 minutes (3 hours - 5 minutes) or until storage is full
    #* take 10 images
    for k in range(10):
        read_data(data_file)  # get data from all snsors and write to output file
        storage += os.path.getsize(data_file)  # add data.csv file size of storage counter
        capture(camera, counter)  # capture image and add metadata to it
        counter += 1  # add one to image counter
        sleep(1)  # wait one second
        print("-----------------------------------------")  # debug

    #* process images
    #! TODO: Spike detection + coral classification

    #*Ignore this for now
    """
    image_file = f"{temporary_folder}/img_{counter}.jpg"  # set image directory
    image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
    common.set_input(interpreter, image)  # set input
    interpreter.invoke()  # invoke interpreter
    classes = classify.get_classes(interpreter, top_k=1)  # get classes
    labels = read_label_file(label_file)  # get labels from label.txt

    for c in classes:
        print("classifying image...")  # debug
        print(f'{labels.get(c.id, c.id)} {c.score:.5f}')  # debug
        if (f'{labels.get(c.id, c.id)}'  == 'lightning' and float(f'{c.score:.5f}') >= 0.3):  # save only images with particles
            print("classified as lightning, saving...")  # debug
            os.rename(image_file, f"{temporary_folder}/particle_{counter}.jpg")  # rename image to particle(number of picture).jpg
            os.replace(f"{temporary_folder}/particle_{counter}.jpg", f"{output_folder}/particle_{counter}.jpg")
            storage += os.path.getsize(f"{output_folder}/particle_{counter}.jpg")  # add image size to used storage
            print("saved image, storage used: {storage}")  # debug
            counter += 1  # increase image counter by one
        else:
            print("classified as a blank image, deleting...")  # debug
            os.remove(image_file)  # delete empty image
    """

    if spike == 0:  # if spike is not detected
        for d in range(10):  # run ten times (delete nine images and save one as a backup)
            delete_counter = (counter - d) - 1  # resovle number of images selected to be deleted
            if d != 9:  # delete first nine images
                os.remove(f"{temporary_folder}/img_{delete_counter}.jpg")  # remove unnecessary images
                print(f"removing image: {delete_counter}")  # debug
                #print(delete_counter)  # debug
            else:  # save last image
                print(f"saving image: {delete_counter}") # debug
                os.replace(f"{temporary_folder}/img_{delete_counter}.jpg", f"{output_folder}/img_{delete_counter}.jpg")  # move image to output folder
                storage += os.path.getsize(f"{output_folder}/img_{delete_counter}.jpg")  # add image size to used storage space

    if spike == 1:  # if spike is detected
        print("saving all images")  # debug
        for d in range(10):  # run ten times (move all images)
            move_counter = (counter - d) - 1  # resovle number of images selected to be dmoved
            os.replace(f"{temporary_folder}/img_{move_counter}.jpg", f"{output_folder}/img_{move_counter}.jpg")  # move image to output folder
            storage += os.path.getsize(f"{output_folder}/img_{move_counter}.jpg")  # add image size to used storage space


    #* reset variables
    spike = 0
    print("=========================================") # debug

    currentTime = datetime.now()  # update current time

print(f"Program ended. All output files are located in {output_folder}")  # debug
time_eplased = currentTime - startTime
storage_used = round(storage / (1024 * 1024), 3)
max_storage_form = round(max_storage / (1024 * 1024), 3)
print(f"Time elapsed: {time_eplased}, storage used: {storage_used}/{max_storage_form}MB")