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
from PIL import Image as PILImage
from orbit import ISS
from skyfield.api import load
import cv2
import math
from fractions import Fraction

#* define variables
startTime = datetime.now()  # get program start time
endTime = startTime + timedelta(minutes=9, seconds=35)  # run program for 9 minutes
failsafeTime = endTime - timedelta(minutes=2)  # time after which it is safe to take images regardless of classification

base_folder = Path(__file__).parent.resolve()  # determine working directory
data_file = base_folder/'result.txt'  # set result.txt path
backup_file = base_folder/'backup.txt'  # set path to backup file (current speed is saved periodically)
model_file = base_folder/'viewtype.tflite' # set model path
label_file = base_folder/'viewtype_labels.txt' # set label file path

img_counter = 1000  # image counter (start from 1000 for better naming scheme)
img_saved = 0  # number of saved images
img_limit = 40  # max number of images
storage_limit = 250000000 # storage limit
storage = 0  # used storage

# camera resolution (max 4056*3040 -> crashes (out of resources))
camera_width = 3042
camera_height = 2280
focal_lenght = 5
sensor_width = 6.287

speed = []  # array of speed values to be averaged

#* define functions
def average(list):
    return sum(list) / len(list)

def write_to_txt(filename, data):
    if len(data) > 0:
        try:
            print(f"Number of values in data array: {len(data)}")
            speed = average(data)  # calculate average speed
            with open(filename, 'a') as f:   # write average speed to file
                f.write("{:.4f}".format(speed) + '\n')
                print("Written data to txt file")

            return os.path.getsize(filename)
        except:
            e = sys.exc_info()  # get error message
            print(f"Failed to write to txt file")  # print error
            print("  Error: {}".format( e))  # print error details
    else:
        print("No data to be saved!")

    return 0

def img_delete(images):
    print("Deleting images...")
    for img in images:  # get paths from array
        os.remove(img)  # delete image
        print(f"Removing: {img}")  # debug

def convert(angle):  # convert coordinates to degrees
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def capture(counter):
        global img_counter
        img_counter  += 1  # increment image counter

        coords = ISS.coordinates()  # get current coordinates
        south, exif_latitude = convert(coords.latitude)  # convert coords to EXIF-friendly format
        west, exif_longitude = convert(coords.longitude)
        altitude = Fraction(str(round(coords.elevation.m)))

        # Set image EXIF data
        camera.exif_tags['DateTimeOriginal'] = str(datetime.now().strftime("%Y:%m:%d, %H:%M:%S"))
        camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
        camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
        camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
        camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"
        camera.exif_tags['GPS.GPSAltitude'] = str(f"{altitude.numerator}/{altitude.denominator}")

        path = f"{base_folder}/img_{counter}.jpg"  # resolve image path

        camera.capture(path)  # capture camera and save the image
        print(f"{counter} / {img_saved}")  # debug
        return path  # return path so it can be appended to an array

def calculateGSD(elevation, sensor_size, focal_lenght, image_width):  # calculate GPS based on current altitude
    gsd = (elevation * sensor_size) / (focal_lenght * image_width) * 100
    return gsd

#* functions from https://projects.raspberrypi.org/en/projects/astropi-iss-speed
def convert_to_cv(image_1, image_2):  # convert image to opencv format
    image_1_cv = cv2.imread(image_1, 0)
    image_2_cv = cv2.imread(image_2, 0)
    return image_1_cv, image_2_cv

def get_time(image):  # get time of image creation from exif
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')  # format time
    return time

def get_time_difference(image_1, image_2):  # calculate time differnce between images
    time_1 = get_time(image_1)
    time_2 = get_time(image_2)
    time_difference = time_2 - time_1
    return time_difference.seconds

def calculate_features(image_1, image_2, feature_number):  # calculate common features
    orb = cv2.ORB_create(nfeatures = feature_number)
    keypoints_1, descriptors_1 = orb.detectAndCompute(image_1, None)
    keypoints_2, descriptors_2 = orb.detectAndCompute(image_2, None)
    return keypoints_1, keypoints_2, descriptors_1, descriptors_2

def calculate_matches(descriptors_1, descriptors_2):  # get matching features
    brute_force = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = brute_force.match(descriptors_1, descriptors_2)
    matches = sorted(matches, key=lambda x: x.distance)
    return matches

def find_matching_coordinates(keypoints_1, keypoints_2, matches):  # get coordinates from image features
    coordinates_1 = []
    coordinates_2 = []
    for match in matches:
        image_1_idx = match.queryIdx
        image_2_idx = match.trainIdx
        (x1,y1) = keypoints_1[image_1_idx].pt
        (x2,y2) = keypoints_2[image_2_idx].pt
        coordinates_1.append((x1,y1))
        coordinates_2.append((x2,y2))
    return coordinates_1, coordinates_2

def calculate_mean_distance(coordinates_1, coordinates_2):  # calculate distance between two coordinates
    all_distances = 0
    merged_coordinates = list(zip(coordinates_1, coordinates_2))
    for coordinate in merged_coordinates:
        x_difference = coordinate[0][0] - coordinate[1][0]
        y_difference = coordinate[0][1] - coordinate[1][1]
        distance = math.hypot(x_difference, y_difference)
        all_distances = all_distances + distance
    return all_distances / len(merged_coordinates)

def calculate_speed_in_kmps(feature_distance, GSD, time_difference):  # calculate speed usind the distance, GSD and time difference
    distance = feature_distance * GSD / 100000
    speed = distance / time_difference
    return speed

#* camera setup (set iamge resolution)
camera = PiCamera()
camera.resolution = (camera_width, camera_height)

#* attempt to initialize coral TPU
coral = False  # coral setup indicator (True if coral initialized correctly)
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
    print(f"Failed to initialize coral TPU")  # print error
    print("  Error: {}".format( e))  # print error details

#* main loop
while(datetime.now() < endTime and (storage) <= storage_limit):  # run until storage is full or time expires
    print("Capturing images...")
    images = [] # array of paths to two last images
    for i in range(2):  # add image paths to array
        images.append(capture(img_counter))
        sleep(5)

    if coral:  # Classify first image only to save time. The images should not change drastically during one iteration
        print("Classifying images...")
        classified = True  # save or delete images based on classifications
        #! change -> True for testing purposes

        #* Open first image and convert it to coral-friendly format -> no need to classify both images since they will not change significantly
        image = PILImage.open(images[0]).convert('RGB').resize(size, PILImage.ANTIALIAS)  # open image

        #* Classify image
        common.set_input(interpreter, image)  # load interpreter and image to TPU
        interpreter.invoke()  # invoke interpreter

        classes = classify.get_classes(interpreter, top_k=1)  # get classes

        for c in classes:  # get score of all classes
            print(f"class ID: {c.id} class label: {labels.get(c.id, c.id)} image score: {float(f'{c.score:.5f}')}")  # debug
            if(f'{labels.get(c.id, c.id)}'  == 'usable' and float(f'{c.score:.5f}') >= 0.8):  # if classified as usable with accuracy higher than 0.8
                classified = True  # mark image as usable for distance calculation

    if (not coral) or (coral and classified):
        try:
            print("Processing images...")
            gsd = calculateGSD(ISS.coordinates().elevation.m, sensor_width, focal_lenght, camera_width)  # recalculate GSD for every set of images
            print(f"GSD: {gsd}")

            time_difference = get_time_difference(images[0], images[1]) # Get time difference between images
            image_1_cv, image_2_cv = convert_to_cv(images[0], images[1]) # Create OpenCV image objects
            keypoints_1, keypoints_2, descriptors_1, descriptors_2 = calculate_features(image_1_cv, image_2_cv, 1000) # Get keypoints and descriptors
            matches = calculate_matches(descriptors_1, descriptors_2) # Match descriptors
            
            if len(matches) == 0:  # skip loop iteration if no matches were found
                print("No matches found")
                continue

            coordinates_1, coordinates_2 = find_matching_coordinates(keypoints_1, keypoints_2, matches)
            distance = calculate_mean_distance(coordinates_1, coordinates_2)
            current_speed = round(calculate_speed_in_kmps(distance, gsd, time_difference), 5)  # calculate current speed
            
            print(f"Distance: {distance}")
            print(f"Current Speed: {current_speed}")

            if storage != 0:  # ignore first iteration
                storage -= os.path.getsize(backup_file)  # substract old backup file size

            storage += write_to_txt(backup_file, [current_speed])  # add current size of backup file
            
            speed.append(current_speed)  # add current speed to array

        except:
            e = sys.exc_info()  # get error message
            print(f"Failed to process images")  # print error
            print("  Error: {}".format( e))  # print error details

    # When coral is active, save only classified images
    # When coral is inactive, save all images
    # When time is almost up, save all images regardless of coral and classification
    # Always check number of saved images
    if (coral and classified and (img_saved + 2) <= img_limit) or (not coral and (img_saved + 2) <= img_limit) or (datetime.now() >= failsafeTime and img_saved <= 10):
        for i in range(2):  # add size of last set of images to storage and increment image counter
            storage += os.path.getsize(images[i - 1])
            img_saved += 1
        print(f"Used storage: {round((storage)/(1024*1024), 2)}MB")
    else:
        img_delete(images)  # delete images

    sleep(10)

#* write final speed to txt file
storage += write_to_txt(data_file, speed)

#* final output message
print("#-----------------------------------------#")
print(f"Time elapsed: {datetime.now() - startTime}")
print(f"Storage used: {round((storage)/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB,")
print(f"Saved images: {img_saved}")
print("#-----------------------------------------#")