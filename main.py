import pygame
from Box2D import b2World, b2Vec2, b2PolygonShape, b2CircleShape

# Initialisation de Pygame
pygame.init()

# Constantes
WIDTH, HEIGHT = 800, 600
FPS = 60
PPM = 60.0  # Pixels par mètre (pour convertir coordonnées Box2D en pixels)

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLORS = [(255, 100, 100), (100, 255, 100), (100, 100, 255),
          (255, 255, 100), (255, 100, 255), (100, 255, 255)]

# Créer la fenêtre
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cercles tombants - PyBox2D")
clock = pygame.time.Clock()

# Créer le monde physique Box2D (gravité en y négatif)
world = b2World(gravity=(0, -10), doSleep=True)

# Créer le sol (corps statique)
ground_body = world.CreateStaticBody(
    position=(WIDTH / (2 * PPM), 1),
    shapes=b2PolygonShape(box=(WIDTH / (2 * PPM), 1))
)

# Créer les murs latéraux
left_wall = world.CreateStaticBody(
    position=(1, HEIGHT / (2 * PPM)),
    shapes=b2PolygonShape(box=(1, HEIGHT / (2 * PPM)))
)

right_wall = world.CreateStaticBody(
    position=(WIDTH / PPM - 1, HEIGHT / (2 * PPM)),
    shapes=b2PolygonShape(box=(1, HEIGHT / (2 * PPM)))
)

# Liste pour stocker les cercles
circles = []


def create_circle(x, y, radius=0.5):
    """Crée un cercle dynamique à la position donnée"""
    body = world.CreateDynamicBody(
        position=(x / PPM, (HEIGHT - y) / PPM),
        bullet=False
    )
    circle = body.CreateCircleFixture(
        shape=b2CircleShape(radius=radius),
        density=1.0,
        friction=0.3,
        restitution=0.6  # Rebond
    )
    color = COLORS[len(circles) % len(COLORS)]
    circles.append({'body': body, 'radius': radius, 'color': color})


def draw():
    """Dessine tous les objets"""
    screen.fill(WHITE)

    # Dessiner le sol
    ground_y = HEIGHT - ground_body.position.y * PPM
    pygame.draw.rect(screen, BLACK, (0, ground_y, WIDTH, HEIGHT - ground_y))

    # Dessiner les murs
    pygame.draw.rect(screen, BLACK, (0, 0, left_wall.position.x * PPM * 2, HEIGHT))
    wall_x = right_wall.position.x * PPM - left_wall.position.x * PPM
    pygame.draw.rect(screen, BLACK, (wall_x, 0, WIDTH - wall_x, HEIGHT))

    # Dessiner les cercles
    for circle in circles:
        pos = circle['body'].position
        x = int(pos.x * PPM)
        y = int(HEIGHT - pos.y * PPM)
        radius = int(circle['radius'] * PPM)
        pygame.draw.circle(screen, circle['color'], (x, y), radius)
        pygame.draw.circle(screen, BLACK, (x, y), radius, 1)

    pygame.display.flip()


# Boucle principale
running = True
spawn_timer = 0

while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Créer un cercle au clic de souris
            x, y = pygame.mouse.get_pos()
            create_circle(x, y, radius=0.5 + (len(circles) % 3) * 0.2)

    # Créer automatiquement des cercles
    spawn_timer += dt
    if spawn_timer > 0.5 and len(circles) < 50:
        import random

        x = random.randint(100, WIDTH - 100)
        create_circle(x, 50, radius=0.4 + random.random() * 0.4)
        spawn_timer = 0

    # Mettre à jour la physique
    world.Step(1.0 / FPS, 10, 10)

    # Dessiner
    draw()

pygame.quit()