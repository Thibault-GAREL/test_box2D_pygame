# ============================================
# physics.py - Gestion de la physique Box2D
# ============================================

from Box2D import b2World, b2PolygonShape, b2RevoluteJointDef
import math


class PhysicsWorld:
    """Gestionnaire du monde physique Box2D"""

    def __init__(self, gravity=(0, -10)):
        self.world = b2World(gravity=gravity, doSleep=True)
        self.ground = None
        self.create_ground()

    def create_ground(self):
        """Crée le sol"""
        self.ground = self.world.CreateStaticBody(
            position=(0, 1),
            shapes=b2PolygonShape(box=(20, 0.5))
        )

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
    """Représente un quadrupède simple avec 3 muscles"""

    def __init__(self, physics_world, x=6, y=3):
        self.physics_world = physics_world
        world = physics_world.world

        # Créer les os
        self.body = Bone(world, x, y, 1.0, 0.3, density=10)
        self.back_thigh = Bone(world, x - 0.8, y - 0.5, 0.15, 0.5, density=3)
        self.back_shin = Bone(world, x - 0.8, y - 1.3, 0.15, 0.4, density=2)
        self.front_leg = Bone(world, x + 0.8, y - 0.7, 0.15, 0.6, density=3)

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


# ============================================
# display.py - Gestion de l'affichage Pygame
# ============================================

import pygame


class Display:
    """Gestionnaire de l'affichage avec Pygame"""

    def __init__(self, width=1200, height=700, title="Quadrupède"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.PPM = 100.0  # Pixels par mètre

    def to_screen(self, pos):
        """Convertit les coordonnées Box2D en coordonnées Pygame"""
        return (int(pos[0] * self.PPM), int(self.height - pos[1] * self.PPM))

    def clear(self, color=(30, 30, 40)):
        """Efface l'écran"""
        self.screen.fill(color)

    def draw_ground(self, ground_body):
        """Dessine le sol"""
        vertices = [(ground_body.transform * v) * self.PPM
                    for v in ground_body.fixtures[0].shape.vertices]
        vertices = [(v[0], self.height - v[1]) for v in vertices]
        pygame.draw.polygon(self.screen, (100, 150, 100), vertices)

    def draw_bone(self, bone, color=(255, 255, 255)):
        """Dessine un os (rectangle blanc)"""
        vertices = [(bone.body.transform * v) * self.PPM
                    for v in bone.fixture.shape.vertices]
        vertices = [(v[0], self.height - v[1]) for v in vertices]
        pygame.draw.polygon(self.screen, color, vertices)

    def draw_muscle(self, muscle, color=(255, 0, 0)):
        """Dessine un muscle (ligne rouge)"""
        # Position des points d'ancrage
        pos_a = muscle.body_a.transform * muscle.anchor_a
        pos_b = muscle.body_b.transform * muscle.anchor_b

        # Convertir en coordonnées écran
        screen_a = self.to_screen(pos_a)
        screen_b = self.to_screen(pos_b)

        # Dessiner la ligne et les points
        pygame.draw.line(self.screen, color, screen_a, screen_b, 4)
        pygame.draw.circle(self.screen, (200, 0, 0), screen_a, 5)
        pygame.draw.circle(self.screen, (200, 0, 0), screen_b, 5)

    def draw_text(self, text, position, color=(255, 255, 255)):
        """Affiche du texte à l'écran"""
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, position)

    def draw_instructions(self):
        """Affiche les instructions de contrôle"""
        instructions = [
            "Contrôles des 3 muscles :",
            "Q/A : Muscle 1 (hanche arrière)",
            "W/S : Muscle 2 (genou arrière)",
            "E/D : Muscle 3 (épaule avant)",
            "ESC : Quitter"
        ]

        for i, text in enumerate(instructions):
            self.draw_text(text, (10, 10 + i * 25))

    def update(self):
        """Rafraîchit l'affichage"""
        pygame.display.flip()

    def tick(self, fps=60):
        """Limite le framerate"""
        self.clock.tick(fps)

    def quit(self):
        """Ferme Pygame"""
        pygame.quit()


# ============================================
# main.py - Boucle principale
# ============================================


def main():
    # Initialiser les systèmes
    physics_world = PhysicsWorld(gravity=(0, -10))
    display = Display(width=1200, height=700, title="Quadrupède - 3 muscles")
    quadruped = Quadruped(physics_world, x=6, y=3)

    # Paramètres de simulation
    TARGET_FPS = 60
    TIME_STEP = 1.0 / TARGET_FPS

    # Boucle principale
    running = True
    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Gestion des touches (contrôle manuel)
        keys = pygame.key.get_pressed()

        # Relâcher tous les muscles
        for i in range(3):
            quadruped.control_muscles(i, 'relax')

        # Muscle 1 (hanche arrière)
        if keys[pygame.K_q]:
            quadruped.control_muscles(0, 'contract')
        elif keys[pygame.K_a]:
            quadruped.control_muscles(0, 'extend')

        # Muscle 2 (genou arrière)
        if keys[pygame.K_w]:
            quadruped.control_muscles(1, 'contract')
        elif keys[pygame.K_s]:
            quadruped.control_muscles(1, 'extend')

        # Muscle 3 (épaule avant)
        if keys[pygame.K_e]:
            quadruped.control_muscles(2, 'contract')
        elif keys[pygame.K_d]:
            quadruped.control_muscles(2, 'extend')

        # Mettre à jour la physique
        quadruped.update()
        physics_world.step(TIME_STEP)

        # Affichage
        display.clear()
        display.draw_ground(physics_world.ground)

        # Dessiner les os
        for bone in quadruped.bones:
            display.draw_bone(bone)

        # Dessiner les muscles
        for muscle in quadruped.muscles:
            display.draw_muscle(muscle)

        display.draw_instructions()
        display.update()
        display.tick(TARGET_FPS)

    display.quit()


if __name__ == "__main__":
    main()