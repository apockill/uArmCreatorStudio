import numpy as np
import cv2
cv2.ocl.setUseOpenCL(False)


# # cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 0)
# # cap.set(cv2.CAP_PROP_WHITE_BALANCE_RED_V, 0)
# cap.set(cv2.CAP_PROP_SETTINGS, 1)
fgbg = cv2.createBackgroundSubtractorMOG2()
cap = cv2.VideoCapture(1)

while(1):

    ret, frame = cap.read()

    fgmask = fgbg.apply(frame)

    cv2.imshow('memes', fgmask)

    k = cv2.waitKey(30) & 0xff
    if k == ord('p'):
        print('place object (press n for next)')
        while cv2.waitKey(100) != ord('n'): pass

        fgmask2 = None
        for i in range(0, 20):
            ret, objectFrame = cap.read()
            fgmask2 = fgbg.apply(objectFrame.copy())

        afterMask = cv2.bitwise_and(objectFrame, objectFrame, mask=fgmask2)

        cv2.imshow('Masked', afterMask)
        cv2.imshow('mask', fgmask2)
        cv2.imshow('without mask', objectFrame)
        cv2.waitKey(30)


cap.release()
cv2.destroyAllWindows()