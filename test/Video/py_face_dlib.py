import multiprocessing as mp  # 多进程支持库
import cv2  # 图像处理库
import dlib  # 机器学习库
import RPi.GPIO as GPIO  # 硬件GPIO控制库

GPIO.setwarnings(False)  # 禁用GPIO占用警告
GPIO.setmode(GPIO.BCM)  # 设置命名方式为BCM
GPIO.setup(26, GPIO.IN)  # 设置BCM命名规则下的26号GPIO为输入墨水

def detect_face(frame,value):  # 人脸检测函数回调
    img = frame
    dets = detector(img, 1)
    for index, face in enumerate(dets):
        left = face.left()
        top = face.top()
        right = face.right()
        bottom = face.bottom()
#因为如果没有检测到脸，上面四个变量是不存在的，
#会报出UnboundLocalError的错误，所以要处理一下。           
    try:
        value[:] = [left,top,right,bottom]
    except UnboundLocalError:
        value[:] = [0,0,0,0]

def draw_line(img,box):
    left = box[0]
    top = box[1]
    right = box[2]
    bottom = box[3]
#给传进来的img画框，并返回
    cv2.rectangle(img, (left*4, top*4), (right*4, bottom*4), (255, 255, 255), 10)
    return img
if __name__=='__main__':
#initial detector and cap
#树莓派的运行内存有限，所以要将采集的图片像素缩小一些，便于计算。
    detector = dlib.get_frontal_face_detector() #获取人脸分类器for face detection
    cap = cv2.VideoCapture(0)  #Turn on the camera
    cap.set(3,640)
    cap.set(4,640)
#initial boxes
#初始化框脸的初始位置
    box1 = mp.Array('i',[0,0,0,0])
    box2 = mp.Array('i',[0,0,0,0])
    
#initial Windowbox
    cv2.namedWindow('success', cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow('success', 200, 200)
#initial frames and processes
#想要几个进程处理图片就用几组，但并不是用的越多越好，
#树莓派的CPU一共有4个核，全部用上可能会影响其他的性能，自己试的时候2个会好一点。
    ret, frame11 = cap.read()
    img11 = cv2.resize(frame11,(160,160))
    res1 = mp.Process(target=detect_face,args=(img11,box1))
    res1.start()
#可以把识别用的图片像素缩小，可以加快速度，同时也可以减少cpu负担，
#然后再把识别框扩大相应倍数，在原图片上放出。
    ret, frame21 = cap.read()
    img21 = cv2.resize(frame21,(160,160))
    res2 = mp.Process(target=detect_face,args=(img21,box2))
    res2.start()
    while(cap.isOpened()):
#process 1
 #如果想要逐帧处理，那就用pass，如果想跳帧就选择上面两句
        if (res1.is_alive()):
            ret, frame12 = cap.read()
            cv2.imshow('success',draw_line(frame12,box1))            
        else:
            ret, frame11 = cap.read()
            cv2.imshow('success',draw_line(frame11,box1))
            img11 = cv2.resize(frame11,(160,160))           
            res1 = mp.Process(target=detect_face,args=(img11,box1))
            res1.start()
#process 2
        if (res2.is_alive()):
            ret, frame22 = cap.read()
            cv2.imshow('success',draw_line(frame22,box2))  

        else:
            ret, frame21 = cap.read()
            cv2.imshow('success',draw_line(frame21,box2))
            img21 = cv2.resize(frame21,(160,160)) 
            res2 = mp.Process(target=detect_face,args=(img21,box2))
            res2.start()

        if cv2.waitKey(1) & 0xFF == ord('q') or GPIO.input(26) == 0:  # 判断26号GPIO的状态若为低电平则退出程序，从而达成被主程序隔离控制的目的。
            Break

    cv2.destroyAllWindows()
cap.release()
#### END ####
