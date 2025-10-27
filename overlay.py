# ============================================
# overlay.py - Système d'overlay visuel AMÉLIORÉ avec image de chat
# ============================================

import pygame
import math
import os


class TextureMapper:
    """Gère le mapping d'une image de chat sur le squelette"""

    def __init__(self, image_path="img/cat_texture.png"):
        """Initialise le mapper avec l'image du chat"""
        self.image = None
        self.image_loaded = False

        # Essayer de charger l'image
        if os.path.exists(image_path):
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image_loaded = True
                print(f"✅ Image chargée : {image_path}")
            except Exception as e:
                print(f"❌ Erreur de chargement : {e}")
                self.image_loaded = False
        else:
            print(f"⚠️  Image non trouvée : {image_path}")
            print("📌 Place 'cat_texture.png' dans le dossier du projet")
            self.image_loaded = False

        # Définir les régions de l'image (coordonnées normalisées 0-1)
        # Format: (x, y, width, height) en pourcentage de l'image
        self.regions = {
            'body': (0.35, 0.3, 0.35, 0.25),  # Corps central
            'neck': (0.7, 0.25, 0.2, 0.25),  # Tête/cou
            'front_thigh': (0.55, 0.5, 0.15, 0.2),  # Cuisse avant
            'front_shin': (0.55, 0.65, 0.12, 0.2),  # Jambe avant
            'front_foot': (0.55, 0.82, 0.1, 0.12),  # Patte avant
            'back_thigh': (0.25, 0.5, 0.15, 0.2),  # Cuisse arrière
            'back_shin': (0.25, 0.65, 0.12, 0.2),  # Jambe arrière
            'back_foot': (0.25, 0.82, 0.1, 0.12),  # Patte arrière
            'tail_bottom': (0.1, 0.25, 0.12, 0.25),  # Queue base
            'tail_mid': (0.05, 0.2, 0.08, 0.15),  # Queue milieu
            'tail_high': (0.02, 0.15, 0.06, 0.12),  # Queue bout
        }

    def get_image_region(self, region_name):
        """Extrait une région de l'image"""
        if not self.image_loaded or region_name not in self.regions:
            return None

        x, y, w, h = self.regions[region_name]
        img_width, img_height = self.image.get_size()

        # Convertir en pixels
        rect = pygame.Rect(
            int(x * img_width),
            int(y * img_height),
            int(w * img_width),
            int(h * img_height)
        )

        # Extraire la sous-image
        try:
            subsurface = self.image.subsurface(rect)
            return subsurface.copy()
        except:
            return None

    def warp_texture_to_bone(self, surface, texture_region, bone_vertices):
        """Applique une texture déformée sur un os"""
        if texture_region is None:
            return

        # Calculer la position et taille de l'os
        if len(bone_vertices) < 4:
            return

        # Calculer le centre et les dimensions
        xs = [v[0] for v in bone_vertices]
        ys = [v[1] for v in bone_vertices]
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)

        # Calculer l'angle de rotation
        dx = bone_vertices[1][0] - bone_vertices[0][0]
        dy = bone_vertices[1][1] - bone_vertices[0][1]
        angle = math.degrees(math.atan2(-dy, dx))

        # Calculer la largeur et hauteur de l'os
        width = math.sqrt(dx ** 2 + dy ** 2)
        height = math.sqrt(
            (bone_vertices[3][0] - bone_vertices[0][0]) ** 2 +
            (bone_vertices[3][1] - bone_vertices[0][1]) ** 2
        )

        # Redimensionner la texture
        if width > 1 and height > 1:
            scaled = pygame.transform.scale(texture_region, (int(width), int(height)))
            # Rotation
            rotated = pygame.transform.rotate(scaled, angle)

            # Position finale
            rect = rotated.get_rect(center=(center_x, center_y))

            # Appliquer avec transparence
            surface.blit(rotated, rect.topleft)


class VisualOverlay:
    """Gestionnaire d'overlay visuel pour le quadrupède - VERSION AMÉLIORÉE"""

    def __init__(self, display, cat_image_path="img/cat_texture.png"):
        self.display = display
        self.render_mode = 2  # 0 = IMAGE, 1 = TEXTURE, 2 = SKELETON

        # Initialiser le texture mapper
        self.texture_mapper = TextureMapper(cat_image_path)

        # Couleurs pour le mode TEXTURE
        self.colors = {
            'body': (180, 140, 100),
            'legs': (160, 120, 90),
            'neck': (170, 130, 95),
            'tail': (150, 110, 80),
            'muscle_relaxed': (255, 100, 100),
            'muscle_active': (255, 50, 50),
            'joint': (255, 200, 100),
        }

        # Surface pour les effets de glow
        self.glow_surface = pygame.Surface((display.width, display.height), pygame.SRCALPHA)

        # Surface pour la texture (séparée)
        self.texture_surface = pygame.Surface((display.width, display.height), pygame.SRCALPHA)

    def toggle_mode(self):
        """Bascule entre les 3 modes : IMAGE -> TEXTURE -> SKELETON -> IMAGE"""
        self.render_mode = (self.render_mode + 1) % 3
        mode_names = ["IMAGE", "TEXTURE", "SKELETON"]
        print(f"🔄 Mode changé : {mode_names[self.render_mode]}")

    def get_bone_vertices(self, bone):
        """Récupère les vertices d'un os en coordonnées écran avec offset caméra"""
        vertices = [(bone.body.transform * v) * self.display.PPM
                    for v in bone.fixture.shape.vertices]
        vertices = [(v[0] - self.display.camera_x * self.display.PPM,
                     self.display.height - (v[1] - self.display.camera_y * self.display.PPM))
                    for v in vertices]
        return vertices

    # ==================== MODE IMAGE ====================

    def draw_image_bone(self, bone, region_name):
        """Dessine un os avec texture d'image"""
        vertices = self.get_bone_vertices(bone)
        texture_region = self.texture_mapper.get_image_region(region_name)

        if texture_region:
            self.texture_mapper.warp_texture_to_bone(
                self.texture_surface,
                texture_region,
                vertices
            )
        else:
            # Fallback : dessiner en couleur si texture indisponible
            pygame.draw.polygon(self.texture_surface, self.colors.get(region_name.split('_')[0], (200, 200, 200)),
                                vertices)

    # ==================== MODE TEXTURE ====================

    def draw_textured_bone(self, bone, color, add_shine=True):
        """Dessine un os avec texture stylisée (mode actuel)"""
        vertices = self.get_bone_vertices(bone)

        pygame.draw.polygon(self.display.screen, color, vertices)

        darker = tuple(max(0, c - 30) for c in color)
        pygame.draw.polygon(self.display.screen, darker, vertices, 2)

        if add_shine and len(vertices) >= 4:
            shine_color = tuple(min(255, c + 40) for c in color)
            mid_top1 = ((vertices[0][0] + vertices[1][0]) // 2,
                        (vertices[0][1] + vertices[1][1]) // 2)
            mid_top2 = ((vertices[2][0] + vertices[3][0]) // 2,
                        (vertices[2][1] + vertices[3][1]) // 2)
            pygame.draw.line(self.display.screen, shine_color, mid_top1, mid_top2, 2)

    # ==================== MODE SKELETON ====================

    def draw_skeleton_bone(self, bone):
        """Dessine un os en mode skeleton (blanc avec coins arrondis)"""
        vertices = self.get_bone_vertices(bone)

        if len(vertices) >= 4:
            pygame.draw.polygon(self.display.screen, (255, 255, 255), vertices)

            # Coins arrondis
            radius = 3
            for vertex in vertices:
                pygame.draw.circle(self.display.screen, (255, 255, 255),
                                   (int(vertex[0]), int(vertex[1])), radius)

    # ==================== MUSCLES ====================

    def draw_muscle(self, muscle):
        """Dessine un muscle (adapté au mode)"""
        pos_a = muscle.body_a.transform * muscle.anchor_a
        pos_b = muscle.body_b.transform * muscle.anchor_b

        screen_a = self.display.to_screen(pos_a)
        screen_b = self.display.to_screen(pos_b)

        # Couleur basée sur la tension
        if abs(muscle.target_speed) > 0.1:
            color = self.colors['muscle_active']
            thickness = 6

            # Glow uniquement en modes TEXTURE et SKELETON
            if self.render_mode > 0:
                glow_radius = 25 if self.render_mode == 2 else 15
                self.draw_glow_line(screen_a, screen_b, color, radius=glow_radius)
        else:
            color = self.colors['muscle_relaxed']
            thickness = 4

        # Ligne du muscle
        pygame.draw.line(self.display.screen, color, screen_a, screen_b, thickness)

        # Articulations (seulement en mode TEXTURE)
        if self.render_mode == 1:
            joint_color = self.colors['joint']
            pygame.draw.circle(self.display.screen, joint_color, screen_a, 6)
            pygame.draw.circle(self.display.screen, joint_color, screen_b, 6)

        # Petits cercles
        pygame.draw.circle(self.display.screen, color, screen_a, 5)
        pygame.draw.circle(self.display.screen, color, screen_b, 5)

    def draw_glow_line(self, pos_a, pos_b, color, radius=10):
        """Dessine un effet de glow autour d'une ligne"""
        steps = 5 if self.render_mode == 2 else 3
        base_alpha = 50 if self.render_mode == 2 else 30

        for i in range(steps):
            alpha = base_alpha - i * 10
            glow_radius = radius - i * 4
            glow_color = (*color, alpha)

            pygame.draw.circle(self.glow_surface, glow_color, pos_a, glow_radius)
            pygame.draw.circle(self.glow_surface, glow_color, pos_b, glow_radius)

    # ==================== DESSIN PRINCIPAL ====================

    def draw_quadruped(self, quadruped):
        """Dessine le quadrupède selon le mode sélectionné"""
        # Réinitialiser les surfaces
        self.glow_surface.fill((0, 0, 0, 0))
        self.texture_surface.fill((0, 0, 0, 0))

        # ===== MODE 0 : IMAGE =====
        if self.render_mode == 0:
            # Dessiner avec textures d'image
            bone_regions = {
                quadruped.body: 'body',
                quadruped.neck: 'neck',
                quadruped.front_thigh: 'front_thigh',
                quadruped.front_shin: 'front_shin',
                quadruped.front_foot: 'front_foot',
                quadruped.back_thigh: 'back_thigh',
                quadruped.back_shin: 'back_shin',
                quadruped.back_foot: 'back_foot',
                quadruped.tail_bottom: 'tail_bottom',
                quadruped.tail_mid: 'tail_mid',
                quadruped.tail_high: 'tail_high',
            }

            for bone, region in bone_regions.items():
                self.draw_image_bone(bone, region)

            # Appliquer la texture surface
            self.display.screen.blit(self.texture_surface, (0, 0))

        # ===== MODE 1 : TEXTURE =====
        elif self.render_mode == 1:
            for bone in quadruped.bones:
                if bone == quadruped.body:
                    self.draw_textured_bone(bone, self.colors['body'], add_shine=True)
                elif bone == quadruped.neck:
                    self.draw_textured_bone(bone, self.colors['neck'], add_shine=True)
                elif bone in [quadruped.tail_bottom, quadruped.tail_mid, quadruped.tail_high]:
                    self.draw_textured_bone(bone, self.colors['tail'], add_shine=False)
                else:
                    self.draw_textured_bone(bone, self.colors['legs'], add_shine=True)
            # ===== MUSCLES =====
            # Pré-calculer les glows
            for muscle in quadruped.muscles:
                if abs(muscle.target_speed) > 0.1 and self.render_mode > 0:
                    pos_a = muscle.body_a.transform * muscle.anchor_a
                    pos_b = muscle.body_b.transform * muscle.anchor_b
                    screen_a = self.display.to_screen(pos_a)
                    screen_b = self.display.to_screen(pos_b)
                    color = self.colors['muscle_active']
                    glow_radius = 25 if self.render_mode == 2 else 15
                    self.draw_glow_line(screen_a, screen_b, color, radius=glow_radius)

            # Appliquer le glow
            if self.render_mode > 0:
                self.display.screen.blit(self.glow_surface, (0, 0))

            # Dessiner les muscles
            for muscle in quadruped.muscles:
                self.draw_muscle(muscle)


        # ===== MODE 2 : SKELETON =====
        elif self.render_mode == 2:
            for bone in quadruped.bones:
                self.draw_skeleton_bone(bone)
            # ===== MUSCLES =====
            # Pré-calculer les glows
            for muscle in quadruped.muscles:
                if abs(muscle.target_speed) > 0.1 and self.render_mode > 0:
                    pos_a = muscle.body_a.transform * muscle.anchor_a
                    pos_b = muscle.body_b.transform * muscle.anchor_b
                    screen_a = self.display.to_screen(pos_a)
                    screen_b = self.display.to_screen(pos_b)
                    color = self.colors['muscle_active']
                    glow_radius = 25 if self.render_mode == 2 else 15
                    self.draw_glow_line(screen_a, screen_b, color, radius=glow_radius)

            # Appliquer le glow
            if self.render_mode > 0:
                self.display.screen.blit(self.glow_surface, (0, 0))

            # Dessiner les muscles
            for muscle in quadruped.muscles:
                self.draw_muscle(muscle)



    def draw_status(self):
        """Affiche le statut du mode de rendu"""
        mode_names = ["IMAGE", "TEXTURE", "SKELETON"]
        mode_colors = [(100, 200, 255), (100, 255, 100), (255, 255, 100)]

        current_mode = mode_names[self.render_mode]
        current_color = mode_colors[self.render_mode]

        # Afficher le mode actuel
        self.display.draw_text(f"Mode: {current_mode}",
                               (10, self.display.height - 30), current_color)

        # Instructions
        self.display.draw_text("TAB: Changer mode (Image/Texture/Skeleton)",
                               (10, self.display.height - 55), (200, 200, 200))

        # Avertissement si image non chargée
        if self.render_mode == 0 and not self.texture_mapper.image_loaded:
            self.display.draw_text("⚠️  cat_texture.png non trouvé !",
                                   (10, self.display.height - 80), (255, 100, 100))