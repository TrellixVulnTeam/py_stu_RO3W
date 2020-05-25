# coding=utf-8
from matplotlib import pyplot as plt

# 通过实例化一个figure并且传递参数，能够在后台自动使用该figure实例
# 在图像模糊的时候可以传入dpi参数
fig = plt.figure(figsize=(20, 8), dpi=80)
x = range(2, 26, 2)
y = [15, 13, 14.5, 17, 20, 25, 26, 26, 27, 22, 18, 15]
# 绘图
plt.plot(x, y)

plt.savefig("./sig_size.png")  # 保存图片
# 展示图形
plt.show()
