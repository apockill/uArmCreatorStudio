import numpy as np
import cv2
from matplotlib import pyplot as plt




while True:
    capL = cv2.VideoCapture(1)
    retL, frameL = capL.read()
    capL.release()

    capR = cv2.VideoCapture(2)
    retR, frameR = capR.read()
    capR.release()

    frameL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
    frameR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

    if not type(frameL) == type(None):
        #cv2.imshow("window1", frameL)
        pass
    else:
        print "Error getting frameL"

    if not type(frameR) == type(None):
        #cv2.imshow("window2", frameR)
        pass
    else:
        print "Error getting frameR"

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    #frameL = cv2.cvtColor(frameL, cv2.COLOR_BGR2GRAY)
    #frameR = cv2.cvtColor(frameR, cv2.COLOR_BGR2GRAY)

    stereo = cv2.StereoBM_create(16, 15)
    disparity = stereo.compute(frameL, frameR)
    #cv2.imshow('gray', disparity)
    plt.imshow(disparity,'gray')
    plt.show()







