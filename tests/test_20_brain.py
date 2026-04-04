import time
import math # 用于处理符号函数 copysign
# 假设你的 PhysicsBrain 类定义在 src/analysis/Brain.py 中
from src.analysis.Brain import PhysicsBrain 

# --- 核心时间尺度解耦 ---
PHYSICS_DT = 0.001  # 物理世界的“普朗克时间”，极其细腻 (1ms 积分步长)
VISION_DT = 0.05    # 摄像头的采样周期，相对迟钝 (50ms，即 20FPS 视觉刷新)

KP = 0.8
KI = 0.05
KD = 0.2
TARGET_X = 100.0

# --- 物理世界的非线性边界 ---
MAX_VOLTAGE = 5.0           # 硬件最大输出电压，防止电解液沸腾
STATIC_FRICTION_TH = 0.5    # 接触线钉扎阈值：克服静摩擦所需的最小力

def test_virtual_droplet():
    # 1. 实例化“大脑”
    brain = PhysicsBrain(Kp=KP, Ki=KI, Kd=KD, target_x=TARGET_X)
    
    # 2. 初始化虚拟物理世界参数
    pos = 0.0
    vel = 0.0
    mass = 1.0
    friction_c = 0.3 # 动摩擦/粘性摩擦系数
    
    print(f"{'时间(s)':<8} | {'位置(x)':<8} | {'速度(v)':<8} | {'控制电压(V)':<10} | {'物理驱动力(N)':<10}")
    print("-" * 65)

    # 模拟总时长 3 秒
    total_time = 3.0
    # 总视觉帧数 = 3.0s / 0.05s = 60 帧
    vision_frames = int(total_time / VISION_DT)

    # ==========================================
    # [外层循环：控制系统] 按照视觉帧率运转
    # ==========================================
    for frame in range(vision_frames):
        current_time = frame * VISION_DT
        
        # --- [Think] 大脑睁眼获取视觉数据，计算决策 ---
        # 大脑认为过了 VISION_DT 的时间，给出这一帧的理想电压
        voltage = brain.think([pos, 0], dt=VISION_DT)
        
        # 【执行器约束】：电压饱和截断（防止烧毁或产生气泡）
        voltage = max(min(voltage, MAX_VOLTAGE), -MAX_VOLTAGE)

        # 解析实际电毛细驱动力
        if abs(voltage) > brain.voltage_threshold:
            active_v = abs(voltage) - brain.voltage_threshold
            force = (active_v ** 2) / brain.k_factor
            force *= (1 if voltage > 0 else -1)
        else:
            force = 0.0
            
        # 打印这一视觉帧的瞬间观测数据
        if frame % 2 == 0:
            print(f"{current_time:<7.2f} | {pos:<7.2f} | {vel:<7.2f} | {voltage:<9.2f} | {force:<9.2f}")

        # ==========================================
        # [内层循环：物理世界] 按照物理步长高频演化
        # ==========================================
        # 在下一个视觉帧到来前，物理世界需要走过 50 次 1ms 的微小步伐
        physics_steps_per_frame = int(VISION_DT / PHYSICS_DT)
        
        for _ in range(physics_steps_per_frame):
            # --- [Act & Physics] 非线性物理模型结算 ---
            
            # 判断液滴状态：静止还是运动？
            if abs(vel) < 1e-4: # 几乎静止，受到静摩擦（接触线钉扎）主导
                if abs(force) > STATIC_FRICTION_TH:
                    # 驱动力大于阈值，抵消掉静摩擦后产生合力
                    net_force = force - math.copysign(STATIC_FRICTION_TH, force)
                else:
                    # 驱动力不足以克服钉扎，合力为0，被死死卡住
                    net_force = 0.0 
            else:
                # 运动状态：驱动力 - 粘性摩擦 - 一个基础的滑动阻力
                net_force = force - (friction_c * vel) - math.copysign(0.1, vel)
            
            # 运动学高频积分：微观尺度上的 a, v, x 演化
            acc = net_force / mass
            vel += acc * PHYSICS_DT
            pos += vel * PHYSICS_DT

if __name__ == "__main__":
    test_virtual_droplet()