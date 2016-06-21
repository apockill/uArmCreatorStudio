
import cv2
import numpy as np
xTest = [[x, -15, 15] for x in range(-15, 15, 2)]
yTest = [[y, -15, 15] for y in range(-25, -5, 2)]
zTest = [[0, -15, z]  for z in range(  7, 25, 2)]
combined = xTest + yTest + zTest

print(len(combined), combined)