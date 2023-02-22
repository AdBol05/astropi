from PIL import Image
import os

# Path to the directory containing the images
directory = "/path/to/images"

# Loop through all the files in the directory
for filename in os.listdir(directory):
    # Check if the file is an image
    if filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
        # Open the image
        image_path = os.path.join(directory, filename)
        image = Image.open(image_path)

        # Convert the image to grayscale
        gray_image = image.convert("L")

        # Save the grayscale image
        gray_image_path = os.path.join(directory, f"gray_{filename}")
        gray_image.save(gray_image_path)

        print(f"Converted {filename} to grayscale.")