# ============================================
# skinned_overlay.py - Système de skinning
# ============================================

import pygame
import math
import numpy as np


class SkinVertex:
    """Un vertex de la peau avec ses poids d'influence des os"""

    def __init__(self, local_pos, influences):
        """
        local_pos: position locale (x, y) en mètres
        influences: dict {bone_name: weight} où weight est entre 0 et 1
        """
        self.local_pos = local_pos
        self.influences = influences
        self.world_pos = (0, 0)

    def calculate_position(self, bones_dict):
        """Calcule la position mondiale du vertex basée sur les influences des os"""
        final_x = 0
        final_y = 0

        for bone_name, weight in self.influences.items():
            if bone_name in bones_dict:
                bone = bones_dict[bone_name]
                # Position de l'os dans le monde
                bone_world_pos = bone.body.position
                bone_angle = bone.body.angle

                # Transformer la position locale du vertex dans l'espace de l'os
                cos_a = math.cos(bone_angle)
                sin_a = math.sin(bone_angle)

                rotated_x = self.local_pos[0] * cos_a - self.local_pos[1] * sin_a
                rotated_y = self.local_pos[0] * sin_a + self.local_pos[1] * cos_a

                world_x = bone_world_pos[0] + rotated_x
                world_y = bone_world_pos[1] + rotated_y

                # Accumuler avec le poids
                final_x += world_x * weight
                final_y += world_y * weight

        self.world_pos = (final_x, final_y)
        return self.world_pos


class SkinnedMesh:
    """Mesh skinné représentant le corps du renard"""

    def __init__(self):
        self.vertices = []
        self.triangles = []  # Liste de triplets d'indices de vertices
        self.colors = []  # Couleur pour chaque triangle
        self.create_fox_mesh()

    def create_fox_mesh(self):
        """Crée la géométrie du renard avec les poids de skinning"""

        # === CORPS PRINCIPAL ===
        # Corps central (fortement influencé par 'body')
        body_vertices = [
            # Centre du corps
            SkinVertex((0, 0), {'body': 1.0}),
            SkinVertex((0.3, 0.15), {'body': 0.9, 'front_thigh': 0.1}),
            SkinVertex((0.3, -0.15), {'body': 0.9, 'front_thigh': 0.1}),
            SkinVertex((-0.3, 0.15), {'body': 0.9, 'back_thigh': 0.1}),
            SkinVertex((-0.3, -0.15), {'body': 0.9, 'back_thigh': 0.1}),
            # Épaules et hanches plus larges
            SkinVertex((0.5, 0.2), {'body': 0.7, 'front_thigh': 0.3}),
            SkinVertex((0.5, -0.2), {'body': 0.7, 'front_thigh': 0.3}),
            SkinVertex((-0.5, 0.2), {'body': 0.7, 'back_thigh': 0.3}),
            SkinVertex((-0.5, -0.2), {'body': 0.7, 'back_thigh': 0.3}),
        ]

        # === COU ET TÊTE ===
        neck_head_vertices = [
            # Cou
            SkinVertex((0.7, 0.1), {'body': 0.3, 'neck': 0.7}),
            SkinVertex((0.7, -0.1), {'body': 0.3, 'neck': 0.7}),
            SkinVertex((0.85, 0.08), {'neck': 0.8, 'head': 0.2}),
            SkinVertex((0.85, -0.08), {'neck': 0.8, 'head': 0.2}),
            # Tête
            SkinVertex((1.0, 0.12), {'neck': 0.2, 'head': 0.8}),
            SkinVertex((1.0, -0.12), {'neck': 0.2, 'head': 0.8}),
            SkinVertex((1.15, 0.08), {'head': 1.0}),
            SkinVertex((1.15, -0.08), {'head': 1.0}),
            # Museau
            SkinVertex((1.25, 0.04), {'head': 1.0}),
            SkinVertex((1.25, -0.04), {'head': 1.0}),
            # Oreilles
            SkinVertex((1.05, 0.2), {'head': 1.0}),
            SkinVertex((1.05, -0.2), {'head': 1.0}),
        ]

        # === QUEUE ===
        tail_vertices = [
            SkinVertex((-0.6, 0.1), {'body': 0.3, 'tail_bottom': 0.7}),
            SkinVertex((-0.6, -0.1), {'body': 0.3, 'tail_bottom': 0.7}),
            SkinVertex((-0.8, 0.15), {'tail_bottom': 0.8, 'tail_mid': 0.2}),
            SkinVertex((-0.8, -0.15), {'tail_bottom': 0.8, 'tail_mid': 0.2}),
            SkinVertex((-1.0, 0.2), {'tail_bottom': 0.3, 'tail_mid': 0.5, 'tail_high': 0.2}),
            SkinVertex((-1.0, -0.2), {'tail_bottom': 0.3, 'tail_mid': 0.5, 'tail_high': 0.2}),
            SkinVertex((-1.2, 0.18), {'tail_mid': 0.4, 'tail_high': 0.6}),
            SkinVertex((-1.2, -0.18), {'tail_mid': 0.4, 'tail_high': 0.6}),
            SkinVertex((-1.35, 0.12), {'tail_high': 1.0}),
            SkinVertex((-1.35, -0.12), {'tail_high': 1.0}),
        ]

        # === PATTES AVANT ===
        front_leg_vertices = [
            # Cuisse
            SkinVertex((0.5, -0.3), {'body': 0.2, 'front_thigh': 0.8}),
            SkinVertex((0.6, -0.3), {'body': 0.1, 'front_thigh': 0.9}),
            SkinVertex((0.55, -0.5), {'front_thigh': 0.9, 'front_shin': 0.1}),
            # Tibia
            SkinVertex((0.5, -0.7), {'front_thigh': 0.2, 'front_shin': 0.8}),
            SkinVertex((0.6, -0.7), {'front_thigh': 0.1, 'front_shin': 0.9}),
            SkinVertex((0.55, -0.95), {'front_shin': 0.7, 'front_ankle': 0.3}),
            # Cheville
            SkinVertex((0.5, -1.15), {'front_shin': 0.2, 'front_ankle': 0.6, 'front_foot': 0.2}),
            SkinVertex((0.6, -1.15), {'front_shin': 0.1, 'front_ankle': 0.7, 'front_foot': 0.2}),
            # Pied
            SkinVertex((0.5, -1.35), {'front_ankle': 0.3, 'front_foot': 0.7}),
            SkinVertex((0.65, -1.35), {'front_ankle': 0.2, 'front_foot': 0.8}),
            SkinVertex((0.55, -1.45), {'front_foot': 1.0}),
        ]

        # === PATTES ARRIÈRE ===
        back_leg_vertices = [
            # Cuisse
            SkinVertex((-0.5, -0.3), {'body': 0.2, 'back_thigh': 0.8}),
            SkinVertex((-0.6, -0.3), {'body': 0.1, 'back_thigh': 0.9}),
            SkinVertex((-0.55, -0.5), {'back_thigh': 0.9, 'back_shin': 0.1}),
            # Tibia
            SkinVertex((-0.5, -0.7), {'back_thigh': 0.2, 'back_shin': 0.8}),
            SkinVertex((-0.6, -0.7), {'back_thigh': 0.1, 'back_shin': 0.9}),
            SkinVertex((-0.55, -1.0), {'back_shin': 0.7, 'back_ankle': 0.3}),
            # Cheville
            SkinVertex((-0.5, -1.2), {'back_shin': 0.2, 'back_ankle': 0.6, 'back_foot': 0.2}),
            SkinVertex((-0.6, -1.2), {'back_shin': 0.1, 'back_ankle': 0.7, 'back_foot': 0.2}),
            # Pied
            SkinVertex((-0.5, -1.4), {'back_ankle': 0.3, 'back_foot': 0.7}),
            SkinVertex((-0.65, -1.4), {'back_ankle': 0.2, 'back_foot': 0.8}),
            SkinVertex((-0.55, -1.5), {'back_foot': 1.0}),
        ]

        # Combiner tous les vertices
        start_idx = 0
        self.vertices = body_vertices + neck_head_vertices + tail_vertices + front_leg_vertices + back_leg_vertices

        # Créer les triangles pour le corps
        self.create_body_triangles(start_idx, len(body_vertices))
        start_idx += len(body_vertices)

        self.create_neck_head_triangles(start_idx, len(neck_head_vertices))
        start_idx += len(neck_head_vertices)

        self.create_tail_triangles(start_idx, len(tail_vertices))
        start_idx += len(tail_vertices)

        self.create_leg_triangles(start_idx, len(front_leg_vertices), is_front=True)
        start_idx += len(front_leg_vertices)

        self.create_leg_triangles(start_idx, len(back_leg_vertices), is_front=False)

    def create_body_triangles(self, start_idx, count):
        """Crée les triangles pour le corps"""
        orange = (255, 140, 0)
        # Simplifier: créer un "tube" avec les vertices du corps
        # Triangles connectant le haut et le bas du corps
        for i in range(4):
            self.triangles.append((start_idx + i, start_idx + i + 1, start_idx + i + 5))
            self.colors.append(orange)
            self.triangles.append((start_idx + i + 1, start_idx + i + 6, start_idx + i + 5))
            self.colors.append(orange)

    def create_neck_head_triangles(self, start_idx, count):
        """Crée les triangles pour le cou et la tête"""
        orange = (255, 140, 0)
        white = (255, 255, 255)
        # Cou et tête: bandes de triangles
        for i in range(0, 8, 2):
            self.triangles.append((start_idx + i, start_idx + i + 1, start_idx + i + 2))
            self.colors.append(orange)
            self.triangles.append((start_idx + i + 1, start_idx + i + 3, start_idx + i + 2))
            self.colors.append(orange)

        # Museau
        self.triangles.append((start_idx + 6, start_idx + 8, start_idx + 7))
        self.colors.append(white)
        self.triangles.append((start_idx + 7, start_idx + 8, start_idx + 9))
        self.colors.append(white)

        # Oreilles
        self.triangles.append((start_idx + 4, start_idx + 10, start_idx + 6))
        self.colors.append((40, 40, 40))
        self.triangles.append((start_idx + 5, start_idx + 7, start_idx + 11))
        self.colors.append((40, 40, 40))

    def create_tail_triangles(self, start_idx, count):
        """Crée les triangles pour la queue"""
        orange = (255, 100, 0)
        white = (240, 240, 240)
        # Queue: bandes de triangles qui s'affinent
        for i in range(0, 8, 2):
            color = white if i >= 6 else orange
            self.triangles.append((start_idx + i, start_idx + i + 1, start_idx + i + 2))
            self.colors.append(color)
            self.triangles.append((start_idx + i + 1, start_idx + i + 3, start_idx + i + 2))
            self.colors.append(color)

    def create_leg_triangles(self, start_idx, count, is_front):
        """Crée les triangles pour une patte"""
        orange = (255, 140, 0)
        dark_brown = (60, 40, 20)
        # Patte: séries de triangles formant un "tube"
        segments = [(0, 2, orange), (2, 5, orange), (5, 7, dark_brown), (7, 10, dark_brown)]

        for seg_start, seg_end, color in segments:
            if seg_end < count:
                for i in range(seg_start, seg_end - 1):
                    if i + 1 < count:
                        self.triangles.append((start_idx + i, start_idx + i + 1, start_idx + i + 2))
                        self.colors.append(color)

    def update_vertices(self, bones_dict):
        """Met à jour toutes les positions des vertices"""
        for vertex in self.vertices:
            vertex.calculate_position(bones_dict)

    def draw(self, display):
        """Dessine le mesh skinné"""
        # Dessiner tous les triangles
        for triangle, color in zip(self.triangles, self.colors):
            points = []
            for idx in triangle:
                world_pos = self.vertices[idx].world_pos
                screen_pos = display.to_screen(world_pos)
                points.append(screen_pos)

            if len(points) == 3:
                pygame.draw.polygon(display.screen, color, points)
                # Contour pour mieux voir
                pygame.draw.polygon(display.screen, (0, 0, 0), points, 1)


class SkinnedOverlay:
    """Système d'overlay avec skinning"""

    def __init__(self):
        self.mesh = SkinnedMesh()
        self.bones_dict = {}

    def update_bones(self, quadruped):
        """Met à jour le dictionnaire des os"""
        self.bones_dict = {
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

    def draw_quadruped(self, display, quadruped):
        """Dessine le quadrupède avec skinning"""
        self.update_bones(quadruped)
        self.mesh.update_vertices(self.bones_dict)
        self.mesh.draw(display)