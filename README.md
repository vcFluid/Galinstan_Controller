# Above_All:
1.I made these code at 2025_10_11, and upload them into github at 2026_1_28
2.What I want to gain from this item is
    2-1 Python learning.                                        ☆☆☆☆☆
    2-2 The Physical mechanisms of liquid metals Galinstan.     ☆☆☆☆☆
    2-3 Practise my academic English-expression.                ☆☆☆
    2-4 Academic Norms.                                         ☆☆☆☆☆
    2-5 How to use github to creat my personal repository       ☆☆
    2-6 Software Engineering Architecture                       ☆☆☆

# References:




# The Complete code implementation ideas
Please navigate to the folder Map_to_Aim 😉

# 两个方向

    理论推到得到F的理论解，直接求出到目标位置需要的电场强、通电时间

    用两个位矢（初始构型位矢和目标位矢）计算出参变量，拟合出半理论半经验公式

#### 当前目标
在二维平板中，提供准一维匀强电场，通过调控电路通断、电极正负，实现液滴加速与减速

从而实现在一个方向上（准一维）输入一个坐标值，使液态金属运动到该指定坐标

#### 最终目标
在二维平板中，使用类似的方法实现液态金属的二维精确运动 

# 项目拆解
## 1、摄像头初始化(opencv)
[已完成](camera_initialization.py)
    目标：
        ①初始化摄像头，获得每一毫秒图像信息（RGB数组信息）
        ②通用性（更换摄像机，更换摄像机分辨率、刷新率）

## 2、储存图像数据，获取液滴参考位置(opencv)
[已完成]()
    目标：
        ①将第1步获取的RGB数组储存，并转换为灰度图√
        ②定义x-y坐标系
        ③利用灰度图数组定义液滴位置(x)（由于液态金属形状可能会改变，如何确定液态金属的位置？）
        ④获得液态金属初始参考位置，并记录
        ⑤停止记录

## 3、输入指定坐标
[未完成]()
    目标：
        自动检测坐标位置是否合适（防止设定位置超出平板范围，导致碰壁）

## 4、利用物理关系计算到达指定位置所需通电/断电时间
[未完成]()

## 5、输出到arduino板
[未完成]()
如何解决从python结果到arduino板的输出？？————串口通信

## 6、arduino板输出电极信号至继电器
[未完成]()

## 7、整合恒稳直流电源(12-30V)至继电器

# 可以更新的地方
## 1、寻找最适摄像头参数（防止性能溢出）
## 2、由测定静止液滴参考位置 更新 为可以测定任意时刻处于低俗运动中液滴的参考位置
## 3、检测一个运动中的液滴的位置
## 4、是不是可以接入ai大模型训练，用大量不同电压，不同通断电时间，运动到的位置的统计规律，利用线性插值法，得到经验方程
## 5、使液滴由准一维运动变为按某个固定轨迹运动（从L形到矩形到圆形到圆锥曲线）
## 6、视觉捕捉是否可借助AI确定液态金属（对于大尺度情况）的外形，
