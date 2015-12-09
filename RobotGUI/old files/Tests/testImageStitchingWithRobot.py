import cv2
import Robot
import numpy as np
from Video import ImageStitching

"""
This program tests the ImageStitching.py library with the Robot.py library. The robot performs
several movements while taking pictures, and then sends those pictures to be stitched. 

The final result is displayed on screen until the letter 'q' is pressed.
"""



picturePositions = [{'rotation': -13, 'stretch': 107},
                    {'rotation': -13, 'stretch': 42}]




#  TAKE BASE PHOTO (This is the seed to all the rest of the photos)
Robot.moveTo(relative=False, **Robot.home)
Robot.moveTo(height=150, relative=False)

cap = cv2.VideoCapture(1)
cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,  2000)
cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 2000)

_, throwaway = cap.read()  #Wait for camera to adjust to lighting. Toss this frame (camera buffer)
cv2.imshow('main', throwaway)
cv2.waitKey(1000)

images_array = []
for index, position in enumerate(picturePositions):

    Robot.moveTo(relative = False, **position)
    cv2.waitKey(750)
    print "Taking image ", index
    _, _= cap.read()  #Throw away this frame. Fixes oddities with the cameras buffering.
    _, img = cap.read()
    cv2.imshow('main', img)
    cv2.waitKey(10)
    images_array.append(img)


final_img = ImageStitching.stitchImages(images_array[0], images_array[1:], 0)

#  REPLACE ALL BLACK IN BACKGROUND WITH WHITE (NEEDS DEBUGGING)
#lower = np.array([0, 0, 0])
#upper = np.array([0, 0, 0])
#mask = cv2.inRange(final_img, lower, upper)
#final_img = cv2.bitwise_not(final_img, final_img, mask= mask)

cv2.imshow("main", final_img)
cv2.imwrite("F:\Google Drive\Projects\Git Repositories\RobotStorage\RobotArm\stitched.png", final_img)

while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

