import cv2
import os
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
from PIL import Image

dark_file = "./dark.h264"
lightning_file = "./lightning.h264"
dark_folder = "./dark"
lightning_folder = "./lightning"
model_file = './lightning.tflite' # set model directory
label_file = './labels.txt' # set label file directory

#* create output and temporary directories if they don't exist
if not os.path.exists(lightning_folder):
    print(f"Creating temporary directory in: {lightning_folder}")
    os.mkdir(lightning_folder)

if not os.path.exists(dark_folder):
    os.mkdir(dark_folder)
    print(f"Creating output directory in: {dark_folder}")

print("Processing please wait...")

#* parse videos to extract frames
video1 = cv2.VideoCapture(lightning_file)
    # Check if video was opened successfully
if not video1.isOpened():
    raise Exception("Could not open video")

# Read the video frame-by-frame
success, frame = video1.read()
#print(frame)
#cv2.imwrite(f"{output_folder}/frame_{i}.jpg", frame)

interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
interpreter.allocate_tensors()  # set up TPU
size = common.input_size(interpreter)  # get preffered input image size
labels = read_label_file(label_file)  # get labels from label.txt

#* Convert frame to coral-friendly format
#?print("converting frame to coral-usable format")  # debug
frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # comnvert to RGB
frame = cv2.resize(frame, size)  # resize to match the input size of coral model
frame = frame.astype('float32') / 255.0  # convert to float in range from 0.0 - 1.0

common.set_input(interpreter, frame)  # load model and image to TPU
interpreter.invoke()  # invoke interpreter
                    
classes = classify.get_classes(interpreter, top_k=1)  # get classes

for c in classes:  # get score of all classes
    print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')

# Release the video
video1.release()

print("================================================")

image_file = './data/lightning/frame_10000.jpg'  # set image directory
image = Image.fromarray(frame, 'RGB').convert('RGB').resize(size, Image.ANTIALIAS)  # open image

common.set_input(interpreter, image)  # load model and image to TPU
interpreter.invoke()  # invoke interpreter
                    
classes = classify.get_classes(interpreter, top_k=1)  # get classes
for c in classes:  # get score of all classes
    print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')
