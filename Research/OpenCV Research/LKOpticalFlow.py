import numpy as np
import cv2

cap = cv2.VideoCapture(1)

# params for ShiTomasi corner detection
feature_params = dict( maxCorners=100,
                       qualityLevel=0.3,
                       minDistance=7,
                       blockSize=7)

# Parameters for lucas kanade optical flow
lk_params = dict( winSize =(15, 15),
                  maxLevel=2,
                  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Create some random colors
color = np.random.randint(0, 255, (100, 3))

# Take first frame and find corners in it
ret, old_frame = cap.__read()
old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)




while True:
    p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

    # Create a mask image for drawing purposes

    ret, frame = cap.__read()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if not ret: print "ERROR no frame grabbed"
    if p0 is None:
        print "p0 is None! Restarting loop."
        old_gray = frame_gray.copy()
        continue

    mask = np.zeros_like(old_frame)

    # calculate optical flow
    p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

    # Select good points
    good_new = p1[st == 1]
    good_old = p0[st == 1]

    avg = [0, 0]
    # draw the tracks
    for i, (new, old) in enumerate(zip(good_new, good_old)):
        a, b = new.ravel()
        c, d = old.ravel()
        #mask = cv2.line(mask, (a,b),(c,d), color[i].tolist(), 2)
        #frame = cv2.circle(frame,(a,b),5,color[i].tolist(),-1)
        #drawing is inplace replacement, line() and circle() will return None!
        vector  = [a - c, d - b]
        avg[0] += vector[0]
        avg[1] += vector[1]
        cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
        cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
    cv2.line(mask, (320, 240), (int(avg[0] * 5 + 320), int(-avg[1] * 5 + 240)), (255, 255, 255), 5)


    img = cv2.add(frame,mask)

    cv2.imshow('frame', img)

    k = cv2.waitKey(100) & 0xff
    if k == 27:
        break

    # Now update the previous frame and previous points
    old_gray = frame_gray.copy()
    p0 = good_new.reshape( -1, 1, 2)

cv2.destroyAllWindows()
cap.release()