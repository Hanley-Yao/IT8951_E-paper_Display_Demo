
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

m = 120  # 定义时钟功能文字大小 具体依屏幕大小而定

k = 120  # CSI采集图像二值阀值 动态阀值还在弄QwQ

'''
该程序是没有A/D模块下使用的
如果有A/D模块可以接电位器动态调文字大小和阀值
'''

print('初始化EPD...')

display = AutoEPDDisplay(vcom=-1.75)

def display_image_8bpp(display):
    img_path = 'img/Hello.png'

    img = Image.open(img_path)

    # TODO: 这应该是内置的
    dims = (display.width, display.height)

    img.thumbnail(dims)
    paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # 与底部对齐
    display.frame_buf.paste(img, paste_coords)

    display.draw_full(constants.DisplayModes.GC16)

display_image_8bpp(display)

print('初始化完成...')

def test_display(display):

    print('VCOM设置为', display.epd.get_vcom())

    epd = display.epd

    print('系统信息:')
    print('  显示屏尺寸: {}x{}'.format(epd.width, epd.height))
    print('  img缓冲区地址: {:X}'.format(epd.img_buf_address))
    print('  固件版本: {}'.format(epd.firmware_version))
    print('  LUT版本: {}'.format(epd.lut_version))
    print()

    print('清除显示器...')
    display.clear()


    print('显示渐变...')

    # 将帧缓冲区设置为渐变
    for i in range(16):
        color = i*0x10
        box = (
            i*display.width//16,      # xmin
            0,                        # ymin
            (i+1)*display.width//16,  # xmax
            display.height            # ymax
        )

        display.frame_buf.paste(color, box=box)

    # 更新显示
    display.draw_full(constants.DisplayModes.GC16)

    print('局部刷新...')
    # 清晰的图像为白色
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    start = time.process_time()

    _place_text(display.frame_buf, '富强 民主 文明 和谐' , y_offset=-150)
    display.draw_full(constants.DisplayModes.GLD16)

    elapsed = (time.process_time() - start)
    print("  writing 富强 民主 文明 和谐... time used:",elapsed)
    start = time.process_time()

    _place_text(display.frame_buf, '自由 平等 公正 法治', y_offset=0)
    display.draw_partial(constants.DisplayModes.GLD16)
    elapsed = (time.process_time() - start)
    print("  writing 自由 平等 公正 法治... time used:",elapsed)
    start = time.process_time()

    _place_text(display.frame_buf, '爱国 敬业 诚信 友善', y_offset=150)
    display.draw_partial(constants.DisplayModes.GLD16)
    elapsed = (time.process_time() - start)
    print("  writing 爱国 敬业 诚信 友善... time used:",elapsed)


def Display(display):

    global KEY_main

    global i

    global b

    epd = display.epd

    camera = PiCamera()
    camera.resolution = (epd.width, epd.height)
    camera.framerate = 30
    rawCapture = PiRGBArray(camera, size=(epd.width, epd.height))

    display.clear()

    i = 0

    b = 1

    while True:

        for frame in camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):
            start = time.process_time()
            # 清晰的图像为白色
            display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))
            # 获取代表图像的原始NumPy数组，然后初始化时间戳
            # 和占用/未占用的字节
            image = frame.array
            # 清除流以准备下一帧
            rawCapture.truncate(0)

            img = Image.fromarray(image)

            if b == 1:

                img = img.convert('1')

                # TODO: 这应该是内置的
                dims = (display.width, display.height)

                img.thumbnail(dims)
                paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # 与底部对齐
                display.frame_buf.paste(img, paste_coords)

                if i == 0:

                    display.draw_full(constants.DisplayModes.A2)  # 全局刷新
                    i = 1

                display.draw_partial(constants.DisplayModes.A2)  # 局部刷新

                elapsed = (time.process_time() - start)


            elif b == 0:

                img = img.convert('L')

                threshold = k

                table = []
                for i in range(256):
                    if i < threshold:
                        table.append(0)
                    else:
                        table.append(1)

                img = img.point(table,'1')

                # TODO: 这应该是内置的
                dims = (display.width, display.height)

                img.thumbnail(dims)
                paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # 与底部对齐
                display.frame_buf.paste(img, paste_coords)

                if i == 0:

                    display.draw_full(constants.DisplayModes.A2)  # 全局刷新
                    i = 1

                display.draw_partial(constants.DisplayModes.A2)  # 局部刷新

                elapsed = (time.process_time() - start)


            elif b == 2:
                # TODO: 这应该是内置的
                dims = (display.width, display.height)

                img.thumbnail(dims)
                paste_coords = [dims[i] - img.size[i] for i in (0,1)]  # 与底部对齐
                display.frame_buf.paste(img, paste_coords)

                if i == 0:

                    display.draw_full(constants.DisplayModes.GLD16)  # 全局刷新
                    i = 1

                display.draw_partial(constants.DisplayModes.GLD16)  # 局部刷新

                elapsed = (time.process_time() - start)


            #print("Display time used:",elapsed)  # 滚动

            #print("\rDisplay time used:{}".format(elapsed), end="")  # 静止

            if KEY_main != 1:
                break

        break

    camera.close()

def nowTime(display):

    sleep(1)

    display.clear()
    # 清晰的图像为白色
    display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

    Time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()+1))

    _place_text(display.frame_buf, '%s' %(Time), y_offset=0)
    display.draw_full(constants.DisplayModes.GLD16)

    sleep(0.5)

    global KEY_main

    while True:

        start = time.process_time()

        Time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()+1))

        display.frame_buf.paste(0xFF, box=(0, 0, display.width, display.height))

        _place_text(display.frame_buf, '%s' %(Time), y_offset=0)
        display.draw_partial(constants.DisplayModes.DU)

        elapsed = (time.process_time() - start)

        time_sleep = 1

        t = (time_sleep - elapsed)

        if t < 0:
            t = 0
            
        sleep(t)

        if KEY_main != 0:
            break

# 此功能只是其他功能的帮助者
def _place_text(img, text, x_offset=0, y_offset=0):
    '''
    在图像的某个位置放置一些居中的文本。
    '''

    fontsize = m

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('ttf from China/SIMYOU.TTF', fontsize)

    img_width, img_height = img.size
    text_width, _ = font.getsize(text)
    text_height = fontsize

    draw_x = (img_width - text_width)//2 + x_offset
    draw_y = (img_height - text_height)//2 + y_offset

    draw.text((draw_x, draw_y), text, font=font)



def main():

#     test_display(display)      # 测试屏幕功能

    global KEY_main

    global i

    global b

    while True:

        cmd = input()


        if (cmd == "q"):  # 键入"q"时清屏
            display.clear()

        elif (cmd == "n"):  # 键入"n"时启动时钟

            KEY_main = 0
            main_nowTime_Key = threading.Thread(target=nowTime, args = (display, ))
            main_nowTime_Key.setDaemon(True)
            main_nowTime_Key.start()

        elif (cmd == "d" or cmd == "w" or cmd == "r" or cmd == "t" or cmd == "y"):  #键入"d" or "w" or "r" or "t" or "y"时

            if (cmd == "w"):  # 当键入为"w"时在Display函数中全局刷新

                i = 0

            elif (cmd == "t"):  # 当键入为"t"时镜像为二值化

                b = 0

            elif (cmd == "r"):  # 当键入为"r"时镜像为抖动(默认)

                b = 1

            elif (cmd == "y"):  # 当键入为"y"时镜像为16灰度模式

                b = 2

            elif (cmd == "d"):  # 当键入为"d"时启动Display_HDMI镜像

                KEY_main = 1
                main_Display_Key = threading.Thread(target=Display, args = (display, ))
                main_Display_Key.setDaemon(True)
                main_Display_Key.start()

        elif (cmd == "s"):  # 当键入为"s"时退出demo

            KEY_main = 100

            sleep(1)

            display.clear()

            break

if __name__ == '__main__':
    main()
