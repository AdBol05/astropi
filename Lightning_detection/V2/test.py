import cv2
import os

dark_file = "./dark.h264"
lightning_file = "./lightning.h264"
dark_folder = "./dark"
lightning_folder = "./lightning"

#* create output and temporary directories if they don't exist
if not os.path.exists(lightning_folder):
    print(f"Creating temporary directory in: {lightning_folder}")
    os.mkdir(lightning_folder)

if not os.path.exists(dark_folder):
    os.mkdir(dark_folder)
    print(f"Creating output directory in: {dark_folder}")

print("Processing please wait...")

#* parse videos to extract frames
video1 = cv2.VideoCapture(input_file)
    # Check if video was opened successfully
if not video1.isOpened():
    raise Exception("Could not open video")

# Read the video frame-by-frame
i = 10000
while video1.isOpened():
    success, frame = video1.read()
    if not success:
        break
    cv2.imwrite(f"{output_folder}/frame_{i}.jpg", frame)
    i += 1
    # Release the video
video1.release()
