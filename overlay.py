# ============================================
# overlay.py - Système d'overlay avec PARTIES DÉCOUPÉES
# ============================================

import pygame
import math
import os


class BoneTexture:
    """Charge et dessine une texture pour un os spécifique"""

    def __init__(self, image_path, scale=1.0):
        """Charge l'image pour cet os

        Args:
            image_path: Chemin vers l'image
            scale: Facteur d'échelle (1.0 = taille originale, 0.5 = moitié, etc.)
        """
        self.image = None
        self.loaded = False
        self.scale = scale
        self.initial_angle = None  # Stockera l'angle initial de l'os

        if os.path.exists(image_path):
            try:
                original = pygame.image.load(image_path).convert_alpha()

                # Appliquer le scaling
                if scale != 1.0:
                    new_width = int(original.get_width() * scale)
                    new_height = int(original.get_height() * scale)
                    self.image = pygame.transform.scale(original, (new_width, new_height))
                else:
                    self.image = original

                self.loaded = True
                print(f"✅ Chargé : {os.path.basename(image_path)} (échelle: {scale}x)")
            except Exception as e:
                print(f"❌ Erreur : {image_path} - {e}")
        else:
            print(f"⚠️ Non trouvé : {image_path}")

    def draw(self, screen, bone, display, offset=(0, 0), rotation_offset=0):
        """Dessine la texture sur l'os avec rotation RELATIVE et offset

        Args:
            screen: Surface pygame
            bone: Os du squelette
            display: Objet Display
            offset: Tuple (x, y) en pixels pour décaler l'image
            rotation_offset: Angle en DEGRÉS à ajouter à la rotation (positif = horaire)
        """
        if not self.loaded or self.image is None:
            return

        # Récupérer la position et l'angle de l'os
        bone_pos = bone.body.position
        bone_angle = bone.body.angle

        # Stocker l'angle initial au premier appel
        if self.initial_angle is None:
            self.initial_angle = bone_angle

        # Calculer la rotation RELATIVE (angle actuel - angle initial)
        relative_angle = bone_angle - self.initial_angle

        # Ajouter le rotation_offset (converti en radians)
        final_angle = relative_angle + math.radians(rotation_offset)

        # Rotation de l'image selon l'angle RELATIF + offset de rotation
        rotated_image = pygame.transform.rotate(
            self.image,
            -math.degrees(final_angle)  # Rotation relative + offset
        )

        # Position à l'écran
        screen_pos = display.to_screen(bone_pos)

        # Appliquer l'offset (rotation de l'offset selon l'angle FINAL)
        offset_x, offset_y = offset
        if offset_x != 0 or offset_y != 0:
            # Rotation de l'offset selon l'angle final
            cos_a = math.cos(-final_angle)
            sin_a = math.sin(-final_angle)
            rotated_offset_x = offset_x * cos_a - offset_y * sin_a
            rotated_offset_y = offset_x * sin_a + offset_y * cos_a

            screen_pos = (
                screen_pos[0] + rotated_offset_x,
                screen_pos[1] + rotated_offset_y
            )

        # Centrer l'image sur la position (avec offset)
        rect = rotated_image.get_rect(center=screen_pos)

        # Dessiner
        screen.blit(rotated_image, rect.topleft)


class TexturedOverlay:
    """Système d'overlay utilisant des parties découpées"""

    def __init__(self, parts_folder="fox_parts", global_scale=1.0):
        """Initialise et charge toutes les textures

        Args:
            parts_folder: Dossier contenant les images
            global_scale: Échelle globale pour toutes les images (0.3 = 30% de la taille)
        """
        self.parts_folder = parts_folder
        self.textures = {}
        self.global_scale = global_scale

        # Facteurs d'échelle individuels par partie (multipliés par global_scale)
        # Ajuste ces valeurs si certaines parties sont trop grandes/petites
        self.part_scales = {
            'body': 1.3,
            'neck': 1.1,
            'head': 1.0,
            'front_thigh': 1.0,
            'front_shin': 1.0,
            'front_ankle': 1.0,
            'front_foot': 1.0,
            'back_thigh': 1.0,
            'back_shin': 1.0,
            'back_ankle': 1.0,
            'back_foot': 1.0,
            'tail_bottom': 1.0,
            'tail_mid': 1.0,
            'tail_high': 1.0,
        }

        # Décalages (offsets) en pixels pour ajuster la position de chaque image
        # Format: (offset_x, offset_y) où x+ = droite, y+ = bas
        self.part_offsets = {
            'body': (0, 25),
            'neck': (-80, -30),
            'head': (0, 0),
            'front_thigh': (0, 0),
            'front_shin': (0, 0),
            'front_ankle': (0, 0),
            'front_foot': (0, 0),
            'back_thigh': (0, 0),
            'back_shin': (0, 0),
            'back_ankle': (0, 0),
            'back_foot': (0, 0),
            'tail_bottom': (0, 0),
            'tail_mid': (0, 0),
            'tail_high': (0, 0),
        }

        # Rotation offsets en DEGRÉS pour ajuster l'angle de chaque image
        # Valeur positive = rotation horaire, négative = anti-horaire
        self.rotation_offsets = {
            'body': 0,
            'neck': 0,
            'head': 0,
            'front_thigh': 0,
            'front_shin': 0,
            'front_ankle': 0,
            'front_foot': 0,
            'back_thigh': 0,
            'back_shin': 0,
            'back_ankle': 0,
            'back_foot': 0,
            'tail_bottom': 0,
            'tail_mid': 0,
            'tail_high': 0,
        }

        # Définir l'ordre de dessin (arrière vers avant pour le Z-ordering)
        # Tu as dit : dessiner body en dernier pour qu'il soit au premier plan
        self.draw_order = [
            # 'tail_high',  # Queue (fond)
            # 'tail_mid',
            # 'tail_bottom',
            # 'back_foot',  # Patte arrière (fond)
            # 'back_ankle',
            # 'back_shin',
            # 'back_thigh',
            # 'front_foot',  # Patte avant
            # 'front_ankle',
            # 'front_shin',
            # 'front_thigh',
            'neck',  # Cou
            # 'head',  # Tête
            'body',  # Corps (premier plan)
        ]

        # Mapping nom -> fichier (note: anckle vs ankle dans les noms de fichiers)
        self.file_mapping = {
            'body': 'fox_texture_body.png',
            'neck': 'fox_texture_neck.png',
            'head': 'fox_texture_head.png',
            'front_thigh': 'fox_texture_front_thigh.png',
            'front_shin': 'fox_texture_front_shin.png',
            'front_ankle': 'fox_texture_front_anckle.png',  # Note: anckle
            'front_foot': 'fox_texture_front_foot.png',
            'back_thigh': 'fox_texture_back_thigh.png',
            'back_shin': 'fox_texture_back_shin.png',
            'back_ankle': 'fox_texture_back_anckle.png',  # Note: anckle
            'back_foot': 'fox_texture_back_foot.png',
            'tail_bottom': 'fox_texture_tail_bottom.png',
            'tail_mid': 'fox_texture_tail_mid.png',
            'tail_high': 'fox_texture_tail_high.png',
        }

        # Charger toutes les textures
        self.load_textures()

    def load_textures(self):
        """Charge toutes les textures des parties avec leur échelle"""
        print(f"\n🦊 Chargement des textures depuis {self.parts_folder}/")
        print(f"📏 Échelle globale: {self.global_scale}x")

        for part_name, filename in self.file_mapping.items():
            filepath = os.path.join(self.parts_folder, filename)
            # Calculer l'échelle finale = global_scale × part_scale
            final_scale = self.global_scale * self.part_scales.get(part_name, 1.0)
            self.textures[part_name] = BoneTexture(filepath, scale=final_scale)

        loaded_count = sum(1 for tex in self.textures.values() if tex.loaded)
        print(f"✅ {loaded_count}/{len(self.textures)} textures chargées\n")

    def draw_quadruped(self, display, quadruped):
        """Dessine le quadrupède avec les textures dans le bon ordre"""

        # Mapping nom de partie -> os du quadrupède
        bone_mapping = {
            'body': quadruped.body,
            'neck': quadruped.neck,
            'head': quadruped.head,
            'front_thigh': quadruped.front_thigh,
            'front_shin': quadruped.front_shin,
            'front_ankle': quadruped.front_ankle,
            'front_foot': quadruped.front_foot,
            'back_thigh': quadruped.back_thigh,
            'back_shin': quadruped.back_shin,
            'back_ankle': quadruped.back_ankle,
            'back_foot': quadruped.back_foot,
            'tail_bottom': quadruped.tail_bottom,
            'tail_mid': quadruped.tail_mid,
            'tail_high': quadruped.tail_high,
        }

        # Dessiner dans l'ordre (arrière vers avant)
        for part_name in self.draw_order:
            if part_name in self.textures and part_name in bone_mapping:
                texture = self.textures[part_name]
                bone = bone_mapping[part_name]
                offset = self.part_offsets.get(part_name, (0, 0))
                rotation_offset = self.rotation_offsets.get(part_name, 0)
                texture.draw(display.screen, bone, display, offset=offset, rotation_offset=rotation_offset)


class VisualOverlay:
    """Gestionnaire d'overlay visuel - VERSION PARTIES DÉCOUPÉES"""

    def __init__(self, display, parts_folder="fox_parts", global_scale=0.3):
        """Initialise l'overlay

        Args:
            display: Objet Display
            parts_folder: Dossier contenant les images
            global_scale: Échelle globale (0.3 = 30% de la taille, ajuste selon tes besoins)
        """
        self.display = display
        self.render_mode = 0  # 0=TEXTURED, 1=SKELETON

        # Nouveau système avec parties découpées
        self.textured_overlay = TexturedOverlay(parts_folder, global_scale=global_scale)

        # Couleurs pour le mode skeleton
        self.colors = {
            'bone': (255, 255, 255),
            'joint': (255, 200, 100),
            'muscle_relaxed': (255, 100, 100),
            'muscle_active': (255, 50, 50),
        }

        self.glow_surface = pygame.Surface((display.width, display.height), pygame.SRCALPHA)

    def toggle_mode(self):
        """Bascule entre TEXTURED et SKELETON"""
        self.render_mode = (self.render_mode + 1) % 2
        mode_names = ["TEXTURED", "SKELETON"]
        print(f"🔄 Mode : {mode_names[self.render_mode]}")

    def get_bone_vertices(self, bone):
        """Récupère les sommets d'un os à l'écran"""
        vertices = [(bone.body.transform * v) * self.display.PPM
                    for v in bone.fixture.shape.vertices]
        return [(v[0] - self.display.camera_x * self.display.PPM,
                 self.display.height - (v[1] - self.display.camera_y * self.display.PPM))
                for v in vertices]

    def draw_skeleton_bone(self, bone):
        """Dessine un os en mode skeleton"""
        vertices = self.get_bone_vertices(bone)
        if len(vertices) >= 4:
            pygame.draw.polygon(self.display.screen, self.colors['bone'], vertices)
            for vertex in vertices:
                pygame.draw.circle(self.display.screen, self.colors['bone'],
                                   (int(vertex[0]), int(vertex[1])), 3)

    def draw_muscle(self, muscle):
        """Dessine un muscle"""
        pos_a = muscle.body_a.transform * muscle.anchor_a
        pos_b = muscle.body_b.transform * muscle.anchor_b
        screen_a = self.display.to_screen(pos_a)
        screen_b = self.display.to_screen(pos_b)

        if abs(muscle.target_speed) > 0.1:
            color = self.colors['muscle_active']
            thickness = 6
            self.draw_glow_line(screen_a, screen_b, color, radius=25)
        else:
            color = self.colors['muscle_relaxed']
            thickness = 4

        pygame.draw.line(self.display.screen, color, screen_a, screen_b, thickness)
        pygame.draw.circle(self.display.screen, color, screen_a, 5)
        pygame.draw.circle(self.display.screen, color, screen_b, 5)

    def draw_glow_line(self, pos_a, pos_b, color, radius=10):
        """Effet de glow pour les muscles actifs"""
        steps = 5
        base_alpha = 50
        for i in range(steps):
            alpha = base_alpha - i * 10
            glow_radius = radius - i * 4
            glow_color = (*color, alpha)
            pygame.draw.circle(self.glow_surface, glow_color, pos_a, glow_radius)
            pygame.draw.circle(self.glow_surface, glow_color, pos_b, glow_radius)

    def draw_quadruped(self, quadruped):
        """Dessine le quadrupède selon le mode"""
        self.glow_surface.fill((0, 0, 0, 0))

        if self.render_mode == 0:
            # MODE TEXTURED : Dessiner avec les parties découpées
            self.textured_overlay.draw_quadruped(self.display, quadruped)

        elif self.render_mode == 1:
            # MODE SKELETON : Dessiner le squelette
            for bone in quadruped.bones:
                self.draw_skeleton_bone(bone)

            # Muscles actifs avec glow
            for muscle in quadruped.muscles:
                if abs(muscle.target_speed) > 0.1:
                    pos_a = muscle.body_a.transform * muscle.anchor_a
                    pos_b = muscle.body_b.transform * muscle.anchor_b
                    screen_a = self.display.to_screen(pos_a)
                    screen_b = self.display.to_screen(pos_b)
                    self.draw_glow_line(screen_a, screen_b, self.colors['muscle_active'], radius=25)

            self.display.screen.blit(self.glow_surface, (0, 0))

            # Dessiner tous les muscles
            for muscle in quadruped.muscles:
                self.draw_muscle(muscle)

    def draw_status(self):
        """Affiche le mode actuel"""
        mode_names = ["TEXTURED", "SKELETON"]
        mode_colors = [(255, 150, 50), (255, 255, 100)]

        current_mode = mode_names[self.render_mode]
        current_color = mode_colors[self.render_mode]

        self.display.draw_text(f"Mode: {current_mode}",
                               (10, self.display.height - 30), current_color)
        self.display.draw_text("TAB: Changer mode (Textured/Skeleton)",
                               (10, self.display.height - 55), (200, 200, 200))

        # Afficher le nombre de textures chargées
        loaded = sum(1 for tex in self.textured_overlay.textures.values() if tex.loaded)
        total = len(self.textured_overlay.textures)
        self.display.draw_text(f"Textures: {loaded}/{total}",
                               (10, self.display.height - 80), (150, 200, 255))