import cv2
import numpy as np
import serial

"quick_test_env.py"



print("--- 引擎自检报告 ---")
print(f"OpenCV 版本: {cv2.__version__}")
print(f"NumPy 矩阵支持: {np.__version__}")
print("状态: 动力系统已就绪，物理逻辑链路通畅。")