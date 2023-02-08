
#TODO:create and test coral TPU model
from pathlib import Path
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.dataset import read_label_file
from PIL import Image

base_folder = Path(__file__).parent.resolve()  # determine working directory
model_file = base_folder/'lightning.tflite' # set model directory
label_file = base_folder/'labels.txt' # set label file directory
dark_image = base_folder/'empty.jpg'
lightning_image = base_folder/'lightning.jpg'


#?def classify(model_file, label_file, input):


def classify(model_file, label_file, input_file):
    interpreter = make_interpreter(f"{model_file}")  # create an interpreter instance
    interpreter.allocate_tensors()  # set up TPU
    size = common.input_size(interpreter)  # get preffered input image size
    labels = read_label_file(label_file)  # get labels from label.txt
    classes = classify.get_classes(interpreter, top_k=1)  # get classes
    
    image = Image.open(input_file).convert('RGB').resize(size, Image.ANTIALIAS)  # open image
    common.set_input(interpreter, image)  # load model and image to TPU
    interpreter.invoke()  # invoke interpreter

    for c in classes:  # get score of all classes
        print(f'{labels.get(c.id, c.id)} | {c.score:.5f}')

classify(model_file, label_file, dark_image)
classify(model_file, label_file, lightning_image)