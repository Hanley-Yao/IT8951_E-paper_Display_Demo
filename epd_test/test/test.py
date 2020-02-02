
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

a = Queue(1)
b = Queue(1)
c = Queue(1)

def fun1():
    while True:
        imga = Image.open("img/1.png")
        a.put(imga)
        imgb = Image.open("img/2.png")
        b.put(imgb)
        imgc = Image.open("img/3.png")
        c.put(imgc)

def fun2():
    while True:
        img = a.get()
        print("a")

def fun3():
    while True:
        img = b.get()
        print("b")
def fun4():
    while True:
        img = c.get()
        print("c")
p1 = Process(target = fun1)
p2 = Process(target = fun2)
p3 = Process(target = fun3)
p4 = Process(target = fun4)
p1.start()
p2.start()
p3.start()
p4.start()
p1.join()
p2.join()
p3.join()
p4.join()