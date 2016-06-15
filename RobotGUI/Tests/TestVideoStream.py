from time import sleep

from RobotGUI.Logic import Video


if __name__ == '__main__':
    # cameras = Video.getConnectedCameras()

    try:
        vStream = Video.VideoStream()
        vStream.setNewCamera(1)
        vStream.setPaused(False)
    except:
        print("error")


    while True:
        # print("1")
        frame = vStream.getFrame()


        if frame is not None:
            pass
            # print("Is not none")
            # cv2.imshow("main", frame.copy())
            # cv2.waitKey(1)

        # keyPressed = chr(ch + (ch == -1) * 256).lower().strip()
        #
        #
        # if keyPressed == 'p':
        #     if vStream.paused:
        #         vStream.play()
        #         cv2.waitKey(250)
        #     else:
        #         vStream.pause()
        #         cv2.waitKey(250)

#

