
#* importing necessary libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
from picamera import PiCamera
from orbit import ISS
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import cv2
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
model_file = base_folder/'lightning.tflite' # set model directory #! particle.tflite is just for testing
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

def move(name, cnt):
    outpath = f"{output_folder}/{name}_{cnt}.h264"  # resolve output path
    os.replace(f"{temporary_folder}/vid_{cnt}.h264", outpath)  # move image to output folder
    return outpath  # return output path so it can be used for size determination

def capture(vid_path, delay):  #! Will need to be converted to mp4 using ffmpeg after we receive the data
    camera.start_recording(vid_path)  #! ffmpeg -framerate 30 -i vid_10000.h264 -c copy vid_1000.mp4
    sleep(delay)
    camera.stop_recording()


#* sense hat setup (enable magnetometer)
sense = SenseHat()
sense.set_imu_config(True, False, False)

#* camera setup (set iamge resolution and frequency)
camera = PiCamera()
camera.resolution = (1296, 972)  # max 4056*3040
camera.framerate = 30

#* define thread functions
def get_data(startTime, endTime, storage_limit, data_file):
    storage = 0  # data.csv file size counter
    counter = 0  # readings counter
    currentTime = datetime.now()  # get current time before loop start
    while (currentTime < endTime and storage < storage_limit):  # run until storage or time runs out
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

def get_images(startTime, endTime, storage_limit, counter, output_folder, temporary_folder, model_file, label_file):
    storage = 0  # image storage counter (size added after image is moved to output folder or if classification fails and images are left in temp folder instead of being deleted)
    currentTime = datetime.now()  # get current time before loop start

    while (currentTime < endTime and storage < storage_limit):  # run until storage or time runs out
        if counter % 10 == 0:  # save every 10th video regardless the classification
            print(f"Started recording video: {counter}")  # debug
            vid_path = f"{output_folder}/vid_{counter}.h264"  # set video path to output folder
            capture(vid_path, 30)  # capture 30 second video
            storage += os.path.getsize(vid_path)  # add video size to storage counter
            print(f"Finished recording video {counter}, used storage: {storage}")  # debug

        else:
            print(f"Started recording video: {counter}")  # debug
            vid_path = f"{temporary_folder}/vid_{counter}.h264"  # set video path to temporary folder
            capture(vid_path, 10)  # capture 10 second video
            print(f"Finished recording video {counter}")  # debug

            try:  # attempt to create array of individual frames form video and classify them
                video = cv2.VideoCapture(vid_path)  # read video from file
                if not video.isOpened():  # check if the video was successfully opened
                    print(f"Error: Could not open file {vid_path}")  # debug
                    exit()

                captured = False  # set default capture indicator to false
                print("Processing video...")  # debug
                while True:  # run until the end of the video
                    success, frame = video.read()  # read frame from the video
                    if not success:  # check if the video has ended
                        break  # end loop

                    interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
                    interpreter.allocate_tensors()  # set up TPU
                    size = common.input_size(interpreter)  # get preffered input image size

                    #* Convert frame to coral-friendly format
                    #?print("converting frame to coral-usable format")  # debug
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # comnvert to RGB
                    frame = cv2.resize(frame, size)  # resize to match the input size of coral model
                    frame = frame.astype('float32') / 255.0  # convert to float in range from 0.0 - 1.0

                    #* Classify frame
                    #?print("classifing frame")  # debug
                    labels = read_label_file(label_file)  # get labels from label.txt
                    common.set_input(interpreter, frame)  # load model and image to TPU
                    interpreter.invoke()  # invoke interpreter
                    
                    classes = classify.get_classes(interpreter, top_k=1)  # get classes

                    for c in classes:  # get score of all classes
                        print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')
                        if(f'{labels.get(c.id, c.id)}'  == 'lightning' and float(f'{c.score:.5f}') >= 0.3):  # if classified as lightning with accuracy higher than 0.3
                            captured = True  # will be set true if at least one of the frames contains lightning
                            print("Lightning detected")  # debug
                    
                    if captured:  # if at least one of the frames contains lightning its not necessary to classify other frames
                        break  # end loop

                video.release()  # close the video

                if captured:  # move video to output directory if at least one of frames classified as lightning
                    out_path = move("lightning", counter)  # move video to output directory and get its path
                    storage += os.path.getsize(out_path)  # add image size to storage counter
                    print(f"Video {counter} classified as lightning, moved to output directory, used storage: {storage}")  # debug

                else:  # delete video if classified as empty
                    print(f"Video {counter} classified as empty, deleting")  # debug
                    os.remove(vid_path)  # delete video

            except:
                e = sys.exc_info()  # get error message
                print(f"Failed Classify video {counter}")  # print error
                print("  Error: {}".format( e))  # print error details

        currentTime = datetime.now()  # update time
        counter += 1  # increment counter

    # debug at the end of thread
    print("#------------------------------------------------------------------------------------------------------#")
    print(f"Image thread exited, storage used: {round(storage/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB, time elapsed: {datetime.now() - startTime}")
    print("#------------------------------------------------------------------------------------------------------#")

#* initialization
create_csv(data_file)  # create data.csv file
print("starting threads")  # debug
# define two threads (one for image collection, and one for sensor reading)
t1 = threading.Thread(target = get_data, args = [startTime, endTime, data_storage_limit, data_file])
t2 = threading.Thread(target = get_images, args = [startTime, endTime, image_storage_limit, 10000, output_folder, temporary_folder, model_file, label_file])

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