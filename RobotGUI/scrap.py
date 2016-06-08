import cv2

im_l = cv2.imread("img1.png")
im_r = cv2.imread("img2.png")

sift = cv2.xfeatures2d.SIFT_create(1000)
features_l, des_l = sift.detectAndCompute(im_l, None)
features_r, des_r = sift.detectAndCompute(im_r, None)
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50)
flann = cv2.FlannBasedMatcher(index_params,search_params)