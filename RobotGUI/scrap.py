import cv2


objImage = cv2.imread('test.png')

cv2.imshow('test', objImage)
cv2.waitKey(30)

cv2.imwrite('test2.png', objImage, data='hello')