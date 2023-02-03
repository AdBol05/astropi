import csv
from sense_hat import SenseHat
from orbit import ISS
from pathlib import Path
from time import sleep
from datetime import datetime, timedelta
import os
import threading, queue
import sys

startTime = datetime.now()
endTime = startTime + timedelta(minutes=175)
sense = SenseHat()

path = os.path.dirname(os.path.realpath(__file__))
dataPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data") #create folder dedicated to generated data
print( 'PATH: {}'.format( dataPath)) #debug, show data path
if not os.path.exists( dataPath):
    os.mkdir( dataPath) #create folder if not there already
dataFile = os.path.join(dataPath, "data")


def csvWriter(file, id):
    try:
        with open("{}{}.csv".format(str(file),str(id)), "w") as f:
            writer = csv.writer(f)
            writer.writerow(["index", "time", "compass", "compassRawX", "compassRawY", "compassRawZ", "latitude", "longitude", "elevation"])
            i = 0
            while datetime.now() < endTime:
                task = csvWrite.get()
                writer.writerow([i, task[0], task[1], task[2].get("x"), task[2].get("y"), task[2].get("z"), task[3].latitude, task[3].longitude, task[3].elevation])
    except:
        e = sys.exc_info()#[0]
        print('Writer thread closed due to exception')
        print('  E: {}'.format( e))



csvWrite = queue.Queue()

for i in range(0,2):
    threading.Thread(target = csvWriter, args = [dataFile, i]).start()

currentTime = datetime.now()

while currentTime<endTime:
    compass = sense.get_compass()
    compassRaw = sense.get_compass_raw()
    currentTime = datetime.now()
    csvWrite.put([currentTime, compass, compassRaw, ISS.coordinates()])
    sleep(0)
print("finished")