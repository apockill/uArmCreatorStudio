
import cv2
from matplotlib import pyplot as plt



def drawEdged(frame, thresholdMethod, low, high, **kwargs):

    bilateralConstant = kwargs.get('bilateralConstant', 10)
    returnContours    = kwargs.get('returnContours', False)
    contourMethod     = kwargs.get('contourMethod', cv2.RETR_LIST)  #RETR_EXTERNAL makes sure that only 'outmost' contours are counted

    #grayImg = cv2.bilateralFilter(gray, bilateralConstant, bilateralConstant, 27)  #Blurs photo while maintaining edge integrity. Up the 2nd number for more lag but accuracy

    #self.vid.windowFrame["Main"] = gray

    ret, thresholdImg = cv2.threshold(frame.copy(), low, high, thresholdMethod)                 #Use a threshold on the image (black and white)


    edged = cv2.Canny(thresholdImg, 100, 130)                                           #Gets edged version of photo. 2nd and 3rd numbers are the thresholds (100,130 for optimal)

    cnts, _ = cv2.findContours(edged.copy(), contourMethod, cv2.CHAIN_APPROX_SIMPLE  )

    cv2.drawContours(edged, cnts, -1, (255, 255, 255), 3)

    return cnts, thresholdImg, edged

def getShapeCount(cnts, edged, **kwargs):
    """
    WHAT IT DOES:   Finds all shapes that have 'sides' sides, and returns an array of the coordinates of these arrays.

    INPUT
    KWARGS:
    "bilateralConstant" :   (default 15), and increases how well the image is blurred before analyzed for edges.
    "returnFrame" :         (default: False) If true, the function will ONLY return an edged frame of the object, and stop halfway.
    "minArea"      :        (default: 600) This defines the minimum amount of pixels in a shape to be considered as a shape. (Stops small contours
                                From being mistaken as shapes)

    OUTPUT:
    if returnFrame is true, then it will output: shapeArray, edgedFrame
    edgedFrame: the processed frame before contours are drawn and shapes are found.
    SHAPETARGET:
     shapeArray structure: (for a rectangle)
        shapeArray[0] returns 4 coordinates (points of a shape) of shape 0 out of len(shapeArray)
        shapeArray[0][0] would return the [x,y] of point 1 of shape 0 of the array of shapes.
        [
            [
            array([249, 229]),
            array([227, 372]),
            array([275, 378]),
            array([296, 237])
            ],

            [
            array([250, 229]),
            array([296, 237]),
            array([274, 378]),
            array([227, 371])
            ],

            [
            array([ 43, 258]),
            array([ 36, 298]),
            array([  1, 331]),
            array([ 36, 299])
            ]
        ]
    """

    #SETUP:
    periTolerance     = kwargs.get('peri',              .05)                #Percent "closeness" to being flat edged
    minArea           = kwargs.get('minArea',           50)
    maxArea           = kwargs.get('maxArea',           10000)
    sides             = kwargs.get('sides',             4)
    deleteSimilar     = kwargs.get('deleteSimilar',     True)               #Deletes squares that are almost the same coordinates. Might cause lag

    ################################GET SHAPE CONTOUR ARRAYS##############################################


    cnts = sorted(cnts, key = cv2.contourArea, reverse = True)  #to limit, add [:20] to the end of the array


    #RECORD ALL CONTOURS WITH ONLY 'sides' SIDES
    shapesDetected = []                                  #Array of all 'shape' contours found in the image so far
    for c in cnts:
        peri = cv2.arcLength(c, True)                              #approximate the contour
        approx = cv2.approxPolyDP(c, periTolerance * peri, True)   #This is how precise you want it to look at the contours. (Aka, the curvature of 2%)
        if len(approx) == sides:
            if  minArea < cv2.contourArea(approx) < maxArea:           #Get rid of small anomalies that were mistakenly recognized as contours (size)
                shapesDetected.append(approx)

    if len(shapesDetected) == 0:  #If no shapes detected, end function.
        return 0


    ################################BEGIN ARRAY MODIFICATIONS TO MAKE IT USEFUL################################
    #CONVERT ARRAY TO THE PREDEFINED STRUCTURE (DOCUMENTED ABOVE)
    shapeArray = []
    for  shape in range(0, len(shapesDetected)):
        shapeArray.append([])
        for value in range(0, len(shapesDetected[shape])):
            shapeArray[shape].append(shapesDetected[shape][value][0])  #adds an [x, y] to the array of shape. There should be 'sides' amount of cells in each shape cell.


    ##############################GET RID OF DUPLICATE OBJECTS BY COMPARING COORDINATES#########################
    tolerance = 2  #How many pixels two coordinates in a shape must be away in order to be considered different shapes
    shapeCount = 0
    for shape in range(len(shapeArray)):  #Gets rid of weird overlapping shapes and also finished making the shapeTargets array

        similarCoords = 0  #Keeps track of how many coordinates were within the tolerance
        if deleteSimilar:
            for otherShape in range(shape + 1, len(shapeArray)):
                for coordShape in range(len(shapeArray[shape])):
                    for coordOtherShape in range(len(shapeArray[otherShape])):
                        shapeX = shapeArray[shape][coordShape][0]
                        shapeY = shapeArray[shape][coordShape][1]
                        otherShapeX = shapeArray[otherShape][coordOtherShape][0]
                        otherShapeY = shapeArray[otherShape][coordOtherShape][1]
                        if (shapeX - tolerance) < otherShapeX < (shapeX + tolerance):  #not within tolerance
                            if (shapeY - tolerance) < otherShapeY < (shapeY + tolerance):
                                similarCoords += 1

        if similarCoords < 3 or not deleteSimilar:
            shapeCount += 1


    return shapeCount

cap = cv2.VideoCapture(1)

while True:
    ret0, img0 = cap.read()
    #img0 = cv2.imread("F:\Google Drive\Projects\Git Repositories\RobotStorage\RobotArm\stitched.png")
    img = cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
    cv2.imshow('Main', img)
    cv2.waitKey(1)
    print 'Starting program'

    tests = [{'threshMethod':cv2.THRESH_BINARY,             'title': 'BINARY    ', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.THRESH_BINARY_INV,         'title': 'BINARY_INV', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             {'threshMethod':cv2.THRESH_TRUNC,              'title': 'TRUNC     ', 'img': None,     'low': -1, 'high': -1, 'complexity': -1}]
             #{'threshMethod':cv2.THRESH_TOZERO,             'title': 'TOZERO    ', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.THRESH_TOZERO_INV,         'title': 'TOZERO_INV', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.THRESH_OTSU,               'title': 'OTSU      ', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.ADAPTIVE_THRESH_GAUSSIAN_C,'title': 'ADAP GAUSS', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.CALIB_CB_ADAPTIVE_THRESH,  'title': 'ADAP CALIB', 'img': None,     'low': -1, 'high': -1, 'complexity': -1},
             #{'threshMethod':cv2.ADAPTIVE_THRESH_MEAN_C,    'title': 'ADAP MEAN ', 'img': None,     'low': -1, 'high': -1, 'complexity': -1}]]

        #FOR TESTING SPECIFIC VALUES
    # low  = float(raw_input("Low?:"))    #Default 127
    # high = 255  #float(raw_input("High?:"))   #Default 255
    # for index, test in enumerate(tests):
    #
    #     test['complexity'], test['img'], _ = drawEdged(img, test['threshMethod'], low, low)
    #     test['low']  = low
    #     test['high'] = high
    #
    #     print "Threshold:\t", test['title'], " low:\t", test['low'], 'high:\t', test['high'], 'complexity:\t', test['complexity']





        #FOR OPTIMIZATION:
    between  = [0, 255]
    stepLow  = 5
    stepHigh = 20
    for index, test in enumerate(tests):
        best = {'low': -1, 'high': -1, 'complexity': -1}

        for lowTest in range(between[0], between[1], stepLow):
            for highTest in range(between[0], between[1], stepHigh):
                contours, _, edged = drawEdged(img, test['threshMethod'], lowTest, highTest)
                complexity  = getShapeCount(contours, edged)

                if complexity >= best['complexity']:
                    best = {'low': lowTest, 'high': highTest, 'complexity': complexity}

        contours, test['img'], edged = drawEdged(img, test['threshMethod'], best['low'], best['high'])
        test['complexity'] = getShapeCount(contours, edged)
        test['low']  = best['low']
        test['high'] = best['high']

        print "Threshold:\t", test['title'], " low:\t", test['low'], 'high:\t', test['high'], 'complexity:\t', test['complexity']



    for index, test in enumerate(tests):
        plt.subplot(5, 4, index + 1),
        plt.imshow(test['img'], 'gray')
        plt.title(test['title'])
        plt.xticks([]), plt.yticks([])

    plt.show()

