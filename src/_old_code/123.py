import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# 气体常数
gamma = 1.4  # 比热比
M1 = 3       # 来流马赫数
p1 = 1       # 来流压力 (atm)
theta2 = 20  # 上壁面偏转角 (度)
theta3 = 15  # 下壁面偏转角 (度)

def calc_theta(beta, M1, gamma):
    """计算给定激波角对应的偏转角"""
    sin_beta = np.sin(beta)
    cos_beta = np.cos(beta)
    numerator = 2 * (1/np.tan(beta)) * (M1**2 * sin_beta**2 - 1)
    denominator = M1**2 * (gamma + np.cos(2*beta)) + 2
    return np.arctan(numerator / denominator)

def calc_dtheta_dbeta(beta, M1, gamma):
    """计算偏转角对激波角的导数"""
    sin_beta = np.sin(beta)
    cos_beta = np.cos(beta)
    M1_sq = M1**2
    M1_sq_sin2 = M1_sq * sin_beta**2
    
    term1 = -2 * (1/np.sin(beta)**2) * (M1_sq_sin2 - 1)
    term2 = 2 * (1/np.tan(beta)) * (2 * M1_sq_sin2 * cos_beta)
    numerator = term1 + term2
    denominator = M1_sq * (gamma + np.cos(2*beta)) + 2
    
    term3 = M1_sq * (-2 * np.sin(2*beta))
    df_dbeta = term3
    
    return (numerator * denominator - (2 * (1/np.tan(beta)) * (M1_sq_sin2 - 1)) * df_dbeta) / denominator**2

def calc_oblique_shock(M1, theta, gamma):
    """
    计算斜激波参数
    输入：
        M1 - 来流马赫数
        theta - 偏转角 (度)
        gamma - 比热比
    输出：
        beta - 激波角 (度)
        p_ratio - 压力比 p2/p1
        M2 - 激波后马赫数
    """
    if abs(theta) < 1e-6:
        beta = np.degrees(np.arcsin(1/M1))  # 马赫角
        p_ratio = 1
        M2 = M1
        return beta, p_ratio, M2
    
    theta_rad = np.radians(theta)
    
    # 使用牛顿迭代法求解激波角beta
    beta_guess = np.radians(45)  # 初始猜测
    max_iter = 100
    tol = 1e-8
    
    for _ in range(max_iter):
        f = calc_theta(beta_guess, M1, gamma) - theta_rad
        df = calc_dtheta_dbeta(beta_guess, M1, gamma)
        
        beta_new = beta_guess - f/df
        
        if abs(beta_new - beta_guess) < tol:
            break
        
        beta_guess = beta_new
    
    beta = np.degrees(beta_guess)
    
    # 确保解是弱激波解 (M2 > 1)
    M1n = M1 * np.sin(beta_guess)  # 法向马赫数
    M2n = np.sqrt((1 + (gamma-1)/2*M1n**2) / (gamma*M1n**2 - (gamma-1)/2))  # 法向马赫数
    M2 = M2n / np.sin(beta_guess - theta_rad)  # 激波后马赫数
    
    # 如果是强激波解，尝试弱激波解
    if M2 < 1:
        # 尝试从不同的初始值开始
        beta_guess = np.radians(30)
        for _ in range(max_iter):
            f = calc_theta(beta_guess, M1, gamma) - theta_rad
            df = calc_dtheta_dbeta(beta_guess, M1, gamma)
            
            beta_new = beta_guess - f/df
            
            if abs(beta_new - beta_guess) < tol:
                break
            
            beta_guess = beta_new
        
        beta = np.degrees(beta_guess)
        M1n = M1 * np.sin(beta_guess)
        M2n = np.sqrt((1 + (gamma-1)/2*M1n**2) / (gamma*M1n**2 - (gamma-1)/2))
        M2 = M2n / np.sin(beta_guess - theta_rad)
    
    # 计算压力比
    p_ratio = 1 + 2*gamma/(gamma+1)*(M1n**2 - 1)
    
    return beta, p_ratio, M2

def pressure_difference(phi, M2, M3, theta2, theta3, p2_p1, p3_p1, gamma):
    """计算两个路径的压力差"""
    # 路径1：区域2 → 区域4
    delta_theta_2 = phi - theta2
    _, p_ratio_2, _ = calc_oblique_shock(M2, delta_theta_2, gamma)
    p4_p1_1 = p2_p1 * p_ratio_2
    
    # 路径2：区域3 → 区域4'
    delta_theta_3 = phi - (-theta3)
    _, p_ratio_3, _ = calc_oblique_shock(M3, delta_theta_3, gamma)
    p4_p1_2 = p3_p1 * p_ratio_3
    
    # 压力差
    return p4_p1_1 - p4_p1_2

def solve_shock_intersection(M1, theta2, theta3, gamma):
    """
    求解激波相交问题
    输入：
        M1 - 来流马赫数
        theta2 - 上壁面偏转角 (度)
        theta3 - 下壁面偏转角 (度)
        gamma - 比热比
    输出：
        theta4 - 区域4的偏转角 (度)
        p4_p1 - 区域4的压力比
        phi - 流动方向 (度)
    """
    # 首先计算区域2和3的参数
    _, p2_p1, M2 = calc_oblique_shock(M1, theta2, gamma)
    _, p3_p1, M3 = calc_oblique_shock(M1, -theta3, gamma)
    
    # 定义目标函数：寻找p4 = p4'的条件
    obj_fun = lambda phi: pressure_difference(phi, M2, M3, theta2, theta3, p2_p1, p3_p1, gamma)
    
    # 使用fsolve求解
    phi_guess = 0  # 初始猜测
    phi_sol = fsolve(obj_fun, phi_guess)[0]
    
    # 计算对应的应的压力比
    delta_theta_2 = phi_sol - theta2
    _, p_ratio_2, _ = calc_oblique_shock(M2, delta_theta_2, gamma)
    p4_p1 = p2_p1 * p_ratio_2
    
    theta4 = phi_sol
    phi = phi_sol
    
    return theta4, p4_p1, phi

# ==================== 第一步：计算区域2和3的参数 ====================

# 计算区域2的参数 (上壁面激波后)
beta2, p2_p1, M2 = calc_oblique_shock(M1, theta2, gamma)
p2 = p2_p1 * p1

# 计算区域3的参数 (下壁面激波后)
beta3, p3_p1, M3 = calc_oblique_shock(M1, -theta3, gamma)  # 负号表示下壁面
p3 = p3_p1 * p1

print("区域2参数：")
print(f"激波角 beta2 = {beta2:.2f}°")
print(f"压力比 p2/p1 = {p2_p1:.4f}")
print(f"马赫数 M2 = {M2:.4f}")
print(f"压力 p2 = {p2:.4f} atm\n")

print("区域3参数：")
print(f"激波角 beta3 = {beta3:.2f}°")
print(f"压力比 p3/p1 = {p3_p1:.4f}")
print(f"马赫数 M3 = {M3:.4f}")
print(f"压力 p3 = {p3:.4f} atm\n")

# ==================== 第二步：绘制p-theta图 ====================

# 生成激波的p-theta曲线
theta_range = np.arange(-40, 40.1, 0.1)  # 偏转角范围 (度)
p_ratio_pos = np.zeros_like(theta_range)  # 正激波压力比
p_ratio_neg = np.zeros_like(theta_range)  # 负激波压力比

for i, theta in enumerate(theta_range):
    if theta > 0:
        _, p_ratio_pos[i], _ = calc_oblique_shock(M1, theta, gamma)
    else:
        _, p_ratio_neg[i], _ = calc_oblique_shock(M1, theta, gamma)

# 生成区域2和3的激波p-theta曲线
theta_range_2 = np.arange(0, theta2+0.1, 0.1)
p_ratio_2 = np.zeros_like(theta_range_2)
for i, theta in enumerate(theta_range_2):
    _, p_ratio_2[i], _ = calc_oblique_shock(M1, theta, gamma)

theta_range_3 = np.arange(-theta3, 0.1, 0.1)
p_ratio_3 = np.zeros_like(theta_range_3)
for i, theta in enumerate(theta_range_3):
    _, p_ratio_3[i], _ = calc_oblique_shock(M1, theta, gamma)

# 绘制p-theta图
plt.figure(figsize=(12, 8))
plt.grid(True)

# 绘制激波的p-theta曲线
plt.plot(theta_range, p_ratio_pos, 'b-', linewidth=1.5, label='右行激波 (M1=3)')
plt.plot(theta_range, p_ratio_neg, 'r-', linewidth=1.5, label='左行激波 (M1=3)')

# 绘制区域2和3的激波
plt.plot(theta_range_2, p_ratio_2, 'g--', linewidth=2, label='区域2激波')
plt.plot(theta_range_3, p_ratio_3, 'm--', linewidth=2, label='区域3激波')

# 标记关键点
plt.plot(0, 1, 'ko', markersize=8, markerfacecolor='k', label='区域1 (M1=3, p1=1atm)')
plt.plot(theta2, p2_p1, 'go', markersize=8, markerfacecolor='g', 
         label=f'区域2 (θ={theta2:.1f}°, p/p1={p2_p1:.3f})')
plt.plot(-theta3, p3_p1, 'mo', markersize=8, markerfacecolor='m', 
         label=f'区域3 (θ={-theta3:.1f}°, p/p1={p3_p1:.3f})')

# ==================== 第三步：求解区域4和4'的参数 ====================

# 求解激波相交问题
theta4_sol, p4_p1_sol, phi_sol = solve_shock_intersection(M1, theta2, theta3, gamma)

# 计算实际压力
p4 = p4_p1_sol * p1
p4_prime = p4  # 区域4'的压力等于区域4的压力

print("求解结果：")
print(f"区域4和4'的压力比 p4/p1 = {p4_p1_sol:.4f}")
print(f"区域4和4'的压力 p4 = p4' = {p4:.4f} atm")
print(f"折射激波后的流动方向 Φ = {phi_sol:.4f}°")

# 在图上标记求解结果
plt.plot(phi_sol, p4_p1_sol, 'ro', markersize=10, markerfacecolor='r', 
         label=f'区域4,4\' (Φ={phi_sol:.1f}°, p/p1={p4_p1_sol:.3f})')

# 绘制从区域2到区域4的激波
theta_2_to_4 = np.linspace(theta2, phi_sol, 100)
p_2_to_4 = np.zeros_like(theta_2_to_4)
for i, theta in enumerate(theta_2_to_4):
    delta_theta = theta - theta2
    _, p_ratio, _ = calc_oblique_shock(M2, delta_theta, gamma)
    p_2_to_4[i] = p2_p1 * p_ratio
plt.plot(theta_2_to_4, p_2_to_4, 'c-.', linewidth=1.5, label='区域2→4激波')

# 绘制从区域3到区域4'的激波
theta_3_to_4prime = np.linspace(-theta3, phi_sol, 100)
p_3_to_4prime = np.zeros_like(theta_3_to_4prime)
for i, theta in enumerate(theta_3_to_4prime):
    delta_theta = theta - (-theta3)
    _, p_ratio, _ = calc_oblique_shock(M3, delta_theta, gamma)
    p_3_to_4prime[i] = p3_p1 * p_ratio
plt.plot(theta_3_to_4prime, p_3_to_4prime, 'y-.', linewidth=1.5, label='区域3→4\'激波')

# 添加图表表标题和标签
plt.xlabel('偏转角 θ (度)', fontsize=12)
plt.ylabel('压力比 p/p_1', fontsize=12)
plt.title('斜激波相交的p-theta图', fontsize=14, fontweight='bold')
plt.legend(loc='best', fontsize=10)

# 调整坐标轴范围
plt.xlim([-30, 30])
plt.ylim([0.5, 10])

# 保存图片
plt.savefig('/home/user/vibecoding/workspace/shock_wave_calculation/shock_wave_intersection.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n图片已已保存为 shock_wave_intersection.png")
