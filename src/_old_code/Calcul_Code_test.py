import cv2
import serial #用于在 Python 中实现与外部设备的串口通信。这里用来与 Arduino 板子通信，发送移动指令。
import time #导入时间库，用于实现程序中的延时（time.sleep()），例如等待 Arduino 初始化或等待液滴移动完成。
import numpy as np #导入 NumPy 库，这是 Python 科学计算的基础库。OpenCV 的很多函数都依赖于 NumPy 数组来表示图像。虽然在这个简化版本中没有直接调用np，但它是cv2正常工作所必需的。


class SimpleDropletControl: #封装一个简易控制液滴运动的类
    def __init__(self, com_port='COM3', baudrate=9600): 
        # com_port参数为端口号，baudrate为串口通信波特率
        # 初始化串口
        self.ser = serial.Serial(com_port, baudrate, timeout=1)
        time.sleep(2)  # 等待Arduino初始化
        # 初始化摄像头
        self.cap = cv2.VideoCapture(1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # 通过实验标定的时间参数（需要由实验测试得出）
        self.time_params = {
            # 格式: 距离(mm): (加速时间, 滑行时间, 减速时间)
            50: (0.8, 0.3, 0.7), ##a = {key:value}
            100: (1.2, 0.5, 1.0),
            150: (1.8, 0.7, 1.5),
            200: (2.4, 0.9, 2.0),
            250: (3.0, 1.1, 2.5)
        }
    
    #读取液滴当前位置
    #目标：读取失败时打印提示信息，读取成功则返回一个x坐标给函数
    def detect_position(self):
        print("任务1-检测液滴位置")
        ret, frame = self.cap.read() #读取摄像机捕捉的RGB数组信息
        if not ret: #读取失败的逻辑（摄像头被拔掉、线路损坏...)
            return None
            
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
    
    #定义移动到目标位置的函数
    def move_to_target(self, target_x):
        current_x = self.detect_position() ##调用先前定义的detect_position函数
        if current_x is None:
            print("无法检测到液滴!")
            return False
            
        distance = abs(target_x - current_x)
        direction = "RIGHT" if target_x > current_x else "LEFT"
        
        #获取时间参数（可以用线性插值法）这个函数(get_time_parameters())之后再定义
        accel_time, coast_time, decel_time = self.get_time_parameters(distance)
        
        #发送移动命令到Arduino
        #####IMPORTANT!!!!这一步需要对接Arduino！！！！！！！  
        command = f"MOVE {direction} {accel_time:.2f} {coast_time:.2f} {decel_time:.2f}\n"
        self.ser.write(command.encode())
        
        print(f"移动命令: {command.strip()}")
        
        #等待运动完成
        total_time = accel_time + coast_time + decel_time + 0.5  # 加0.5秒缓冲
        time.sleep(total_time)
        
        #检查最终位置
        final_x = self.detect_position()
        if final_x is not None:
            error = abs(final_x - target_x)
            print(f"移动完成! 误差: {error} 像素")
            return error < 20  # 误差小于20像素认为成功
        else:
            print("移动完成，最终位置偏差较大")
            return False
    
##########IMOPRTANT!!!!!!!!这一步是实现精确运动的核心计算函数！！！！！————————————-
##########数据来源依托于__inti__初始化方法中定义的时间“字典”！
    #定义move_to_target(a,b)中的时间参数计算函数（可以考虑线性插值法）
    def get_time_parameters(self, distance):
        distances = sorted(self.time_params.keys())
        
        if distance <= distances[0]:
            return self.time_params[distances[0]]
        elif distance >= distances[-1]:
            return self.time_params[distances[-1]]
        else:
            #找到包围的距离区间
            for i in range(len(distances)-1):
                if distances[i] <= distance <= distances[i+1]:
                    #线性插值
                    d1, d2 = distances[i], distances[i+1]
                    t1 = self.time_params[d1]
                    t2 = self.time_params[d2]
                    
                    ratio = (distance - d1) / (d2 - d1)
                    
                    accel = t1[0] + ratio * (t2[0] - t1[0])
                    coast = t1[1] + ratio * (t2[1] - t1[1])
                    decel = t1[2] + ratio * (t2[2] - t1[2])
                    
                    return (accel, coast, decel)
        
        return self.time_params[100]  #默认值
    

    ##这是一个便于实验收集时间表的程序~~~ QwQ
    def calibrate_system(self):
        """系统标定：测试不同距离所需的时间"""
        print("开始系统标定...")
        print("请将液滴放置在起始位置，按回车继续")
        input()
        
        start_pos = self.detect_position()
        if start_pos is None:
            print("无法检测液滴位置")
            return
            
        test_distances = [50, 100, 150, 200, 250]  #像素距离
        
        for distance in test_distances:
            print(f"\n测试距离: {distance} 像素")
            print("请记录实际运动情况，并输入最佳时间参数")
            
            #测试加速时间
            accel = float(input("加速时间(秒): "))
            coast = float(input("滑行时间(秒): "))
            decel = float(input("减速时间(秒): "))
            
            self.time_params[distance] = (accel, coast, decel)
            
            print(f"已记录: {distance}px -> ({accel}s, {coast}s, {decel}s)")
        
        print("\n标定完成!")
        print("时间参数:", self.time_params)
    
    def manual_control(self):
        """手动控制模式"""
        print("手动控制模式")
        print("命令: move [left/right] [时间] - 单向移动")
        print("      stop - 停止")
        print("      exit - 退出")
        
        while True:
            cmd = input("> ").strip().split()
            if not cmd:
                continue
                
            if cmd[0] == "move" and len(cmd) == 3:
                direction = cmd[1].upper()
                move_time = float(cmd[2])
                
                if direction == "RIGHT":
                    self.ser.write(f"MOVE RIGHT {move_time} 0 0\n".encode())
                elif direction == "LEFT":
                    self.ser.write(f"MOVE LEFT {move_time} 0 0\n".encode())
                    
            elif cmd[0] == "stop":
                self.ser.write(b"STOP\n")
                
            elif cmd[0] == "exit":
                break
    
    def cleanup(self):
        """清理资源"""
        self.ser.write(b"STOP\n")
        self.ser.close()
        self.cap.release()
        cv2.destroyAllWindows()

# 使用示例
if __name__ == "__main__":
    #请根据实际情况修改串口号
    controller = SimpleDropletControl(com_port='COM3')
    
    try:
        print("选择模式: 1-标定, 2-自动移动, 3-手动控制")
        choice = input().strip()
        
        if choice == "1":
            controller.calibrate_system()
        elif choice == "2":
            target = int(input("输入目标位置(像素): "))
            success = controller.move_to_target(target)
            print(f"移动结果: {'成功' if success else '失败'}")
        elif choice == "3":
            controller.manual_control()
            
    finally:
        controller.cleanup()