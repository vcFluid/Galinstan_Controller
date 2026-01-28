import os
import cv2
import numpy as np


FRAME_WIDTH = 1280      #分辨率参数
FRAME_HEIGHT = 720  
FPS = 60                #刷新率参数
CAMERA_INDEX = 0        #选择摄像头

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
            # 修正：保存到指定路径
            cv2.imwrite(frames_save_path, frame)
            print("图片已保存")

    cap.release()
    cv2.destroyAllWindows()
##结束定义摄像头调用函数Camera_Use##

##开始定义计算位置坐标相关的函数##

#液滴检测相关参数(可调)
THRESHOLD_VALUE = 127  #灰度阈值分割参数
BLUR_KERNEL = (5, 5)   #高斯模糊核大小
INITIAL_FRAMES = 10    #计算初始位置的帧数

#创建存储目录
os.makedirs("recorded_rgb", exist_ok=True)
os.makedirs("recorded_gray", exist_ok=True)

def get_droplet_x(gray_frame):
    #高斯模糊去噪
    blurred = cv2.GaussianBlur(gray_frame, BLUR_KERNEL, 0)
    
    #阈值分割（假设液滴与背景有明显灰度差异）
    #若液滴比背景亮，使用THRESH_BINARY；反之使用THRESH_BINARY_INV
    ret, thresh = cv2.threshold(blurred, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)
    
    #查找轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None  #未检测到液滴
    
    #假设最大轮廓为液滴（可根据实际场景调整筛选逻辑）
    max_contour = max(contours, key=cv2.contourArea)
    
    #计算轮廓边界框中心x坐标
    x, y, w, h = cv2.boundingRect(max_contour)
    center_x = x + w // 2
    
    return center_x

def record_and_analyze():
    """主函数：记录图像数据并获取液滴初始位置"""
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    #设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)
    
    if not cap.isOpened():
        print(f"无法打开摄像头 {CAMERA_INDEX}")
        return
    
    #初始化存储变量
    rgb_frames = []          #存储RGB图像数据
    gray_frames = []         #存储灰度图像数据
    droplet_positions = []   #存储液滴x坐标
    is_recording = False     #记录状态标志
    frame_count = 0          #帧计数器
    
    print("操作说明：")
    print("  - 按 'r' 键开始记录数据")
    print("  - 按 't' 键停止记录并计算初始位置")
    print("  - 按 'q' 键退出程序")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧")
            break
        
        #转换为RGB格式（OpenCV默认读取为BGR）
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        #转换为灰度图
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #记录模式处理
        if is_recording:
            #存储帧数据
            rgb_frames.append(rgb_frame)
            gray_frames.append(gray_frame)
            
            #检测液滴位置
            droplet_x = get_droplet_x(gray_frame)
            if droplet_x is not None:
                droplet_positions.append(droplet_x)
                #在画面上标记液滴位置
                cv2.circle(frame, (droplet_x, frame.shape[0]//2), 5, (0, 255, 0), -1)
                cv2.putText(frame, f"X: {droplet_x}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            frame_count += 1
            cv2.putText(frame, f"Recording: {frame_count} frames", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        #显示实时画面
        cv2.imshow("Droplet Tracking", frame)
        
        #按键处理
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            if not is_recording:
                is_recording = True
                frame_count = 0
                print("开始记录数据...")
        elif key == ord('t'):
            if is_recording:
                is_recording = False
                print("停止记录，正在处理数据...")
                
                #保存图像数据
                np.save("recorded_rgb/all_frames.npy", np.array(rgb_frames))
                np.save("recorded_gray/all_frames.npy", np.array(gray_frames))
                
                #保存单帧图像
                for i, (rgb, gray) in enumerate(zip(rgb_frames, gray_frames)):
                    cv2.imwrite(f"recorded_rgb/frame_{i}.jpg", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                    cv2.imwrite(f"recorded_gray/frame_{i}.jpg", gray)
                
                #计算初始参考位置（取前N帧的平均值）
                if len(droplet_positions) >= INITIAL_FRAMES:
                    initial_pos = np.mean(droplet_positions[:INITIAL_FRAMES])
                    with open("initial_reference_position.txt", "w") as f:
                        f.write(f"初始参考位置X: {initial_pos:.2f}\n")
                        f.write(f"计算依据: 前{INITIAL_FRAMES}帧平均值\n")
                        f.write(f"坐标系: 图像左上角为原点，X轴向右\n")
                    print(f"初始参考位置计算完成: X = {initial_pos:.2f}")
                else:
                    print("记录帧数不足，无法计算初始位置")
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    record_and_analyze()


Camera_Use(CAMERA_INDEX)
