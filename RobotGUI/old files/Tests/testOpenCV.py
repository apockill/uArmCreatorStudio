import cv2


print "Starting program!"
cap = cv2.VideoCapture(0)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    cv2.waitKey(100)
    if not ret:
        print "Frame empty, trying again..."
    else:
        cv2.imshow('window', frame)
    if cv2.waitKey(100) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()