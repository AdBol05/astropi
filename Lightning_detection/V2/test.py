
#* importing necessary libraries
from sense_hat import SenseHat
from orbit import ISS
from skyfield.api import load
import os

print(f"ISS at timescale approach: {ISS.at(load.timescale().now()).subpoint()}")
print(f"ISS coords approach: {ISS.coordinates()}")