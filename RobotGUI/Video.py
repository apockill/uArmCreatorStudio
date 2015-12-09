import cv2

def getConnectedCameras():
    tries = 10
    cameraList = []

    for i in range(0, tries):
        testCap = cv2.VideoCapture(i)

        if testCap.isOpened():
            cameraList.append(i)
    return cameraList