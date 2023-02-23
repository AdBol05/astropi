import csv
from sense_hat import SenseHat
from pathlib import Path
from time import sleep
from datetime import datetime, timedelta
from orbit import ISS
import os
import threading, queue
import sys

startTime = datetime.now() #time at which script starts
print(startTime) #print time of start
endTime = startTime + timedelta(minutes=177) #time at which script should end (3 minutes of headroom)
sense = SenseHat() #create instance of sensehat 

path = os.path.dirname(os.path.realpath(__file__)) #get path to script
dataPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data") #create folder dedicated to generated data
print( 'PATH: {}'.format( dataPath)) #debug, show data path
if not os.path.exists( dataPath):
    os.mkdir( dataPath) #create folder if not there already
dataFile = os.path.join(dataPath, "data") #path to generic datafile without index
positionFile = os.path.join(dataPath, "position.csv") #path to positon log file

def csvWriter(file, id):
    try:
        with open("{}{}.csv".format(str(file),str(id)), "w") as f: #create and open indexed datafile
            writer = csv.writer(f) #create csv file writer
            writer.writerow(["index", "time", "compass", "compassRawX", "compassRawY", "compassRawZ"]) #write header to csv for readability
            while datetime.now() < endTime: #repeat until end time
                task = csvWrite.get() #wait for task from queue
                writer.writerow([task[0], task[1], task[2], task[3].get("x"), task[3].get("y"), task[3].get("z")]) #write data into csv
    except:
        e = sys.exc_info() #get exception name
        print('Writer thread {} closed due to exception'.format(id)) #print out the thread where the exception happened
        print('  E: {}'.format(e)) #print out exception and let thread exit by finishing code

def positionWriter(file):
    try:
        with open("{}".format(str(file)), "w") as f: #create and open position log file
            writer = csv.writer(f) #create csv file writer
            writer.writerow(["time", "latitude", "longitude", "altitude"]) #write header to csv for readability
            currentPositionTime = datetime.now() #create a variable storing current time for position writer
            while currentPositionTime < endTime: #repeat until end time
                position = ISS.coordinates() #get approximate position of data fetch
                currentPositionTime = datetime.now() #save time of current loop to variable
                writer.writerow([currentPositionTime, position.latitude.degrees, position.longitude.degrees, position.elevation.m]) #write data to csv file
    except:
        e = sys.exc_info() #get exception name
        print('Position thread closed due to exception') #print out the thread where the exception happened
        print('  E: {}'.format(e)) #print out exception and let thread exit by finishing code




csvWrite = queue.Queue() #create a queue for giving data writer threeads tasks

for i in range(0,2):
    threading.Thread(target = csvWriter, args = [dataFile, i]).start() #create 2 data saving threads with ids 0, 1 pointed at dataFile 

threading.Thread(target = positionWriter, args = [positionFile]).start() #create a position loggging thread

currentTime = datetime.now() #get time of main loop start
i = 0 #main loop counter
try:
    while currentTime<endTime: #run main loop until endTime
        compass = sense.get_compass() #get data from magnetometer
        compassRaw = sense.get_compass_raw() #get data from magnetometer
        currentTime = datetime.now() #get time of data fetch
        csvWrite.put([i, currentTime, compass, compassRaw]) #put magnetometer, time and position data in queue for saving in writer therads
        i += 1 #increment main loop counter
except:
    e = sys.exc_info() #get exception name
    print('Main thread closed due to exception') #print out the thread where the exception happened
    print('  E: {}'.format(e)) #print out exception and let thread exit by finishing code
print("finished") #script end message
print(datetime.now()) #print out script end time