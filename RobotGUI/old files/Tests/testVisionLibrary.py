from threading import Thread
from time import sleep
import cv2
import Vision  #All camera and object-rec commands


def runAction():
    pass



if '__main__' == __name__:
    print 'Start!'
    #SET UP VIDEO CLASS AND WINDOWS VARIABLES
    vid                 = Vision.Video()
    vid.createNewWindow("Main", xPos = 10, yPos = 10)

    #SETUP UP OTHER VARIABLES/CLASSES
    objTracker          = Vision.ObjectTracker(vid)
    screenDimensions    = vid.getDimensions()
    global exitApp
    exitApp = False
    keyPressed          = ''  #Keeps track of the latest key pressed

    #START SEPERATE THREAD FOR MOVING ROBOT
    actionThread = Thread(target = runAction)
    actionThread.start()
    vid.getVideo()

    #DISPLAY VIDEO/IMAGE REC. MAIN THREAD.
    while not exitApp:
        vid.getVideo()

        #IF THE CAMERA HAS BEEN UNPLUGGED, RECONNECT EVERYTHING:
        if objTracker.getMovement() == 0:
            print "ERROR: __main__(XXX): Camera NOT detected."
            sleep(1)
            print "__main(XXX)__: Attempting to reconnect..."
            vid.cap = cv2.VideoCapture(1)


        #DO FRAME OPERATIONS:
        shapeArray, edgedFrame = objTracker.getShapes(sides=4, threshHold = cv2.THRESH_OTSU, returnFrame = True)




        #SET FRAMES FOR THE WINDOWS:
        vid.windowFrame["Main"]     = objTracker.drawShapes(shapeArray)




        #DISPLAY THINGS
        vid.display("Main")

        ch = cv2.waitKey(10)
        keyPressed = chr(ch + (ch == -1) * 256).lower().strip()  #Convert ascii to character, and the (ch == -1)*256 is to fix a bug.
        if keyPressed == chr(27): exitApp = True  #If escape has been pressed

        if keyPressed == ord(' '):  #PAUSE
                    vid.paused = not vid.paused


    #CLOSE EVERYTHING CORRECTLY
    actionThread.join(1000)  #Ends the robot thread, waits 1 second to do so.
    cv2.destroyWindow('window')