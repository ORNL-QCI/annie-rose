import matplotlib.pyplot as plt
import numpy as np
import time

x = np.linspace(0, 6*np.pi, 100)
y = np.sin(x)
yy = np.cos(x)

# You probably won't need this if you're embedding things in a tkinter plot...
plt.ion()

fig, (ax, ax2) = plt.subplots(1, 2, sharey=True)
line1, = ax.plot(x, y, 'r-') # Returns a tuple of line objects, thus the comma

#ax2 = fig.add_subplot(222)
line2, = ax2.plot(x, yy, 'r-')

counter = 0

for phase in np.linspace(0, 100*np.pi, 50):
    line1.set_ydata(np.sin(x + phase))
    fig.canvas.draw()
    if counter == 10:
        counter = 0
        line2.set_ydata(np.cos(x + phase))
    counter += 1
    fig.canvas.draw()
    time.sleep(0.001)



'''
f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
ax1.plot(x, y)
ax1.set_title('Sharing Y axis')
ax2.scatter(x, y)
'''
