
from . import constants
from .constants import Pins, Commands, Registers, DisplayModes, PixelModes
from .spi import SPI

from time import sleep

import RPi.GPIO as GPIO
import numpy as np

class EPD:
    '''
    电子纸显示器（EPD）的接口.

    参量
    ----------

    vcom：浮动
         产生最佳显示的VCOM电压.因而异
         设备到设备.
    '''

    def __init__(self, vcom=-1.5):

        self.spi = SPI()

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(Pins.HRDY, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(Pins.RESET, GPIO.OUT, initial=GPIO.HIGH)

        # 重启
        GPIO.output(Pins.RESET, GPIO.LOW)
        sleep(0.1)
        GPIO.output(Pins.RESET, GPIO.HIGH)

        self.width            = None
        self.height           = None
        self.img_buf_address  = None
        self.firmware_version = None
        self.lut_version      = None
        self.update_system_info()

        self._set_img_buf_base_addr(self.img_buf_address)

        # 启用I80打包模式
        self.write_register(Registers.I80CPCR, 0x1)

        self.set_vcom(vcom)

    def __del__(self):
        GPIO.cleanup()

    def load_img_area(self, buf, rotate_mode=constants.Rotate.NONE, xy=None, dims=None):
        '''
        将buf中的像素数据（字节数组，每个像素1个）写入设备内存.
        此功能实际上不会显示图像（请参阅EPD.display_area）.

        参量
        ----------

        buf : 字节
            包含像素数据的字节数组

        旋转模式：常量 旋转，可选
            数据粘贴到设备存储器的循环模式

        xy : (int, int), 可选
            粘贴区域左上角的x，y坐标。 如果省略,
            假定图像为整个显示区域.

        dims : (int, int), 可选
            粘贴区域的尺寸.如果省略xy（或设置为None）
            尺寸假定为显示器的尺寸为.
        '''

        endian_type = constants.EndianTypes.LITTLE
        pixel_format = constants.PixelModes.M_4BPP

        if xy is None:
            self._load_img_start(endian_type, pixel_format, rotate_mode)
        else:
            self._load_img_area_start(endian_type, pixel_format, rotate_mode, xy, dims)

        buf = self._pack_pixels(buf, pixel_format)
        self.spi.write_pixels(buf)

        self._load_img_end()

    def display_area(self, xy, dims, display_mode):
        '''
        将显示的一部分更新为设备内存中当前存储的内容
        对于那个地区.可以使用EPD.write_img_area将更新后的数据写入设备存储器.
        '''
        self.spi.write_cmd(Commands.DPY_AREA, xy[0], xy[1], dims[0], dims[1], display_mode)

    def update_system_info(self):
        '''
        获取有关系统的信息，并将其存储在类属性中
        '''
        self.spi.write_cmd(Commands.GET_DEV_INFO)
        data = self.spi.read_data(20)
        self.width  = data[0]
        self.height = data[1]
        self.img_buf_address = data[3] << 16 | data[2]
        self.firmware_version = ''.join([chr(x>>8)+chr(x&0xFF) for x in data[4:12]])
        self.lut_version      = ''.join([chr(x>>8)+chr(x&0xFF) for x in data[12:20]])

    def get_vcom(self):
        '''
        获取设备的VCOM电压电流值
        '''
        self.spi.write_cmd(Commands.VCOM, 0)
        vcom_int = self.spi.read_int()
        return -vcom_int/1000

    def set_vcom(self, vcom):
        '''
        设置设备的VCOM电压
        '''
        self._validate_vcom(vcom)
        vcom_int = int(-1000*vcom)
        self.spi.write_cmd(Commands.VCOM, 1, vcom_int)

    def _validate_vcom(self, vcom):
        # TODO: 找出vcom的实际限制
        if not -5 < vcom < 0:
            raise ValueError("vcom must be between -5 and 0")

    @staticmethod
    def _pack_pixels(buf, pixel_format):
        '''
        取一个缓冲区，其中每个字节代表一个像素,然后根据pixel_format将其打包为16位字.
        '''
        buf = np.array(buf, dtype=np.ubyte)

        if pixel_format == PixelModes.M_8BPP:
            rtn = np.zeros((buf.size//2,), dtype=np.uint16)
            rtn |= buf[1::2]
            rtn <<= 8
            rtn |= buf[::2]

        elif pixel_format == PixelModes.M_2BPP:
            rtn = np.zeros((buf.size//8,), dtype=np.uint16)
            for i in range(7, -1, -1):
                rtn <<= 2
                rtn |= buf[i::8] >> 6

        elif pixel_format == PixelModes.M_3BPP:
            rtn = np.zeros((buf.size//4,), dtype=np.uint16)
            for i in range(3, -1, -1):
                rtn <<= 4
                rtn |= (buf[i::4] & 0xFE) >> 4

        elif pixel_format == PixelModes.M_4BPP:
            rtn = np.zeros((buf.size//4,), dtype=np.uint16)
            for i in range(3, -1, -1):
                rtn <<= 4
                rtn |= buf[i::4] >> 4

        return rtn

    def run(self):
        self.spi.write_cmd(Commands.SYS_RUN)

    def standby(self):
        self.spi.write_cmd(Commands.STANDBY)

    def sleep(self):
        self.spi.write_cmd(Commands.SLEEP)

    def wait_display_ready(self):
        while(self.read_register(Registers.LUTAFSR)):
            sleep(0.01)

    def _load_img_start(self, endian_type, pixel_format, rotate_mode):
        arg = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.write_cmd(Commands.LD_IMG, arg)

    def _load_img_area_start(self, endian_type, pixel_format, rotate_mode, xy, dims):
        arg0 = (endian_type << 8) | (pixel_format << 4) | rotate_mode
        self.spi.write_cmd(Commands.LD_IMG_AREA, arg0, xy[0], xy[1], dims[0], dims[1])

    def _load_img_end(self):
        self.spi.write_cmd(Commands.LD_IMG_END)

    def read_register(self, address):
        '''
        读取设备寄存器
        '''
        self.spi.write_cmd(Commands.REG_RD, address)
        return self.spi.read_int()

    def write_register(self, address, val):
        '''
        写入设备寄存器
        '''
        self.spi.write_cmd(Commands.REG_WR, address)
        self.spi.write_data((val,))

    def _set_img_buf_base_addr(self, address):
        word0 = address >> 16
        word1 = address & 0xFFFF
        self.write_register(Registers.LISAR+2, word0)
        self.write_register(Registers.LISAR, word1)

    ##########
    # the following functions are transcribed from example code from waveshare, but have not
    # been tested

    # def mem_burst_read_trigger(self, address, count):
    #     # these are both 32 bits, so we need to split them
    #     # up into two 16 bit values

    #     addr0 = address & 0xFFFF
    #     addr1 = address >> 16

    #     len0 = count & 0xFFFF
    #     len1 = count >> 16

    #     self.spi.write_cmd(Commands.MEM_BST_RD_T,
    #                        addr0, addr1, len0, len1)

    # def mem_burst_read_start(self):
    #     self.spi.write_cmd(Commands.MEM_BST_RD_S)

    # def mem_burst_write(self, address, count):
    #     addr0 = address & 0xFFFF
    #     addr1 = address >> 16

    #     len0 = count & 0xFFFF
    #     len1 = count >> 16

    #     self.spi.write_cmd(Commands.MEM_BST_WR,
    #                    addr0, addr1, len0, len1)

    # def mem_burst_end(self):
    #     self.spi.write_cmd(Commands.MEM_BST_END)

    # def display_area_1bpp(self, xy, dims, display_mode, background_gray, foreground_gray):

    #     # set display to 1bpp mode
    #     old_value = self.read_register(Registers.UP1SR+2)
    #     self.write_register(Registers.UP1SR+2, old_val | (1<<2))

    #     # set color table
    #     self.write_register(Registers.BGVR, (background_gray << 8) | foreground_gray)

    #     # display image
    #     self.display_area(xy, dims, display_mode)
    #     self.wait_display_ready()

    #     # back to normal mode
    #     old_value = self.read_register(Registers.UP1SR+2)
    #     self.write_register(Registers.UP1SR+2, old_value & ~(1<<2))

    # def display_area_buf(self, xy, dims, display_mode, display_buf_address):
    #     self.spi.write_cmd(Commands.DPY_BUF_AREA, xy[0], xy[1], dims[0], dims[1], display_mode,
    #                        display_buf_address & 0xFFFF, display_buf_address >> 16)
