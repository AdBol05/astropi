from picamera import PiCamera
from pathlib import Path
from time import sleep

counter = 1000

camera = PiCamera()
camera.resolution = (1296, 972)
base_folder = Path(__file__).parent.resolve()


while (counter <= 1100):
    camera.capture(f"{base_folder}/image_{counter}.jpg")
    print("took a picture ", counter)
    sleep(2)
    counter += 1
