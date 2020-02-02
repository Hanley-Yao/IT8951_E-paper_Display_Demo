
import tkinter as tk
from PIL import Image, ImageChops, ImageTk

from .constants import DisplayModes

try:
    from .interface import EPD
except ModuleNotFoundError:
    EPD = None

class AutoDisplay:
    '''
    该基类会自动跟踪对其frame_buf属性的更改
    仅更新显示中需要更新的部分

    通过调用update（）方法来完成更新，该方法应该派生类
    实行。
    '''

    def __init__(self, width, height, flip=False, track_gray=False):
        self.width = width
        self.height = height
        self.flip = flip

        self.frame_buf = Image.new('L', (width, height), 0xFF)

        # 跟踪我们已更新的内容,
        # 这样我们就可以自动仅对
        # 显示屏的相关部分
        self.prev_frame = None

        self.track_gray = track_gray
        if track_gray:
            # 跟踪自上次灰度更新以来发生的变化
            # 以便我们确保清除所有黑色/白色中间体
            # 毫无变化地开始
            self.gray_change_bbox = None

    def _get_frame_buf(self):
        '''
        返回框架buf，根据翻转旋转
        '''
        if self.flip:
            return self.frame_buf.rotate(180)
        else:
            return self.frame_buf

    def draw_full(self, mode):
        '''
        将完整图像写入设备，然后使用模式显示
        '''

        self.update(self._get_frame_buf().getdata(), (0,0), (self.width, self.height), mode)

        if self.track_gray:
            if mode == DisplayModes.DU:
                diff_box = self._compute_diff_box(self.prev_frame, self._get_frame_buf(), round_to=4)
                self.gray_change_bbox = self._merge_bbox(self.gray_change_bbox, diff_box)
            else:
                self.gray_change_bbox = None

        self.prev_frame = self._get_frame_buf().copy()

    def draw_partial(self, mode):
        '''
        只写限制已更改图像像素的矩形
        自上次调用draw_full或draw_partial以来
        '''

        if self.prev_frame is None:  # 自初始化以来的首次调用
            self.draw_full(mode)

        # 计算此帧的差异
        # TODO: 此类中不应具有round_to
        diff_box = self._compute_diff_box(self.prev_frame, self._get_frame_buf(), round_to=4)

        if self.track_gray:
            self.gray_change_bbox = self._merge_bbox(self.gray_change_bbox, diff_box)
            # 将灰度更改重置为零
            if mode != DisplayModes.DU:
                diff_box = self._round_bbox(self.gray_change_bbox, round_to=4)
                self.gray_change_bbox = None

        self.prev_frame = self._get_frame_buf().copy()

        # 没事做
        if diff_box is None:
            return

        buf = self._get_frame_buf().crop(diff_box)

        # 变平为黑色或白色
        if mode == DisplayModes.DU:
            buf = buf.point(lambda x: 0x00 if x < 0xB0 else 0xFF)

        xy = (diff_box[0], diff_box[1])
        dims = (diff_box[2]-diff_box[0], diff_box[3]-diff_box[1])

        self.update(buf.getdata(), xy, dims, mode)

    def clear(self):
        '''
        清除显示屏，设备图像缓冲区和帧缓冲区（例如在启动时）
        '''
        # 将帧缓冲区设置为全白
        self.frame_buf.paste(0xFF, box=(0, 0, self.width, self.height))
        self.draw_full(DisplayModes.INIT)

    @classmethod
    def _compute_diff_box(cls, a, b, round_to=2):
        '''
        找到四个坐标，给出a和b之间的差异的边界框
        确保它们可以被round_to整除

        参量
        ----------

        a : PIL.Image
            第一张图片

        b : PIL.Image
            第二张图片

        round_to : int
            使bbox对齐的倍数
        '''
        box = ImageChops.difference(a, b).getbbox()
        if box is None:
            return None
        return cls._round_bbox(box, round_to)

    @staticmethod
    def _round_bbox(box, round_to=4):
        '''
        修整边界框，使边缘可以被round_to整除
        '''
        minx, miny, maxx, maxy = box
        minx -= minx%round_to
        maxx += round_to-1 - (maxx-1)%round_to
        miny -= miny%round_to
        maxy += round_to-1 - (maxy-1)%round_to
        return (minx, miny, maxx, maxy)

    @staticmethod
    def _merge_bbox(a, b):
        '''
        返回同时包含bbox a和b的边界框
        '''
        if a is None:
            return b

        if b is None:
            return a

        minx = min(a[0], b[0])
        miny = min(a[1], b[1])
        maxx = max(a[2], b[2])
        maxy = max(a[3], b[3])
        return (minx, miny, maxx, maxy)

    def update(self, data, xy, dims, mode):
        raise NotImplementedError


class AutoEPDDisplay(AutoDisplay):
    '''
    此类初始化EPD，并使用它来显示更新。
    '''

    def __init__(self, epd=None, vcom=-1.75, **kwargs):

        if epd is None:
            if EPD is None:
                raise RuntimeError('导入EPD接口时出现问题。 您是否建立了 '
                                   '与后端 "pip install ./" 或 "python setup.py '
                                   'build_ext --inplace"?')

            epd = EPD(vcom=vcom)
        self.epd = epd
        AutoDisplay.__init__(self, self.epd.width, self.epd.height, **kwargs)

    def update(self, data, xy, dims, mode):

        # 发送图像到控制器
        self.epd.wait_display_ready()
        self.epd.load_img_area(
            data,
            xy=xy,
            dims=dims
        )

        # 显示发送的图像
        self.epd.display_area(
            xy,
            dims,
            mode
        )


class VirtualEPDDisplay(AutoDisplay):
    '''
    此类会打开一个Tkinter窗口，显示将在
    EPD，无需物理电子纸设备即可进行测试
    '''

    def __init__(self, dims=(1200,800)):
        AutoDisplay.__init__(self, dims[0], dims[1])

        self.root = tk.Tk()
        self.pil_img = self.frame_buf.copy()
        self.tk_img = ImageTk.PhotoImage(self.pil_img)
        self.panel = tk.Label(self.root, image=self.tk_img)
        self.panel.pack(side="bottom", fill="both", expand="yes")

    def __del__(self):
        self.root.destroy()

    def update(self, data, xy, dims, mode):
        data_img = Image.frombytes(self.frame_buf.mode, dims, bytes(data))
        self.pil_img.paste(data_img, box=xy)
        self.tk_img = ImageTk.PhotoImage(self.pil_img)
        self.panel.configure(image=self.tk_img) # 不知道这是否真的必要

        # 允许Tk做任何需要做的事
        self.root.update()
