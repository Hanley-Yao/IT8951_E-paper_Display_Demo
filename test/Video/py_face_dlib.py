import multiprocessing as mp  # �����֧�ֿ�
import cv2  # ͼ�����
import dlib  # ����ѧϰ��
import RPi.GPIO as GPIO  # Ӳ��GPIO���ƿ�

GPIO.setwarnings(False)  # ����GPIOռ�þ���
GPIO.setmode(GPIO.BCM)  # ����������ʽΪBCM
GPIO.setup(26, GPIO.IN)  # ����BCM���������µ�26��GPIOΪ����īˮ

def detect_face(frame,value):  # ������⺯���ص�
    img = frame
    dets = detector(img, 1)
    for index, face in enumerate(dets):
        left = face.left()
        top = face.top()
        right = face.right()
        bottom = face.bottom()
#��Ϊ���û�м�⵽���������ĸ������ǲ����ڵģ�
#�ᱨ��UnboundLocalError�Ĵ�������Ҫ����һ�¡�           
    try:
        value[:] = [left,top,right,bottom]
    except UnboundLocalError:
        value[:] = [0,0,0,0]

def draw_line(img,box):
    left = box[0]
    top = box[1]
    right = box[2]
    bottom = box[3]
#����������img���򣬲�����
    cv2.rectangle(img, (left*4, top*4), (right*4, bottom*4), (255, 255, 255), 10)
    return img
if __name__=='__main__':
#initial detector and cap
#��ݮ�ɵ������ڴ����ޣ�����Ҫ���ɼ���ͼƬ������СһЩ�����ڼ��㡣
    detector = dlib.get_frontal_face_detector() #��ȡ����������for face detection
    cap = cv2.VideoCapture(0)  #Turn on the camera
    cap.set(3,640)
    cap.set(4,640)
#initial boxes
#��ʼ�������ĳ�ʼλ��
    box1 = mp.Array('i',[0,0,0,0])
    box2 = mp.Array('i',[0,0,0,0])
    
#initial Windowbox
    cv2.namedWindow('success', cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow('success', 200, 200)
#initial frames and processes
#��Ҫ�������̴���ͼƬ���ü��飬���������õ�Խ��Խ�ã�
#��ݮ�ɵ�CPUһ����4���ˣ�ȫ�����Ͽ��ܻ�Ӱ�����������ܣ��Լ��Ե�ʱ��2�����һ�㡣
    ret, frame11 = cap.read()
    img11 = cv2.resize(frame11,(160,160))
    res1 = mp.Process(target=detect_face,args=(img11,box1))
    res1.start()
#���԰�ʶ���õ�ͼƬ������С�����Լӿ��ٶȣ�ͬʱҲ���Լ���cpu������
#Ȼ���ٰ�ʶ���������Ӧ��������ԭͼƬ�Ϸų���
    ret, frame21 = cap.read()
    img21 = cv2.resize(frame21,(160,160))
    res2 = mp.Process(target=detect_face,args=(img21,box2))
    res2.start()
    while(cap.isOpened()):
#process 1
 #�����Ҫ��֡�����Ǿ���pass���������֡��ѡ����������
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

        if cv2.waitKey(1) & 0xFF == ord('q') or GPIO.input(26) == 0:  # �ж�26��GPIO��״̬��Ϊ�͵�ƽ���˳����򣬴Ӷ���ɱ������������Ƶ�Ŀ�ġ�
            Break

    cv2.destroyAllWindows()
cap.release()
#### END ####
