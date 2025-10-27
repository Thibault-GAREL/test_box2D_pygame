import pygame
# Import depuis physics.py
from physics import PhysicsWorld, Quadruped
# Import depuis display.py
from display import Display
# Import du système d'overlay AMÉLIORÉ
from overlay import VisualOverlay
# Import du système d'herbe
from grass import GrassField
# Import du système de parallaxe
from parallax import ParallaxManager


def main():
    # Initialiser les systèmes
    physics_world = PhysicsWorld(gravity=(0, -10))
    display = Display(width=1200, height=700, title="Quadrupède muscles - Chat texture")
    quadruped = Quadruped(physics_world, x=6, y=3)

    # Initialiser le système d'overlay visuel avec l'image du chat
    # IMPORTANT : cat_texture.png doit être dans le même dossier !
    overlay = VisualOverlay(display, cat_image_path="cat_texture.png")

    # Initialiser le champ d'herbe
    grass_field = GrassField(width=40, density=30)

    # Initialiser le système de parallaxe
    parallax = ParallaxManager()

    # Ajouter des couches d'arrière-plan (du plus lointain au plus proche)

    # Couches qui se répètent (pour les paysages):
    # parallax.add_layer("img/sky.png", depth=0.1, y_position=0, repeat=True)
    parallax.add_layer("img/mountain2.png", depth=0.2, y_position=0, repeat=False)
    parallax.add_layer("img/hills.png", depth=0.5, y_position=0, repeat=False)

    # Éléments uniques positionnés (repeat=False):
    # parallax.add_layer("tree_big.png", depth=0.6, x_position=-8, y_position=1, repeat=False)  # Arbre à gauche
    # parallax.add_layer("rock.png", depth=0.7, x_position=12, y_position=0.5, repeat=False)  # Rocher à droite
    # parallax.add_layer("cloud.png", depth=0.1, x_position=5, y_position=8, repeat=False)  # Nuage flottant

    print("💡 Pour ajouter des arrière-plans, décommentez les lignes add_layer() dans main.py")
    print("   - depth: 0.0=lointain, 1.0=proche")
    print("   - x_position: position horizontale en mètres (0=centre)")
    print("   - y_position: position verticale en mètres (0=sol)")
    print("   - repeat: True=répète horizontalement, False=image unique")

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
                # Basculer le mode suivi de caméra avec F1
                elif event.key == pygame.K_F1:
                    follow = display.toggle_follow_mode()
                    print(f"📷 Mode caméra: {'SUIVI AUTO' if follow else 'MANUEL'}")

        # Gestion des touches (contrôle manuel)
        keys = pygame.key.get_pressed()

        # ===== CONTRÔLES CAMÉRA (flèches directionnelles) =====
        if not display.follow_mode:  # Seulement en mode manuel
            if keys[pygame.K_LEFT]:
                display.move_camera(-display.camera_speed, 0)
            if keys[pygame.K_RIGHT]:
                display.move_camera(display.camera_speed, 0)
            if keys[pygame.K_UP]:
                display.move_camera(0, display.camera_speed)
            if keys[pygame.K_DOWN]:
                display.move_camera(0, -display.camera_speed)

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

        # Mettre à jour l'herbe
        grass_field.update(quadruped)

        # ===== MISE À JOUR CAMÉRA =====
        # En mode suivi automatique, la caméra suit le corps du quadrupède
        if display.follow_mode:
            body_pos = quadruped.body.body.position
            display.follow_target(body_pos, smoothness=0.08)

        # === AFFICHAGE ===
        display.clear()

        # Dessiner les arrière-plans parallaxe EN PREMIER (du plus lointain au plus proche)
        parallax.draw(display)

        display.draw_ground(physics_world.ground)

        # Dessiner l'herbe AVANT le quadrupède (pour qu'elle soit derrière)
        grass_field.draw(display)

        # Utiliser le système d'overlay pour dessiner le quadrupède
        # Il gère automatiquement les 3 modes : IMAGE, TEXTURE, SKELETON
        overlay.draw_quadruped(quadruped)

        display.draw_instructions()
        display.draw_camera_info()  # Affiche les infos de caméra
        overlay.draw_status()  # Affiche le mode actuel

        display.update()
        display.tick(TARGET_FPS)

    # Fermer proprement Pygame
    display.quit()


if __name__ == "__main__":
    main()