import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
y3 = np.sin(x) * np.cos(x)

fig, ax1 = plt.subplots()

# 첫 번째 데이터 세트와 y축
color = 'tab:red'
ax1.plot(x, y1, color=color)
ax1.set_ylabel('sin(x)', color=color)
ax1.tick_params(axis='y', labelcolor=color)

# 두 번째 y축 생성
ax2 = ax1.twinx()
color = 'tab:blue'
ax2.plot(x, y2, color=color)
ax2.set_ylabel('cos(x)', color=color)
ax2.tick_params(axis='y', labelcolor=color)

# 세 번째 y축 생성 및 오프셋 조정
ax3 = ax1.twinx()
spine = ax3.spines["right"]
spine.set_position(("outward", 60))  # y축의 위치를 오른쪽으로 60 포인트 이동
ax3.plot(x, y3, 'tab:green')
ax3.set_ylabel('sin(x)*cos(x)', color='tab:green')
ax3.tick_params(axis='y', labelcolor='tab:green')

fig.tight_layout()  # 레이아웃 조정
plt.show()
