import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider  # , Button, RadioButtons
from mpl_toolkits.mplot3d import Axes3D

traj = np.load(sys.path[0] + "/6circle_vel.npy")
agents = traj.shape[0]
timesteps = traj.shape[1]

speed = np.zeros([agents, timesteps])
speed = np.sqrt(traj[:, :, 0]**2 + traj[:, :, 1]**2 + traj[:, :, 2]**2)

plt.xlabel('Time (s)')
plt.ylabel('Speed (a.u.)')

timeNeeded = 0.5 * timesteps
timeArray = np.linspace(0, timeNeeded, timesteps)

for i in range(0, agents):
    plt.plot(timeArray, speed[i])

SAVE = False
if SAVE:
    plt.savefig(sys.path[0] + "/opt_vel.pdf", dpi=None, facecolor='w', edgecolor='w',
                orientation='portrait', papertype=None, format=None,
                transparent=False, bbox_inches='tight', pad_inches=0,
                frameon=None, metadata=None)
else:
    plt.show()
