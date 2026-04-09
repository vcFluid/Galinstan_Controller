/*
--- Galinstan 准一维控制执行器固件 (v2.0) ---
物理架构:
- D5 (PWM) -> L298N ENA  (控制场强梯度)
- D4 (DO)  -> L298N IN1  (控制极性层 A)
- D7 (DO)  -> L298N IN2  (控制极性层 B)

指令协议: "DIR:x,PWM:y\n" (x=0/1, y=0-255)
回传协议: "Direction:300,PWM_Voltage:128\n" (用于上位机时序数据分析)
*/

// --- 物理引脚定义映射 ---
const int IN1_PIN = 4;   // 极性逻辑 A 
const int IN2_PIN = 7;   // 极性逻辑 B (差分互补端)
const int ENA_PIN = 5;   // 驱动器使能端 (PWM)

String inputString = "";         // 串口数据流缓存
bool stringComplete = false;     // 指令帧结束标志

void setup() {
  Serial.begin(115200);          // 必须与 Python 端的波特率绝对对齐
  
  // 注册物理输出通道
  pinMode(IN1_PIN, OUTPUT);
  pinMode(IN2_PIN, OUTPUT);
  pinMode(ENA_PIN, OUTPUT);
  
  // 初始化系统为最低能态 (全量断电，防止上电抖动)
  digitalWrite(IN1_PIN, LOW);
  digitalWrite(IN2_PIN, LOW);
  analogWrite(ENA_PIN, 0);
}

void loop() {
  // 检查是否在中断中捕获到了完整的指令帧
  if (stringComplete) {
    parseAndExecute(inputString);
    inputString = "";            // 释放缓存
    stringComplete = false;      // 重置锁存器
  }
}

// 硬件级串口中断：异步捕获数据流
void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    // 遇到换行符，判定为一帧指令结束
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}

// 核心控制律：解析语义并转化为物理场
void parseAndExecute(String cmd) {
  int dirIndex = cmd.indexOf("DIR:");
  int pwmIndex = cmd.indexOf("PWM:");
  
  // 如果指令格式合法
  if (dirIndex != -1 && pwmIndex != -1) {
    // 1. 提取指令参量
    int dirValue = cmd.substring(dirIndex + 4, cmd.indexOf(',')).toInt();
    int pwmValue = cmd.substring(pwmIndex + 4).toInt();
    
    // 2. 边界条件约束 (防止溢出导致寄存器错乱)
    pwmValue = constrain(pwmValue, 0, 255);
    
    // 3. 注入物理量：建立差分电场
    if (dirValue == 1) {
      digitalWrite(IN1_PIN, HIGH);
      digitalWrite(IN2_PIN, LOW);   // 电流路径 A -> B
    } else {
      digitalWrite(IN1_PIN, LOW);
      digitalWrite(IN2_PIN, HIGH);  // 电流路径 B -> A
    }
    
    // 4. 释放动力
    analogWrite(ENA_PIN, pwmValue); 
    
    // 5. 遥测回传：构建闭环数据资产
    // 将 DIR 映射至 300，是为了在串口绘图器中避免与 PWM (0-255) 曲线重叠
    Serial.print("Direction:");
    Serial.print(dirValue * 300); 
    Serial.print(",");
    Serial.print("PWM_Voltage:");
    Serial.println(pwmValue);
  }
}