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
endTime = startTime + timedelta(minutes=9, seconds=15)  # run program for 9 minutes

base_folder = Path(__file__).parent.resolve()  # determine working directory
output_folder = base_folder/'output'  # set output folder path
temporary_folder = base_folder/'temp'  # set temporary folder path
data_file = output_folder/'data.txt'  # set data.csv path
model_file = base_folder/'viewtype.tflite' # set model path
label_file = base_folder/'viewtype_labels.txt' # set label file path

img_counter = 1000  # image counter (start from 1000 for better naming scheme)
img_saved = 0  # number of saved images
img_limit = 40  # max number of images
storage_limit = 250000000 # image storage limit
storage_img = 0  # used image storage
storage_txt = 0  # used text storage

# camera resolution (max 4056*3040 -> crashes (out of resources))
camera_width = 2028
camera_height = 1520
focal_lenght = 7     #?
sensor_width = 3.76  #?

#* create output and temporary directories if they don't exist
if not os.path.exists(temporary_folder):
    print(f"Creating temporary directory in: {temporary_folder}")  # debug
    os.mkdir(temporary_folder)

if not os.path.exists(output_folder):
    os.mkdir(output_folder)
    print(f"Creating output directory in: {output_folder}")  # debug

#* define functions
def average(list):
    return sum(list) / len(list)

def write_to_txt(filename, data):
    with open(filename, 'a') as f:
        f.write("{:.4f}".format(data) + '\n')
        print("Written data to txt file")

def img_save(counter):
    print("Saving images...")
    size = 0
    for i in range(2):  # loop over last images
        id = counter - (i + 1)  # resolve image number
        path = f"{output_folder}/img_{id}.jpg"  # resolve image path
        os.replace(f"{temporary_folder}/img_{id}.jpg", path)  # move image to output folder
        size += os.path.getsize(path)  # add image size to counter
        print(f"saving to: {path}")  # debug

    return size  # return size of all moved file so it can be added to used storage

def img_delete(counter):
    print("Deleting images...")
    for i in range(2):  # loop over last images
        id = counter - (i + 1)  # resolve image number
        path = f"{temporary_folder}/img_{id}.jpg"  # resolve image path
        os.remove(path)  # delete image
        print(f"Removing: {path}")  # debug

def convert(angle):  # convert coordinates to degrees
    sign, degrees, minutes, seconds = angle.signed_dms()
    exif_angle = f'{degrees:.0f}/1,{minutes:.0f}/1,{seconds*10:.0f}/10'
    return sign < 0, exif_angle

def convert_to_cv(image_1, image_2):  # convert image to opencv format
    image_1_cv = cv2.imread(image_1, 0)
    image_2_cv = cv2.imread(image_2, 0)
    return image_1_cv, image_2_cv

def get_time(image):
    with open(image, 'rb') as image_file:
        img = Image(image_file)
        time_str = img.get("datetime_original")
        time = datetime.strptime(time_str, '%Y:%m:%d %H:%M:%S')
    return time

def get_time_difference(image_1, image_2):
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

def capture(counter):
        global img_counter
        img_counter  += 1  # increment image counter
        
        coords = ISS.coordinates()  # get current coordinates
        south, exif_latitude = convert(coords.latitude)  # convert ccords to EXIF-friendly format
        west, exif_longitude = convert(coords.longitude)
        altitude = Fraction(str(round(coords.elevation.m)))

        print(str((altitude.numerator, altitude.denominator)))

        # Set image EXIF data
        camera.exif_tags['DateTimeOriginal'] = str(datetime.now().strftime("%Y:%m:%d, %H:%M:%S"))
        camera.exif_tags['GPS.GPSLatitude'] = exif_latitude
        camera.exif_tags['GPS.GPSLatitudeRef'] = "S" if south else "N"
        camera.exif_tags['GPS.GPSLongitude'] = exif_longitude
        camera.exif_tags['GPS.GPSLongitudeRef'] = "W" if west else "E"
        camera.exif_tags['GPS.GPSAltitude'] = str(altitude)

        path = f"{temporary_folder}/img_{counter}.jpg"

        camera.capture(path)  # capture camera and save the image
        print(f"{counter} / {img_saved}")  # debug
        return path

def calculateGSD(elevation, sensor_size, focal_lenght, image_width):
    gsd = (elevation * sensor_size) / (focal_lenght * image_width)
    return gsd

#* camera setup (set iamge resolution)
camera = PiCamera()
camera.resolution = (camera_width, camera_height)

#* attempt to initialize coral TPU
coral = False
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
while(datetime.now() < endTime and (storage_img + storage_txt) <= storage_limit):  # run until storage is full or time expires
    print("Capturing images...")

    img1 = capture(img_counter)
    sleep(5)

    img2 = capture(img_counter)
    sleep(5)
    
    if coral:  # Classify first image only to save time. The images should not change drastically during one iteration
        print("Classifying images...")
        classified = True  # save or delete images based on classifications
        #! change -> True for testing purposes

        #* Open image and convert it to coral-friendly format
        image = PILImage.open(f"{temporary_folder}/img_{img_counter - 1}.jpg").convert('RGB').resize(size, PILImage.ANTIALIAS)  # open image

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
            #TODO: calculate GSD based on current altitude
            gsd = calculateGSD(ISS.coordinates().elevation.m, sensor_width, focal_lenght, camera_width)
            print(gsd)

            time_difference = get_time_difference(img1, img2) # Get time difference between images
            image_1_cv, image_2_cv = convert_to_cv(img1, img2) # Create OpenCV image objects
            keypoints_1, keypoints_2, descriptors_1, descriptors_2 = calculate_features(image_1_cv, image_2_cv, 1000) # Get keypoints and descriptors
            matches = calculate_matches(descriptors_1, descriptors_2) # Match descriptors
            coordinates_1, coordinates_2 = find_matching_coordinates(keypoints_1, keypoints_2, matches)

            distance = calculate_mean_distance(coordinates_1, coordinates_2)
            #TODO: calculate speed

            print(f"Time difference: {time_difference}")
            print(f"Distance: {distance}")
        except:
            e = sys.exc_info()  # get error message
            print(f"Failed to process images")  # print error
            print("  Error: {}".format( e))  # print error details

    if (coral and classified and (img_saved + 2) <= img_limit) or (not coral and (img_saved + 2) <= img_limit):
        storage_img += img_save(img_counter)  # save images
        img_saved += 2
        print(f"Used storage: {round((storage_img)/(1024*1024), 2)}MB")
    else:
        img_delete(img_counter)  # delete images

    sleep(30)

#* final output message
print("#------------------------------------------------------------------------------------------------------#")
print(f"Program ended. All output files are located in {output_folder}")  # debug
print(f"Time elapsed: {datetime.now() - startTime}")
print(f"Storage used: {round((storage_img + storage_txt)/(1024*1024), 2)}/{round(storage_limit/(1024*1024), 2)}MB,")
print(f"Saved images: {img_saved}")
print("#------------------------------------------------------------------------------------------------------#")