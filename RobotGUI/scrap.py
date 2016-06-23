
import cv2
import numpy as np
testCoords = []
testCoords += [[  6, -10,  z] for z in range(  8, 25, 3)]
print(len(testCoords))
print(testCoords)

testCoords = []

testCoords += [[ 10 + z%2,  -6 + z%2,  z] for z in range(  8, 25, 3)]

print(len(testCoords))
print(testCoords)