import os
import sys
import numpy as np
from direct.showbase import DirectObject


class DroneRecorder(DirectObject.DirectObject):

    def __init__(self, droneManager):
        self.droneManager = droneManager
        self.recordingLstPos = []
        self.recordingLstVel = []
        self.isRecording = False
        self.accept('space', self.toggleRecording)


    def recordDronesTask(self, task):
        task.delayTime = 0.05
        self.recordingLstPos.append(self.droneManager.getAllPositions())
        self.recordingLstVel.append(self.droneManager.getAllVelocities())
        # print("recording")
        return task.again


    def save(self):
        posTraj = np.asarray(self.recordingLstPos)
        posTraj = np.swapaxes(posTraj, 0, 1)  # make array in the shape agent, timestep, dimension
        np.save(sys.path[0] + "/trajectories/pos_traj.npy", posTraj)
        velTraj = np.asarray(self.recordingLstVel)
        velTraj = np.swapaxes(velTraj, 0, 1)  # make array in the shape agent, timestep, dimension
        np.save(sys.path[0] + "/trajectories/vel_traj.npy", velTraj)
        print("recording saved")


    def toggleRecording(self):
        if not self.isRecording:
            print("recording started")
            self.isRecording = True
            self.droneManager.base.taskMgr.doMethodLater(0, self.recordDronesTask, "RecordDrones")
        else:
            self.isRecording = False
            self.droneManager.base.taskMgr.remove("RecordDrones")
            self.save()
            # self.recordingLst = []
            # self.recordingLstVel = []
