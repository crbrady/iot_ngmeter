from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import numpy as np

def picamtest1():
    camera = PiCamera()
    camera.resolution = (832, 512)
    camera.rotation = 270
    camera.capture("tmpImage.jpg", format="jpeg")


def picamtest2():
    camera = PiCamera()
    camera.resolution = (820, 500)
    camera.rotation = 270
    rawCapture = PiRGBArray(camera, size=(820, 500))
    time.sleep(0.1)
    
    img = io.BytesIO()
    camera.capture(img, format="bgr",use_video_port=True)
    rawCapture.truncate(0)



    cv2.imshow('detected circles',output_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
picamtest1()