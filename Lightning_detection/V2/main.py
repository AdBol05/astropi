
#* importing necessary libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
from orbit import ISS
from PIL import Image
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import os
import sys
import threading, queue

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=175)  # run program for 175 minutes (5min headroom from the 3hr limit)
data_storage_limit = 3000000   # Max data.csv file size is 3MB
image_storage_limit = 2990000000  # Max combined image size is 2.99GB

#* set up paths (resolve all paths and create file structure)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set tempoprary folder path
data_file = output_folder/'data.csv'  # set data.csv path
model_file = ''  #? base_folder/'model.tflite' # set model directory
label_file = base_folder/'labels.txt' # set label file directory

#* create output and temporary directories if they don't exist
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
        header = ("index", "date", "coords", "magnetometer_X", "magnetometer_Y", "magnetometer_Z")  # write first line (data type)
        csv.writer(f).writerow(header)  # write header to csv file

def read_data(data_file, count):  # data collection
    coords = ISS.coordinates()  # get position from timescale
    mag = sense.get_compass_raw()  # get magnetometer data
    data = (count, datetime.now(), coords, mag.get("x"), mag.get("y"), mag.get("z"))  # assign data to row

    with open(data_file, 'a', buffering=1) as f:  # open csv file
        csv.writer(f).writerow(data)  # write data row to scv file
        print("Written data to .csv file")  # 175debug

def angle2exif(angle):  # convert raw coords angle to EXIF friendly format
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def capture(cam, count):  # take a picture and add metadata to it (cam -> camera, cnt -> image counter)
    coords = ISS.coordinates()  # get current ISS coordinates
    south, exif_lat = angle2exif(coords.latitude)  # convert coordinates to exif friendly format
    west, exif_long = angle2exif(coords.longitude)

    # add coordinates to image metadata
    cam.exif_tags['GPS.GPSLatitude'] = exif_lat
    cam.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
    cam.exif_tags['GPS.GPSLongitude'] = exif_long
    cam.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"

    cam.capture(f"{temporary_folder}/img_{count}.jpg")  # capture camera and save the image

def move(name, cnt):
    os.replace(f"{temporary_folder}/img_{cnt}.jpg", f"{output_folder}/{name}_{cnt}.jpg")  # move image to output folder


#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (set iamge resolution and zoom)
camera = PiCamera()
camera.resolution = (1296, 972)  # max 4056*3040
#TODO: fix image crop camera.zoom = (0.20, 0.155, 0.80, 0.845)

#* define thread functions
def get_data(startTime, endTime, storage_limit, data_file):
    storage = 0
    counter = 0
    currentTime = datetime.now()  # get current time before loop start
    while (currentTime < endTime and storage < storage_limit):
        if counter != 0:  # ignore first iteration
            storage -= os.path.getsize(data_file)  # subtract old data.csv file size from storage counter

        read_data(data_file, counter)  # get data from all sensors and write to output file
        storage += os.path.getsize(data_file)  # add new data.csv file size to storage counter
        currentTime = datetime.now()  # update time
        counter += 1
        print(f"Read data from sensors, used data storage: {storage}")
        sleep(1)

    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Data collection thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

def get_images(startTime, endTime, storage_limit, camera, counter, sequence, output_folder, temporary_folder, model_file, label_file):
    storage = 0
    #spike = 0  #? Probably useless (spike will most likely not be detected from magnetometer readings)
    currentTime = datetime.now()  # get current time before loop start

    #* attempt to initialize coral TPU
    try:
        interpreter = make_interpreter(f"{model_file}")  # assign model to interpreter
        interpreter.allocate_tensors()  # set up TPU
        size = common.input_size(interpreter)  # resize image
    except:
        e = sys.exc_info()  # get error message
        print("Failed to initialize coral TPU")  # print error
        print("  Error: {}".format( e))  # print error details

    while (currentTime < endTime and storage < storage_limit):
        for k in range(sequence):
            capture(camera, counter)
            counter += 1  # add one to image counter
            print(f"Took image: {counter}, used image storage: {storage}")

        for d in range(sequence):  # run a couple times (save the only last image)
            delete_counter = (counter - d) - 1  # resovle number of images selected to be deleted

            if d != (sequence-1):  # Classify images
                print(f"Classifying image {counter}")
                try:  #! Will fail becuase there is no model or label file available yet!
                    image_file =  f'{temporary_folder}/img_{counter}.jpg'  # set image directory
                    image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
                    common.set_input(interpreter, image)  # set input
                    interpreter.invoke()  # invoke interpreter
                    classes = classify.get_classes(interpreter, top_k=1)  # get classes
                    labels = read_label_file(label_file)  # get labels from label.txt

                    for c in classes:
                        if(f'{labels.get(c.id, c.id)}'  == 'lightning' and float(f'{c.score:.5f}') >= 0.3):  # if classified as lightning with accuracy higher than 0.3
                            print(f"Image {counter} classified as lightning, moving to output folder")
                            move_counter = (counter - d) - 1  # resovle number of images selected to be dmoved
                            move("lightning", move_counter)  #move images classified as lightning to output folder
                            storage += os.path.getsize(f"{output_folder}/lightning_{move_counter}.jpg")  # add image size to used storage space
                        else:
                            print(f"Image {counter} classified as empty, deleting")
                            os.remove(f"{temporary_folder}/img_{delete_counter}.jpg")  # remove unnecessary images
                except:
                    e = sys.exc_info()  # get error message
                    storage += os.path.getsize(f"{temporary_folder}/img_{delete_counter}.jpg")  # add image size to storage counter
                    print(f"Failed to classify image {delete_counter} Leaving image in temp and adding it to storage counter")  # print error
                    print("  Error: {}".format( e))  # print error details

            else:  # save first image
                print(f"#saving image: {delete_counter}") # debug
                move("img", delete_counter)  # move image to output folder
                storage += os.path.getsize(f"{output_folder}/img_{delete_counter}.jpg")  # add image size to used storage space

        currentTime = datetime.now()  # update time

    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Image thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

#* initialization
create_csv(data_file)  # create data.csv file
print("starting threads")
# define two threads (one for image collection, and one for sensor reading)
t1 = threading.Thread(target = get_data, args = [startTime, endTime, data_storage_limit, data_file])
t2 = threading.Thread(target = get_images, args = [startTime, endTime, image_storage_limit , camera, 10000, 10, output_folder, temporary_folder, model_file, label_file])

#* start threads
t1.start()
t2.start()

#* wait for threads to finish
t1.join()
t2.join()

print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print("If temp folder is not empty, image classification probably failed. Check program output for error messages.")
print("#------------------------------------------------------------------------------------------------------#")