import numpy as np

Critical_V = 1.2 # 克服氧化层静摩擦的临界电压 (V)
K_FACTOR = 0.5 # 阻力与电势平方的无量纲转换系数

"""
参数解释:
Kp(刚度): 比例增益，控制系统对当前误差的响应强度。较高的 Kp 会使系统更快地响应，但过高可能导致过度振荡。
Ki(耐力): 积分增益，控制系统对过去误差的累积响应。
Kd(阻尼): 微分增益，控制系统对误差变化率的响应。较高的 Kd 可以提供更好的阻尼，减少振荡，但过高可能导致系统反应过慢。
target_x: 目标位置的 x 坐标，系统将努力将液态金属球移动到这个位置。
voltage_threshold: 驱动电压的死区补偿值，确保系统能够克服静摩擦启动液滴运动。
k_factor: 驱动力与电压平方的转换系数，基于 Lippmann 方程和摩擦力模型进行非线性映射。
"""

class PhysicsBrain:
    def __init__(self, Kp=1.0, Ki=0.0, Kd=0.0, target_x=0.0): # 默认 PID 参数和目标位置，可以在实例化时传入自定义值以适应不同的系统特性和控制需求。
        # 1. 控制学参数
        self.Kp = Kp # Class内，Kp等于__init__中传入的值，在main.py中实例化时被设置为0.4，这个值是根据经验和初步测试调整的，旨在提供适度的响应速度和稳定性。
        self.Ki = Ki # Class内, Ki等于__init__中传入的值，在main.py中实例化时被设置为0.01，这个值是一个较小的积分增益，主要用于消除系统的稳态误差，防止系统长时间偏离目标位置。
        self.Kd = Kd # Class内, Kd等于__init__中传入的值，在main.py中实例化时被设置为0.1，这个值是一个适中的微分增益，用于提供足够的阻尼，防止系统过度振荡，同时保持良好的响应速度。
        self.target_x = target_x
        
        # 2. 物理学参数 (可供未来实验拟合更新)
        self.voltage_threshold = Critical_V # 克服氧化层静摩擦的临界电压 (V)
        self.k_factor = K_FACTOR          # 阻力与电势平方的无量纲转换系数
        
        # 3. 状态寄存器
        self.integral_error = 0.0 # PID 积分项的累积误差，用于消除稳态误差
        self.last_error = 0.0 # PID 微分项的上一个误差值，用于计算误差变化率
        
    def update_target(self, new_target_x):
        self.target_x = new_target_x
        self.integral_error = 0.0
        self.last_error = 0.0  # 核心：防止目标切换时的微分尖峰

    def think(self, current_pos, dt):
        """
        核心物理演算中枢
        输入: 物理坐标 current_pos [x], 时间步长 dt (秒)
        输出: 理想控制电压 V_ideal (伏特)
        """
        if current_pos is None or dt <= 1e-5:
            return 0.0

        curr_x = current_pos[0]
        error = self.target_x - curr_x
        
        # --- 步骤 A: 计算期望驱动力 (PID 算子) ---
        p_term = self.Kp * error
        
        self.integral_error += error * dt
        # 积分抗饱和 (Anti-windup): 限制积分上限，防止系统在被卡住时积累过大能量
        self.integral_error = np.clip(self.integral_error, -50, 50) 
        i_term = self.Ki * self.integral_error
        
        d_term = self.Kd * (error - self.last_error) / dt
        
        F_ideal = p_term + i_term + d_term
        
        # 状态更新
        self.last_error = error
        
        # --- 步骤 B: 物理反演 (Force -> Voltage) ---
        if abs(F_ideal) < 1e-4:
            return 0.0 # 极小误差直接判定为到达目标
            
        # 根据 Lippmann 方程与摩擦力模型进行非线性映射
        direction = 1 if F_ideal > 0 else -1
        
        # 驱动力转化 + 死区补偿
        V_magnitude = np.sqrt(self.k_factor * abs(F_ideal)) + self.voltage_threshold
        
        V_ideal = direction * V_magnitude
        
        return V_ideal