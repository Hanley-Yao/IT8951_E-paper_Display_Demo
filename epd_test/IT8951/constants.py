
# 密码
class Pins:
    CS    = 8
    HRDY  = 24
    RESET = 17

# 命令代码
class Commands:
    SYS_RUN      = 0x01
    STANDBY      = 0x02
    SLEEP        = 0x03
    REG_RD       = 0x10
    REG_WR       = 0x11
    MEM_BST_RD_T = 0x12
    MEM_BST_RD_S = 0x13
    MEM_BST_WR   = 0x14
    MEM_BST_END  = 0x15
    LD_IMG       = 0x20
    LD_IMG_AREA  = 0x21
    LD_IMG_END   = 0x22

    # 我猜来自Waveshare的“用户定义”命令
    DPY_AREA     = 0x034
    GET_DEV_INFO = 0x302
    DPY_BUF_AREA = 0x037
    VCOM         = 0x039

# 旋转方式
# TODO：确保CW / CCW正确
class Rotate:
    NONE = 0
    CW   = 1
    CCW  = 3
    FLIP = 2  # 180度旋转

# TODO: 摆脱这些M
class PixelModes:
    M_2BPP = 0
    M_3BPP = 1
    M_4BPP = 2
    M_8BPP = 3

#  此处描述了这些波形模式：
#  http://www.waveshare.net/w/upload/c/c4/E-paper-mode-declaration.pdf
class DisplayModes:
    INIT  = 0
    DU    = 1
    GC16  = 2
    GL16  = 3
    GLR16 = 4
    GLD16 = 5
    A2    = 6
    DU4   = 7

class EndianTypes:
    LITTLE = 0
    BIG    = 1

class AutoLUT:
    ENABLE  = 1
    DISABLE = 0

# LUT引擎状态？
ALL_LUTE_BUSY = 0xFFFF

class Registers:
    DBASE = 0x1000           # 基址-仅对I80注册RW访问

    LUT0EWHR  = DBASE + 0x00  # LUT0引擎宽度高度
    LUT0XYR   = DBASE + 0x40  # LUT0 XY
    LUT0BADDR = DBASE + 0x80  # LUT0基地址
    LUT0MFN   = DBASE + 0xC0  # LUT0模式和帧号
    LUT01AF   = DBASE + 0x114 # LUT0 / LUT1活动标志

    UP0SR     = DBASE + 0x134  # 更新参数0设置
    UP1SR     = DBASE + 0x138  # 更新参数1设置
    LUT0ABFRV = DBASE + 0x13C  # LUT0 alpha混合和填充矩形值
    UPBBADDR  = DBASE + 0x17C  # 更新缓冲区基地址
    LUT0IMXY  = DBASE + 0x180  # LUT0图像缓冲区X / Y偏移
    LUTAFSR   = DBASE + 0x224  # LUT状态（所有LUT引擎的状态）

    BGVR      = DBASE + 0x250  # 位图（1bpp）图像颜色表

    I80CPCR = 0x04

    MBASE = 0x200
    MCSR  = MBASE + 0x0
    LISAR = MBASE + 0x8
