
#TODO:create and test coral TPU model
from pathlib import Path
from orbit import ISS
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import cv2




base_folder = Path(__file__).parent.resolve()  # determine working directory
model_file = base_folder/'lightning.tflite' # set model directory
label_file = base_folder/'labels.txt' # set label file directory
dark_image = base_folder/'empty.jpg'
lightning_image = base_folder/'lightning.jpg'
vid_path = base_folder/'lightning.h264'

"""
interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
interpreter.allocate_tensors()  # set up TPU
size = common.input_size(interpreter)  # get preffered input image size
labels = read_label_file(label_file)  # get labels from label.txt
    
image = Image.open(dark_image).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
common.set_input(interpreter, image)  # load model and image to TPU
interpreter.invoke()  # invoke interpreter

classes = classify.get_classes(interpreter, top_k=1)  # get classes

for c in classes:  # get score of all classes
    print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')

#?coral(model_file, label_file, dark_image)
#?coral(model_file, label_file, lightning_image)
"""

video = cv2.VideoCapture(vid_path)  # read video from file
if not video.isOpened():  # check if the video was successfully opened
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
    labels = read_label_file(label_file)  # get labels from label.txt

    #* Convert frame to coral-friendly format
    #?print("converting frame to coral-usable format")  # debug
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # comnvert to RGB
    frame = cv2.resize(frame, size)  # resize to match the input size of coral model
    frame = frame.astype('float32') / 255.0  # convert to float in range from 0.0 - 1.0

    #* Classify frame
    #?print("classifing frame")  # debug
    common.set_input(interpreter, frame)  # load model and image to TPU
    interpreter.invoke()  # invoke interpreter
                    
    classes = classify.get_classes(interpreter, top_k=1)  # get classes

    for c in classes:  # get score of all classes
        print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')
        if(f'{labels.get(c.id, c.id)}'  == 'lightning' and float(f'{c.score:.5f}') >= 0.3):  # if classified as lightning with accuracy higher than 0.3
            captured = True  # will be set true if at least one of the frames contains lightning
            print("Lightning detected")  # debug
                    

video.release()  # close the video