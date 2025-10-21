
# ============================================
# display.py - Gestion de l'affichage Pygame
# ============================================

import pygame


class Display:
    """Gestionnaire de l'affichage avec Pygame"""

    def __init__(self, width=1200, height=700, title="Quadrupède"):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.PPM = 100.0  # Pixels par mètre

    def to_screen(self, pos):
        """Convertit les coordonnées Box2D en coordonnées Pygame"""
        return (int(pos[0] * self.PPM), int(self.height - pos[1] * self.PPM))

    def clear(self, color=(30, 30, 40)):
        """Efface l'écran"""
        self.screen.fill(color)

    def draw_ground(self, ground_body):
        """Dessine le sol"""
        vertices = [(ground_body.transform * v) * self.PPM
                    for v in ground_body.fixtures[0].shape.vertices]
        vertices = [(v[0], self.height - v[1]) for v in vertices]
        pygame.draw.polygon(self.screen, (100, 150, 100), vertices)

    def draw_bone(self, bone, color=(255, 255, 255)):
        """Dessine un os (rectangle blanc)"""
        vertices = [(bone.body.transform * v) * self.PPM
                    for v in bone.fixture.shape.vertices]
        vertices = [(v[0], self.height - v[1]) for v in vertices]
        pygame.draw.polygon(self.screen, color, vertices)

    def draw_muscle(self, muscle, color=(255, 0, 0)):
        """Dessine un muscle (ligne rouge)"""
        # Position des points d'ancrage
        pos_a = muscle.body_a.transform * muscle.anchor_a
        pos_b = muscle.body_b.transform * muscle.anchor_b

        # Convertir en coordonnées écran
        screen_a = self.to_screen(pos_a)
        screen_b = self.to_screen(pos_b)

        # Dessiner la ligne et les points
        pygame.draw.line(self.screen, color, screen_a, screen_b, 4)
        pygame.draw.circle(self.screen, (200, 0, 0), screen_a, 5)
        pygame.draw.circle(self.screen, (200, 0, 0), screen_b, 5)

    def draw_text(self, text, position, color=(255, 255, 255)):
        """Affiche du texte à l'écran"""
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, position)

    def draw_instructions(self):
        """Affiche les instructions de contrôle"""
        instructions = [
            "Contrôles des 3 muscles :",
            "Q/A : Muscle 1 (hanche arrière)",
            "W/S : Muscle 2 (genou arrière)",
            "E/D : Muscle 3 (épaule avant)",
            "ESC : Quitter"
        ]

        for i, text in enumerate(instructions):
            self.draw_text(text, (10, 10 + i * 25))

    def update(self):
        """Rafraîchit l'affichage"""
        pygame.display.flip()

    def tick(self, fps=60):
        """Limite le framerate"""
        self.clock.tick(fps)

    def quit(self):
        """Ferme Pygame"""
        pygame.quit()
