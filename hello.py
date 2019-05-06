import numpy as np

timestep = .5
trajectory_length = 5
# jerk_traj = np.array([[0,0,0]])
# acc_traj = np.array([[0,0,0]])
# vel_traj = np.array([[0,0,0]])
# pos_traj = np.array([[0,0,0]]) # set initial position here

jerk_traj = np.array([[0,0,1],[0,0,1],[0,-2,0],[0,0,-1],[0,0,-1]])
acc_traj = np.zeros([trajectory_length, 3])
vel_traj = np.zeros([trajectory_length, 3])
pos_traj = np.zeros([trajectory_length, 3])

def integrate():
    for i in range(0, trajectory_length - 1):
        acc_traj[i+1] = acc_traj[i] + (timestep * jerk_traj[i])
        vel_traj[i+1] = vel_traj[i] + (timestep * acc_traj[i]) + (0.5 * timestep**2 * jerk_traj[i])
        pos_traj[i+1] = pos_traj[i] + (timestep * vel_traj[i]) + (0.5 * timestep**2 * acc_traj[i]) + (0.1666 * timestep**3 * jerk_traj[i])

#print(jerk_traj[2] + (timestep * jerk_traj[2]))

print("jerk_trajectory:\n", jerk_traj, "\n")
print("acc_trajectory:\n", acc_traj, "\n")
print("vel_trajectory:\n", vel_traj, "\n")
print("pos_trajectory:\n", pos_traj, "\n")

#acc_traj = np.append(acc_traj, acc_traj[1] + (timestep * jerk_traj[1]), axis=0)