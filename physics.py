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
            friction=0.5
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
        thigh_height = 0.4
        shin_height = 0.4
        self.body = Bone(world, x, y, 1.1, width_bone, density=density_bone)
        self.back_thigh = Bone(world, x - 0.8, y - 0.5, width_bone, thigh_height, density=density_bone) # cuisse
        self.back_shin = Bone(world, x - 0.8, y - 1.3, width_bone, shin_height, density=density_bone) # tibia
        self.front_thigh = Bone(world, x + 0.8, y - 0.5, width_bone, thigh_height, density=density_bone)
        self.front_shin = Bone(world, x + 0.8, y - 1.3, width_bone, shin_height, density=density_bone)
        self.neck = Bone(world, x + 0.9, y + 0.1, width_bone, 0.4, density=density_bone)
        self.tail_bottom = Bone(world, x - 0.9, y + 0.1, width_bone, 0.4, density=density_bone)
        self.tail_mid = Bone(world, x - 1, y + 0.3, width_bone, 0.2, density=density_bone)
        self.tail_high = Bone(world, x - 1.1, y + 0.4, width_bone, 0.2, density=density_bone)

        self.bones = [self.body, self.back_thigh, self.back_shin, self.front_thigh, self.front_shin, self.neck, self.tail_bottom, self.tail_mid, self.tail_high]

        # Créer les 3 muscles
        self.muscle1 = Muscle(
            world, self.body.body, self.back_thigh.body,
            (-0.5, -0.05), (0, 0.25),
            -math.pi / 4, math.pi / 4, max_torque=600
        )

        self.muscle2 = Muscle(
            world, self.back_thigh.body, self.back_shin.body,
            (0, -0.25), (0, 0.2),
            -math.pi * 0.8, 0, max_torque=400
        )

        self.muscle3 = Muscle(
            world, self.body.body, self.front_thigh.body,
            (0.5, -0.05), (0, 0.25),
            -math.pi / 4, math.pi / 4, max_torque=600
        )

        self.muscle4 = Muscle(
            world, self.front_thigh.body, self.front_shin.body,
            (0, -0.25), (0, 0.2),
            -math.pi * 0.8, 0, max_torque=400
        )

        self.muscle5 = Muscle(
            world, self.body.body, self.neck.body,
            (0.55, 0.05), (0, 0.2),
            math.pi * 0.7, math.pi * 0.7, max_torque=40
        )

        self.muscle6 = Muscle(
            world, self.body.body, self.tail_bottom.body,
            (-0.55, 0.05), (0, 0.2),
            -math.pi * 0.6, -math.pi * 0.6, max_torque=40
        )
        self.muscle7 = Muscle(
            world, self.tail_bottom.body, self.tail_mid.body,
            (0, -0.2), (0, 0.15),
            -math.pi * 0.5, -math.pi * 0.5, max_torque=40
        )

        self.muscle8 = Muscle(
            world, self.tail_mid.body, self.tail_high.body,
            (0, -0.15), (0, 0.15),
            -math.pi * 0.4, -math.pi * 0.4, max_torque=40
        )

        self.muscles = [self.muscle1, self.muscle2, self.muscle3, self.muscle4, self.muscle5, self.muscle6, self.muscle7, self.muscle8]

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


    def is_upside_down(self, threshold=math.pi / 4):
        """
        Vérifie si le quadrupède est retourné (dos au sol)
        threshold: angle en radians (par défaut π/4 = 45°)
        Retourne True si l'angle du corps dépasse le seuil
        """
        angle = self.body.body.angle % (2 * math.pi)

        # Normaliser l'angle entre -π et π
        if angle > math.pi:
            angle -= 2 * math.pi

        # Le quadrupède est retourné si l'angle est proche de ±π (180°)
        return abs(abs(angle) - math.pi) < threshold
