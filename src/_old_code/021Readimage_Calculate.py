import os
import cv2
FRAME_WIDTH = 1280      #分辨率参数
FRAME_HEIGHT = 720  
FPS = 60                #刷新率参数
CAMERA_INDEX = 1        #选择摄像头

WIDTH = 810
HEIGHT = 985
Time_Delay = 25

LOOP = 1        #定义循环参数，勿改！！！！

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
        
        i = 1
        cv2.imshow(f'USB Camera {camera_index}', frame)
        cv2.imwrite(f'capture_{i}.jpg', frame)
        i = i + 1


        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('s'):
            cv2.imwrite(f'capture_{camera_index}.jpg', frame)

            print("图片已保存")
    
    cap.release()
    cv2.destroyAllWindows()
##结束定义摄像头调用函数Camera_Use##


Camera_Use(CAMERA_INDEX)