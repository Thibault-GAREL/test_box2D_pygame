# ============================================
# overlay.py - Système d'overlay visuel avec sprites/textures
# ============================================

import pygame
import math


class VisualOverlay:
    """Gestionnaire d'overlay visuel pour le quadrupède"""

    def __init__(self, display):
        self.display = display
        self.show_skeleton = False  # Mode skeleton (False = textures, True = skeleton)

        # Couleurs pour les différents éléments
        self.colors = {
            'body': (180, 140, 100),  # Marron clair pour le corps
            'legs': (160, 120, 90),  # Marron plus foncé pour les pattes
            'neck': (170, 130, 95),  # Pour le cou
            'tail': (150, 110, 80),  # Pour la queue
            'muscle_relaxed': (255, 100, 100),  # Rouge clair
            'muscle_active': (255, 50, 50),  # Rouge vif
            'joint': (255, 200, 100),  # Jaune/orange pour les articulations
        }

        # Surface pour les effets de glow
        self.glow_surface = pygame.Surface((display.width, display.height), pygame.SRCALPHA)

    def toggle_mode(self):
        """Bascule entre mode skeleton et mode texture"""
        self.show_skeleton = not self.show_skeleton

    def draw_rounded_bone(self, bone, color):
        """Dessine un os avec des bords arrondis"""
        vertices = [(bone.body.transform * v) * self.display.PPM
                    for v in bone.fixture.shape.vertices]
        vertices = [(v[0], self.display.height - v[1]) for v in vertices]

        if len(vertices) >= 4:
            # Dessiner le rectangle principal
            pygame.draw.polygon(self.display.screen, color, vertices)

            # Ajouter des cercles aux coins pour les bords arrondis
            radius = 3  # Rayon des coins arrondis
            for vertex in vertices:
                pygame.draw.circle(self.display.screen, color, (int(vertex[0]), int(vertex[1])), radius)

    def draw_textured_bone(self, bone, color, add_shine=True):
        """Dessine un os avec texture et effets visuels"""
        vertices = [(bone.body.transform * v) * self.display.PPM
                    for v in bone.fixture.shape.vertices]
        vertices = [(v[0], self.display.height - v[1]) for v in vertices]

        # Fond principal avec la couleur
        pygame.draw.polygon(self.display.screen, color, vertices)

        # Contour légèrement plus foncé
        darker = tuple(max(0, c - 30) for c in color)
        pygame.draw.polygon(self.display.screen, darker, vertices, 2)

        if add_shine and len(vertices) >= 4:
            # Effet de brillance sur le dessus
            shine_color = tuple(min(255, c + 40) for c in color)
            # Ligne de brillance au milieu supérieur
            mid_top1 = ((vertices[0][0] + vertices[1][0]) // 2,
                        (vertices[0][1] + vertices[1][1]) // 2)
            mid_top2 = ((vertices[2][0] + vertices[3][0]) // 2,
                        (vertices[2][1] + vertices[3][1]) // 2)
            pygame.draw.line(self.display.screen, shine_color, mid_top1, mid_top2, 2)

    def draw_textured_muscle(self, muscle, skip_glow=False):
        """Dessine un muscle avec effet de tension visuelle"""
        pos_a = muscle.body_a.transform * muscle.anchor_a
        pos_b = muscle.body_b.transform * muscle.anchor_b

        screen_a = self.display.to_screen(pos_a)
        screen_b = self.display.to_screen(pos_b)

        # Couleur basée sur la tension (interpolation)
        if abs(muscle.target_speed) > 0.1:
            # Muscle actif
            color = self.colors['muscle_active']
            thickness = 6
            # Effet de glow pour les muscles actifs (seulement si pas déjà fait)
            if not skip_glow:
                glow_radius = 25 if self.show_skeleton else 15
                self.draw_glow_line(screen_a, screen_b, color, radius=glow_radius)
        else:
            # Muscle relâché
            color = self.colors['muscle_relaxed']
            thickness = 4

        # Ligne principale du muscle
        pygame.draw.line(self.display.screen, color, screen_a, screen_b, thickness)

        # Articulations aux extrémités (seulement en mode TEXTURE)
        if not self.show_skeleton:
            joint_color = self.colors['joint']
            pygame.draw.circle(self.display.screen, joint_color, screen_a, 6)
            pygame.draw.circle(self.display.screen, joint_color, screen_b, 6)

        # Petits cercles rouges au centre (dans les deux modes)
        pygame.draw.circle(self.display.screen, color, screen_a, 5)
        pygame.draw.circle(self.display.screen, color, screen_b, 5)

    def draw_glow_line(self, pos_a, pos_b, color, radius=10):
        """Dessine un effet de glow autour d'une ligne"""
        # Plus d'étapes et alpha plus élevé en mode skeleton
        steps = 5 if self.show_skeleton else 3
        base_alpha = 50 if self.show_skeleton else 30

        for i in range(steps):
            alpha = base_alpha - i * (10 if self.show_skeleton else 10)
            glow_radius = radius - i * 4
            glow_color = (*color, alpha)

            # Glow au point A
            pygame.draw.circle(self.glow_surface, glow_color, pos_a, glow_radius)
            # Glow au point B
            pygame.draw.circle(self.glow_surface, glow_color, pos_b, glow_radius)

    def draw_quadruped(self, quadruped):
        """Dessine le quadrupède complet avec overlay"""
        # Réinitialiser les surfaces de transparence
        self.glow_surface.fill((0, 0, 0, 0))

        # Dessiner les os
        for i, bone in enumerate(quadruped.bones):
            if self.show_skeleton:
                # Mode SKELETON - Affichage avec bords arrondis
                self.draw_rounded_bone(bone, (255, 255, 255))
            else:
                # Mode TEXTURE - Affichage stylisé
                if bone == quadruped.body:
                    self.draw_textured_bone(bone, self.colors['body'], add_shine=True)
                elif bone in [quadruped.neck]:
                    self.draw_textured_bone(bone, self.colors['neck'], add_shine=True)
                elif bone in [quadruped.tail_bottom, quadruped.tail_mid, quadruped.tail_high]:
                    self.draw_textured_bone(bone, self.colors['tail'], add_shine=False)
                else:
                    self.draw_textured_bone(bone, self.colors['legs'], add_shine=True)

        # Pré-calculer les glows (sans les dessiner encore)
        for muscle in quadruped.muscles:
            if abs(muscle.target_speed) > 0.1:
                pos_a = muscle.body_a.transform * muscle.anchor_a
                pos_b = muscle.body_b.transform * muscle.anchor_b
                screen_a = self.display.to_screen(pos_a)
                screen_b = self.display.to_screen(pos_b)
                color = self.colors['muscle_active']
                glow_radius = 25 if self.show_skeleton else 15
                self.draw_glow_line(screen_a, screen_b, color, radius=glow_radius)

        # Appliquer les effets de glow AVANT de dessiner les muscles
        self.display.screen.blit(self.glow_surface, (0, 0))

        # Dessiner les muscles par-dessus le glow
        for muscle in quadruped.muscles:
            self.draw_textured_muscle(muscle, skip_glow=True)

    def draw_status(self):
        """Affiche le statut de l'overlay"""
        mode_text = "Mode: TEXTURE" if not self.show_skeleton else "Mode: SKELETON"
        color = (100, 255, 100) if not self.show_skeleton else (255, 255, 100)

        self.display.draw_text(mode_text, (10, self.display.height - 30), color)
        self.display.draw_text("TAB: Toggle Mode (Texture/Skeleton)",
                               (10, self.display.height - 55), (200, 200, 200))