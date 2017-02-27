import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

style.use('fivethirtyeight')

fig = plt.figure();
ax1 = fig.add_subplot(1,1,1)

def animate(i): #interval
	graph_data = open('example.txt','r').read()
	lines = graph_data.split("\n")
	xs = []
	ys = []
	for line in lines:
		values = line.split(',')
		if len(line)>1:
			x = values[0].strip()
			y = values[1].strip()
			xs.append(x)
			ys.append(y)
	ax1.clear()
	ax1.scatter(xs, ys)
	axes = plt.gca()
	axes.set_xlim(0, 20)
	axes.set_ylim(0, 20)

ani = animation.FuncAnimation(fig, animate, interval=1000) #update every 1000 milliseconds
plt.show()

