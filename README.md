# :(这是一个出自高一学生之手的垃圾项目

###### 别问我为啥把所有代码写一个文件里面...因为我不会分开写...别骂我

[[IT8951_E-paper_Display_Demo](https://github.com/Yellow-feces/IT8951_E-paper_Display_Demo)]是一个高一学生无聊闲着蛋疼整出来的没用玩意，可使用树莓派+IT8951实现一些没用的功能。

* 使用Pyhon编写

* 用了好多好多大佬的库

* 功耗有点大

本项目适配9.7寸的eink屏幕(1200*825)当然也可以自己改成兼容其他尺寸的程序，毕竟9.7寸的不太便宜。

这个Demo需要比较复杂的硬件连接与软件配置，非常麻烦...若想要复现整个项目可能需要花费1200RMB左右(如果不使用微雪的屏幕,在咸鱼上能找到一些比较便宜的屏幕,不过据我所知只有微雪的屏幕对比度最高残影最少效果最好,但是必须提的一点就是相同尺寸的屏幕速度都是完全一样的)

## 想要构建这个项目你需要准备一些东西:

### 屏幕

为此选用了台湾E Ink生产的型号为**ED097TC2**玻璃基板电子墨水屏幕(下简称EPD)这款屏幕：

* 对角线尺寸为9.7寸
* 有效分辨率为1200\*825像素密度150PPI
* 面板刷新率85Hz
* 对比度经典值12：1



### 时序控制器

驱动这款EPD屏幕使用的是台湾ITe半导体为驱动EPD开发的一款专用Tcon芯片**型号为IT8951**(我用的现成的开发板,不过原理图是开源的有能力自己打板子焊接一个便宜很多很多)。



### 微电脑

计算部分采用**树莓派4B 1G运行内存版本**以及一张16G的SD卡作为储存其硬件SPI串口频率高达到**125Mhz**，足以满足本项目微电脑与Tcon芯片间的数据传输需求



### 交互

  终端需要有交互功能，此方案设计了一个**增量旋转编码器**便于用户操作，旋转编码器采用了标准规格的16分段周期方波信号编码器。



### 图像采集

  终端设备中提供了使用摄像头进行**人脸识别的Demo程序**(百度上找的随便加进去装逼用)，本方案采用了型号为**OV5647** 的CSI摄像头。

  介于兼容性与性价比，本项目可以采用USB/CSI两种接口的HDMI采集卡方案:

* HDMI to USB 免驱动转换器(某宝二十多块钱)
* 东芝TC358743转换卡，用好处在于低功耗和低延迟(相对HDMI to USB模块，但是比较贵)



### 实时时钟

   由于树莓派自身没有实时时钟，在断电后无法保持时间走动，若无网络连接就会导致系统时间错误，本项目采用I2C总线通信的**DS1307时钟模块**保持系统时间。



### 温湿度传感器

   为获取较为精确的近似室内温湿度，本项目采用I2C总线通信的**AHT10温湿度采集模块**。



### 数字功放

   经评估性价比以及兼容性后采用**PAM8610**数字功放。

   选用了性能强大的数字功放后，扬声器的选择就相对自由了，经过设备内剩余空位的测量与计算，最后选用了两个8Ω5W双振膜低音扬声器。



### 功放电源

由于PAM8610数字功放的最佳工作电压为15V，本项目采用了**AT30 DC-DC BUCK/BOOST**供电。



### 外壳(裸奔完全没必要)

  为此本项目使用了一块7075航空铝板作为背面外壳，由于7075铝材较为坚固且耐腐蚀。由于树莓派4B的CPU发热量较大，7075航空铝材背板起到固定以及散热作用。

  而其他部分采用较为柔软的KT泡沫板作为材料搭建，能够很好的于屏幕贴合保护屏幕。



### 隔热

  由于EPD显示原理的特殊性。**局部的温度差异**会导致**显示效果局部改变**影响观感，为此本项目选用硅酸铝陶瓷纤维隔热片双面覆盖铜箔。其能很好的隔绝树莓派在运行时产生的热量，使得屏幕表面任何区域的温度都基本一致**，**最大限度保证了显示效果。



## 模块接线图:

目标文件`附件/线路连接图`



## 构建Demo运行环境：

###### 因为我本人很菜，写的程序不仅仅很乱并且需要一堆依赖...别打我...另外我用的版本是[2019-09-26-raspbian-buster-full]

### 1.配置

修改目标文件`/boot/config.txt`

向文件末尾添加如下文本

```sh
hdmi_force_hotplug = 1

hemi_group = 2

hdmi_mode = 87

hdmi_ignore_edid = 0xa5000080

hdmi_cvt 1200 825 60 5 0 0

disable_overscan = 1

dtparram = spi = on

dtparam = audio = on

dtoverlay = vc4-fkms-v3d

max_framebuffers = 2

start_x = 1

gpu_mem = 128

enable_uart = 1

dtoverlay = w1-gpio
```

其作用在于

使树莓派在启动时强制打开硬件视频输出并且使得硬件输出的分辨率设置为1200*825以适配电子墨水屏幕的分辨率以达到最优效果。

打开对硬件SPI控制器的支持

设置较大的视频内存以支持大量对硬件图像缓冲区的请求支持。



### 2.自动挂载硬件

修改目标文件`/etc/modules`

向文件末尾添加如下文本

```sh
i2c-dev

bcm2835-v42

spi-bcm2708

i2c-bcm2708

snd-bcm2835enable_uart = 1

dtoverlay = w1-gpio
```

其作用在于

开机时自动挂载`I2C`硬件总线、`v4l2`摄像头硬件、`SPI`硬件总线、`UART`硬件总线、`GPIO`硬件总线

   从而达到开机后可以通过程序直接调用这些接口与外部设备进行通信。



### 3.同步时钟

本项目采用的DS1307时钟模块在开机完成后需要使用脚本自动将时钟时间同步至系统。

修改目标文件`/etc/rc.local`

在末尾`exit0`前一行添加如下文本使树莓派在进入系统后自动运行这些命令

```sh
modprobe i2c-dev

echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device

hwclock -r

hwclock -s
```



### 4.项目依赖软件

本项目需要实现通过无线WIFI网络发送文件至树莓派本地文件夹内。为了提供最佳的客户端兼容性。本项目采用qrcp开源文件传输工具。

*项目地址：https://github.com/claudiodangelis/qrcp*

此程序能够创建一个Web网页，在任意终端（手机、Pad或者电脑等）的浏览器上打开特定的内网网址即可在网页上上传文件。

通过安装qrcp后创建`qrcp.config`文件写入如下配置：

```sh
{

    "fqdn": "", 

    "interface": "wlan0", 

    "port": 43700,

    "keepAlive": false,

    "path": "read", 

    "secure":false, 

    "tls-key": "", 

    "tls-cert": ""
}
```

其作用在于

配置使用`wlan0`网卡（默认的WIFI网卡）

配置使用固定端口`43700`

配置文件夹路径`read`

由于qrcp为命令行程序，项目中采用命令脚本对其进行操作

`/root/qrcp_run.sh`源代码如下：

该脚本文件用于运行qrcp程序：

```sh
#!/bin/bash

### BEGIN INIT INFO

# Provides:          tuzixini

# Required-Start:    $local_fs $network

# Required-Stop:     $local_fs

# Default-Start:     2 3 4 5

# Default-Stop:      0 1 6

# Short-Description: self define auto start

# Description:       self define auto start

### END INIT INFO

while true

do
        sudo echo "ds3231 0x68" | sudo tee  /sys/class/i2c-adapter/i2c-1/new_device
        sudo hwclock -s
        sudo qrcp receive -c /root/qrcp.config --output=/home/pi/epaper_test/IT8951/test/备忘录
done
```

在目标文件`/etc/rc.local`中`exit0`上一行写入

```sh
sh /root/qrcp_run.sh &
```

其作用在于开机就使qrcp程序运行保证网络文件传输通道顺畅。

注：目标文件`rc.local`全部内容如下

```sh
#!/bin/sh -e
#

# rc.local

#

# This script is executed at the end of each multiuser runlevel.

# Make sure that the script will "exit 0" on success or any other

# value on error.

#

# In order to enable or disable this script just change the execution

# bits.

#

# By default this script does nothing.

# Print the IP address

_IP=$(hostname -I) || true

if [ "$_IP" ]; then

  printf "My IP address is %s\n" "$_IP"
  
fi

# qrcp 

sh /root/qrcp_run.sh &

# I2C-clock

modprobe i2c-dev

echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device

hwclock -r

hwclock -s

exit 0
```



### 5.人脸识别程序

目标文件`test/Video/py_face_dlib.py`

此程序是基于Python3编写的人脸识别演示Demo用于演示项目主程序调用外部程序的功能。人脸识别演示Demo部分代码来源于网络,本项目中对其进行了修改使其适配电子墨水屏。

**注：此程序需要使用主程序通过GPIO进行调用与控制**(我太菜懒得 写/写不好)



### 6.主程序

本项目的主程序通过Python3编写

源代码`test/test.py`

流程图`附件/程序流程图`

**注**：此程序将屏幕控制与应用功能结合，对于驱动电子墨水屏幕需要采用开源驱动

*项目地址：https://github.com/GregDMeyer/IT8951*

GregDMeyer开发者的IT8951项目属于Python库

在Linux终端安装过程如下：

```sh
git clone https://github.com/GregDMeyer/IT8951
cd IT8951
pip3 install -r requirements.txt
pip3 install ./
```

IT8951库中的主要自定义函数用法如下：

```python
display.frame_buf.paste([图像],paste_coords)
#  向缓冲区写入图像
display.[刷新模式](constants.DisplayModes[波形模式])
#  将图像缓冲区的图像以定义的模式输出到屏幕
```

#### 还要一堆依赖库自己看着办咋装吧...反正我觉得挺折腾人的QAQ

```
argparse
time
cv2
numpy
datetime
threading
matplotlib
requests
RPi.GPIO
queue
os
smbus
socket
mss
qrcode
PIL
IT8951
picamera
multiprocessing
```

**注**：由于电子墨水屏幕的特殊性，其视觉上的刷新速度较慢。关于[刷新模式]驱动程序提供了局部刷新与全局刷新两个刷新模式。其区别在于发送的数据量不同。正常来说局部刷新只发送需要刷新位置的部分图像，这样可以减少数据的传输量进而提升设备的运行速度。关于[波形模式]也是由于同样的原因，由于其原理的特殊性，电子墨水屏幕只能显示16色分色灰度图像。显示越多的颜色就意味着要进行更多次对墨水的刷新（因为无法精确获取每一个墨水的状态，刷新新的灰度就必须将墨囊刷新至全黑或者全白的极限状态这样控制器才能对屏幕颜色进行精确的控制）操作流程变多了自然就需要消耗更多的时间。而大部分使用场景我们只需要让屏幕显示简单的黑或白色而灰度则用扩散抖动（**Floyd-Steinberg**）进行半色调处理后得到完全黑白的图像。使用不刷新灰度的波形模式可以更快的显示输出图像。

##### 程序的大略思路：

本项目将IT8951库函数封装如一个进进程。主程序开始运行后调用Queue库实现跨进程的管道数据传输。当管道内有数据包时读取端会自动取出并继续运行代码。这种方式常被称为阻塞，通过向管道写入数据来激活一个被阻塞的进程。分别向三个管道别写入需要刷新的`[图像]`数据`[刷新模式]`以及`[波形模式]`以此激活专用于屏幕刷新的进程取出数据根据得到的数据处理图像刷新电子墨水屏幕。

而其他部分则通过旋转编码器控制`SPC_Menu`进程的多个绘图子进程和子线程向管道内写入数据实现实时控制的屏幕刷新。

而父进程`SPC_Menu`提前创建的子进程先进行初始化之后等待父进程的命令才会继续运行，本项目中采用共享内存变量的方式控制子进程的运行与阻塞。主进程SPC_Menu创建一个多进程可读取的共享内存变量`KEY`。`SPC_Menu`的子线程每秒钟判断十次`KEY`的值。每一个子进程都有属于自己的特定值，若KEY等于自己的特定值则运行否则阻塞。

###### 这是一个项目烂透了，希望多多指教，别骂我就好QAQ



## 本项目依赖以及类似的项目：


- [GregDMeyer](https://github.com/GregDMeyer/IT8951) - 这是我项目驱动屏幕的核心
- [claudiodangelis](https://github.com/claudiodangelis/qrcp) - 我的项目接收图片的核心
- [waveshare](https://github.com/waveshare/IT8951) - 微雪C语言例程

## License

MIT. See [LICENSE](https://github.com/Yellow-feces/IT8951_E-paper_Display_Demo/blob/master/LICENSE).

