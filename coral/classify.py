# import all ibraries needed
from pathlib import Path
from PIL import Image
from pycoral.adapters
import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
import os

script_dir = Path(__file__).parent.resolve() # resolve working directory

counter = 1

model_file = script_dir/'models/astropi-day-vs-nite.tflite' # name of model
data_dir = script_dir/'data'  # data directory
label_file = data_dir/'day-vs-night.txt' # Name of your label file

image_file = data_dir/'tests'/"img_7.jpg" # Name of image for classification
interpreter = make_interpreter(f"{model_file}")  # assign model to interpreter
interpreter.allocate_tensors()  # set up tensor cores
size = common.input_size(interpreter)  # set image size
image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
common.set_input(interpreter, image)
interpreter.invoke()
classes = classify.get_classes(interpreter, top_k=1)
labels = read_label_file(label_file)


for c in classes:
    print(f'{labels.get(c.id, c.id)} {c.score:.5f}')

    if (f'{labels.get(c.id, c.id)}'  == 'day' and float(f'{c.score:.5f}') >= 0.3):
        print("day it is")
        os.rename(image_file, data_dir/'tests'/f'day_{counter}.jpg')
    else:
        print("day it is not")
        os.remove(image_file)
