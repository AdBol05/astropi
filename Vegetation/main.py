#!/usr/bin/env python3

import time
from picamera import PiCamera
#import picamera.array
import threading, queue
import os
from orbit import ISS
#from skyfield.api import load
from pycoral.utils import edgetpu
from pycoral.adapters import common
from pycoral.adapters import classify
from PIL import Image
import numpy
import random
import sys

print('START {}'.format( time.time()))

#initialising globally useful variables
path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data') #create folder dedicated to generated data
print( 'PATH: {}'.format( data_path)) #debug, show data path
if not os.path.exists( data_path):
    os.mkdir( data_path) #create folder if not there already
camera = PiCamera() #initialize camera
RESOLUTION_X = 1312
RESOLUTION_Y = 976
camera.resolution = (RESOLUTION_X,RESOLUTION_Y) #set camera resolution
camera.zoom = (0.20, 0.155, 0.80, 0.845) #crop image to get rid of black space
total_size = 0 #storage taken
mylock = threading.Lock()

def save_image_thread(worker_num):
    try:
        global total_size
        while True: #loop checking for task in queue

            task = save_queue.get() #wait for item in queue
            print( 'sTASK-{}: {}'.format(worker_num, task[0])) #for debugging
            if task[0] == SAVE_TASK:   #save image task
                img = Image.fromarray(task[2]) #create a PIL image from numpy array
                image_path = os.path.join(data_path,'capture{}.png'.format(task[1]))
                img.save(image_path, format = 'png') #compress as png and save into file
                file_size = os.stat(image_path).st_size

                file_coords = open(os.path.join(data_path, 'coord{}.txt'.format(worker_num)), 'a') #open text file specific to thread in append mode
                file_coords.write('c{} T{} ts{} p{}\n'.format(task[1], worker_num, time.time(), task[3])) #append positional data to text file
                file_coords.close() #close text file
                judge_queue.put([JUDGE_TASK, task[1]]) #put judge task on queue with image index

                mylock.acquire()
                try:
                    total_size += file_size #add new file's size to total storage space taken with lock for threading
                    if total_size > 2945000000:
                        stop_queue.put(STOP_TASK) #send stop event for main thread if out of space
                        break
                    #trace_size = total_size #for debugging
                finally:
                    mylock.release()
                #print('{}'.format(trace_size)) #for debugging

            if task[0] == STOP_TASK:  #exit thread task
                break

    except:
        e = sys.exc_info()#[0]
        print('Save thread number {} ended because of an error'.format(worker_num)) #end thread safely in case of exception
        print('  E: {}'.format( e))


def judge_image_thread():
    try:
        global total_size
        lines = open(os.path.join(path, "labels.txt")).readlines() #get individual lines of text from labels file
        pairs = [line.split(' ', maxsplit=1) for line in lines] #split lines into index and label name
        labels = {int(index): label.strip() for index, label in pairs} #create labels from the split lines
        model_file = os.path.join(path, 'mobilenet_v1_1.0_224_l2norm_quant_edgetpu_modified.tflite') #get path to tflite model
        interpreter = edgetpu.make_interpreter(model_file) #create interpreter with model file
        interpreter.allocate_tensors()
        size = common.input_size(interpreter) #get input size of interpreter
        storage_taken = 0 #keeps amount of storage taken up by images
        while True:

            task = judge_queue.get() #get task from queue
            print( 'jTASK: {}'.format(task[0])) #for debugging
            if task[0] == JUDGE_TASK:   #judge image

                image_path = os.path.join(data_path, 'capture{}.png'.format(task[1])) #creates image path string
                image = Image.open(image_path).convert('RGB').resize(size, Image.ANTIALIAS) #gets PIL image from file
                common.set_input(interpreter, image) #sets image as interpreter input
                interpreter.invoke() #invoke interpreter to classify image
                classes = classify.get_classes(interpreter, 1, 0) #get interpreter output
                if 0 != (task[1] % 5) and labels.get(classes[0].id) != "land": #checks first class to see whether it should be kept, keeps every 5th

                    #print(labels.get(classes[0].id)) #for debugging
                    file_size = os.stat(image_path).st_size
                    os.remove(image_path) #deletes image if not satisfactory

                    mylock.acquire()
                    try:
                        total_size -= file_size #reduce total stored size by the size of the file to be deleted with a lock for threading
                    finally:
                        mylock.release()

            if task[0] == STOP_TASK: #check for stop task in this thread's queue
                break #exits thread

    except:
        e = sys.exc_info()#[0]
        print('Judge thread closed due to exception')
        print('  E: {}'.format( e))



#initialising threads and queues for communication
save_queue = queue.Queue(maxsize=20)   #possible states 'save', 'stop'; used in save_image_thread(); maxsize to keep ram usage down in case a thread dies
SAVE_TASK = 'save'

judge_queue = queue.Queue()   #possible states 'judge', 'stop'; used in judge_image_thread()
JUDGE_TASK = 'judge'

stop_queue = queue.Queue() #possible state 'stop'; used to stop main loop when out of storage

STOP_TASK = 'stop'

save_thread_range = range(0, 2) #range of indexes for image saving threads

for i in save_thread_range:
    threading.Thread(target = save_image_thread, args = [i]).start() #create a saving thread for each index

threading.Thread(target = judge_image_thread).start() #create a thread judging images

#loop, sends tasks to threads every 2s (loop_time), keeps cycle count, ends after roughly 10500s (end_time)
try:
    index = 0 #amount of cycles executed
    loop_time = 2 #holds time between cycles in seconds
    perf_counter_current = time.perf_counter() #reads from perf_counter and stores in variable for potential reuse in each cycle
    perf_counter_next = perf_counter_current + loop_time #stores time of next cycle's time
    end_time = perf_counter_current + 10500 #time to end, should be roughly 5 minutes before 3 hour mark for a buffer
    while perf_counter_current < end_time: #loop until time runs out

        perf_counter_current = time.perf_counter() #save perf_counter to local variable for reuse
        if perf_counter_current >= perf_counter_next: #checks if main code should be cycled

            #print(time.time()) #for debugging
            if save_queue.full != True:
                image_buffer = numpy.empty((RESOLUTION_Y, RESOLUTION_X, 3), dtype = numpy.uint8) #creates a numpy array to save an image into
                position = ISS.coordinates() #get ISS location
                camera.capture(image_buffer, format = 'rgb') #saves a raw rgb image into the array
                save_queue.put([SAVE_TASK, index, image_buffer, position]) #puts image array with meta information onto q for png compression in saving thread
                image_buffer = None #gets rid of main thread's reference to the image array
            perf_counter_next = perf_counter_current + loop_time #sets next cycle's time
            index += 1 #increments image index


        if not stop_queue.empty(): #checks for stop signal from storage space check
            if stop_queue.get() == STOP_TASK: #checks for stop signal from storage space check

                break #breaks main loop if storage full


        #print('.', end='',flush=True) #for debugging purposes
        time.sleep(0.05) #might reduce cpu usage without affecting accuracy much
except:
    e = sys.exc_info()#[0]
    print('Closed early due to exception')
    print('  E: {}'.format( e))

for i in save_thread_range:
    save_queue.put([STOP_TASK]) #gives save threads stop signals based on their index range

judge_queue.put([STOP_TASK]) #gives judge thread a stop signal

print('DONE {} Size {}'.format(time.time(), total_size))
