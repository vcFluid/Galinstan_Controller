import cv2 # OpenCV 用于图像处理，相当于视觉系统的“眼睛”
import numpy as np # NumPy 用于矩阵运算，处理坐标数据和图像数据
from collections import deque # 双向队列用于存储历史坐标，方便计算速度和加速度；其中from A import B 是 Python 的导入语法，表示从模块 A 中导入 B 类或函数。

class GalinstanTracker: #声明一个名为 GalinstanTracker 的类，[负责跟踪液态金属球的位置和运动状态。]
    def __init__(self, buffer_sec=4, fps=30): #初始化函数，设置坐标缓存的时间长度和帧率，确保能够存储足够的历史数据以计算速度和加速度。
        # 建立 1-4 秒的坐标缓存 [x, y, timestamp]
        self.history = deque(maxlen=buffer_sec * fps)
        self.origin = None # 参考点 (x0, y0)
        self.alpha = 0.1   # 初始标定系数 mm/pixel

    def process_frame(self, frame):
        # 1. 预处理：灰度 + 模糊（减阻）
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        # 2. 提取液滴：二值化 + 闭运算（确保连通性）
        _, mask = cv2.threshold(blurred, 50, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 3. 计算质心（矩方法）
        M = cv2.moments(mask)
        if M["m00"] > 50: # 过滤噪声点
            cX = M["m10"] / M["m00"]
            cY = M["m01"] / M["m00"]
            
            # 初始化参考点
            if self.origin is None:
                self.origin = (cX, cY)
            
            current_pos = [cX, cY]
            self.history.append(current_pos)
            return current_pos
        return None

    def get_focus_score(self, frame):
        """为未来 XYZ 运动预留：计算拉普拉斯方差作为对焦评价"""
        return cv2.Laplacian(frame, cv2.CV_64F).var()