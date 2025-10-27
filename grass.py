# ============================================
# grass.py - Système d'herbe low poly déformable
# ============================================

import random
import math
import pygame


class GrassBlade:
    """Représente un brin d'herbe low poly"""

    def __init__(self, x, y, height=0.15):
        self.base_x = x
        self.base_y = y
        self.height = height + random.uniform(-0.03, 0.03)

        # Angle actuel (0 = vertical, positif = penché à droite)
        self.angle = 0
        self.target_angle = 0
        self.velocity = 0

        # Style low poly : nombre de segments (2-3 pour low poly)
        self.segments = random.choice([2, 3])

        # Courbure naturelle aléatoire
        self.natural_curve = random.uniform(-0.1, 0.1)

        # Rigidité (spring constant)
        self.stiffness = random.uniform(0.15, 0.25)
        self.damping = 0.85

        # Largeur du brin (style low poly = visible)
        self.width = random.uniform(0.02, 0.04)

        # Couleur low poly (variations de vert)
        green_base = random.randint(80, 120)
        self.color = (
            random.randint(40, 60),
            green_base,
            random.randint(30, 50)
        )

        # Couleur tip (plus clair)
        self.tip_color = (
            self.color[0] + 20,
            min(255, self.color[1] + 40),
            self.color[2] + 20
        )

    def apply_force(self, foot_x, foot_y, radius=0.3):
        """Applique une force basée sur la proximité d'un pied"""
        dx = self.base_x - foot_x
        dy = self.base_y - foot_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance < radius:
            # Force inversement proportionnelle à la distance
            force_magnitude = (1 - distance / radius) ** 2

            # Direction de la force (opposée au pied)
            if abs(dx) > 0.01:
                direction = 1 if dx > 0 else -1
                self.target_angle = direction * force_magnitude * 1.2
            else:
                self.target_angle = 0

    def update(self):
        """Met à jour la physique du brin (spring simulation)"""
        # Force de rappel vers la position naturelle (avec courbure)
        spring_force = -(self.angle - self.natural_curve) * self.stiffness

        # Appliquer la force
        self.velocity += spring_force
        self.velocity *= self.damping

        # Mettre à jour l'angle
        self.angle += self.velocity

        # Limiter l'angle max
        self.angle = max(-1.4, min(1.4, self.angle))

    def get_polygon_points(self, ppm, screen_height, camera_x, camera_y):
        """Retourne les points du polygone low poly pour le rendu"""
        # Convertir position de base en coordonnées écran
        base_screen_x = (self.base_x - camera_x) * ppm
        base_screen_y = screen_height - (self.base_y - camera_y) * ppm

        points = []

        # Base du brin (triangle ou quad)
        half_width = self.width * ppm / 2
        points.append((base_screen_x - half_width, base_screen_y))
        points.append((base_screen_x + half_width, base_screen_y))

        # Calculer les segments avec courbure
        current_x = base_screen_x
        current_y = base_screen_y

        for i in range(1, self.segments + 1):
            progress = i / self.segments

            # Hauteur de ce segment
            segment_height = (self.height / self.segments) * ppm

            # Angle total incluant la courbure naturelle
            total_angle = self.angle + self.natural_curve * progress

            # Calculer la position du point
            current_x += math.sin(total_angle) * segment_height
            current_y -= math.cos(total_angle) * segment_height

            # Largeur décroissante vers le haut (effilé)
            segment_width = half_width * (1 - progress * 0.6)

            if i == self.segments:
                # Pointe (triangle)
                points.append((current_x, current_y))
            else:
                # Segment intermédiaire
                points.append((current_x + segment_width, current_y))

        # Retour par l'autre côté
        current_x = base_screen_x
        current_y = base_screen_y

        for i in range(1, self.segments):
            progress = i / self.segments
            segment_height = (self.height / self.segments) * ppm
            total_angle = self.angle + self.natural_curve * progress

            current_x += math.sin(total_angle) * segment_height
            current_y -= math.cos(total_angle) * segment_height
            segment_width = half_width * (1 - progress * 0.6)

            points.insert(2, (current_x - segment_width, current_y))

        return points


class GrassField:
    """Gestionnaire du champ d'herbe"""

    def __init__(self, width=40, density=25):
        """
        width: largeur du champ en mètres
        density: nombre de brins par mètre carré
        """
        self.blades = []
        self.width = width

        # Générer l'herbe
        num_blades = int(width * 2 * density)  # 2m de hauteur

        for _ in range(num_blades):
            x = random.uniform(-width / 2, width / 2)
            y = random.uniform(0.5, 1.2)  # Légèrement au-dessus du sol
            height = random.uniform(0.1, 0.2)

            blade = GrassBlade(x, y, height)
            self.blades.append(blade)

        print(f"🌾 {len(self.blades)} brins d'herbe générés")

    def update(self, quadruped):
        """Met à jour tous les brins en fonction des pieds du quadrupède"""
        # Récupérer les positions des pieds
        feet_positions = [
            (quadruped.back_foot.body.position.x, quadruped.back_foot.body.position.y),
            (quadruped.front_foot.body.position.x, quadruped.front_foot.body.position.y)
        ]

        # Mettre à jour chaque brin
        for blade in self.blades:
            # Réinitialiser la target
            blade.target_angle = blade.natural_curve

            # Appliquer les forces de chaque pied
            for foot_x, foot_y in feet_positions:
                # Seulement si le pied est proche du sol
                if foot_y < 1.0:
                    blade.apply_force(foot_x, foot_y, radius=0.35)

            # Mettre à jour la physique
            blade.update()

    def draw(self, display):
        """Dessine tous les brins d'herbe"""
        screen = display.screen
        ppm = display.PPM
        screen_height = display.height
        camera_x = display.camera_x
        camera_y = display.camera_y

        # Trier les brins par profondeur (Y) pour un rendu correct
        sorted_blades = sorted(self.blades, key=lambda b: b.base_y, reverse=True)

        for blade in sorted_blades:
            # Culling : ne dessiner que les brins visibles
            blade_screen_x = (blade.base_x - camera_x) * ppm
            if -50 < blade_screen_x < display.width + 50:
                points = blade.get_polygon_points(ppm, screen_height, camera_x, camera_y)

                if len(points) >= 3:
                    # Dessiner le polygone avec gradient (base plus sombre)
                    pygame.draw.polygon(screen, blade.color, points)

                    # Contour low poly (optionnel, pour accentuer le style)
                    pygame.draw.polygon(screen,
                                        (max(0, blade.color[0] - 20),
                                         max(0, blade.color[1] - 20),
                                         max(0, blade.color[2] - 20)),
                                        points, 1)