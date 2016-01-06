import cv2
import numpy as np
from time import time
cap = cv2.VideoCapture(1)

ret, frame1 = cap.read()
prvs = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)
hsv = np.zeros_like(frame1)
hsv[...,1] = 255
avg = [0, 0]

while True:

    ret, frame2 = cap.read()
    copyFrame = frame2.copy()
    if not ret: print "ERROR! No frame grabbed"

    lastTime = time()

    next = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    #                                  (prvs, next, N/A, N/A, N/A, Lower = faster, Little Effect,  5, 1)
    flow = cv2.calcOpticalFlowFarneback(prvs, next, 0.5,   1,  5,              1,             5,  5, 2)

    #Get average vector for movement
    avg = cv2.mean(flow)
    print "time", time() - lastTime

    cv2.line(copyFrame, (320, 240), (int(avg[0] * 100 + 320), int(avg[1] * 100 + 240)), (0, 0, 255), 5)



    # mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
    #
    # #print len(mag), len(ang)
    #
    #
    #
    #
    #
    #
    # hsv[...,0] = ang*180/np.pi/2
    # hsv[...,2] = cv2.normalize(mag,None,0,255,cv2.NORM_MINMAX)
    #
    # bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)

    cv2.imshow('frame2', copyFrame)
    k = cv2.waitKey(1) & 0xff
    if k == 27:
        break



    prvs = next.copy()

cap.release()
cv2.destroyAllWindows()

    #.7 seconds
    # avg[0] = 0
    # avg[1] = 1
    # for i in xrange(0, 480):          #, y in enumerate(flow):
    #      for j in xrange(0, 640):  #, x in enumerate(y):
    #          avg[0] += flow[i][j][0]
    #          avg[1] += flow[i][j][1]
    # avg[0] /= (640 * 480)
    # avg[1] /= (640 * 480)