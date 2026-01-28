import os
import cv2
FRAME_WIDTH = 1280      #分辨率参数
FRAME_HEIGHT = 720  
FPS = 60                #刷新率参数
CAMERA_INDEX = 1        #选择摄像头

frames_save_path = r"D:\IETitem\code\picture1.jpg\\"
WIDTH = 810
HEIGHT = 985
Time_Delay = 25

LOOP = 1        #定义循环参数，勿改！

##开始定义摄像头调用函数Camera_Use##
def Camera_Use(camera_index=0): 
    print("稍后将显示指定摄像头的实时画面")
    cap = cv2.VideoCapture(camera_index)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    if not cap.isOpened():
        print(f"哦哟，打不开摄像头哦 {camera_index}")
        return
        
    REAL_WIDTH=cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    REAL_HEIGHT=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    REAL_FPS=cap.get(cv2.CAP_PROP_FPS)
    print(REAL_WIDTH, REAL_HEIGHT, REAL_FPS)

    print("按 'q' 键退出，按 's' 键保存图片")

    while True:
        ret, frame = cap.read() 
        if not ret:
            print("error.摄像头信号丢失.无法读取帧")
            break

        cv2.imshow(f'USB Camera {camera_index}', frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'picture{camera_index}.jpg', frame)

            print("图片已保存")

    cap.release()
    cv2.destroyAllWindows()
##结束定义摄像头调用函数Camera_Use##

##定义坐标计算函数obtain_position##

def obtain_position():
        print("任务1-检测液滴位置")
        frame = frames_save_path #读取摄像机捕捉的RGB数组信息
            
        #转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #简单阈值处理；当像素值小于等于127时，在图像中设置为255（THRESH_BINARY_INV函数方法），否则设置为0
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        #寻找轮廓
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:##当没有找到轮廓时的逻辑
            print("靠，图像中无任何轮廓")
            return None
            
        #找到最大轮廓（防止有气泡等干扰）
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        
        # 简化为x坐标（一维位置）
        print(f"报告!找到液滴，它当前在{x}")
        return x


Camera_Use(CAMERA_INDEX)

obtain_position()