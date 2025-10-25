import pygame
# Import depuis physics.py
from physics import PhysicsWorld, Quadruped
# Import depuis display.py
from display import Display
# Import du système d'overlay AMÉLIORÉ
from overlay import VisualOverlay

def main():
    # Initialiser les systèmes
    physics_world = PhysicsWorld(gravity=(0, -10))
    display = Display(width=1200, height=700, title="Quadrupède muscles - Chat texture")
    quadruped = Quadruped(physics_world, x=6, y=3)

    # Initialiser le système d'overlay visuel avec l'image du chat
    # IMPORTANT : cat_texture.png doit être dans le même dossier !
    overlay = VisualOverlay(display, cat_image_path="cat_texture.png")

    # Paramètres de simulation
    TARGET_FPS = 60
    TIME_STEP = 1.0 / TARGET_FPS

    # Boucle principale
    running = True
    while running:
        # Gestion des événements Pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Basculer entre les 3 modes avec TAB
                elif event.key == pygame.K_TAB:
                    overlay.toggle_mode()

        # Gestion des touches (contrôle manuel)
        keys = pygame.key.get_pressed()

        # Relâcher tous les muscles
        for i in range(6):
            quadruped.control_muscles(i, 'relax')

        # Muscle 1 (hanche arrière)
        if keys[pygame.K_r]:
            quadruped.control_muscles(0, 'contract')
        elif keys[pygame.K_f]:
            quadruped.control_muscles(0, 'extend')

        # Muscle 2 (genou arrière)
        if keys[pygame.K_t]:
            quadruped.control_muscles(1, 'contract')
        elif keys[pygame.K_g]:
            quadruped.control_muscles(1, 'extend')

        # Muscle 3 (épaule avant)
        if keys[pygame.K_y]:
            quadruped.control_muscles(2, 'contract')
        elif keys[pygame.K_h]:
            quadruped.control_muscles(2, 'extend')

        # Muscle 4 (coude avant)
        if keys[pygame.K_e]:
            quadruped.control_muscles(3, 'contract')
        elif keys[pygame.K_d]:
            quadruped.control_muscles(3, 'extend')

        if keys[pygame.K_z]:
            quadruped.control_muscles(4, 'contract')
        elif keys[pygame.K_s]:
            quadruped.control_muscles(4, 'extend')

        if keys[pygame.K_a]:
            quadruped.control_muscles(5, 'contract')
        elif keys[pygame.K_q]:
            quadruped.control_muscles(5, 'extend')

        if quadruped.is_upside_down():
            display.draw_text("RETOURNÉ!", (display.width // 2 - 50, 50), (255, 0, 0))

        # Mettre à jour la physique
        quadruped.update()
        physics_world.step(TIME_STEP)

        # === AFFICHAGE ===
        display.clear()
        display.draw_ground(physics_world.ground)

        # Utiliser le système d'overlay pour dessiner le quadrupède
        # Il gère automatiquement les 3 modes : IMAGE, TEXTURE, SKELETON
        overlay.draw_quadruped(quadruped)

        display.draw_instructions()
        overlay.draw_status()  # Affiche le mode actuel

        display.update()
        display.tick(TARGET_FPS)

    # Fermer proprement Pygame
    display.quit()


if __name__ == "__main__":
    main()