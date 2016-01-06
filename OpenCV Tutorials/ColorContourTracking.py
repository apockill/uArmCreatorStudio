import cv2
import numpy as np

# create video capture
cap = cv2.VideoCapture(1)


def bgr2hsv(colorBGR):
        """
        Input: A tuple OR list of the format (h, s, v)
        OUTPUT: A tuple OR list (depending on what was sent in) of the fromat (r, g, b)
        """
        isList = colorBGR is list

        r, g, b = colorBGR[2], colorBGR[1], colorBGR[0]

        r, g, b = r / 255.0, g / 255.0, b / 255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx - mn
        if mx == mn:
            h = 0
        elif mx == r:
            h = (60 * ((g - b) / df) + 360) % 360
        elif mx == g:
            h = (60 * ((b - r) / df) + 120) % 360
        elif mx == b:
            h = (60 * ((r - g) / df) + 240) % 360
        if mx == 0:
            s = 0
        else:
            s = df/mx
        v = mx

        if isList:
            return [h, s, v]
        else:
            return h, s, v





# low, high = getRange(c, 50)
goalHSV = 0
tolerance = 50

print "goal: ", goalHSV, "tolerance: ", tolerance
#Track this color
while True:
    # read the frames
    ret, frame = cap.read()
    if not ret: print "ERROR capturing frame!"


    # smooth it
    frame = cv2.blur(frame, (3, 3))

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    low, high = getRange(goalHSV, tolerance)
    if goalHSV - tolerance < 0 or goalHSV + tolerance > 180:
        #If the color crosses 0, you have to do two thresholds
        print "doing smart thresh", low, high
        lowThresh   = cv2.inRange(hsv,    np.array((0, 80, 80)), np.array((low, 255, 255)))
        upperThresh = cv2.inRange(hsv, np.array((high, 80, 80)), np.array((180, 255, 255)))
        finalThresh = upperThresh + lowThresh
    else:
        print "doing dumb thresh", low, high, goalHSV
        finalThresh  = cv2.inRange(hsv, np.array((low, 80, 80)), np.array((high, 255, 255)))

    thresh3 = finalThresh.copy()

    # find contours in the threshold image
    contours, hierarchy = cv2.findContours(thresh3, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # finding contour with maximum area and store it as best_cnt
    max_area = 0
    best_cnt = None
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            best_cnt = cnt

    # finding centroids of best_cnt and draw a circle there
    if best_cnt is not None:
        M = cv2.moments(best_cnt)
        cx, cy = int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        cv2.circle(frame, (cx, cy), 5, 255, -1)

    # Show it, if key pressed is 'Esc', exit the loop
    cv2.imshow('frame', frame)
    cv2.imshow('thresh', finalThresh)
    if cv2.waitKey(33) == ord('q'):
        break

    if cv2.waitKey(33) == ord('s'):
        fromY = 0
        toY   = 480
        fromX = 0
        toX   = 640
        rect  = frame[fromY:toY, fromX:toX]
        goalHSV = bgr2hsv(cv2.mean(rect))[0]
        print "New HSV: ", goalHSV



# Clean up everything before leaving
cv2.destroyAllWindows()
cap.release()