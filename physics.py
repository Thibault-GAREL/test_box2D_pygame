# ============================================
# physics.py - Gestion de la physique Box2D
# ============================================

from Box2D import b2World, b2PolygonShape, b2RevoluteJointDef
import math


class PhysicsWorld:
    """Gestionnaire du monde physique Box2D"""

    def __init__(self, gravity=(0, -10)):
        self.world = b2World(gravity=gravity, doSleep=True) # Do sleep pour ne pas calculer les objets qui ne bouge plus
        self.ground = None
        self.create_ground()

    def create_ground(self):
        """Crée le sol"""
        self.ground = self.world.CreateStaticBody(
            position=(0, 0),
            shapes=b2PolygonShape(box=(20, 0.5)) # rect de largeur 40 (en gros on part du centre et on fait 20 de chaque côté)
        )
        self.ground.fixtures[0].friction = 0.8

    def step(self, time_step, vel_iterations=10, pos_iterations=10):
        """Avance la simulation d'un pas"""
        self.world.Step(time_step, vel_iterations, pos_iterations)


class Bone:
    """Représente un os du squelette"""

    def __init__(self, world, x, y, width, height, density=5.0):
        self.body = world.CreateDynamicBody(
            position=(x, y),
            angle=0
        )
        self.fixture = self.body.CreatePolygonFixture(
            box=(width / 2, height / 2),
            density=density,
            friction=0.3
        )
        self.width = width
        self.height = height


class Muscle:
    """Représente un muscle (joint moteur entre deux os)"""

    def __init__(self, world, body_a, body_b, anchor_a, anchor_b,
                 min_angle, max_angle, max_torque=500, max_speed=5.0):
        joint_def = b2RevoluteJointDef(
            bodyA=body_a,
            bodyB=body_b,
            localAnchorA=anchor_a,
            localAnchorB=anchor_b,
            enableLimit=True,
            lowerAngle=min_angle,
            upperAngle=max_angle,
            enableMotor=True,
            maxMotorTorque=max_torque,
            motorSpeed=0
        )
        self.joint = world.CreateJoint(joint_def)
        self.target_speed = 0
        self.max_speed = max_speed
        self.body_a = body_a
        self.body_b = body_b
        self.anchor_a = anchor_a
        self.anchor_b = anchor_b

    def contract(self, strength=1.0):
        """Contracter le muscle (flexion)"""
        self.target_speed = -self.max_speed * strength

    def extend(self, strength=1.0):
        """Étendre le muscle (extension)"""
        self.target_speed = self.max_speed * strength

    def relax(self):
        """Relâcher le muscle"""
        self.target_speed = 0

    def update(self):
        """Mettre à jour la vitesse du moteur"""
        self.joint.motorSpeed = self.target_speed

    def get_angle(self):
        """Retourne l'angle actuel du joint"""
        return self.joint.angle

    def get_speed(self):
        """Retourne la vitesse angulaire actuelle"""
        return self.joint.speed


class Quadruped:
    """Représente un quadrupède simple avec des muscles"""

    def __init__(self, physics_world, x=6, y=3):
        self.physics_world = physics_world
        world = physics_world.world

        # Créer les os
        width_bone = 0.05
        density_bone = 3
        self.body = Bone(world, x, y, 1.5, width_bone, density=density_bone)
        self.back_thigh = Bone(world, x - 0.8, y - 0.5, width_bone, 0.5, density=density_bone)
        self.back_shin = Bone(world, x - 0.8, y - 1.3, width_bone, 0.4, density=density_bone)
        self.front_leg = Bone(world, x + 0.8, y - 0.7, width_bone, 0.6, density=density_bone)

        self.bones = [self.body, self.back_thigh, self.back_shin, self.front_leg]

        # Créer les 3 muscles
        self.muscle1 = Muscle(
            world, self.body.body, self.back_thigh.body,
            (-0.5, -0.15), (0, 0.25),
            -math.pi / 2, math.pi / 4, max_torque=600
        )

        self.muscle2 = Muscle(
            world, self.back_thigh.body, self.back_shin.body,
            (0, -0.25), (0, 0.2),
            -math.pi * 0.8, 0, max_torque=400
        )

        self.muscle3 = Muscle(
            world, self.body.body, self.front_leg.body,
            (0.5, -0.15), (0, 0.3),
            -math.pi / 2, math.pi / 4, max_torque=500
        )

        self.muscles = [self.muscle1, self.muscle2, self.muscle3]

    def control_muscles(self, muscle_index, action):
        """
        Contrôle un muscle spécifique
        muscle_index: 0, 1 ou 2
        action: 'contract', 'extend' ou 'relax'
        """
        if 0 <= muscle_index < len(self.muscles):
            if action == 'contract':
                self.muscles[muscle_index].contract(1.0)
            elif action == 'extend':
                self.muscles[muscle_index].extend(1.0)
            elif action == 'relax':
                self.muscles[muscle_index].relax()

    def update(self):
        """Met à jour tous les muscles"""
        for muscle in self.muscles:
            muscle.update()

    def get_state(self):
        """Retourne l'état du quadrupède (pour l'IA plus tard)"""
        state = {
            'body_pos': self.body.body.position,
            'body_angle': self.body.body.angle,
            'body_velocity': self.body.body.linearVelocity,
            'muscle_angles': [m.get_angle() for m in self.muscles],
            'muscle_speeds': [m.get_speed() for m in self.muscles]
        }
        return state


