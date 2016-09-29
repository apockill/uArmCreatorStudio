from Logic import Video
import cv2


# Create a VideoStream and start a video-retrieval thread
vStream = Video.VideoStream()
vStream.startThread()
vStream.setNewCamera(0)

# Play video until the user presses "q"
key = None
while not key == ord("q"):
    # Request the latest frame from the VideoStream
    frame = vStream.getFilteredFrame()

    # If the camera has started up, then show the frame
    if frame is not None: cv2.imshow("frame", frame)

    key = cv2.waitKey(10)

# Close the VideoStream Thread
vStream.endThread()
