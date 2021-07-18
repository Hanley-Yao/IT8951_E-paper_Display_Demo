'''
@ 版权所有：Copyright (c) 2020 

@ 授权类型：MIT License

@ 文件名：test.py

@ 文件功能描述：基于树莓派的电子墨水屏智能终端设计主程序部分

@ 创建日期：2020年10月20日

@ 创建人：Yellow_feces

'''

#encoding: utf8

#### 导入函数库 ####
import argparse  # 导入命令行接口库
import time  # 导入时间库
import cv2  # 导入opencv图像处理库
import numpy as np  # 导入数据处理库
import datetime  # 导入日期处理库
import threading  # 导入Python内置的多线程库
import matplotlib  # 导入绘图库
import requests  # 导入网络请求库
import RPi.GPIO as GPIO  # 导入控制树莓派GPIO硬件库
import queue  # 导入队列支持库
import os  # 导入文件系统库
import smbus  # 导入I2C总线支持库
import socket  # 导入网络接口库 
import mss  # 导入截取Linux屏幕的库
import qrcode  # 导入二维码生成库
from time import sleep  #从time模块中引入 sleep 命名空间  
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageFile  # 从PIL模块中引入 符合要求的 命名空间
from IT8951 import constants  # 从开源驱动库IT8951引入 constants 命名空间
from IT8951.display import AutoEPDDisplay  # 从开源驱动库IT8951引入 AutoEPDDisplay 命名空间
from picamera.array import PiRGBArray  # 从树莓派摄像头库picamera.array引入 PiRGBArray 命名空间
from picamera import PiCamera  # 从树莓派摄像头库picamera引入 PiCamera 命名空间
from multiprocessing import Queue,Process,Value  # 从多进程管理库multiprocessing引入 Queue,Process 命名空间

ImageFile.LOAD_TRUNCATED_IMAGES = True  # queue可能出现错误以外阶段图像数据,使用次命令忽略错误强制执行

# 部分功能函数的封装

class Tool:

    '''
    类说明:封装项目中常用的函数方便开发时快速调用
    '''

    def Log_time():

        '''
        功能说明:获取当前精确到毫秒的时间并返回
        '''
        
        return datetime.datetime.now()

    def get_IP():

        '''
        功能说明:获取当前设备的IP地址并返回
        
        若IP获取成功返回正常的IP地址,若IP地址获取报错或者失败则返回错误
        '''
        try:

            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            s.connect(('8.8.8.8', 80))

            ip = s.getsockname()[0]

        except OSError:

            ip=('无网络连接,远程备忘录将不可用')

        return ip

    def draw_QR(URL):

        '''
        功能说明:输入一个字符串输出一个对应的二维码图片

        Args:
            获取调用时的输入的字符串,通过预设参数生成二维码图像

        Returns:
            返回二维码图像
        '''

        QR = qrcode.QRCode(

        version=2, 

            error_correction=qrcode.constants.ERROR_CORRECT_L,  # 定义二维码容错率,此处为最低

            box_size=4,  # 定义每一个黑色块所需的像素个数

            border=0     # 定义生成的二维码边框半径,本方案不需要则为0

        )

        QR.add_data(URL)

        QR.make(fit=True)# 填充数据

        QR = QR.make_image() # 生成图片

        return QR

    def get_T_RH():

        '''
        功能说明:读取AHT10的寄存器块并返回

        读取预设地址的I2C设备缓冲区数据

        格式化读取到的数据

        返回已格式化的温湿度值
        '''
    
        bus.write_i2c_block_data(56, 172, [51, 0])

        data = bus.read_i2c_block_data(56, 0)

        temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]

        temp = round((((temp*200) / 1048576) - 50) , 2)

        temp = (u'温度: {0:.1f}℃'.format(temp))

        RH = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4

        RH = round((RH * 100 / 1048576) , 2)

        RH = (u'湿度: {0}%'.format(RH))

        return RH , temp

    def place_text(img, text, fontsize, x_offset=0, y_offset=0):  # 在图像上绘制文字

        '''
        功能说明:向输入的图片的预定起始坐标绘制预定大小的预定字符串
        
        Args:
            img : 传入待绘制的图像
            text : 传入待绘制的字符串
            fontsize : 文字高度
            x_offset : 起始顶点 x 坐标若不指定默认为0
            y_offset : 起始顶点 y 坐标若不指定默认为0

        Returns:
            返回绘制完成的图像
        '''
        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype('/home/pi/epaper_test/IT8951/test/ttf from China/STXIHEI.TTF', fontsize, encoding="utf-8")

        draw.text((x_offset, y_offset), text, (0, 0, 0), font=font)

        return img

    def RIP(img):  # 图片二值化

        '''功能说明:将输入的图像进行二分色处理,阀值由main函数初始化的LUT决定

        Args:
            img : 原图

        Returns:
            返回处理完成的图像
        '''

        img = img.convert('L')

        img = img.point(table, '1')

        return img

# 与旋转编码器控制有关函数的类封装

class SPC:  # 旋转编码器控制

    def restoration():

        '''
        函数功能:改变调用进程内的全局变量,用于控制旋转编码器读取流程
        '''

        global run, cmd, new_cmd

        run = 0

        cmd = new_cmd = -1

    def SW_IN(SW):

        '''
        函数功能:改变调用进程内的全局变量,当按钮SW被按下时调用,用于记录非实时按键事件发生
        '''

        global run

        run = 1

    def RK_IN():

        '''
        函数功能:初始化Demo演示需要用到的前台APP进程,并且通过判断旋转编码器状态选择需要运行或者停止的APP进程

        实现方式:通过超时阻塞的方式 若等待旋转编码器SIA相未变化300ms

                就自动截除阻塞扫描 SW 是否被按下过(也就是SW_IN是否令run = 1)

                按下有按下则运行对应的APP进程若没有则停止所有APP进程并显示应用列表菜单栏
        '''

        print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：正在初始化...")

        global run, cmd, new_cmd, page_number

        flag = 0

        resetflag = 0

        cmd = 5  # 设置开机后自动 启动的功能，本项目中序号5为即使时钟投屏功能

        run = 1  # 当run为1时main函数才会运行一个指定的进程/线程

        new_cmd = 0

        page_number = 0

        first = 0

        KEY=Value('i',0)

        #### 导入贴图资源文件,并分别保存到各个变量中 ####

        EPD.full_img = Image.open("/home/pi/epaper_test/IT8951/test/images/white.png")

        img_OFF = Image.open("/home/pi/epaper_test/IT8951/test/images/OFF.png")

        img_1 = Image.open("/home/pi/epaper_test/IT8951/test/images/1.png")

        img_2 = Image.open("/home/pi/epaper_test/IT8951/test/images/2.png")

        img_3 = Image.open("/home/pi/epaper_test/IT8951/test/images/3.png")

        img_4 = Image.open("/home/pi/epaper_test/IT8951/test/images/4.png")

        img_5 = Image.open("/home/pi/epaper_test/IT8951/test/images/5.png")

        img_6 = Image.open("/home/pi/epaper_test/IT8951/test/images/6.png")

        img_7 = Image.open("/home/pi/epaper_test/IT8951/test/images/7.png")

        img_8 = Image.open("/home/pi/epaper_test/IT8951/test/images/8.png")

        menu_list = [img_1, img_1, img_2, img_3, img_4, img_5, img_6, img_7, img_8]

        GPIO.add_event_detect(SW, GPIO.RISING, callback=SPC.SW_IN, bouncetime=250)  # 打开对SW的上升/下降沿检测

        GPIO.add_event_detect(AR, GPIO.RISING, callback=APP.ebook, bouncetime=480)  # 打开对翻书按钮的边缘检测
         
        GPIO.add_event_detect(FR, GPIO.RISING, callback=APP.ebook, bouncetime=480)

        print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：初始化前台 APP 子进程...")

        DESKTOP = Process(target=APP.desktop, args=(KEY, ))
        DESKTOP.start()  # 开始初始化 desktop

        NOWTIME = Process(target=APP.nowTime, args=(KEY, ))
        NOWTIME.start()  # 开始初始化 nowTime

        NOWVIDEO = Process(target=APP.nowVideo, args=(KEY, ))
        NOWVIDEO.start() # 开始初始化 nowVideo

        print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：初始化完成")

        print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：转动旋转编码器选择应用,按下打开")

        while True:

            #print(" ", Tool.Log_time(), " | \r"+"当前:KEY: %f" % cmd, end = "",flush=True)

            GPIO.wait_for_edge(SIA, GPIO.BOTH,timeout=300)

            lastSib = GPIO.input(SIB)

            while not GPIO.input(SIA):

                currentSib = GPIO.input(SIB)

                flag = 1

            if flag:

                if lastSib == 0 and currentSib == 1:

                    cmd += 1

                if lastSib == 1 and currentSib ==0:

                    cmd -=1

                flag =0


            if (new_cmd == cmd and run == 0):  # 控制硬件都未发送改变时则不再进行之后的一系列判断,较少计算量

                continue

            #### 数据处理 ####
            if cmd <= 0:

                cmd = 1

            elif cmd > 8:

                cmd = 1

            new_cmd = cmd

            #### 菜单及启动管理 ####

            if run == 0:

                BF = KEY.value

                KEY.value = 0

                if BF == 0:  # 阻止重复运行

                    pass

                else:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：暂停所有的前台 APP 子进程")

                if first == 0:  # 在其他程序运行后自动清理屏幕

                    APP.clear()

                    first = 1

                else:

                    if cmd % 2 == 0:

                        EPD.put_queue(EPD.partial, EPD.A2, menu_list[cmd])

                    else:

                        EPD.put_queue(EPD.full, EPD.A2, menu_list[cmd])

            else:

                first = 0

                if cmd == 1:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：清除屏幕")

                    APP.clear()

                    SPC.restoration()

                elif cmd == 2:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：运行 desktop")

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：启动独立程序'py_face_dlib.py'请稍等")

                    os.popen('cd /home/pi/epaper_test/IT8951/test/Video && python3 py_face_dlib.py')

                    APP.clear()

                    KEY.value = cmd

                    GPIO.output(POPE ,True)

                    SPC.restoration()

                elif cmd == 3:
                    
                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：运行 desktop")

                    APP.clear()

                    KEY.value = cmd

                    SPC.restoration()

                elif cmd == 4:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：允许前台 APP 子线程 ebook 调用")

                    APP.clear()

                    img = EPD.full_img

                    print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 ebook ：分别按下右侧两个按钮可以实现前后翻页")

                    img = Tool.place_text(img, "按下右侧按钮翻页→→→", 100, 40, 350)

                    img = Tool.RIP(img)  # 图片二值化

                    EPD.put_queue(EPD.full, EPD.A2, img)

                    SPC.restoration()

                elif cmd == 5:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：运行 nowTime")
                    
                    APP.clear()

                    KEY.value = cmd

                    SPC.restoration()

                elif cmd == 6:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：运行 nowVideo 并显示 1 号视频设备画面")

                    APP.clear()

                    KEY.value = cmd

                    SPC.restoration()

                elif cmd == 7:

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：运行 nowVideo 并显示 0 号视频设备画面")

                    APP.clear()

                    KEY.value = cmd

                    SPC.restoration()

                else:

                    EPD.put_queue(EPD.full, EPD.GC16, img_OFF)

                    DESKTOP.terminate()

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：结束 desktop")

                    NOWTIME.terminate()

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：结束 nowTime")

                    NOWVIDEO.terminate()

                    print(" ", Tool.Log_time(), " |   main 的子进程 SPC_Menu ：结束 nowTime")

                    break

# 关于电子墨水屏幕控制有关的类封装

class EPD:  # 电子墨水屏幕控制部分

    '''
    类说明:封装与电子墨水屏刷新技术有关的函数,将复杂的调用流程简单化
    '''

    #### Waveform_mode ####
    INIT    = 0
    DU      = 1
    GC16    = 2
    GL16    = 3
    GLR16   = 4
    GLD16   = 5
    A2      = 6
    DU4     = 7

    #### Renewal_mode ####
    full    = 0
    partial = 1


    # 向队列内输入图像以及刷新信息

    def put_queue(renewal_mode, waveform_mode, draw_image):

        '''
        功能说明:将输入的数据分别写入三个管道内待 draw() 进程读取并刷新

        Args:
            renewal_mode : 刷新模式分别有全局与局部刷新.

                区别在于向IT8951发送的数据量不同,

                前者将发送完整的图像数据而后者发送的是将要刷新的部分.

            waveform_mode : 官方波形的波形模式共有8种,其分别用于:

            注:详细官方资料位于文件夹[附件]->[辅助资料]->[E-paper-mode-declaration.pdf]
                
                ① INIT 模式用于完全擦除显示并使其保持白色状态

                ② DU 是一个快速,不闪烁的刷新模式.此模式支持从任何灰度转换

                有黑色或白色.它不能用于更新为除黑色或白色以外的任何灰色

                ③ GC16 模式用于更新全部显示,并提供较高的图像质量

                ④ GL16 只刷新非白色部分,能一定程度减少闪存储存数据量

                ⑤ GLR16 实际上波形与 GC16 完全一样,通过预处理的图像可以获得更好的显示效果

                ⑥ GLD16 实际上波形与 GC16 完全一样,通过预处理的图像可以获得更好的显示效果

                ⑦ DU4 是一个快速,不闪烁的刷新模式.此模式支持从任何灰度转换

                有黑色或白色.它能够显示4个灰度等级

                ⑧ A2 是最快速的刷新模式,通过A2模式可以快速的刷新屏幕,但是残影较大

                本项目大量使用 A2 模式进行显示输出,保证了较高的显示输出速度

            draw_image:输入的图像数据

        '''

        Renewal_mode.put(renewal_mode)

        Waveform_mode.put(waveform_mode)

        Draw_image.put(draw_image) # 写入队列


    # 获取队列图像以及刷新信息

    def get_queue():  

        '''
        功能说明:用于一次性取出三个管道内的数据并返回
        '''

        waveform_mode = Waveform_mode.get()

        draw_image = Draw_image.get()  # 非阻塞读取队列

        return renewal_mode, waveform_mode, draw_image


    # 刷新屏幕

    def draw(): 

        '''
        功能说明:将写入的图像以规定的模式显示到电子墨水屏

        实现方式:等待三个管道内的数据全部被取出之后通过开源库IT8951将图像显示到电子墨水屏幕上
        '''

        print(" ", Tool.Log_time(), " |   main 进程的子进程 draw ：初始化完成,等待数据...")

        while True:

            renewal_mode, waveform_mode, draw_image = EPD.get_queue()  
        
            # 函数"get_queue([图片], [输出模式], [波形模式])" 
            # 输出模式分别有全局和局部为1打开局部模式,使用封装的queue库当队列为空自动阻塞

            paste_coords = [dims[i] - draw_image.size[i] for i in (0,1)]  # 矫正图片位置

            display.frame_buf.paste(draw_image, paste_coords)  # 写入图像缓冲区

            if renewal_mode == 1:  # 如果为1局部模式打开
            
                display.draw_partial(waveform_mode)
        
            else:  # 否则

                display.draw_full(waveform_mode)


    # 不要直接调用

    def clear():  

        '''
        功能说明:当管道内存在任意数据就使用GC16模式向屏幕刷新一张纯白色的图像达到清除屏幕上内容的目的

        实现方式:当管道内存在数据就将其取出并向put_queue函数中的三个管道写入刷新纯白图像的数据
        '''

        print(" ", Tool.Log_time(), " |   main 进程的子进程 clear ：初始化完成,等待运行命令...")

        EPD.full_img = Image.open("/home/pi/epaper_test/IT8951/test/images/white.png")

        while True:

            FB_clear.get()  # 无数据则阻塞

            EPD.put_queue(EPD.full, EPD.GC16, EPD.full_img)

# 前台 APP 封装类

class APP: 

    '''
    类说明:封装用户应用
    '''

    def hello_word():

        '''
        功能说明:显示开机欢迎界面
        '''
        
        print(" ", Tool.Log_time(), " |   main 进程的子进程 hello_word ：初始化完成,正在运行")

        APP.clear()

        img_ON = Image.open("/home/pi/epaper_test/IT8951/test/images/ON.png")

        EPD.put_queue(EPD.full, EPD.DU, img_ON)

        sleep(1.5)

        for i in range(7):

            img = Image.open("/home/pi/epaper_test/IT8951/test/images/0%s.png"% i)

            EPD.put_queue(EPD.full, EPD.A2, img)

        print(" ", Tool.Log_time(), " |   main 进程的子进程 hello_word ：运行结束")
    

    # 清屏调用APP.clear

    def clear(full = 1):  

        '''
        功能说明:向FB_clear.put写入任意数据以激活函数
        '''

        FB_clear.put(EPD.full)


    # 显示树莓派自身的桌面

    def desktop(KEY):  

        '''
        功能说明:用于向put_queue发送关于树莓派桌面的图像信息使屏幕刷新

        实现方式:通过mss库与pyautogui库分别截取屏幕以及获取鼠标光标位置

                从而合成出当前的桌面状态并发送至put_queue显示输出
        '''

        print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 desktop ：正在初始化...")

        x_one=0

        one = 0

        try:

            import pyautogui as pag

            ink_pt_img = Image.open('/home/pi/epaper_test/IT8951/test/images/ink_pt.png')  # 指针材质

            with mss.mss() as sct:

                print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 desktop ：初始化完成,等待运行命令...")

                while True:

                    if KEY.value != 3 and KEY.value != 2:

                        GPIO.output(POPE ,False)

                        sleep(0.1)

                        continue

                    for num, monitor in enumerate(sct.monitors[1:], 1):  # 排除第一个图像缓冲区

                        sct_img = sct.grab(monitor)  # 获取图像缓冲区上的图像

                        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")  # 格式化图像

                    x,y = pag.position()

                    img = img.convert('1')

                    img.paste(ink_pt_img, (x, y), ink_pt_img)

                    EPD.put_queue(EPD.full, EPD.A2, img)

        except BaseException:

            print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 desktop ：初始化失败")

            while True:

                if KEY.value != 3 and KEY.value != 2:

                    GPIO.output(POPE ,False)

                    sleep(0.1)

                    continue

                else:

                    img = Image.open("/home/pi/epaper_test/IT8951/test/images/white.png")

                    print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 desktop ：SSH 登录无法使用 desktop")

                    img = Tool.place_text(img, "desktop 错误", 75, 50, 300)

                    img = Tool.place_text(img, "使用 SSH 登录无法使用本APP", 75, 50, 400)

                    img = Tool.RIP(img)  # 图片二值化

                    EPD.put_queue(EPD.full, EPD.A2, img)

                    KEY.value = 0

    # 显示图像序列

    def ebook(Pin):

        '''
        功能说明:用于向put_queue发送符合要求的序列图像文件

        实现方式:判断按下按钮的编号增减文件名并读取图像文件并发送给put_queue用于显示输出
        '''

        global cmd, page_number

        if cmd != -1:

            return

        if Pin == 6:

            page_number += 1

        else:

            page_number -= 1

        try:

            img = Image.open("/home/pi/epaper_test/IT8951/test/images/book/%s.png"% page_number)

            EPD.put_queue(EPD.full, EPD.GLD16, img)

            print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 ebook ：页码 ", page_number)

        except FileNotFoundError:

            page_number = 0

            APP.clear()
            
            img = Image.open("/home/pi/epaper_test/IT8951/test/images/white.png")

            img = Tool.place_text(img, "无更多页面", 100, 200, 250)

            img = Tool.RIP(img)  # 图片二值化

            EPD.put_queue(EPD.full, EPD.A2, img)

            print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 ebook ：无法完成翻页操作,请重试")

    # 应用界面

    def nowTime(KEY):

        '''
        功能说明:用于向put_queue发送绘制完成的应用界面

        实现方式:获取精确时间用于绘制时钟,读取外部硬件状态或者外部文件状态
                并将相对应的数据与图像绘制到屏幕的预设位置并向put_queue发送显示输出到电子墨水屏幕
        '''

        print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowTime ：正在初始化...")

        count = 24

        file_new = 0

        new_ip = 0

        font_L = ImageFont.truetype("/home/pi/epaper_test/IT8951/test/ttf from China/STXIHEI.TTF", 60, encoding="utf-8")  # 初始化STXIHEI字体为大号
    
        font_M = ImageFont.truetype("/home/pi/epaper_test/IT8951/test/ttf from China/STXIHEI.TTF", 40, encoding="utf-8")  # 初始化STXIHEI字体为中号
    
        font_S = ImageFont.truetype("/home/pi/epaper_test/IT8951/test/ttf from China/STXIHEI.TTF", 30, encoding="utf-8")  # 初始化STXIHEI字体为小号

        img_S = Image.open('/home/pi/epaper_test/IT8951/test/images/S.png').convert("RGBA")  

        img_M = Image.open('/home/pi/epaper_test/IT8951/test/images/M.png').convert("RGBA")  

        img_T = Image.open('/home/pi/epaper_test/IT8951/test/images/T.png').convert("RGBA")  

        oclock = Image.open('/home/pi/epaper_test/IT8951/test/images/oclock_A.png').convert("RGBA")  
    

        x,y=(50, 50)  # 定义标准时钟钟面起始位置

        print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowTime ：初始化完成,等待运行命令...")

        while True:

            if KEY.value != 5:

                sleep(0.1)
                
                continue

            img = Image.new('RGB', (1200, 825), (255, 255, 255))  # 创建空白画布

            try:

                test_report="/home/pi/epaper_test/IT8951/test/备忘录"              # 目录地址

                lists = os.listdir(test_report)                                    # 列出目录的下所有文件和文件夹保存到lists

                lists.sort(key=lambda fn:os.path.getctime(test_report + "/" + fn)) # 按时间排序

                file = os.path.join(test_report,lists[-1])                         # 获取最新的文件保存到file_new

                if file == file_new:  # 若没有新的文件则不重复读取旧图像并处理

                    pass
               
                else:  # 若有新的文件则打开并且使用convert("1")处理为散点图(通过Floyd-Steinberg扩散抖动算法)
                    
                    print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowTime ：打开并处理最新上传的图像文件")

                    memo = Image.open(file).convert("1")

                file_new = file

            except BaseException:  # 若文件夹内无图像或者图像文件不合法(无法读取/无法处理)则按照当前时间输出预设的一些图像

                Time = int(time.strftime('%H'))

                if Time <= 10 and Time >= 4:

                    memo = Image.open("/home/pi/epaper_test/IT8951/test/images/t_1.jpg")

                elif Time > 10 and Time <= 18:

                    memo = Image.open("/home/pi/epaper_test/IT8951/test/images/t_2.jpg")

                else:

                    memo = Image.open("/home/pi/epaper_test/IT8951/test/images/t_3.jpg")

            ## 绘制秒针 ##
            Time_S = (-6*(float(0.000001*int(datetime.datetime.now().strftime('%f')))+int((time.strftime('%S',time.localtime(time.time()+1)))))) 
            
            # 通过读取系统时钟计算出精确的旋转角度

            img_S_rotate = img_S.rotate(Time_S)
        
            img.paste(img_S_rotate, (x, y), img_S_rotate)

            ## 绘制分针 ##
            Time_M = (-6*(float(1/60*int(datetime.datetime.now().strftime('%S')))+int((time.strftime('%M')))))  

            # 通过读取系统时钟计算出精确的旋转角度
  
            img_M_rotate = img_M.rotate(Time_M)
        
            img.paste(img_M_rotate, (x, y), img_M_rotate)

            ## 绘制时针 ##
            Time_T = (-6*(float(1/60*int(datetime.datetime.now().strftime('%M')))+int((time.strftime('%H')))))  

            # 通过读取系统时钟计算出精确的旋转角度

            img_T_rotate = img_T.rotate(Time_T)
        
            img.paste(img_T_rotate, (x, y), img_T_rotate)


            img.paste(memo, (610, 20)) 
        
            img.paste(oclock, (x, y+2), oclock) 

            Time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()+1))  # 绘制数字时钟并且修正延迟

            draw = ImageDraw.Draw(img)
        
            draw.text((50, 610), Time, (0, 0, 0), font=font_L)  # 绘制数字时间

            ip = Tool.get_IP()  # 调用get_IP()函数获取当前终端的内网IP,若无WiFi连接或者无法获取IP地址则返回 "无网络连接,远程备忘录将不可用"

            URL = "http://"+ip+":43700/receive/read"  # 格式化链接地址


            QR = Tool.draw_QR(URL)  # 调用draw_QR()函数导入新的链接URL获取最新二维码

            if URL != 'http://无网络连接,远程备忘录将不可用:43700/receive/read':

                img.paste(QR, (1, 1))

            else:  # 当无WiFi连接或者无法获取IP地址返回 "无网络连接,远程备忘录将不可用" 时显示"无网络连接,远程备忘录将不可用"到屏幕左下角

                URL = "无网络连接,远程备忘录将不可用"

            draw.text((5, 785), URL, (0, 0, 0), font=font_S)

            if count == 24:

                RH , temp = Tool.get_T_RH()

                count = 0

            draw.text((50, 680), RH, (0, 0, 0), font=font_M)

            draw.text((50, 725), temp, (0, 0, 0), font=font_M)

            count += 1

            img = Tool.RIP(img)  # 图片二值化

            EPD.put_queue(EPD.partial, EPD.A2, img)


    # 显示输出实时外部图像采集器画面

    def nowVideo(KEY):

        '''
        功能说明:读取指定的外部图像采集器的图像数据并刷新

        实现方式:由于默认状态下外部图像采集设备采集到的图像数据会进入[先进后出]的数据"栈"

                如果读取速度低于采集速度就会导致读取到的图像非实时从而使得延迟变大.

                如果我们需要得到实时画面就需要将[先进后出]的数据结构转换成[先进先出]的结构

                之后再处理[先进先出]数据列表中的最新数据并且写入put_queue显示输出
        '''


        print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowVideo ：初始化完成,等待运行命令...")

        while True:

            key = KEY.value

            if key != 6 and key != 7:

                sleep(0.1)
                
                continue

            if key == 6:

                P = 1  # 图像采集设备编号 1 为 HDMI to USB 模块

                if os.path.exists('/dev/video1') == False:  # 判断是否存在 1 号图像采集设备

                    img = Image.new('RGB', (1200, 825), (255, 255, 255))  # 创建空白画布

                    img = Tool.place_text(img, "错误:未插入 HDMI to USB 拓展卡", 80, 20, 350)

                    print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowTime ：未插入 HDMI to USB 拓展卡")

                    img = Tool.RIP(img)  # 图片二值化

                    EPD.put_queue(EPD.full, EPD.A2, img)

                    KEY.value = 0  # 错误时停止运行

                    continue

            else:

                P = 0  # 图像采集设备编号 0 为 CSI 摄像头模块

            try:

                cap = cv2.VideoCapture(P)

                cap.set(3,1280)

                cap.set(4,960)

                while True:

                    for i in range(2):

                        ret,video_image = cap.read()
            
                    video_image = video_image[40:920,0:1280]

                    img = Image.fromarray(cv2.cvtColor(video_image,cv2.COLOR_BGR2RGB))

                    img = img.convert('1')

                    EPD.put_queue(EPD.full, EPD.A2, img)

                    key = KEY.value

                    if key != 6 and key != 7:

                        cap.release()
                    
                        cv2.destroyAllWindows()
                        
                        break  
    
            except:

                print(" ", Tool.Log_time(), " |     SPC_Menu 的子进程 nowTime ：读取视频设备或处理图像错误")

                img = Tool.place_text(img, "错误:无法读取视频设备或处理图像", 75, 20, 350)

                img = Tool.RIP(img)  # 图片二值化

                sleep(1)

                KEY.value = 0  # 错误时停止运行

                continue

if __name__ == "__main__":

    print("\n-------------------------------------------- Demo Run --------------------------------------------\n")

    ## 创建二值化LUT表 ##

    print(" ", Tool.Log_time(), " | main：正在初始化二值化 LUT...")

    threshold = 200  # 设定二值化阈值
         
    table = []

    for i in range(256):

        if i < threshold:

            table.append(0)

        else:

            table.append(1)

    print(" ", Tool.Log_time(), " | main：LUT 初始化完成")
    
    global cmd, run

    EPD.full_img = Image.open("/home/pi/epaper_test/IT8951/test/images/white.png")

    print(" ", Tool.Log_time(), " | main：正在初始化 EPD 驱动程序...")

    display = AutoEPDDisplay(vcom=-1.83, rotate=None, spi_hz=124444449)  # 设置Vcom值已经SPI时钟频率(部分设备可能无法支持高频SPI通信)

    dims = (display.width, display.height)

    print(" ", Tool.Log_time(), " | main：EPD 驱动程序初始化完成")

    print(" ", Tool.Log_time(), " | main：正在初始化 SMBus 总线...")

    bus = smbus.SMBus(1)

    bus.write_i2c_block_data(56, 225, [8, 0])

    bus.read_byte(0x38)

    print(" ", Tool.Log_time(), " | main：SMBus 总线初始化完成")

    print(" ", Tool.Log_time(), " | main：正在初始化 GPIO 控制器...")

    SIA = 16   # SPC A相
    SIB= 20    # SPC B相
    SW = 12    # SPC 按钮

    AR = 6     # 按钮向前
    FR = 22    # 按钮向后

    POPE = 26  # GPIO控制软件通道

    GPIO.setup(POPE,  GPIO.OUT)
    GPIO.output(POPE ,True)

    GPIO.setup(SW, GPIO.IN,pull_up_down=GPIO.PUD_UP)  # 设置[引脚]为上拉模式
    GPIO.setup(SIA,GPIO.IN,pull_up_down=GPIO.PUD_UP)
    GPIO.setup(SIB,GPIO.IN,pull_up_down=GPIO.PUD_UP)

    GPIO.setup(AR, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)  
    GPIO.setup(FR, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

    print(" ", Tool.Log_time(), " | main：GPIO 控制器初始化完成")

    print(" ", Tool.Log_time(), " | main：正在初始化 Queue 队列...")

    Draw_image = Queue(1)
    Renewal_mode = Queue(1)
    Waveform_mode = Queue(1)

    FB_clear = Queue()  # 写入任何数据都会执行清屏操作 

    print(" ", Tool.Log_time(), " | main：Queue 队列初始化完成")

    print(" ", Tool.Log_time(), " | main：正在初始化子进程...")

    DRAW = Process(target=EPD.draw, args=())
    DRAW.start()

    CLEAR = Process(target=EPD.clear, args=())
    CLEAR.start()

    HELLO_WORD = Process(target=APP.hello_word, args=())
    HELLO_WORD.start()

    HELLO_WORD.join()

    SPC_Menu = Process(target=SPC.RK_IN, args=())
    SPC_Menu.start()

    SPC_Menu.join()  # 等待 SPC 结束

    print(" ", Tool.Log_time(), " | main：SPC_Menu 结束")

    print(" ", Tool.Log_time(), " | main：开始清理子进程...")

    sleep(0.5)  # 等待DRAW处理完最后的数据

    print(" ", Tool.Log_time(), " | main：结束子进程 draw")

    DRAW.terminate()

    print(" ", Tool.Log_time(), " | main：结束子进程 clear ")

    CLEAR.terminate()

    print(" ", Tool.Log_time(), " | main：成功结束所有子进程")
    
    print("\n-------------------------------------------- Demo END --------------------------------------------\n")
        