
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
import cv2
import numpy as np
import os
import sys
import threading

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=175)  # run program for 175 minutes (5min headroom from the 3hr limit)
data_storage_limit = 2000000   # Max data.csv file size is 3MB
image_storage_limit = 2990000000  # Max combined image size is 2.99GB

#* set up paths (resolve all paths and create file structure)
base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set tempoprary folder path
data_file = output_folder/'data.csv'  # set data.csv path
model_file = base_folder/'particle.tflite' # set model directory #! particle.tflite is just for testing
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
        #? print("Written data to .csv file")  # debug

def move(name, cnt):
    os.replace(f"{temporary_folder}/vid_{cnt}.h264", f"{output_folder}/{name}_{cnt}.h264")  # move image to output folder


#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (set iamge resolution and zoom)
camera = PiCamera()
camera.resolution = (1296, 972)  # max 4056*3040
camera.framerate = 30
#TODO: fix image crop camera.zoom = (0.20, 0.155, 0.80, 0.845)

#* define thread functions
def get_data(startTime, endTime, storage_limit, data_file):
    storage = 0  # data.csv file size counter
    counter = 0
    currentTime = datetime.now()  # get current time before loop start
    while (currentTime < endTime and storage < storage_limit):
        if counter != 0:  # ignore first iteration
            storage -= os.path.getsize(data_file)  # subtract old data.csv file size from storage counter

        read_data(data_file, counter)  # get data from all sensors and write to output file
        storage += os.path.getsize(data_file)  # add new data.csv file size to storage counter
        currentTime = datetime.now()  # update time
        counter += 1  # increase counter by one
        print(f"Read data from sensors, used data storage: {storage}")  # debug
        sleep(1)  # wait one second

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Data collection thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

def get_images(startTime, endTime, storage_limit, camera, counter, sequence, output_folder, temporary_folder, model_file, label_file):
    storage = 0  # image storage counter (size added after image is moved to output folder or if classification fails and images are left in temp folder instead of being deleted)
    currentTime = datetime.now()  # get current time before loop start

    #* attempt to initialize coral TPU
    try:
        interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
        interpreter.allocate_tensors()  # set up TPU
        size = common.input_size(interpreter)  # get preffered input image size
    except:
        e = sys.exc_info()  # get error message
        print("Failed to initialize coral TPU")  # print error
        print("  Error: {}".format( e))  # print error details

    while (currentTime < endTime and storage < storage_limit):
        
        print(f"Started recording video {counter}")
        vid_path = f"{temporary_folder}/vid_{counter}.h264"  #! Will need to be converted to mp4 using ffmpeg after we receive the data
        camera.start_recording(vid_path, format="h264")  #! ffmpeg -framerate 30 -i vid_10000.h264 -c copy vid_1000.mp4 
        sleep(10)
        camera.stop_recording()

        #storage += os.path.getsize(vid_path)
        print(f"Finished recording video {counter}, used storage: {storage}")

        try:  # attempt to create array of individual frames form video
            video = cv2.VideoCapture(vid_path)  # read video from file
            if not video.isOpened():  # check if the video was successfully opened
                print(f"Error: Could not open file {vid_path}")
                exit()

            frames = []  # create array of frames
            while True:
                success, frame = video.read()  # read frame from the video
                if not success:  # check if the video has ended
                    break
                frames.append(frame)  #! very memory intensive (will most likely overflow)

        except:
            print(f"Failed to create frame array")  # print error
            print("  Error: {}".format( e))  # print error details

        try:  # attempt to calssify image  #! Will fail because there is no tflite model file available yet!
            captured = False
            print(f"Calssifying frames from video: {counter}")
            print(frames)
            for i in frames:
            
                #?----------------------------------------------------------------

                #! This just does not work
                #! How the hell should I do this?
                #?image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)

                print("Attempting to convert frame to coral-friendly format")  # debug
                image = frames[i].convert('RGB').resize(size, Image.ANTIALIAS)
                print(image)  # debug

                common.set_input(interpreter, image)  # load model and image to TPU
                interpreter.invoke()  # invoke interpreter
                
                classes = classify.get_classes(interpreter, top_k=1)  # get classes
                labels = read_label_file(label_file)  # get labels from label.txt
            
                #?----------------------------------------------------------------

                for c in classes:  # get score of all classes
                    if(f'{labels.get(c.id, c.id)}'  == 'lightning' and float(f'{c.score:.5f}') >= 0.3):  # if classified as lightning with accuracy higher than 0.3
                        captured = True  # will be set true if at least one of the frames contains lightning

            if captured:
                print(f"Video {counter} classified as lightning, moving to output directory")
                move("lightning", counter)
                storage += os.path.getsize(vid_path)  # add image size to storage counter
                    
            else:
                print(f"Video {counter} classified as empty, deleting")
                os.remove(vid_path)

        except:  # if something goes wrong, print error message, leave video in temp directory and add its size to storage counter
            e = sys.exc_info()  # get error message
            storage += os.path.getsize(vid_path)  # add image size to storage counter
            print(f"Failed to classify frames from video {counter} Leaving video in temp and adding it to storage counter")  # print error
            print("  Error: {}".format( e))  # print error details
        #! Fails with "TypeError('only integer scalar arrays can be converted to a scalar index')"
        #! What does that even mean?

        captured = False
        frames = []  # reset frame array
        currentTime = datetime.now()  # update time
        counter += 1

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Image thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

#* initialization
create_csv(data_file)  # create data.csv file
print("starting threads")  # debug
# define two threads (one for image collection, and one for sensor reading)
t1 = threading.Thread(target = get_data, args = [startTime, endTime, data_storage_limit, data_file])
t2 = threading.Thread(target = get_images, args = [startTime, endTime, image_storage_limit , camera, 10000, 10, output_folder, temporary_folder, model_file, label_file])

#* start threads
t1.start()
t2.start()

#* wait for threads to finish
t1.join()
t2.join()

#* final output message
print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print("If temp folder is not empty, image classification probably failed. Check program output for error messages.")
print("#------------------------------------------------------------------------------------------------------#")