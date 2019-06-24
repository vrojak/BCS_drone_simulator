import random
import re
import time
import math
import numpy as np

from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.crazyflie.commander import Commander

# pylint: disable=no-name-in-module
from panda3d.core import Vec3
from panda3d.core import Loader
from panda3d.core import BitMask32
from panda3d.core import LineSegs
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletGhostNode

class Drone:

    RIGIDBODYMASS = 1
    RIGIDBODYRADIUS = 0.1
    GHOSTRADIUS = 0.3

    NAVIGATIONFORCE = 1
    AVOIDANCEFORCE = 25
    FORCEFALLOFFDISTANCE = .5
    LINEARDAMPING = 0.97

    def __init__(self, manager, name: str, position: Vec3, uri="drone address", printDebugInfo=False):

        self.base = manager.base
        self.manager = manager
        self.name = name
        self.id = int(''.join(filter(str.isdigit, name))) # a unique number to identify the drone, not used right now
        self.actualDronePosition = Vec3(0, 0, 0)        

        self.canConnect = False # true if the virtual drone has a uri to connect to a real drone
        self.isConnected = False # true if the connection to a real drone is currently active
        self.uri = uri
        if self.uri != "drone address":
            self.canConnect = True

        # add the rigidbody to the drone, which has a mass and linear damping
        self.rigidBody = BulletRigidBodyNode("RigidSphere") # derived from PandaNode
        self.rigidBody.setMass(self.RIGIDBODYMASS) # body is now dynamic
        self.rigidBody.addShape(BulletSphereShape(self.RIGIDBODYRADIUS))
        self.rigidBody.setLinearSleepThreshold(0)
        self.rigidBody.setFriction(0)
        self.rigidBody.setLinearDamping(self.LINEARDAMPING)
        self.rigidBodyNP = self.base.render.attachNewNode(self.rigidBody)
        self.rigidBodyNP.setPos(position)
        self.rigidBodyNP.setCollideMask(BitMask32.bit(1))

        # add the ghost to the drone which acts as a sensor for nearby drones
        self.ghost = BulletGhostNode(self.name) # give drone the same identifier that the drone has in the dict
        self.ghost.addShape(BulletSphereShape(self.GHOSTRADIUS))
        self.ghostNP = self.base.render.attachNewNode(self.ghost)
        self.ghostNP.setPos(position)
        self.ghostNP.setCollideMask(BitMask32.bit(2))

        # add a 3d model to the drone to be able to see it in the 3d scene
        self.base.world.attach(self.rigidBody)
        self.base.world.attach(self.ghost)
        model = self.base.loader.loadModel(self.base.modelDir + "/drones/drone1.egg")
        model.setScale(0.2)
        model.reparentTo(self.rigidBodyNP)

        self.target = position # the target that the virtual drones tries to reach
        self.setpoint = position # the immediate target (setpoint) that the real drone tries to reach, usually updated each frame
        self.waitingPosition = Vec3(position[0], position[1], 0.7)
        
        self.printDebugInfo = printDebugInfo
        if self.printDebugInfo == True: # put a second drone model on top of drone that outputs debug stuff
            model = self.base.loader.loadModel(self.base.modelDir + "/drones/drone1.egg")
            model.setPos(0, 0, .2)
            model.reparentTo(self.rigidBodyNP)

        # initialize line renderers
        self.targetLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.velocityLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.forceLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.actualDroneLineNP = self.base.render.attachNewNode(LineSegs().create())
        self.setpointNP = self.base.render.attachNewNode(LineSegs().create())


    # connect to a real drone with the uri
    def connect(self):
        if self.canConnect == False:
            return
        print(self.name, "@", self.uri, "connecting")
        self.isConnected = True
        self.scf = SyncCrazyflie(self.uri, cf=Crazyflie(rw_cache='./cache'))
        self.scf.open_link()
        self._reset_estimator()
        self.start_position_printing()


    def sendPosition(self):
        cf = self.scf.cf
        cf.param.set_value('flightmode.posSet', '1')

        ##### send position + the negative of the distance to the real drone
        # diff = self.getPos() - self.actualDronePosition
        # self.setpoint = self.getPos() + diff

        ##### send the position + some function of the velocity vector
        vel = self.getVel().length()
        multiplier = 0.5 * (math.tanh(4 * vel - 3) + 1)
        #pos = self.getPos() + self.getVel() * multiplier
        self.setpoint = self.getPos() + self.getVel() * 0.5 * multiplier

        #### send position only
        # self.setpoint = self.getPos()
        
        # print('Sending position {} | {} | {}'.format(self.setpoint[0], self.setpoint[1], self.setpoint[2]))
        cf.commander.send_position_setpoint(self.setpoint[0], self.setpoint[1], self.setpoint[2], 0)


    def disconnect(self):
        print(self.name, "@", self.uri, "disconnecting")
        self.isConnected = False
        cf = self.scf.cf
        cf.commander.send_stop_setpoint()
        time.sleep(0.1)
        self.scf.close_link()


    def returnToWaitingPosition(self):
        self.setTarget(self.waitingPosition)


    def update(self):
        self._updateGhost()
        self._updateTargetForce()
        self._updateAvoidanceForce()

        if self.isConnected:
            self.sendPosition()

        self._drawTargetLine()
        # self._drawVelocityLine()
        # self._drawForceLine()
        # self._drawActualDroneLine()
        # self._drawSetpoint()

        self._printDebugInfo()


    def _updateGhost(self):
        self.ghostNP.setPos(self.getPos())


    def _updateTargetForce(self):
        dist = (self.target - self.getPos())
        if(dist.length() > self.FORCEFALLOFFDISTANCE):
            force = dist.normalized() * self.NAVIGATIONFORCE
        else:
            force = (dist / self.FORCEFALLOFFDISTANCE) * self.NAVIGATIONFORCE 
        velMult = self.getVel().length() + 0.1
        velMult = velMult
        self._addForce(force * 3)


    def _updateAvoidanceForce(self):
        for node in self.ghost.getOverlappingNodes():
            if node.name.startswith("drone"):
                other = self.manager.getDrone(node.name)
                # perp = self.target.cross(other.target) # the direction perpendicular to the target vectors of both drones
                perp = self.getRelativeTargetVector().cross(other.getRelativeTargetVector())
                distVec = other.getPos() - self.getPos()
                if distVec.length() < 0.2:
                    print("BONK")
                distMult = max([0, 2 * self.GHOSTRADIUS - distVec.length()]) # make this stuff better
                distMult = distMult
                # velMult = other.getVel().length() + self.getVel().length() + 1
                velMult = self.getVel().length()
                velMult = velMult + .5
                # self._addForce((perp.normalized() * 0.3 - distVec.normalized() * 0.7) * distMult * velMult * self.AVOIDANCEFORCE)
                self._addForce((perp.normalized() * 0.3 - distVec.normalized() * 0.7) * distMult * velMult * self.AVOIDANCEFORCE)


    def getRelativeTargetVector(self) -> Vec3:
        return self.target - self.getPos()


    def _printDebugInfo(self):
        if self.printDebugInfo == True: 
            print("Drone", self.name, " Amount of overlapping nodes: ", self.ghost.getNumOverlappingNodes())
            for node in self.ghost.getOverlappingNodes():
                print(node)


    def setTarget(self, target: Vec3 = Vec3(0, 0, 0), random=False):
        if random == False:
            self.target = target
        else:
            self.target = self.manager.getRandomRoomCoordinate()
    

    def _addForce(self, force: Vec3):
        self.rigidBody.applyCentralForce(force)


    def getPos(self) -> Vec3:
        return self.rigidBodyNP.getPos()


    def setPos(self, position: Vec3):
        self.rigidBodyNP.setPos(position)


    def getVel(self) -> Vec3:
        return self.rigidBody.getLinearVelocity()

    
    def setVel(self, velocity: Vec3):
        return self.rigidBody.setLinearVelocity(velocity)


    def _drawTargetLine(self):
        self.targetLineNP.removeNode()
        ls = LineSegs()
        #ls.setThickness(1)
        ls.setColor(1.0, 0.0, 0.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.target)
        node = ls.create()
        self.targetLineNP = self.base.render.attachNewNode(node)

    
    def _drawVelocityLine(self):
        self.velocityLineNP.removeNode()
        ls = LineSegs()
        #ls.setThickness(1)
        ls.setColor(0.0, 0.0, 1.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.getPos() + self.getVel())
        node = ls.create()
        self.velocityLineNP = self.base.render.attachNewNode(node)


    def _drawForceLine(self):
        self.forceLineNP.removeNode()
        ls = LineSegs()
        #ls.setThickness(1)
        ls.setColor(0.0, 1.0, 0.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.getPos() + self.rigidBody.getTotalForce())
        node = ls.create()
        self.forceLineNP = self.base.render.attachNewNode(node)   


    def _drawActualDroneLine(self):
        self.actualDroneLineNP.removeNode()
        ls = LineSegs()
        #ls.setThickness(1)
        ls.setColor(0.0, 0.0, 0.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.actualDronePosition)
        node = ls.create()
        self.actualDroneLineNP = self.base.render.attachNewNode(node)

    
    def _drawSetpoint(self):
        self.setpointNP.removeNode()
        ls = LineSegs()
        #ls.setThickness(1)
        ls.setColor(1.0, 1.0, 1.0, 1.0)
        ls.moveTo(self.getPos())
        ls.drawTo(self.setpoint)
        node = ls.create()
        self.setpointNP = self.base.render.attachNewNode(node)  


    def _wait_for_position_estimator(self):
        print('Waiting for estimator to find position...')

        log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
        log_config.add_variable('kalman.varPX', 'float')
        log_config.add_variable('kalman.varPY', 'float')
        log_config.add_variable('kalman.varPZ', 'float')

        var_y_history = [1000] * 10
        var_x_history = [1000] * 10
        var_z_history = [1000] * 10

        threshold = 0.001

        with SyncLogger(self.scf, log_config) as logger:
            for log_entry in logger:
                data = log_entry[1]

                var_x_history.append(data['kalman.varPX'])
                var_x_history.pop(0)
                var_y_history.append(data['kalman.varPY'])
                var_y_history.pop(0)
                var_z_history.append(data['kalman.varPZ'])
                var_z_history.pop(0)

                min_x = min(var_x_history)
                max_x = max(var_x_history)
                min_y = min(var_y_history)
                max_y = max(var_y_history)
                min_z = min(var_z_history)
                max_z = max(var_z_history)

                # print("{} {} {}".
                #       format(max_x - min_x, max_y - min_y, max_z - min_z))

                if (max_x - min_x) < threshold and (
                        max_y - min_y) < threshold and (
                        max_z - min_z) < threshold:
                    break


    def _reset_estimator(self):
        cf = self.scf.cf
        cf.param.set_value('kalman.resetEstimation', '1')
        time.sleep(0.1)
        cf.param.set_value('kalman.resetEstimation', '0')

        self._wait_for_position_estimator()


    def position_callback(self, timestamp, data, logconf):
        x = data['kalman.stateX']
        y = data['kalman.stateY']
        z = data['kalman.stateZ']
        self.actualDronePosition = Vec3(x, y, z)
        #print('pos: ({}, {}, {})'.format(x, y, z))


    def start_position_printing(self):
        log_conf = LogConfig(name='Position', period_in_ms=50)
        log_conf.add_variable('kalman.stateX', 'float')
        log_conf.add_variable('kalman.stateY', 'float')
        log_conf.add_variable('kalman.stateZ', 'float')

        self.scf.cf.log.add_config(log_conf)
        log_conf.data_received_cb.add_callback(self.position_callback)
        log_conf.start()