"""
--- Galinstan 视觉伺服感知引擎 (v2.0 CSRT 版) ---
核心逻辑已由“全局图像分割”更替为“局部特征追踪 (CSRT)”。
外部调用者只需在进入主循环前调用一次 calibrate() 即可，
原有 process_frame() 的 API 契约保持不变。
"""

import cv2
import numpy as np
from collections import deque

class GalinstanTracker:
    def __init__(self, buffer_sec=4, fps=30):
        # 1. 状态寄存器 (维持原样，供物理预测使用)
        self.history = deque(maxlen=buffer_sec * fps)
        self.last_pos = None

        # 2. 核心：初始化 CSRT 追踪器引擎
        try:
            self.tracker = cv2.TrackerCSRT_create()
        except AttributeError:
            self.tracker = cv2.legacy.TrackerCSRT_create()

        self.is_initialized = False

        # 3. 兼容性填充：防报错机制
        # 即使现在不需要调参，也要保留这个字典，防止 UI 端调用时崩溃
        self.params = {"C": 0, "kernel": 0, "min_area": 0} 

    def update_params(self, new_params):
        """
        兼容原有的参数更新接口。
        由于 CSRT 算法无需手动调参，此处直接吞掉传进来的参数，做静默处理。
        """
        pass 

    def calibrate(self, first_frame):
        """
        物理目标锁定（标定）。
        这相当于给导弹的导引头注入目标特征，必须在主循环前调用。
        """
        print("[系统提示] 开启视网膜标定。请框选液态金属，按 SPACE 确认。")
        bbox = cv2.selectROI("Calibration: Select Galinstan", first_frame, showCrosshair=True, fromCenter=False)
        cv2.destroyWindow("Calibration: Select Galinstan")

        if bbox[2] == 0 or bbox[3] == 0:
            print("[致命错误] 未选择有效物理区域。")
            return False

        # 启动追踪器
        self.tracker.init(first_frame, bbox)
        self.is_initialized = True
        return True

    def process_frame(self, frame, debug=False):
        """
        唯一的公共感知接口：输入光场，输出质心坐标 [x, y]。
        """
        if frame is None or not self.is_initialized:
            return None

        # --- 核心感知逻辑 ---
        # 算法会自动寻找与标定阶段最相似的 HOG 特征块
        success, bbox = self.tracker.update(frame)

        debug_canvas = frame.copy() if debug else None

        if success:
            # 提取边界框坐标并计算几何中心
            x, y, w, h = [int(v) for v in bbox]
            cX = x + w // 2
            cY = y + h // 2
            pos = [cX, cY]

            # 更新物理状态记忆
            self.history.append(pos)
            self.last_pos = pos

            # 调试渲染
            if debug:
                cv2.rectangle(debug_canvas, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(debug_canvas, (cX, cY), 4, (0, 0, 255), -1)
                cv2.putText(debug_canvas, f"LOCKED: [{cX}, {cY}]", (cX - 40, cY - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.imshow("Debug_Vision_Tracking", debug_canvas)

            return pos
        else:
            # 目标逃逸或被严重遮挡
            if debug:
                cv2.putText(debug_canvas, "LOST TARGET", (100, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)
                cv2.imshow("Debug_Vision_Tracking", debug_canvas)
            return None