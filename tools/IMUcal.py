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

base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
data_file = output_folder/'data.csv'  # set data.csv path
sense = SenseHat()  # set up sense hat

r = (255, 0, 0)     # red
o = (255, 128, 0)   # orange
y = (255, 255, 0)   # yellow
g = (0, 255, 0)     # green
c = (0, 255, 255)   # cyan
b = (0, 0, 255)     # blue
p = (255, 0, 255)   # purple
n = (255, 128, 128) # pink
w =(255, 255, 255)  # white
k = (0, 0, 0)       # blank

rainbow = [r, o, y, g, c, b, p, n]

if not os.path.exists(output_folder):
    os.mkdir(output_folder)
    print(f"Creating output directory in: {output_folder}")  # debug

#* define functions
def create_csv(data_file):  # creating csv file
    with open(data_file, 'w', buffering=1) as f:  # create csv file and set up logging
        print(f"Creating data.csv file in {data_file}")  # debug
        header = ("index", "X", "Y", "Z")  # write first line (data type)
        csv.writer(f).writerow(header)  # write header to csv file

def read_data(data_file, count):  # data collection
    coords = ISS.coordinates()  # get position from timescale
    acc = sense.get_accelerometer_raw()  # get magnetometer data
    data = (count, round(acc.get("x"), 10), round(acc.get("y"), 10), round(acc.get("z"), 10))  # assign data to row
    print(data)

    with open(data_file, 'a', buffering=1) as f:  # open csv file
        csv.writer(f).writerow(data)  # write data row to scv file


#* main
create_csv(data_file)
count = 0  # number of iterations
while (count < 10000):
    read_data(data_file, count)
    count += 1

    if count % 10 == 0:
        sense.clear()
        for y in range(8):
            colour = rainbow[y]
            for x in range(8):
                sense.set_pixel(x, y, colour)
        
        rainbow = [rainbow[-1]] + rainbow[:-1]


    sleep(0.01)