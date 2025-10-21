import pygame
# Import depuis physics.py
from physics import PhysicsWorld, Quadruped
# Import depuis display.py
from display import Display


def main():
    # Initialiser les systèmes (création des objets depuis physics.py et display.py)
    physics_world = PhysicsWorld(gravity=(0, -10))  # Vient de physics.py
    display = Display(width=1200, height=700, title="Quadrupède muscles")  # Vient de display.py
    quadruped = Quadruped(physics_world, x=6, y=3)  # Vient de physics.py

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

        # Gestion des touches (contrôle manuel)
        keys = pygame.key.get_pressed()

        # Relâcher tous les muscles (méthode de physics.py)
        for i in range(4):
            quadruped.control_muscles(i, 'relax')

        # Muscle 1 (hanche arrière)
        if keys[pygame.K_e]:
            quadruped.control_muscles(0, 'contract')  # Méthode de Quadruped (physics.py)
        elif keys[pygame.K_d]:
            quadruped.control_muscles(0, 'extend')

        # Muscle 2 (genou arrière)
        if keys[pygame.K_z]:
            quadruped.control_muscles(1, 'contract')
        elif keys[pygame.K_s]:
            quadruped.control_muscles(1, 'extend')

        # Muscle 3 (épaule avant)
        if keys[pygame.K_r]:
            quadruped.control_muscles(2, 'contract')
        elif keys[pygame.K_f]:
            quadruped.control_muscles(2, 'extend')

        # Muscle 4 (coude avant)
        if keys[pygame.K_t]:
            quadruped.control_muscles(3, 'contract')
        elif keys[pygame.K_g]:
            quadruped.control_muscles(3, 'extend')

        # Mettre à jour la physique (méthodes de physics.py)
        quadruped.update()  # Met à jour les muscles
        physics_world.step(TIME_STEP)  # Avance la simulation Box2D

        # === AFFICHAGE (toutes ces méthodes viennent de display.py) ===
        display.clear()  # Efface l'écran
        display.draw_ground(physics_world.ground)  # Dessine le sol

        # Dessiner les os (boucle sur les os du quadruped)
        for bone in quadruped.bones:
            display.draw_bone(bone)  # Méthode de Display

        # Dessiner les muscles (boucle sur les muscles du quadruped)
        for muscle in quadruped.muscles:
            display.draw_muscle(muscle)  # Méthode de Display

        display.draw_instructions()  # Affiche les instructions
        display.update()  # Rafraîchit l'écran
        display.tick(TARGET_FPS)  # Limite le FPS

    # Fermer proprement Pygame
    display.quit()  # Méthode de Display


if __name__ == "__main__":
    main()