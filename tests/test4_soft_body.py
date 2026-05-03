import pygame
import Box2D
from Box2D import b2World, b2Vec2, b2PolygonShape, b2FixtureDef

# Initialisation
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Soft Body Simulation")
clock = pygame.time.Clock()

# Conversion pixels <-> mètres
PPM = 20.0  # Pixels par mètre


def to_screen(pos):
    return (int(pos[0] * PPM), int(HEIGHT - pos[1] * PPM))


def to_world(pos):
    return (pos[0] / PPM, (HEIGHT - pos[1]) / PPM)


# Création du monde Box2D
world = b2World(gravity=(0, -10), doSleep=True)

# Création du sol
ground_body = world.CreateStaticBody(
    position=(0, 1),
    shapes=b2PolygonShape(box=(50, 1))
)


# Classe pour le Soft Body
class SoftBody:
    def __init__(self, world, center_x, center_y):
        self.world = world
        self.points = []
        self.relative_positions = []  # Positions relatives au centre de masse
        self.connections = []

        # Constantes physiques
        self.spring_strength = 10.0  # Force de ressort
        self.spring_damping = 1.0  # Amortissement
        self.shape_memory = 50  # Force de retour à la forme originale (très réduite)
        self.collision_stiffness = 200.0  # Rigidité lors des collisions
        self.collision_damping = 10.0  # Amortissement des collisions

        # Forme personnalisée manuelle - Dessine ta forme en listant les points dans l'ordre
        points_positions = [
            (0, 5),  # Sommet
            (2, 3),
            (4, 2),
            (3, 0),
            (4, -2),
            (1, -4),  # Bas droite
            # (0, -3),  # Bas centre
            # (-1, -4),  # Bas gauche
            # (-4, -2),
            # (-3, 0),
            # (-4, 2),
            # (-2, 3),
        ]

        # Centrer la forme (calculer le centre géométrique et recentrer)
        center_x_geom = sum(p[0] for p in points_positions) / len(points_positions)
        center_y_geom = sum(p[1] for p in points_positions) / len(points_positions)

        # Recentrer tous les points autour de (0, 0)
        points_positions = [(x - center_x_geom, y - center_y_geom) for x, y in points_positions]

        self.num_points = len(points_positions)

        # Créer les corps physiques avec plus de masse
        for rel_x, rel_y in points_positions:
            body = world.CreateDynamicBody(
                position=(center_x + rel_x, center_y + rel_y),
                linearDamping=0.5,
                angularDamping=0.5
            )
            body.CreateCircleFixture(radius=0.3, density=5.0, friction=0.5, restitution=0.3)  # Densité augmentée

            self.points.append(body)
            self.relative_positions.append(b2Vec2(rel_x, rel_y))

        # Créer les connexions entre points adjacents (le périmètre)
        for i in range(self.num_points):
            next_i = (i + 1) % self.num_points
            original_length = (self.relative_positions[i] -
                               self.relative_positions[next_i]).length
            self.connections.append({
                'i': i,
                'j': next_i,
                'rest_length': original_length
            })

        # Créer des connexions internes limitées pour la stabilité
        # On connecte chaque point uniquement aux points à distance 2 et 3
        for i in range(self.num_points):
            # Connexion à distance 2 (saute 1 point)
            j = (i + 2) % self.num_points
            if j != i:
                original_length = (self.relative_positions[i] -
                                   self.relative_positions[j]).length
                self.connections.append({
                    'i': i,
                    'j': j,
                    'rest_length': original_length
                })

            # Connexion à distance 3 (saute 2 points) - seulement si assez de points
            if self.num_points > 5:
                j = (i + 3) % self.num_points
                if j != i and j != (i + 1) % self.num_points:
                    original_length = (self.relative_positions[i] -
                                       self.relative_positions[j]).length
                    self.connections.append({
                        'i': i,
                        'j': j,
                        'rest_length': original_length
                    })

        # Créer les connexions entre points adjacents (le périmètre du carré)
        for i in range(self.num_points):
            next_i = (i + 1) % self.num_points
            original_length = (self.relative_positions[i] -
                               self.relative_positions[next_i]).length
            self.connections.append({
                'i': i,
                'j': next_i,
                'rest_length': original_length
            })

        # Créer des connexions diagonales et croisées pour la stabilité
        for i in range(self.num_points):
            for j in range(i + 2, self.num_points):
                if j != (i + 1) % self.num_points and j != i:
                    original_length = (self.relative_positions[i] -
                                       self.relative_positions[j]).length
                    self.connections.append({
                        'i': i,
                        'j': j,
                        'rest_length': original_length
                    })

    def update(self):
        import math

        # Calculer le centre de masse actuel
        center = b2Vec2(0, 0)
        for point in self.points:
            center += point.position
        center *= (1.0 / len(self.points))

        # Calculer l'angle DIRECTEMENT à partir des positions actuelles
        # On compare les positions actuelles avec les positions relatives d'origine
        cos_sum = 0.0
        sin_sum = 0.0
        total_weight = 0.0

        for i in range(self.num_points):
            # Vecteur actuel depuis le centre de masse
            current_vec = self.points[i].position - center
            # Vecteur original (forme de base)
            original_vec = self.relative_positions[i]

            if current_vec.length > 0.1 and original_vec.length > 0.1:
                # Calculer un poids basé sur la vitesse du point
                # Les points en contact avec le sol ont une vitesse plus faible
                velocity = self.points[i].linearVelocity.length
                # Points avec plus de vitesse = plus de poids dans le calcul
                # On ajoute 1.0 pour que même les points statiques comptent un peu
                weight = 1.0 + velocity * 2.0

                # Angle du vecteur actuel
                current_angle = math.atan2(current_vec.y, current_vec.x)
                # Angle du vecteur original
                original_angle = math.atan2(original_vec.y, original_vec.x)
                # Différence d'angle
                angle_diff = current_angle - original_angle

                # Accumuler avec sin et cos pondérés
                cos_sum += math.cos(angle_diff) * weight
                sin_sum += math.sin(angle_diff) * weight
                total_weight += weight

        # Calculer l'angle INSTANTANÉ (pas incrémental)
        if total_weight > 0:
            avg_angle = math.atan2(sin_sum, cos_sum)
        else:
            avg_angle = 0.0

        # Appliquer les forces de ressort entre points connectés
        for conn in self.connections:
            p1 = self.points[conn['i']]
            p2 = self.points[conn['j']]

            diff = p2.position - p1.position
            distance = diff.length

            if distance > 0.01:
                # Force de ressort (Loi de Hooke)
                force_magnitude = self.spring_strength * (distance - conn['rest_length'])
                force_direction = diff / distance
                force = force_direction * force_magnitude

                # Amortissement
                vel_diff = p2.linearVelocity - p1.linearVelocity
                damping_force = vel_diff * self.spring_damping

                total_force = force + damping_force

                p1.ApplyForce(total_force, p1.worldCenter, True)
                p2.ApplyForce(-total_force, p2.worldCenter, True)

        # Appliquer la force de retour à la forme originale (avec rotation)
        cos_angle = math.cos(avg_angle)
        sin_angle = math.sin(avg_angle)

        for i, point in enumerate(self.points):
            # Appliquer la rotation à la position relative originale
            orig_x = self.relative_positions[i].x
            orig_y = self.relative_positions[i].y

            # Rotation de la forme de base
            rotated_x = orig_x * cos_angle - orig_y * sin_angle
            rotated_y = orig_x * sin_angle + orig_y * cos_angle

            target_position = center + b2Vec2(rotated_x, rotated_y)
            to_target = target_position - point.position
            shape_force = to_target * self.shape_memory
            point.ApplyForce(shape_force, point.worldCenter, True)

            # Détecter collision avec le sol et appliquer force de répulsion
            ground_y = 2.0  # Position Y du sol en coordonnées monde
            point_y = point.position.y
            point_radius = 0.3

            # Si le point pénètre le sol
            penetration = (ground_y + point_radius) - point_y
            if penetration > 0:
                # Force de répulsion proportionnelle à la pénétration (loi de Hooke)
                repulsion_force_magnitude = penetration * self.collision_stiffness

                # Amortissement basé sur la vitesse verticale
                velocity_y = point.linearVelocity.y
                damping_force = -velocity_y * self.collision_damping

                total_repulsion = repulsion_force_magnitude + damping_force

                # Appliquer la force verticale vers le haut
                point.ApplyForce(b2Vec2(0, total_repulsion), point.worldCenter, True)

                # Friction horizontale lors du contact
                friction_force = -point.linearVelocity.x * 5.0
                point.ApplyForce(b2Vec2(friction_force, 0), point.worldCenter, True)

    def draw(self, screen):
        # Dessiner les connexions
        for conn in self.connections:
            p1 = to_screen(self.points[conn['i']].position)
            p2 = to_screen(self.points[conn['j']].position)
            pygame.draw.line(screen, (100, 150, 255), p1, p2, 2)

        # Dessiner les points
        for point in self.points:
            pos = to_screen(point.position)
            pygame.draw.circle(screen, (50, 100, 200), pos, 6)
            pygame.draw.circle(screen, (150, 200, 255), pos, 4)


# Créer le soft body (forme personnalisée)
soft_body = SoftBody(world, 20, 20)

# Variables pour l'interaction
selected_point = None
mouse_joint = None

# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = to_world(pygame.mouse.get_pos())
            # Chercher un point proche
            for point in soft_body.points:
                dist = (point.position - b2Vec2(mouse_pos[0], mouse_pos[1])).length
                if dist < 1.0:
                    selected_point = point
                    break

        elif event.type == pygame.MOUSEBUTTONUP:
            selected_point = None

    # Appliquer une force si un point est sélectionné
    if selected_point and pygame.mouse.get_pressed()[0]:
        mouse_pos = to_world(pygame.mouse.get_pos())
        target = b2Vec2(mouse_pos[0], mouse_pos[1])
        force = (target - selected_point.position) * 500
        selected_point.ApplyForce(force, selected_point.worldCenter, True)

    # Mise à jour de la physique
    soft_body.update()
    world.Step(1.0 / 60.0, 10, 10)

    # Affichage
    screen.fill((20, 20, 30))

    # Dessiner le sol
    ground_pos = to_screen(ground_body.position)
    pygame.draw.rect(screen, (100, 100, 100),
                     (0, ground_pos[1] - 20, WIDTH, 40))

    # Dessiner le soft body
    soft_body.draw(screen)

    # Instructions
    font = pygame.font.Font(None, 24)
    text = font.render("Cliquez et tirez sur les points pour déformer le soft body",
                       True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()