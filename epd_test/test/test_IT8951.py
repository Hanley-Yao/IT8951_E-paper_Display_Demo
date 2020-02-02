
#encoding: utf-8

import time
import cv2
import numpy as np
from PIL import Image,ImageEnhance,ImageFilter,ImageDraw,ImageFont
from picamera.array import PiRGBArray
from picamera import PiCamera
import datetime
import threading
from time import sleep
from IT8951 import constants
from IT8951.display import AutoEPDDisplay
import argparse
import matplotlib
import requests
import smbus
from multiprocessing import Queue,Process


print('初始化EPD...')

display = AutoEPDDisplay(vcom=-1.75)

print('OK')

a = Queue(1)
b = Queue(1)
c = Queue(1)

def Display_1(display):
    while True:
        imga = Image.open("img/1.png")
        a.put(imga)

        
        imgb = Image.open("img/2.png")
        b.put(imgb)
        
        imgc = Image.open("img/3.png")
        c.put(imgc)

def Display_2(display):
    
    while True:
        img = Image.open("img/2.png")
        dims = (display.width, display.height)
        img.thumbnail(dims)
        paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # align image with bottom of display
        display.frame_buf.paste(img, paste_coords)
        
        display.draw_full(constants.DisplayModes.A2)

def Display_3(display):

    while True:
        sleep(1)
        pass

def Display_4(display):

    while True:
        sleep(1)
        pass
    
def main():
    
    p1 = Process(target = Display_1, args = (display, ))
    p2 = Process(target = Display_2, args = (display, ))
    p3 = Process(target = Display_3, args = (display, ))
    p4 = Process(target = Display_4, args = (display, ))
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p1.join()
    p2.join()
    p3.join()
    p4.join()
main()