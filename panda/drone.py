# pylint: disable=no-name-in-module
from panda3d.core import Vec3
from panda3d.core import Loader
from panda3d.bullet import BulletSphereShape
from panda3d.bullet import BulletRigidBodyNode
from panda3d.bullet import BulletGhostNode

class Drone:

    def __init__(self, position: Vec3, base):
        self.base = base

        self.rigidBody = BulletRigidBodyNode("RigidSphere") # derived from PandaNode
        self.rigidBody.setMass(1.0) # body is now dynamic
        self.rigidBody.addShape(BulletSphereShape(0.3))
        self.rigidBodyNP = base.render.attachNewNode(self.rigidBody)
        self.rigidBodyNP.setPos(position)

        self.ghost = BulletGhostNode("GhostSphere")
        self.ghost.addShape(BulletSphereShape(1.5))
        self.ghostNP = base.render.attachNewNode(self.ghost)
        self.ghostNP.setPos(position)

        base.world.attach(self.rigidBody)
        base.world.attach(self.ghost)
        model = base.loader.loadModel(base.modelDir + "/drones/drone1.egg")
        model.reparentTo(self.rigidBodyNP)

        self.target = position
        self.rigidBody.setLinearDamping(0.8)


    def setTarget(self, target: Vec3):
        self.target = target


    def updateGhost(self):
        self.ghostNP.setPos(self.rigidBodyNP.getPos())


    def updateForce(self):
        dist = (self.target - self.rigidBodyNP.getPos())
        if(dist.lengthSquared() > 5**2):
            force = dist.normalized()
        else:
            force = dist / 5
        self.rigidBody.applyCentralForce(force * 5)
    