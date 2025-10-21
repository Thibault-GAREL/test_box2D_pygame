import pygame
from Box2D import b2World, b2Vec2, b2PolygonShape, b2_dynamicBody, b2RevoluteJointDef
import math

# Initialisation de Pygame
pygame.init()
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Quadrupède simple - 3 muscles")
clock = pygame.time.Clock()

# Paramètres de conversion Box2D <-> Pygame
PPM = 100.0  # Pixels par mètre
TARGET_FPS = 60
TIME_STEP = 1.0 / TARGET_FPS

# Créer le monde Box2D
world = b2World(gravity=(0, -10), doSleep=True)

# Créer le sol
ground_body = world.CreateStaticBody(
    position=(0, 1),
    shapes=b2PolygonShape(box=(20, 0.5))
)


# Classe pour créer un os (segment de corps)
class Bone:
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


# Classe pour créer un muscle (joint moteur)
class Muscle:
    def __init__(self, world, body_a, body_b, anchor_a, anchor_b,
                 min_angle, max_angle, max_torque=500):
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
        self.max_speed = 5.0
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


# Créer le quadrupède simple
# Corps principal (torse)
body = Bone(world, 6, 3, 1.0, 0.3, density=10)

# Cuisse arrière
back_thigh = Bone(world, 5.2, 2.5, 0.15, 0.5, density=3)

# Tibia arrière
back_shin = Bone(world, 5.2, 1.7, 0.15, 0.4, density=2)

# Patte avant
front_leg = Bone(world, 6.8, 2.3, 0.15, 0.6, density=3)

# Créer les 3 muscles
# Muscle 1 : Hanche arrière (entre corps et cuisse)
muscle1 = Muscle(world, body.body, back_thigh.body,
                 (-0.5, -0.15), (0, 0.25),
                 -math.pi / 2, math.pi / 4, max_torque=600)

# Muscle 2 : Genou arrière (entre cuisse et tibia)
muscle2 = Muscle(world, back_thigh.body, back_shin.body,
                 (0, -0.25), (0, 0.2),
                 -math.pi * 0.8, 0, max_torque=400)

# Muscle 3 : Épaule avant (entre corps et patte avant)
muscle3 = Muscle(world, body.body, front_leg.body,
                 (0.5, -0.15), (0, 0.3),
                 -math.pi / 2, math.pi / 4, max_torque=500)

muscles = [muscle1, muscle2, muscle3]
bones = [body, back_thigh, back_shin, front_leg]


# Fonction pour convertir les coordonnées Box2D en Pygame
def to_screen(pos):
    return (int(pos[0] * PPM), int(SCREEN_HEIGHT - pos[1] * PPM))


# Fonction pour dessiner un os (rectangle blanc)
def draw_bone(bone):
    vertices = [(bone.body.transform * v) * PPM for v in bone.fixture.shape.vertices]
    vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
    pygame.draw.polygon(screen, (255, 255, 255), vertices)


# Fonction pour dessiner un muscle (ligne rouge entre les articulations)
def draw_muscle(muscle):
    # Position du point d'ancrage sur le corps A
    pos_a = muscle.body_a.transform * muscle.anchor_a
    # Position du point d'ancrage sur le corps B
    pos_b = muscle.body_b.transform * muscle.anchor_b

    # Convertir en coordonnées écran
    screen_a = to_screen(pos_a)
    screen_b = to_screen(pos_b)

    # Dessiner la ligne rouge (muscle)
    pygame.draw.line(screen, (255, 0, 0), screen_a, screen_b, 4)
    pygame.draw.circle(screen, (200, 0, 0), screen_a, 5)
    pygame.draw.circle(screen, (200, 0, 0), screen_b, 5)


# Fonction pour dessiner le sol
def draw_ground():
    vertices = [(ground_body.transform * v) * PPM for v in ground_body.fixtures[0].shape.vertices]
    vertices = [(v[0], SCREEN_HEIGHT - v[1]) for v in vertices]
    pygame.draw.polygon(screen, (100, 150, 100), vertices)


# Fonction pour afficher les instructions
def draw_instructions():
    font = pygame.font.Font(None, 24)
    instructions = [
        "Contrôles des 3 muscles :",
        "Q/A : Muscle 1 (hanche arrière)",
        "W/S : Muscle 2 (genou arrière)",
        "E/D : Muscle 3 (épaule avant)",
        "ESC : Quitter"
    ]

    for i, text in enumerate(instructions):
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, (10, 10 + i * 25))


# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Gestion des touches enfoncées
    keys = pygame.key.get_pressed()

    # Relâcher tous les muscles par défaut
    for muscle in muscles:
        muscle.relax()

    # Muscle 1 (hanche arrière)
    if keys[pygame.K_q]:
        muscles[0].contract(1.0)
    elif keys[pygame.K_a]:
        muscles[0].extend(1.0)

    # Muscle 2 (genou arrière)
    if keys[pygame.K_w]:
        muscles[1].contract(1.0)
    elif keys[pygame.K_s]:
        muscles[1].extend(1.0)

    # Muscle 3 (épaule avant)
    if keys[pygame.K_e]:
        muscles[2].contract(1.0)
    elif keys[pygame.K_d]:
        muscles[2].extend(1.0)

    # Mettre à jour les muscles
    for muscle in muscles:
        muscle.update()

    # Simuler la physique
    world.Step(TIME_STEP, 10, 10)

    # Dessiner
    screen.fill((30, 30, 40))
    draw_ground()

    # Dessiner les os (rectangles blancs)
    for bone in bones:
        draw_bone(bone)

    # Dessiner les muscles (lignes rouges)
    for muscle in muscles:
        draw_muscle(muscle)

    draw_instructions()

    pygame.display.flip()
    clock.tick(TARGET_FPS)

pygame.quit()