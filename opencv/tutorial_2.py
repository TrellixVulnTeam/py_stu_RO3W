import cv2 as cv
import numpy as np


def access_pixel(image):
    print(image.shape)
    height = image.shape[0]
    width = image.shape[1]
    channels = image.shape[2]
    print("width:%s, height: %s channels:%s" % (width, height, channels))
    for row in range(height):
        for col in range(width):
            for c in range(channels):
                pv = image[row, col, c]
                image[row, col, c] = 255 - pv
    cv.imshow("pixel deom !", image)


def inverse(image):
    dst = cv.bitwise_not(image)
    cv.imshow("inverse demo", dst)


def create_image():
    # img = np.zeros([400, 400, 3], np.uint8)
    # img[:, :, 0] = np.ones([400, 400]) * 255
    # img[:, :, 2] = np.ones([400, 400]) * 255
    # cv.imshow("new image", img)
    ####
    # img=np.zeros([400,400],np.uint8)

    # img=np.ones([400,400])*127
    # cv.imshow("new img",img)
    # img = np.zeros([400, 400, 1], np.uint8)
    # img[:,:,0]=np.ones([400,400])*60
    # cv.imshow("new image",img)
    # img=np.ones([400,400,1],np.uint8)
    # img=img+0
    # cv.imshow("new image",img)
    # cv.imwrite("./images/write.png",img)
    # ml=np.ones([3,3],np.uint8)
    # ml.fill(122.388)
    # print(ml)
    m3 = np.array([[2, 3, 4], [4, 5, 6], [7, 8, 9]], np.int32)
    m3.fill(9)
    print(m3)


print('--------- Hello Python ------')
src = cv.imread('./images/demo.png')
cv.namedWindow("input image", cv.WINDOW_AUTOSIZE)
cv.imshow("input image", src)
t1 = cv.getTickCount()
create_image()
# access_pixel(src)
# inverse(src)
t2 = cv.getTickCount()
time = (t2 - t1) / cv.getTickFrequency()
print("cv.getTickFrequency():")
print(cv.getTickFrequency())
print("Time : %s ms," % (time))
cv.waitKey(0)

cv.destroyAllWindows()
