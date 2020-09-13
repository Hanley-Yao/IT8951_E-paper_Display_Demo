# IT8951_E-paprt_Display_Demo
    将E-paper接入IT8951
    然后通过SPI或者HAT接入树莓派
    先按照微雪的方法调通微雪的官方Demo
    也就是安装bcm2835的库
    注意！！！树莓派4b需要用bcm2835-1.60
    链接：http://www.airspayce.com/mikem/bcm2835/bcm2835-1.60.tar.gz
    编译安装：
        tar zxvf bcm2835-1.60.tar.gz
        cd bcm2835-1.60
        ./configure
        make
        sudo make check
        sudo make install
    建议如果各种无厘头报错加上-B参数(无条件编译安装)
    然后自己看微雪的教程把屏幕调到能正常显示(http://www.waveshare.net/wiki/9.7inch_e-Paper_HAT)
    微雪的程序“./epd”这步如果报错bcm总线错误就在开头加sudo
    跑完微雪的代码以后使用我的程序
    你需要保证你的树莓派可以正常运行Python3以及正确安装了opencv等库
    不需要编译安装树莓派4b不支持oepncv4安装时注意一下具体方法百度去QwQ
    使用CSI采集需要
    在命令行输入以下命令，这个命令的意思是用nano编辑器打开modules这个文件：
        sudo nano /etc/modules
    在这个文件末尾添加一行
        bcm2835-v4l2
    然后打开树莓派的摄像头，SPI，I2C等接口
    其次克隆库到本地打开
    接着需要按照你屏幕软排上的电压修改一下程序里面display = AutoEPDDisplay(vcom=-1.75)的值
    最后如果你手上有A/D模块(我用的是PCF8591自带电位器)(必须在root模式下运行不然会出现SPI无法访问等报错)
        sudo python3 test_IT8951.py
    如果手上没有A/D模块那也没有关系运行
        sudo python3 test_IT8951_No AD Module.py
    等待程序初始化完成后按照欢迎界面在终端操作
    多进程研发中...PIL的错误希望大佬指点
