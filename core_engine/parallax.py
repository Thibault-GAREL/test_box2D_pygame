# ============================================
# parallax.py - Système d'arrière-plans parallaxe
# ============================================

import pygame
import os


class ParallaxLayer:
    """Représente une couche d'arrière-plan avec effet parallaxe"""

    def __init__(self, image_path, depth, x_position=0, y_position=0, repeat=True, repeat_spacing=None, scale=1.0):
        """
        image_path: chemin vers l'image
        depth: distance de la couche (0.0 = très loin, 1.0 = même plan que le jeu)
                Plus le depth est faible, plus la couche bouge lentement
        x_position: position horizontale en mètres (0 = centre)
        y_position: position verticale en mètres (0 = sol)
        repeat: si True, l'image se répète horizontalement avec espacement
        repeat_spacing: espacement entre répétitions (en mètres). Si None, utilise la largeur de l'image
                       Peut être un tuple (min, max) pour un espacement aléatoire
        scale: échelle de l'image (0.5=2x plus petit, 1.0=taille normale, 2.0=2x plus grand)
        """
        self.depth = depth
        self.x_position = x_position
        self.y_position = y_position
        self.repeat = repeat
        self.repeat_spacing = repeat_spacing
        self.scale = scale
        self.image = None
        self.image_loaded = False

        # Charger l'image
        if os.path.exists(image_path):
            try:
                original_image = pygame.image.load(image_path).convert_alpha()

                # Appliquer le scale si différent de 1.0
                if scale != 1.0:
                    new_width = int(original_image.get_width() * scale)
                    new_height = int(original_image.get_height() * scale)
                    self.image = pygame.transform.scale(original_image, (new_width, new_height))
                else:
                    self.image = original_image

                self.image_loaded = True
                print(
                    f"✅ Parallaxe: {image_path} chargée (depth={depth}, x={x_position}, y={y_position}, scale={scale})")
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
            import random

            # Déterminer l'espacement
            if self.repeat_spacing is None:
                # Espacement par défaut = largeur de l'image
                spacing_px = img_width
            elif isinstance(self.repeat_spacing, tuple):
                # Espacement aléatoire entre min et max (en mètres)
                random.seed(42)  # Seed fixe pour cohérence
                spacing_px = img_width  # Placeholder, sera calculé pour chaque instance
            else:
                # Espacement fixe (en mètres)
                spacing_px = self.repeat_spacing * ppm

            # Calculer la position de départ
            # Utiliser x_position comme point de départ de la répétition
            start_x = final_x

            # Dessiner vers la gauche
            x = start_x
            instance = 0
            while x > -img_width:
                screen.blit(self.image, (x, final_y - img_height))

                # Calculer le prochain espacement (aléatoire si tuple)
                if isinstance(self.repeat_spacing, tuple):
                    random.seed(42 + instance)  # Seed basé sur l'instance pour cohérence
                    spacing = random.uniform(self.repeat_spacing[0], self.repeat_spacing[1]) * ppm
                else:
                    spacing = spacing_px

                x -= img_width + spacing
                instance -= 1

            # Dessiner vers la droite
            x = start_x + img_width
            instance = 1
            while x < display.width + img_width:
                # Calculer l'espacement (aléatoire si tuple)
                if isinstance(self.repeat_spacing, tuple):
                    random.seed(42 + instance)
                    spacing = random.uniform(self.repeat_spacing[0], self.repeat_spacing[1]) * ppm
                else:
                    spacing = spacing_px

                x += spacing
                screen.blit(self.image, (x, final_y - img_height))
                x += img_width
                instance += 1
        else:
            # Image unique à la position spécifiée (avec parallaxe)
            screen.blit(self.image, (final_x, final_y - img_height))


class ParallaxManager:
    """Gestionnaire de toutes les couches parallaxe"""

    def __init__(self):
        self.layers = []

    def add_layer(self, image_path, depth, x_position=0, y_position=0, repeat=True, repeat_spacing=None, scale=1.0):
        """
        Ajoute une couche d'arrière-plan

        Paramètres:
        - image_path: chemin de l'image (ex: "mountains.png")
        - depth: distance 0.0-1.0 (0.0=lointain, 1.0=proche)
        - x_position: position horizontale en mètres (0=centre du monde, utilisé comme point de départ si repeat=True)
        - y_position: position verticale en mètres (0=sol)
        - repeat: True pour répéter l'image horizontalement
        - repeat_spacing: espacement entre répétitions (en mètres)
                         None = collé (utilise la largeur de l'image)
                         Nombre = espacement fixe en mètres (ex: 5 = 5 mètres entre chaque)
                         Tuple = espacement aléatoire (min, max) en mètres (ex: (3, 8))
        - scale: échelle de l'image (0.5=2x plus petit, 1.0=normal, 2.0=2x plus grand)

        Exemples d'utilisation:
        # Ciel qui se répète collé
        add_layer("sky.png", depth=0.0, y_position=5, repeat=True)

        # Arbres espacés aléatoirement, 1.5x plus grands
        add_layer("tree.png", depth=0.6, x_position=-20, y_position=1, repeat=True, repeat_spacing=(5, 10), scale=1.5)

        # Rochers espacés, plus petits
        add_layer("rock.png", depth=0.7, x_position=0, y_position=0.5, repeat=True, repeat_spacing=8, scale=0.7)

        # Montagne unique à gauche, plus grande
        add_layer("mountain.png", depth=0.2, x_position=-15, y_position=3, repeat=False, scale=2.0)
        """
        layer = ParallaxLayer(image_path, depth, x_position, y_position, repeat, repeat_spacing, scale)
        self.layers.append(layer)
        return layer

    def draw_background(self, display):
        """Dessine uniquement les couches d'arrière-plan (avant le sol)"""
        # Trier par depth croissant (les plus lointains d'abord)
        sorted_layers = sorted(self.layers, key=lambda l: l.depth)

        for layer in sorted_layers:
            # Dessiner seulement si depth < 0.9 (arrière-plan)
            if layer.depth < 0.9:
                layer.draw(display)

    def draw_foreground(self, display):
        """Dessine uniquement les couches de premier plan (après le sol)"""
        # Trier par depth croissant
        sorted_layers = sorted(self.layers, key=lambda l: l.depth)

        for layer in sorted_layers:
            # Dessiner seulement si depth >= 0.9 (premier plan)
            if layer.depth >= 0.9:
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