import cv2 # OpenCV 用于图像处理，相当于视觉系统的“眼睛”
import numpy as np # NumPy 用于矩阵运算，处理坐标数据和图像数据
from collections import deque # 双向队列用于存储历史坐标，方便计算速度和加速度；其中from A import B 是 Python 的导入语法，表示从模块 A 中导入 B 类或函数。


class GalinstanTracker: #声明一个名为 GalinstanTracker 的类，[负责跟踪液态金属球的位置和运动状态。]
    def __init__(self, buffer_sec=4, fps=30): #初始化函数，设置坐标缓存的时间长度和帧率，确保能够存储足够的历史数据以计算速度和加速度。
        
        # 建立 1-4 秒的坐标缓存 [x, y, timestamp]
        self.history = deque(maxlen=buffer_sec * fps)
        self.origin = None # 参考点 (x0, y0)
        self.alpha = 0.1   # 初始标定系数 mm/pixel
        self.last_pos = None # 用于记录上一帧位置，实现 ROI

    # 双向队列是指一种数据结构，允许在两端进行高效的插入和删除操作。
    # 在这个代码中，
    # self.history 是一个双向队列，用于存储最近 buffer_sec 秒内的坐标数据，每个元素是一个包含 x 坐标、y 坐标和时间戳的列表。
    # deque 用于存储最近 buffer_sec 秒内的坐标数据，maxlen 参数确保队列不会无限增长，始终保持在指定长度。
    # self.origin 用于存储参考点的坐标，初始值为 None，表示尚未设置。
    # self.alpha 是一个标定系数，初始值为 0.1 mm/pixel，可以根据实际情况进行调整，以将像素坐标转换为物理距离。

    #关于__init__括号内的参数：
    # buffer_sec: 这是一个整数参数，表示坐标缓存的时间长度，以秒为单位。它决定了历史坐标数据的保留时间。例如，如果 buffer_sec 设置为 4，系统将保留最近 4 秒内的坐标数据。
    # fps: 这是一个整数参数，表示每秒钟处理的帧数（frames per second）。它用于计算坐标缓存的最大长度。具体来说，maxlen 参数被设置为 buffer_sec * fps，这意味着队列将最多保留 buffer_sec 秒内的坐标数据。例如，如果 buffer_sec 是 4 秒，fps 是 30，那么 maxlen 将是 120，这意味着队列将最多保留最近 120 帧的坐标数据。
    # self是一个特殊的参数，表示类的实例本身。在类的方法中，self 用于访问实例的属性和方法。通过 self.history、self.origin 和 self.alpha，可以在类的其他方法中访问和修改这些属性。
    # 可以理解为self就是这个类的“姓”，而history、origin和alpha是这个类的“名”。通过self.history、self.origin和self.alpha，我们可以在类的其他方法中访问和修改这些属性，就像我们在日常生活中通过姓氏来识别一个人一样，通过self来识别这个类的实例。

    # Keywords:
    # - class: 用于定义一个类，表示一个对象的蓝图或模板。
    # - def: 用于定义一个函数或方法，表示一个可执行的代码块。
    # - self: 在类的方法中，self 是一个特殊的参数，表示类的实例本身。通过 self 可以访问实例的属性和方法。
    # - __init__: 这是一个特殊的方法，称为构造函数，在创建类的实例时自动调用。它用于初始化实例的属性。
    # - deque: 双向队列，是一种数据结构，允许在两端进行高效的插入和删除操作。在这个代码中，deque 用于存储最近 buffer_sec 秒内的坐标数据。
    # - self.xxx: 这是一个属性访问的语法，表示访问类实例的属性。例如，self.history 表示访问当前实例的 history 属性。


    def process_frame(self, frame):
        if frame is None: return None
        
        # --- 步骤 1: 确定搜索区域 (ROI) ---
        # 如果有上一帧位置，我们只看局部；如果没有，看全图
        h, w = frame.shape[:2]
        roi_size = 150 # 搜索框大小
        
        if self.last_pos is not None:
            x_s = max(0, int(self.last_pos[0] - roi_size//2))
            y_s = max(0, int(self.last_pos[1] - roi_size//2))
            roi_img = frame[y_s:y_s+roi_size, x_s:x_s+roi_size]
        else:
            roi_img = frame
            x_s, y_s = 0, 0

        # --- 步骤 2: 精细化预处理 ---
        gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
        # 增加对比度：让灰色的阴影变白，黑色的球更黑
        # 强制将灰度 > 100 的区域全部视为背景（针对白纸黑球模型）
        _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)

        # --- 步骤 3: 形态学切断 (腐蚀) ---
        # 使用 3x3 核进行腐蚀，切断与阴影的微弱连接
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.erode(thresh, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1) # 再补回来

        # --- 步骤 4: 轮廓筛选 (面积 + 圆度) ---
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_cnt = None
        min_error = float('inf')
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 50 < area < 5000: # 根据你的球大小调整
                # 进阶筛选：计算“圆度”，阴影通常是不规则的
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0: continue
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                # 圆度越接近 1 越像球，阴影的圆度通常很低
                if circularity > 0.6: 
                    # 如果有多个，选面积最接近预期的或离上一帧最近的
                    best_cnt = cnt
                    break

        # --- 步骤 5: 坐标还原 ---
        if best_cnt is not None:
            M = cv2.moments(best_cnt)
            if M["m00"] != 0:
                # 局部坐标转回全局坐标
                cX = (M["m10"] / M["m00"]) + x_s
                cY = (M["m01"] / M["m00"]) + y_s
                self.last_pos = [cX, cY]
                return self.last_pos
        
        # 如果丢帧了，重置 ROI
        self.last_pos = None
        return None

    def get_focus_score(self, frame):
        """为未来 XYZ 运动预留：计算拉普拉斯方差作为对焦评价"""
        return cv2.Laplacian(frame, cv2.CV_64F).var()
        # 这个方法 get_focus_score 是一个占位函数，预留用于未来的 XYZ 运动跟踪功能。它通过计算图像的拉普拉斯方差来评估图像的对焦质量。
        # cv2.Laplacian 是 OpenCV 中的一个函数，用于计算图像的拉普拉斯变换，cv2.CV_64F 表示输出图像的数据类型为 64 位浮点数。
        # var() 方法用于计算拉普拉斯图像的方差，方差越大，表示图像的边缘信息越丰富，对焦质量越好；方差越小，表示图像较为模糊，对焦质量较差。
        # 这个方法可以在未来的 XYZ 运动跟踪中用于评估图像的清晰度，从而帮助调整相机的焦距以获得更清晰的图像。

# 综上，这个程序可以实现的功能可简述为：
# 1. 通过摄像头捕捉图像帧，并使用 OpenCV 进行图像处理，提取液态金属球的质心位置。
# 2. 使用双向队列存储最近几秒钟的坐标数据，以便后续计算速度和加速度。
# 3. 预留了一个方法用于评估图像的对焦质量，为未来的 XYZ 运动跟踪功能做准备。

# 此外，引入的误差有
# 1. 图像噪声：摄像头捕捉的图像可能包含噪声，尤其是在低光照条件下，这可能导致质心计算不准确。
# 2. 液滴形状变化：液态金属球可能会因为运动或外部因素而改变形状，且质量分布可能并不均匀（尤其是考虑到表面的化学反应），这可能影响质心的计算。
# 3. 标定误差：初始的标定系数 alpha 可能不准确，导致像素坐标转换为物理距离时存在误差。
# 4. 处理延迟：图像处理和计算可能会引入延迟，尤其是在高帧率下，这可能影响实时跟踪的效果。


# 关于代码的详细解释可以参照最近这几年的书籍：
# 书1 - 《OpenCV 4计算机视觉编程》，作者：Joseph Howse，出版社：Packt Publishing，出版日期：2020年。
# 书2 - 《Python图像处理与计算机视觉》，作者：Jan Erik Solem，出版社：Manning Publications，出版日期：2012年。
# 这两本书都涵盖了OpenCV的基础知识和应用，适合初学者和有一定经验的开发者。第一本书更侧重于OpenCV 4的最新功能和实践，而第二本书则提供了更广泛的图像处理和计算机视觉技术的介绍。