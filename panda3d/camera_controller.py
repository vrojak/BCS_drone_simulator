import sys,os
from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
#from direct.actor.Actor import Actor
#from direct.interval.IntervalGlobal import Sequence
#from panda3d.core import Point3 # pylint: disable=no-name-in-module
from panda3d.core import Filename
from panda3d.core import DirectionalLight
from panda3d.core import AntialiasAttrib
from panda3d.core import MouseButton
from panda3d.core import KeyboardButton
from panda3d.core import WindowProperties
from panda3d.core import VBase4
from panda3d.core import LVector3f
from panda3d.core import LVecBase3f
#from panda3d.core import CSDefault

class CameraController:

    def __init__(self, base):
        self.base = base
        self.camera = base.camera
        self.base.disableMouse()
        self.cameraControlActive = False
        self.base.accept("t", self.toggleCameraControl)


    def toggleCameraControl(self):
        if self.cameraControlActive:
            self.cameraControlActive = False
            props = WindowProperties()
            props.setCursorHidden(False)
            self.base.win.requestProperties(props)
            self.base.taskMgr.remove("CameraControlTask")
        else:
            self.cameraControlActive = True
            props = WindowProperties()
            props.setCursorHidden(True)
            self.base.win.requestProperties(props)
            self.base.taskMgr.add(self.cameraControlTask, "CameraControlTask")


    def cameraControlTask(self, task):
        mw = self.base.mouseWatcherNode
        curPos = self.camera.getPos()
        curHpr = self.camera.getHpr()
        forward = self.camera.getQuat().getForward()
        right = self.camera.getQuat().getRight()
        up = self.camera.getQuat().getUp()
        moveSpeed = .1
        rotSpeed = 20

        if mw.hasMouse():
            deltaX = rotSpeed * mw.getMouseX()
            deltaY = rotSpeed * mw.getMouseY()
            props = self.base.win.getProperties()
            self.base.win.movePointer(0, int(props.getXSize() / 2), int(props.getYSize() / 2)) # window size has to be a multiple of 2 or this causes trouble
            self.camera.setHpr(curHpr.getX() - deltaX, curHpr.getY() + deltaY, 0)

        deltaPos = LVector3f(0, 0, 0)
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('w','utf-8'))):
            deltaPos += forward * moveSpeed
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('s','utf-8'))):
            deltaPos -= forward * moveSpeed
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('d','utf-8'))):
            deltaPos += right * moveSpeed
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('a','utf-8'))):
            deltaPos -= right * moveSpeed
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('q','utf-8'))):
            deltaPos += up * moveSpeed
        if mw.isButtonDown(KeyboardButton.asciiKey(bytes('e','utf-8'))):
            deltaPos -= up * moveSpeed
        self.camera.setPos(curPos + deltaPos)

        return Task.cont