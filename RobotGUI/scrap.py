
import cv2
import numpy as np


test = [n for n in range(0, 30)]

x = test[:-5:-1]
for t in x:
    print(t)

srcPts = np.array(  [[  -39,    73,  515],
                     [   52,  -132,  580],
                     [   49,   155,  500],
                     [   43,   185,  640],
                     [ -195,   100,  520],
                     [    3,    29,  505],
                     [  -23,   -31,  495],
                     [ -195,   -74,  500],
                     [  -25,  -140,  570]],
                     np.float32)

dstPts = np.array(  [[    1,   -15,   15],
                     [  -10,   -10,   10],
                     [    5,   -10,   15],
                     [    5,   -10,    6],
                     [    1,   -25,   15],
                     [   -2,   -13,   16],
                     [   -5,   -15,   15],
                     [   -7,   -25,   15],
                     [   11,   -14,   10]],
                     np.float32)




print("METHOD 1")
ret, M, mask = cv2.estimateAffine3D(srcPts, dstPts)


M = np.float32([M[0], M[1], M[2], [0 ,0, 0, 1]])
print("Matrix\n", M)
transformFnCv = lambda x: (M * np.vstack((np.matrix(x).reshape(3, 1), 1)))[0:3, :]
print(transformFnCv((-27,    65,  515)))
print(transformFnCv((52, -132, 580)))
print(transformFnCv((40, 95, 430)))

print(transformFnCv((-135, -86, 740)))





print("METHOD 2")
def solveAffine( src, dst):
    p1, p2, p3, p4 = (src[0], src[1], src[2], src[3])
    s1, s2, s3, s4 = (dst[0], dst[1], dst[2], dst[3])

    x = np.transpose(np.matrix([p1, p2, p3, p4]))
    y = np.transpose(np.matrix([s1, s2, s3, s4]))

    # add ones on the bottom of x and y
    x = np.vstack((x,[1,1,1,1]))
    y = np.vstack((y,[1,1,1,1]))

    # solve for A2
    A2 = y * x.I
    print(A2)
    # return function that takes input x and transforms it
    # don't need to return the 4th row as it is
    return lambda x: (A2 * np.vstack((np.matrix(x).reshape(3,1),1)))[0:3,:]

transformFn = solveAffine(srcPts, dstPts)

# print(np.matrix(dstPts[0]).T - transformFn(srcPts[0]))

print(transformFn((-27,    65,  515)))
print(transformFn((52, -132, 580)))
print(transformFn((40, 95, 430)))



