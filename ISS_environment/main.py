# import all required libraries
import csv
from sense_hat import SenseHat
from pathlib import Path
from datetime import datetime, timedelta
from time import sleep
import RPi.GPIO as GPIO

startTime = datetime.now()  # get program start time

blue = (0, 0, 255)  # colour settings for LED matrix
black = (0, 0, 0)

GPIO.setmode(GPIO.BCM)  # set GPIO mapping scheme
GPIO.setup(12, GPIO.IN)  # set pin 12 as input

n = 0  # loop counter
i = 0  # data readings counter


def create_csv(data_file):  # creating csv file
    with open(data_file, 'w') as f:  # create csv file and set up logging
        writer = csv.writer(f)  # set up writer
        header = ("RowNum", " Date/time", " Temperature", " Humidity", " Pressure", " Light",  " Motion")  # write first line (data type)
        writer.writerow(header)  # write header to csv file
        print("Creating data.csv file...")  # debug


def add_csv_data(data_file, data):  # writing data to csv file
    with open(data_file, 'a') as f:  # open csv file
        writer = csv.writer(f)  # set up writer
        writer.writerow(data)  # write data row to csv file
        print("Writing data to .csv file...")  # debug


def read_data(data_file):  # data collection
    global i  # readings counter as a global variable
    i = i + 1  # increase readings counter by one
    t = sense.get_temperature()  # get temperature data from sense hat
    h = sense.get_humidity()  # get humidity data from sense hat
    p = sense.get_pressure()  # get pressure data from sense hat
    l = sense.color.clear
    row = (i, datetime.now(), t, h, p, l, pir)  # assign data to row
    print("sensing data...")  # debug
    add_csv_data(data_file, row)  # write row to csv file


base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder / 'data.csv'  # set data.csv file name and location
sense = SenseHat()  # set up sense hat
sense.color.gain = 60  # set color sensor gain
create_csv(data_file)  # create data.csv file
print("program running...")  # debug

# loop start
currentTime = datetime.now()  # get time before loop start
while currentTime < startTime + timedelta(minutes=175):  # run for 175 minutes (3 hours - 5 minutes => 175 minutes)
    n = n + 1  # increase loop counter by one
    pir = GPIO.input(12)  # define pin 12 as pir and read it's state
    print("loop count: ", n)  # debug

    if n % 60 == 0:  # run every 60 loops
        read_data(data_file)  # collect data from all sensors
        temp = sense.get_temperature()  # get temperature data from sense hat(used to display temperature to LED matrix)
        sense.show_message("Hello, temperature is %d C" % temp, text_colour=blue, back_colour=black)  # print temperature to LED matrix

    if pir == 1:  # run if motion is detected
        print("Motion detected! Collecting data more frequently...")  # debug
        read_data(data_file)  # collect data from all sensors
        sense.show_message("Motion detected!")  # print "Motion detected!" to LED matrix
        sleep(1)  # pause for one second
        for k in range(9):  # run 9 times (10 with data collection above)
            read_data(data_file)  # collect data from all sensors
            sleep(1)  # pause for one second

    currentTime = datetime.now()  # update current time
    sleep(1)  # pause one second before next cycle
print("Program ended")  # debug
