import time
from src.control.actuator import HardwareController, SerialTransmitter

def test_closed_loop_comms():
    controller = HardwareController(max_voltage=5.0, pwm_res=255)
    tx = SerialTransmitter(port='COM3', baudrate=115200)
    
    if tx.ser is None:
        return

    print(f"{'时间(s)':<8} | {'理想电压(V)':<10} | {'下发指令(Tx)':<20} | {'Arduino实际回传(Rx)':<20}")
    print("-" * 65)

    # 模拟一个电压阶跃序列
    test_voltages = [0.0, 2.5, 5.0, -1.2, 0.0]
    
    try:
        start_time = time.time()
        for v in test_voltages:
            current_time = time.time() - start_time
            
            # 1. 下发数字指令 (Tx)
            cmd = controller.generate_instruction(v)
            tx.send_command(cmd)
            
            # 等待极短时间，让电信号经过 USB 抵达单片机，并等待单片机处理和返回
            time.sleep(0.05) 
            
            # 2. 读取物理回传 (Rx)
            rx_data = "无响应"
            if tx.ser.in_waiting > 0:
                # 读取串口缓冲区的所有内容，并剔除首尾的换行符
                rx_data = tx.ser.readline().decode('utf-8', errors='ignore').strip()
            
            # 3. 终端可视化格式化打印
            print(f"{current_time:<7.2f} | {v:<9.2f} | {cmd.strip():<18} | {rx_data}")
            
            time.sleep(1.5) # 维持该电压状态一段时间
            
    except KeyboardInterrupt:
        tx.send_command(controller.generate_instruction(0.0))
        print("\n强制中断，已下发停机指令。")
    finally:
        tx.close()

if __name__ == "__main__":
    test_closed_loop_comms()