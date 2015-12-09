import cv2
import numpy as np


cap = cv2.VideoCapture(1)


while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.imread("F:\Google Drive\Projects\Git Repositories\RobotStorage\RobotArm\stitched.png")

    gray = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    cframe = frame.copy()


    circles = cv2.HoughCircles(gray, 3, 1, 20, np.array([]), param1= 100, param2=30, minRadius=1, maxRadius=100)  #
    #circles = np.uint16(np.around(circles))
    print circles
    if circles is not None:
        a, b, c = circles.shape

        for i in range(b):
            cv2.circle(cframe, (circles[0][i][0], circles[0][i][1]), circles[0][i][2], (0, 0, 255), 3, 3)
            cv2.circle(cframe, (circles[0][i][0], circles[0][i][1]), 2, (0, 255, 0), 3, 2)  # draw center of circle

    # Display the resulting frame
    cv2.imshow('window', cframe)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()