from RobotGUI import Video
import cv2

if __name__ == '__main__':
    cameras = Video.getConnectedCameras()
    vStream = Video.VideoStream()
    vStream.setNewCamera(cameras[0])
    vStream.play()
    frame = vStream.getFrame()
    while True:
        frame = vStream.getFrame()
        if frame is not None:
            cv2.imshow("main", frame)


        ch = cv2.waitKey(1)
        keyPressed = chr(ch + (ch == -1) * 256).lower().strip()

        if keyPressed == 'p':
            if vStream.paused:
                vStream.play()
                cv2.waitKey(250)
            else:
                vStream.pause()
                cv2.waitKey(250)



