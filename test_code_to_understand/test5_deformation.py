import pygame
import numpy as np
import sys

pygame.init()

# Configuration
WIDTH, HEIGHT = 1200, 800
POINT_RADIUS = 6
POINT_COLOR = (255, 100, 100)
POINT_HOVER_COLOR = (255, 200, 100)
SELECTED_COLOR = (100, 255, 100)
GRID_SIZE = 5  # Nombre de points sur chaque dimension

# Initialisation
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Déformation d'image - Cliquez et déplacez les points")
clock = pygame.time.Clock()

# Chargement de l'image
try:
    original_image = pygame.image.load("../img/fox_texture_body.png")
except:
    print("Erreur: Impossible de charger l'image '../img/fox_texture_body.png'")
    pygame.quit()
    sys.exit()

img_width, img_height = original_image.get_size()

# Position de l'image au centre
offset_x = (WIDTH - img_width) // 2
offset_y = (HEIGHT - img_height) // 2

# Création des points de contrôle sur le contour de l'image
original_points = []
current_points = []
POINTS_PER_SIDE = 8  # Nombre de points par côté

# Haut (de gauche à droite)
for i in range(POINTS_PER_SIDE):
    x = offset_x + (img_width * i / (POINTS_PER_SIDE - 1))
    y = offset_y
    original_points.append([x, y])
    current_points.append([x, y])

# Droite (de haut en bas, sans le premier point pour éviter les doublons)
for i in range(1, POINTS_PER_SIDE):
    x = offset_x + img_width
    y = offset_y + (img_height * i / (POINTS_PER_SIDE - 1))
    original_points.append([x, y])
    current_points.append([x, y])

# Bas (de droite à gauche, sans le premier point)
for i in range(1, POINTS_PER_SIDE):
    x = offset_x + img_width - (img_width * i / (POINTS_PER_SIDE - 1))
    y = offset_y + img_height
    original_points.append([x, y])
    current_points.append([x, y])

# Gauche (de bas en haut, sans le premier et dernier point)
for i in range(1, POINTS_PER_SIDE - 1):
    x = offset_x
    y = offset_y + img_height - (img_height * i / (POINTS_PER_SIDE - 1))
    original_points.append([x, y])
    current_points.append([x, y])

original_points = np.array(original_points, dtype=np.float32)
current_points = np.array(current_points, dtype=np.float32)
num_points = len(original_points)

# Variables pour l'interaction
selected_point = None
dragging = False
hover_point = None

# Surface pour l'image déformée
warped_surface = pygame.Surface((WIDTH, HEIGHT))
needs_update = True


def find_closest_point(pos, points, max_dist=20):
    """Trouve le point le plus proche de la position donnée"""
    min_dist = max_dist
    closest = None
    for i, point in enumerate(points):
        dist = np.sqrt((point[0] - pos[0]) ** 2 + (point[1] - pos[1]) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest = i
    return closest


def calculate_edge_weights(x, y, points, img_width, img_height):
    """Calcule les poids basés sur la distance aux points du contour"""
    weights = []
    total_weight = 0

    for i, point in enumerate(points):
        # Distance au point original
        orig_x = point[0] - offset_x
        orig_y = point[1] - offset_y
        dist = np.sqrt((x - orig_x) ** 2 + (y - orig_y) ** 2) + 1e-6

        # Poids inversement proportionnel à la distance
        weight = 1.0 / (dist ** 2)
        weights.append((i, weight))
        total_weight += weight

    # Normaliser les poids
    return [(idx, w / total_weight) for idx, w in weights]


def warp_image_fast(img, orig_points, curr_points):
    """Déforme l'image en utilisant une interpolation basée sur les points du contour"""
    result = pygame.Surface((WIDTH, HEIGHT))
    result.fill((40, 40, 50))

    # Convertir l'image en array numpy pour un accès plus rapide
    img_array = pygame.surfarray.array3d(img)

    # Pour chaque pixel de l'image
    for dst_y in range(offset_y, offset_y + img_height, 2):
        for dst_x in range(offset_x, offset_x + img_width, 2):
            rel_x = dst_x - offset_x
            rel_y = dst_y - offset_y

            if rel_x >= img_width or rel_y >= img_height:
                continue

            # Calculer les poids d'interpolation
            weights = calculate_edge_weights(rel_x, rel_y, orig_points, img_width, img_height)

            # Calculer la position déformée
            deformed_x = sum(curr_points[idx][0] * w for idx, w in weights)
            deformed_y = sum(curr_points[idx][1] * w for idx, w in weights)

            if 0 <= rel_x < img_width and 0 <= rel_y < img_height:
                color = img_array[rel_x, rel_y]
                pygame.draw.rect(result, color, (int(deformed_x), int(deformed_y), 2, 2))

    return result


# Boucle principale
running = True
last_pos = None

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reset avec la touche R
                current_points = original_points.copy()
                needs_update = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clic gauche
                closest = find_closest_point(event.pos, current_points)
                if closest is not None:
                    selected_point = closest
                    dragging = True
                    last_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if dragging:
                    needs_update = True
                dragging = False
                selected_point = None

        elif event.type == pygame.MOUSEMOTION:
            if dragging and selected_point is not None:
                current_points[selected_point] = np.array(event.pos, dtype=np.float32)
                last_pos = event.pos
            else:
                hover_point = find_closest_point(event.pos, current_points)

    # Déformation de l'image seulement si nécessaire
    if needs_update:
        print("Calcul de la déformation...")
        warped_surface = warp_image_fast(original_image, original_points, current_points)
        needs_update = False

    # Affichage
    screen.blit(warped_surface, (0, 0))

    # Si on est en train de déplacer, afficher l'image originale pour la fluidité
    if dragging:
        screen.blit(original_image, (offset_x, offset_y))

    # Dessiner les lignes de connexion entre les points (contour)
    for i in range(num_points):
        next_i = (i + 1) % num_points
        p1 = (int(current_points[i][0]), int(current_points[i][1]))
        p2 = (int(current_points[next_i][0]), int(current_points[next_i][1]))
        pygame.draw.line(screen, (100, 100, 120), p1, p2, 2)

    # Dessiner les points de contrôle
    for i, point in enumerate(current_points):
        if i == selected_point:
            color = SELECTED_COLOR
            radius = POINT_RADIUS + 2
        elif i == hover_point:
            color = POINT_HOVER_COLOR
            radius = POINT_RADIUS + 1
        else:
            color = POINT_COLOR
            radius = POINT_RADIUS

        pygame.draw.circle(screen, color, (int(point[0]), int(point[1])), radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(point[0]), int(point[1])), radius, 1)

    # Instructions
    font = pygame.font.Font(None, 24)
    text1 = font.render("Cliquez et déplacez les points pour déformer l'image", True, (255, 255, 255))
    text2 = font.render("Appuyez sur R pour réinitialiser", True, (255, 255, 255))
    screen.blit(text1, (10, 10))
    screen.blit(text2, (10, 35))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()