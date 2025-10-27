# ============================================
# parallax.py - Système d'arrière-plans parallaxe
# ============================================

import pygame
import os


class ParallaxLayer:
    """Représente une couche d'arrière-plan avec effet parallaxe"""

    def __init__(self, image_path, depth, x_position=0, y_position=0, repeat=True):
        """
        image_path: chemin vers l'image
        depth: distance de la couche (0.0 = très loin, 1.0 = même plan que le jeu)
                Plus le depth est faible, plus la couche bouge lentement
        x_position: position horizontale en mètres (0 = centre)
        y_position: position verticale en mètres (0 = sol)
        repeat: si True, l'image se répète horizontalement
        """
        self.depth = depth
        self.x_position = x_position
        self.y_position = y_position
        self.repeat = repeat
        self.image = None
        self.image_loaded = False

        # Charger l'image
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image_loaded = True
                print(f"✅ Parallaxe: {image_path} chargée (depth={depth}, x={x_position}, y={y_position})")
            except Exception as e:
                print(f"❌ Erreur parallaxe: {e}")
        else:
            print(f"⚠️ Image parallaxe non trouvée: {image_path}")

    def draw(self, display):
        """Dessine la couche avec l'effet parallaxe"""
        if not self.image_loaded:
            return

        screen = display.screen
        ppm = display.PPM

        # Calculer l'offset parallaxe (la caméra affecte moins les objets lointains)
        parallax_offset_x = display.camera_x * self.depth
        parallax_offset_y = display.camera_y * self.depth

        # Position de base de l'image (en mètres)
        base_x = self.x_position
        base_y = self.y_position

        # Appliquer l'effet parallaxe aux positions
        final_x = (base_x - parallax_offset_x) * ppm
        final_y = display.height - (base_y - parallax_offset_y) * ppm

        # Largeur de l'image
        img_width = self.image.get_width()
        img_height = self.image.get_height()

        if self.repeat:
            # Calculer la position de départ pour le tiling
            start_x = final_x - (final_x % img_width) - img_width

            # Dessiner plusieurs copies de l'image pour couvrir l'écran
            x = start_x
            while x < display.width:
                screen.blit(self.image, (x, final_y - img_height))
                x += img_width
        else:
            # Image unique à la position spécifiée (avec parallaxe)
            screen.blit(self.image, (final_x, final_y - img_height))


class ParallaxManager:
    """Gestionnaire de toutes les couches parallaxe"""

    def __init__(self):
        self.layers = []

    def add_layer(self, image_path, depth, x_position=0, y_position=0, repeat=True):
        """
        Ajoute une couche d'arrière-plan

        Paramètres:
        - image_path: chemin de l'image (ex: "mountains.png")
        - depth: distance 0.0-1.0 (0.0=lointain, 1.0=proche)
        - x_position: position horizontale en mètres (0=centre du monde)
        - y_position: position verticale en mètres (0=sol)
        - repeat: True pour répéter l'image horizontalement

        Exemples d'utilisation:
        # Ciel qui se répète tout le long
        add_layer("sky.png", depth=0.0, y_position=5, repeat=True)

        # Montagne unique positionnée à droite
        add_layer("mountain.png", depth=0.2, x_position=10, y_position=3, repeat=False)

        # Arbre à gauche qui suit un peu la caméra
        add_layer("tree.png", depth=0.7, x_position=-5, y_position=1, repeat=False)

        # Sol/herbe qui se répète
        add_layer("ground.png", depth=0.9, y_position=0, repeat=True)
        """
        layer = ParallaxLayer(image_path, depth, x_position, y_position, repeat)
        self.layers.append(layer)
        return layer

    def draw(self, display):
        """Dessine toutes les couches dans l'ordre (du plus lointain au plus proche)"""
        # Trier par depth croissant (les plus lointains d'abord)
        sorted_layers = sorted(self.layers, key=lambda l: l.depth)

        for layer in sorted_layers:
            layer.draw(display)

    def clear(self):
        """Supprime toutes les couches"""
        self.layers.clear()


# ============================================
# Fonctions utilitaires pour créer des arrière-plans procéduraux
# (au cas où l'utilisateur n'a pas d'images)
# ============================================

def create_gradient_sky(width, height, top_color=(50, 100, 180), bottom_color=(150, 200, 255)):
    """Crée un dégradé de ciel procédural"""
    surface = pygame.Surface((width, height))

    for y in range(height):
        progress = y / height
        color = (
            int(top_color[0] + (bottom_color[0] - top_color[0]) * progress),
            int(top_color[1] + (bottom_color[1] - top_color[1]) * progress),
            int(top_color[2] + (bottom_color[2] - top_color[2]) * progress)
        )
        pygame.draw.line(surface, color, (0, y), (width, y))

    return surface


def create_simple_mountains(width, height, color=(100, 120, 140)):
    """Crée des montagnes simples low poly"""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    import random
    random.seed(42)  # Pour avoir toujours les mêmes montagnes

    # Créer plusieurs triangles pour les montagnes
    num_mountains = 5
    for i in range(num_mountains):
        x = (width / num_mountains) * i + random.randint(-50, 50)
        peak_height = random.randint(height // 3, height // 2)
        base_width = random.randint(150, 300)

        points = [
            (x - base_width // 2, height),
            (x, height - peak_height),
            (x + base_width // 2, height)
        ]

        # Variation de couleur
        shade = random.randint(-20, 20)
        mountain_color = (
            max(0, min(255, color[0] + shade)),
            max(0, min(255, color[1] + shade)),
            max(0, min(255, color[2] + shade))
        )

        pygame.draw.polygon(surface, mountain_color, points)

    return surface