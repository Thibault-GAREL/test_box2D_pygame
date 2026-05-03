import pygame
import numpy as np
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2 Cercles avec Texture")
clock = pygame.time.Clock()


class Bone:
    """Un os simple"""

    def __init__(self, x, y, length, angle=0):
        self.x = x
        self.y = y
        self.length = length
        self.angle = angle

    def get_end_pos(self):
        end_x = self.x + self.length * math.cos(math.radians(self.angle))
        end_y = self.y + self.length * math.sin(math.radians(self.angle))
        return end_x, end_y

    def draw(self, surface):
        end_x, end_y = self.get_end_pos()
        pygame.draw.line(surface, (255, 200, 0),
                         (int(self.x), int(self.y)),
                         (int(end_x), int(end_y)), 4)
        pygame.draw.circle(surface, (255, 100, 0),
                           (int(self.x), int(self.y)), 8)
        pygame.draw.circle(surface, (255, 100, 0),
                           (int(end_x), int(end_y)), 8)


class TexturedTube:
    """
    Tube simple entre 2 cercles avec texture
    """

    def __init__(self, bone, radius_start, radius_end, points_around=16):
        self.bone = bone
        self.radius_start = radius_start
        self.radius_end = radius_end
        self.points_around = points_around

        # Créer les vertices
        self.create_tube()

        # Créer une texture
        self.create_texture()

    def create_tube(self):
        """Crée 2 cercles connectés"""
        vertices = []

        # CERCLE 1 (début de l'os)
        for i in range(self.points_around):
            angle = (i / self.points_around) * 2 * math.pi
            x = self.bone.x + self.radius_start * math.cos(angle)
            y = self.bone.y + self.radius_start * math.sin(angle)
            vertices.append([x, y])

        # CERCLE 2 (fin de l'os)
        end_x, end_y = self.bone.get_end_pos()
        for i in range(self.points_around):
            angle = (i / self.points_around) * 2 * math.pi
            x = end_x + self.radius_end * math.cos(angle)
            y = end_y + self.radius_end * math.sin(angle)
            vertices.append([x, y])

        self.original_vertices = np.array(vertices, dtype=float)
        self.vertices = self.original_vertices.copy()

        # Créer les triangles qui connectent les 2 cercles
        self.triangles = []
        for i in range(self.points_around):
            # 4 coins du quad
            p0 = i  # Cercle 1, point i
            p1 = (i + 1) % self.points_around  # Cercle 1, point suivant
            p2 = self.points_around + (i + 1) % self.points_around  # Cercle 2, point suivant
            p3 = self.points_around + i  # Cercle 2, point i

            # 2 triangles pour le quad
            self.triangles.append([p0, p1, p2])
            self.triangles.append([p0, p2, p3])

        # Coordonnées UV pour la texture
        self.uv_coords = []

        # Cercle 1 : u varie de 0 à 1, v = 0
        for i in range(self.points_around):
            u = i / self.points_around
            self.uv_coords.append([u, 0.0])

        # Cercle 2 : u varie de 0 à 1, v = 1
        for i in range(self.points_around):
            u = i / self.points_around
            self.uv_coords.append([u, 1.0])

        self.uv_coords = np.array(self.uv_coords)

    def create_texture(self):
        """Crée une texture pour le tube"""
        tex_w, tex_h = 256, 128
        self.texture = pygame.Surface((tex_w, tex_h))

        # Dégradé vertical (du vert clair au vert foncé)
        for y in range(tex_h):
            t = y / tex_h
            green = int(150 + 70 * t)
            color = (60 + int(40 * t), green, 60 + int(40 * t))
            pygame.draw.line(self.texture, color, (0, y), (tex_w, y))

        # Motifs (écailles)
        for row in range(4):
            for col in range(8):
                x = col * 32 + (16 if row % 2 else 0)
                y = row * 32 + 16

                # Écaille
                pygame.draw.ellipse(self.texture, (80, 180, 80),
                                    (x - 12, y - 10, 24, 20))
                pygame.draw.ellipse(self.texture, (100, 200, 100),
                                    (x - 8, y - 6, 16, 12))

        self.tex_w = tex_w
        self.tex_h = tex_h

    def update(self):
        """Met à jour les positions des vertices selon l'os"""
        bone_angle_rad = math.radians(self.bone.angle)
        cos_a = math.cos(bone_angle_rad)
        sin_a = math.sin(bone_angle_rad)

        # CERCLE 1 (début)
        for i in range(self.points_around):
            angle = (i / self.points_around) * 2 * math.pi

            # Position relative
            rel_x = self.radius_start * math.cos(angle)
            rel_y = self.radius_start * math.sin(angle)

            # Rotation selon l'os
            rot_x = rel_x * cos_a - rel_y * sin_a
            rot_y = rel_x * sin_a + rel_y * cos_a

            # Position finale
            self.vertices[i] = [self.bone.x + rot_x, self.bone.y + rot_y]

        # CERCLE 2 (fin)
        end_x, end_y = self.bone.get_end_pos()
        for i in range(self.points_around):
            angle = (i / self.points_around) * 2 * math.pi

            rel_x = self.radius_end * math.cos(angle)
            rel_y = self.radius_end * math.sin(angle)

            rot_x = rel_x * cos_a - rel_y * sin_a
            rot_y = rel_x * sin_a + rel_y * cos_a

            self.vertices[self.points_around + i] = [end_x + rot_x, end_y + rot_y]

    def draw(self, surface, show_wireframe=False):
        """Dessine le tube avec texture"""
        # Dessiner chaque triangle avec sa portion de texture
        for tri in self.triangles:
            # Coordonnées écran des 3 vertices
            screen_points = [self.vertices[i].astype(int).tolist() for i in tri]

            # Coordonnées UV des 3 vertices
            uv_points = [self.uv_coords[i] for i in tri]

            # Calculer la couleur moyenne depuis la texture
            avg_u = (uv_points[0][0] + uv_points[1][0] + uv_points[2][0]) / 3
            avg_v = (uv_points[0][1] + uv_points[1][1] + uv_points[2][1]) / 3

            tex_x = int(avg_u * self.tex_w) % self.tex_w
            tex_y = int(avg_v * self.tex_h) % self.tex_h

            color = self.texture.get_at((tex_x, tex_y))

            # Dessiner le triangle
            pygame.draw.polygon(surface, color, screen_points)

        # Wireframe
        if show_wireframe:
            for tri in self.triangles:
                points = [self.vertices[i].astype(int).tolist() for i in tri]
                pygame.draw.polygon(surface, (255, 255, 255), points, 1)

    def draw_circles_debug(self, surface):
        """Dessine les cercles pour debug"""
        # Cercle 1
        for i in range(self.points_around):
            pos = self.vertices[i].astype(int).tolist()
            pygame.draw.circle(surface, (255, 0, 0), pos, 3)

        # Cercle 2
        for i in range(self.points_around):
            pos = self.vertices[self.points_around + i].astype(int).tolist()
            pygame.draw.circle(surface, (0, 0, 255), pos, 3)


# ========== CRÉER PLUSIEURS TUBES ==========

# Tube 1 : Gros tube
bone1 = Bone(300, 300, 200, 0)
tube1 = TexturedTube(bone1, radius_start=50, radius_end=30, points_around=20)

# Tube 2 : Petit tube
bone2 = Bone(700, 300, 150, 45)
tube2 = TexturedTube(bone2, radius_start=30, radius_end=40, points_around=16)

# Tube 3 : Tube fin
bone3 = Bone(300, 550, 180, -20)
tube3 = TexturedTube(bone3, radius_start=25, radius_end=15, points_around=12)

tubes = [
    {"bone": bone1, "tube": tube1, "name": "Gros tube"},
    {"bone": bone2, "tube": tube2, "name": "Tube moyen"},
    {"bone": bone3, "tube": tube3, "name": "Tube fin"},
]

# Variables
time = 0
show_wireframe = True
show_skeleton = True
show_circles = False
show_texture = True

# Boucle principale
running = True
font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 42)

while running:
    screen.fill((30, 35, 40))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                show_wireframe = not show_wireframe
            elif event.key == pygame.K_s:
                show_skeleton = not show_skeleton
            elif event.key == pygame.K_c:
                show_circles = not show_circles
            elif event.key == pygame.K_t:
                show_texture = not show_texture

    # Animation
    time += 0.03

    # Animer les os
    bone1.angle = 20 * math.sin(time)
    bone2.angle = 45 + 30 * math.sin(time * 1.5)
    bone3.angle = -20 + 25 * math.sin(time * 0.8)

    # Mettre à jour et dessiner les tubes
    for item in tubes:
        tube = item["tube"]
        bone = item["bone"]

        tube.update()

        if show_texture:
            tube.draw(screen, show_wireframe)

        if show_circles:
            tube.draw_circles_debug(screen)

        if show_skeleton:
            bone.draw(screen)

    # Afficher la texture dans un coin
    if show_texture:
        texture_display = pygame.transform.scale(tube1.texture, (128, 64))
        screen.blit(texture_display, (WIDTH - 140, 10))
        pygame.draw.rect(screen, (255, 255, 255), (WIDTH - 140, 10, 128, 64), 2)
        label = font.render("Texture", True, (255, 255, 255))
        screen.blit(label, (WIDTH - 130, 80))

    # UI
    title = title_font.render("2 Cercles Connectés avec Texture", True, (100, 255, 200))
    screen.blit(title, (WIDTH // 2 - 280, 20))

    y = 80
    instructions = [
        "✓ Seulement 2 cercles par tube",
        "✓ Connectés par des triangles",
        "✓ Texture mappée dessus",
        "✓ Suit le mouvement de l'os",
        "",
        "W = Wireframe " + ("ON" if show_wireframe else "OFF"),
        "S = Skeleton " + ("ON" if show_skeleton else "OFF"),
        "C = Cercles " + ("ON" if show_circles else "OFF"),
        "T = Texture " + ("ON" if show_texture else "OFF"),
        "",
        f"Tube 1: {tube1.points_around} points/cercle",
        f"Tube 2: {tube2.points_around} points/cercle",
        f"Tube 3: {tube3.points_around} points/cercle",
    ]

    for text in instructions:
        label = font.render(text, True, (220, 220, 220))
        screen.blit(label, (10, y))
        y += 30

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

print("\n✅ TUBE SIMPLE : 2 CERCLES + TEXTURE")
print("\n📐 STRUCTURE :")
print("• Cercle 1 (début de l'os) : radius_start")
print("• Cercle 2 (fin de l'os) : radius_end")
print("• Connectés par des quads (2 triangles chacun)")
print("• Texture mappée avec coordonnées UV")
print("\n🎨 TEXTURE :")
print("• Créée automatiquement (dégradé + écailles)")
print("• Mappée avec UV : u=0→1 autour, v=0→1 le long")
print("\n🎮 CONTRÔLES :")
print("W = Wireframe")
print("S = Skeleton")
print("C = Voir les cercles")
print("T = Toggle texture")