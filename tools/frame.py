import cv2
import os

dark_file = "./dark.h264"
lightning_file = "./lightning.h264"
dark_folder = "./dark"
lightning_folder = "./lightning"
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file


print("Processing please wait...")

def parse(input_file, output_folder):
    #* parse videos to extract frames
    video1 = cv2.VideoCapture(lightning_file)
    # Check if video was opened successfully
    if not video1.isOpened():
        raise Exception("Could not open video")

    # Read the video frame-by-frame
    i = 10000
    while video1.isOpened():
        success, frame = video1.read()
        if not success:
            break
        print(frame)
        i += 1
    # Release the video
    video1.release()

parse(dark_file, dark_folder)
parse(lightning_file, lightning_folder)