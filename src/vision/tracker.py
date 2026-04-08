import cv2 # OpenCV 用于图像处理，相当于视觉系统的“眼睛”
import numpy as np # NumPy 用于矩阵运算，处理坐标数据和图像数据
from collections import deque # 双向队列用于存储历史坐标，方便计算速度和加速度；其中from A import B 是 Python 的导入语法，表示从模块 A 中导入 B 类或函数。

BUFFER_SEC = 4 # 坐标缓存的时间长度，单位为秒，确保能够存储足够的历史数据以计算速度和加速度。
FPS = 30 # 设定帧率，确保坐标缓存能够覆盖足够的时间长度以计算速度和加速度。
DEBUG = True # 调试模式开关，开启后会显示中间处理结果的窗口，帮助调试图像处理算法。

class GalinstanTracker: # 定义一个名为 GalinstanTracker 的类，[用于负责跟踪液态金属球的**位置**和**运动状态**]，其包含了一个初始化方法 __init__ 和一个处理图像帧的方法 process_frame，以及一些**私有方法**用于图像预处理、分割和提取质心位置。
    def __init__(self, buffer_sec=BUFFER_SEC, fps=FPS): # 初始化函数，设置坐标缓存的时间长度和帧率，确保能够存储足够的历史数据以计算速度和加速度。
        self.history = deque(maxlen=buffer_sec * fps) # 对象属性 history 是一个双向队列，用于存储最近 buffer_sec 秒内的坐标数据，每个元素是一个包含 x 坐标、y 坐标和时间戳的列表。maxlen 参数确保队列不会无限增长，始终保持在指定长度。
        self.last_pos = None  # 预留给 ROI 追踪的上一个位置，初始值为 None（空），表示尚未设置。
        self.debug_frames = {"preprocessed": None, "mask": None, "blob": None}

        # --- 新增：用于缓存中间调试图 ---
        self.debug_frames = {
            "preprocessed": None,
            "mask": None,
            "blob": None
        }
    def process_frame(self, frame, debug = False): 
        # frame 是一个图像帧，通常是从摄像头捕捉到的图像数据。这个方法的主要功能是处理输入的图像帧，提取液态金属球的质心位置，并将其存储在 history 中以便后续计算速度和加速度。
        # 函数参数的传入逻辑是：外部调用者（例如主程序或测试代码）会捕捉到图像帧，并将其作为参数传递给 process_frame 方法。这个方法会对图像帧进行处理，提取出液态金属球的位置，并将其存储在 history 中以便后续使用。
        # 对比C语言，python中的函数参数传递是通过引用传递的，这意味着当你将一个对象（如列表、字典或自定义类实例）作为参数传递给函数时，函数内部对该对象的修改会影响到外部的对象。这与C语言中的值传递不同，在C语言中，基本数据类型（如整数、浮点数）是通过值传递的，而复杂数据结构（如数组、结构体）通常是通过指针传递的。
        # 这里的frame是形式参数，表示函数定义时使用的变量名，而实际传入的图像帧是实参。当调用process_frame方法时，实参会被传递给形式参数frame，函数内部使用frame来处理图像数据。
        # "当调用函数时，别人会扔进来一个东西，在这个函数内部，这个东西叫frame"

        # 只需在外部函数调用时传入图像帧，process_frame 方法会处理该帧并更新类的状态（如 history 和 last_pos），无需担心参数传递的细节，因为 Python 的引用传递机制会自动处理这些问题。

        # self 是一个特殊的参数，表示类的实例本身。在类的方法中，self 用于访问实例的属性和方法。通过 self.history 和 self.last_pos，可以在类的其他方法中访问和修改这些属性。
        # 为什么不把self删掉? 因为 self 是 Python 类方法的约定参数，用于表示当前实例。它允许方法访问和修改实例的属性和其他方法。如果删除 self，方法将无法访问实例的属性（如 history 和 last_pos），也无法调用其他实例方法，这会导致代码无法正常工作。因此，self 是必不可少的，用于确保类的方法能够正确地操作实例的数据和行为。
        # 也就是说self参数是为了让这个方法能够访问和修改类的属性，类似于姓名中的“姓”，通过self来识别这个类的实例，从而能够访问和修改这个实例的属性（如history和last_pos）。
        # 如果删除self，方法将无法访问这些属性，也无法调用其他实例方法，这会导致代码无法正常工作。因此，self是必不可少的，用于确保类的方法能够正确地操作实例的数据和行为。
        # 例如 history 和 last_pos，以便在处理图像帧时能够存储和更新液态金属球的位置数据。
        """
        唯一的公共接口。无论GalinstanTracker的内部算法如何大改，
        外部调用者永远只传 frame ，永远只得到 [x, y] 或 None。
        """
        if frame is None: return None

        # 1. 预处理 (降噪/对比度)
        processed = self._preprocess(frame, debug=debug) # processed (预加工) 是通过调用私有方法 _preprocess（定义在下方） 对输入的图像帧 frame 进行预处理后的结果。这个预处理步骤通常包括降噪和对比度增强，以便更好地提取液态金属球的特征。
        self.debug_frames["preprocessed"] = processed # 缓存

        # 2. 分割 (二值化/去阴影)
        mask = self._segment(processed, debug=debug) # mask 是通过调用私有方法 _segment（定义在下方） 对预处理后的图像 processed 进行分割处理后的结果。这个分割步骤通常包括二值化和去除阴影，以便突出液态金属球的区域，使其更容易被提取和分析。
        self.debug_frames["mask"] = mask # 缓存

        # 3. 提取 (几何中心/物理过滤)
        pos, blob_canvas = self._find_blob(mask, debug=debug) # pos 是通过调用私有方法 _find_blob（定义在下方） 对分割后的图像 mask 进行提取处理后的结果。这个提取步骤通常包括计算液态金属球的几何中心（质心）并进行物理过滤，以确保提取到的位置是合理的，并且符合预期的物理特性。
        self.debug_frames["blob"] = blob_canvas # 缓存
        
        # 4. 状态维护
        if pos is not None:
            self.history.append(pos) 
            # .append(Y) 是 Python 中列表（list）对象的一个方法，用于在列表的末尾添加一个元素。
            # 在这个代码中，self.history 是一个双向队列（deque），它也支持 append 方法。
            # 当 pos 不为 None 时，表示成功提取到了液态金属球的位置，这个位置 pos 将被添加到 history 中，以便后续计算速度和加速度。
            # 也就是说此时的self.history = (之前的历史数据) + [当前提取到的位置 pos]，通过 append 方法将 pos 添加到 history 的末尾。
            # 且由于 history 是一个双向队列，maxlen 参数确保它不会无限增长，始终保持在指定长度（buffer_sec * fps），这意味着它会自动丢弃最旧的数据，以便始终保留最近 buffer_sec 秒内的坐标数据。
            self.last_pos = pos # 更新 last_pos 为当前提取到的位置 pos，以便在下一次处理图像帧时能够进行 ROI 追踪或其他相关操作。
        return pos

    # --- 以下是“可替换”的模块化私有方法 ---

    def _preprocess(self, frame, debug = False):
        """
        ------- v0.9 CLASH  +   双边滤波 -------
        接口预留：未来可以在这里加入 CLAHE 自适应直方图 
        """

        # 1. 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. 应用 CLAHE (限制对比度的自适应直方图均衡化)
        # clipLimit: 限制对比度放大的阈值，4.0 是一个平衡值
        # tileGridSize: 局部均衡的网格大小，8x8 适合捕获局部细节
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # 3. 双边滤波 (Bilateral Filter)
        # d=9: 像素邻域直径
        # sigmaColor: 颜色空间标准差，越大表示越宽的颜色范围会被平滑
        # sigmaSpace: 坐标空间标准差，越大表示更远的像素会相互影响
        # 相比高斯模糊，它能更好地保护球体边缘不被磨平
        denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)

        if debug:
            # 仅在调试模式下产生侧效应
            cv2.imshow("Debug_1_Preprocessed", denoised)

        return denoised

    def _segment(self, gray_img, debug = DEBUG):
        """
        ------- v0.9 局部光照免疫  +   几何形状修复 -------
        """
        # 1. 自适应阈值：对抗不均匀光照
        # blockSize=11 (必须是奇数), C=2 (从均值中减去的常数)
        # 它可以有效过滤掉大面积的缓慢变化的阴影背景
        thresh = cv2.adaptiveThreshold(
            gray_img, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # 2. 建立几何对称核 (椭圆核)
        # 针对球形/滴状物体，椭圆核比矩形核具有更好的物理适应性
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # 3. 形态学组合拳
        # 先进行‘开运算’：去除背景杂质，切断阴影毛刺
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        # 再进行‘闭运算’：填补球体中心的反光空洞
        mask = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

        # 🚀 修正：Debug 必须在 return 之前
        if debug:
            cv2.imshow("Debug_2_Segmented_Mask", mask)
            
        return mask

    def _find_blob(self, mask, debug=False):
        """
        ------- v0.9 质心坐标提取器 -------
        """
        # 1. 无条件初始化画布：将单通道掩膜转为三通道 BGR，以便后续画彩色标记
        # 即使不开 debug 窗口，按 S 键保存的数据也需要这张带标记的画布
        debug_canvas = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
        
        # 2. 寻找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_candidate = None
        best_cnt = None
        min_dist = float('inf')

        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            
            # 安全检查：避免除以零
            if perimeter == 0: continue
            
            # 计算圆度 (Circularity)
            circularity = (4 * 3.14159 * area) / (perimeter * perimeter)
            
            # --- 物理约束过滤门槛 ---
            # 建议将面积门槛提高到 300，以匹配 Galinstan 液滴的物理尺度
            if 300 < area < 15000 and circularity > 0.3:
                
                # 计算当前轮廓质心
                M = cv2.moments(cnt)
                if M["m00"] == 0: continue
                cX = M["m10"] / M["m00"]
                cY = M["m01"] / M["m00"]
                current_pos = [cX, cY]

                # 3. 运动连续性约束
                if self.last_pos is not None:
                    dist = ((cX - self.last_pos[0])**2 + (cY - self.last_pos[1])**2)**0.5
                    if dist > 150: 
                        # 距离超限，无条件在画布上画黄色，方便录像回溯
                        cv2.drawContours(debug_canvas, [cnt], -1, (0, 255, 255), 1) 
                        continue
                else:
                    dist = 0

                # 追踪逻辑：寻找距离最近的候选者
                if dist < min_dist:
                    min_dist = dist
                    best_candidate = current_pos
                    best_cnt = cnt

            else:
                # 杂质面积/圆度不达标，无条件画绿色小圈
                cv2.drawContours(debug_canvas, [cnt], -1, (0, 255, 0), 1)

        # --- 状态锁定与可视化渲染 ---
        if best_candidate is not None:
            # 最终锁定的目标画成红色
            cv2.drawContours(debug_canvas, [best_cnt], -1, (0, 0, 255), 2)
            cv2.putText(debug_canvas, "TARGET", (int(best_candidate[0]), int(best_candidate[1]-10)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
            
        # 只有在 debug 模式开启时，才把内存中的画布“推”到显示器上
        if debug:
            cv2.imshow("Debug_3_BlobDetection", debug_canvas)

        # 核心修复：返回元组 (坐标列表, 包含所有标记的 Numpy 图像矩阵)
        return best_candidate, debug_canvas
    
    

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




"""
未来可能的AI接入布局方案
class GalinstanTracker:
    def __init__(self, mode='classical', **kwargs):
        self.mode = mode # 'classical' 或 'ai'
        self.history = deque(maxlen=kwargs.get('buffer_len', 120))
        self.last_pos = None
        
        # 预留 AI 模型句柄
        self.ai_model = None
        if self.mode == 'ai':
            self._init_ai_model()

    def _init_ai_model(self):
        
        [接口预留]：在此初始化 YOLO, MobileNet 或自定义的权重文件
        
        print("正在载入 AI 推断引擎...")
        # self.ai_model = load_your_model('weights.pth')
        pass

    def process_frame(self, frame, debug=False):
        if frame is None: return None

        if self.mode == 'ai':
            # AI 轨道：直接输入原图，输出质心
            pos = self._ai_detect(frame)
        else:
            # 经典轨道：经过我们目前写好的管线
            processed = self._preprocess(frame, debug=debug)
            mask = self._segment(processed, debug=debug)
            pos = self._find_blob(mask, debug=debug)

        if pos is not None:
            self.history.append(pos)
            self.last_pos = pos
        return pos

    def _ai_detect(self, frame):
        
        [接口预留]：AI 识别逻辑
        物理本质：利用神经网络对图像进行非线性回归，提取特征质心。
        
        # 伪代码：
        # results = self.ai_model(frame)
        # return results.centroid
        return None
"""