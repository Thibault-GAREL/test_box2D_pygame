import random

import pygame
# Import depuis physics.py
from physics import PhysicsWorld, Quadruped
# Import depuis display.py
from display import Display
# Import du système d'overlay AMÉLIORÉ
from overlay import VisualOverlay
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

    # Initialiser le système de parallaxe
    parallax = ParallaxManager()

    # Ajouter des couches d'arrière-plan (du plus lointain au plus proche)
    # Exemples - remplacez par vos propres images !

    # Couches qui se répètent collées (pour les paysages):
    # parallax.add_layer("sky.png", depth=0.0, y_position=5, repeat=True)
    # parallax.add_layer("mountains.png", depth=0.2, y_position=3, repeat=True)

    # Éléments qui se répètent avec espacement ALÉATOIRE:
    parallax.add_layer("img/cloud.png", depth=0.07, x_position=-1, y_position=6, repeat=True, repeat_spacing=(9, 12), scale=0.4)
    parallax.add_layer("img/cloud2.png", depth=0.05, x_position=5, y_position=5, repeat=True, repeat_spacing=(5, 7), scale=0.3)

    parallax.add_layer("img/mountain2.png", depth=0.1, x_position=0, y_position=0, repeat=True, repeat_spacing=(9, 12))

    parallax.add_layer("img/hill1.png", depth=0.15, x_position=-4, y_position=-0.16, repeat=True, repeat_spacing=(6, 10))
    parallax.add_layer("img/hill2.png", depth=0.14, x_position=15, y_position=-0.16, repeat=True, repeat_spacing=(5, 10))
    parallax.add_layer("img/hill3.png", depth=0.19, x_position=-15, y_position=-0.16, repeat=True, repeat_spacing=(4, 8))
    parallax.add_layer("img/hill4.png", depth=0.23, x_position=8, y_position=-0.16, repeat=True, repeat_spacing=(6, 8))
    parallax.add_layer("img/hill1.png", depth=0.15, x_position=-6, y_position=-0.16, repeat=True, repeat_spacing=(6, 10))
    parallax.add_layer("img/hill2.png", depth=0.14, x_position=20, y_position=-0.16, repeat=True, repeat_spacing=(5, 10))
    parallax.add_layer("img/hill3.png", depth=0.19, x_position=-19, y_position=-0.16, repeat=True, repeat_spacing=(5, 6))
    parallax.add_layer("img/hill4.png", depth=0.23, x_position=14, y_position=-0.16, repeat=True, repeat_spacing=(6, 8))

    # parallax.add_layer("img/hill4.png", depth=0.15, x_position=-4, y_position=-0.5, repeat=True, repeat_spacing=(-4, -2))

    parallax.add_layer("img/tree3.png", depth=0.7, x_position=0, y_position=0, repeat=True, repeat_spacing=(4, 10))
    parallax.add_layer("img/tree3.png", depth=0.7, x_position=3, y_position=0, repeat=True, repeat_spacing=(4, 10), scale=1.1)

    parallax.add_layer("img/tree4.png", depth=0.6, x_position=-2, y_position=0, repeat=True, repeat_spacing=(4, 10), scale=0.9)
    parallax.add_layer("img/tree4.png", depth=0.5, x_position=-6, y_position=0, repeat=True, repeat_spacing=(4, 10))

    parallax.add_layer("img/bush.png", depth=0.8, x_position=-2, y_position=0.35, repeat=True, repeat_spacing=(4, 10), scale=0.25)
    parallax.add_layer("img/bush2.png", depth=0.83, x_position=-5, y_position=0.35, repeat=True, repeat_spacing=(4, 10), scale=0.15)
    parallax.add_layer("img/bush3.png", depth=0.84, x_position=-7, y_position=0.34, repeat=True, repeat_spacing=(4, 10), scale=0.2)
    parallax.add_layer("img/bush4.png", depth=0.87, x_position=-9, y_position=0.33, repeat=True, repeat_spacing=(4, 10), scale=0.1)


    parallax.add_layer("img/bush.png", depth=0.92, x_position=-2, y_position=0.2, repeat=True, repeat_spacing=(4, 6), scale=0.4)
    parallax.add_layer("img/bush2.png", depth=0.93, x_position=-5, y_position=0.15, repeat=True, repeat_spacing=(4, 7), scale=0.45)
    parallax.add_layer("img/bush3.png", depth=0.97, x_position=-7, y_position=0.1, repeat=True, repeat_spacing=(3, 8), scale=0.2)
    parallax.add_layer("img/bush4.png", depth=0.99, x_position=-9, y_position=0.1, repeat=True, repeat_spacing=(2, 9), scale=0.3)

    # Pour les arbres : https://yellowimages.com/stock/low-poly-tree-png-yi3601918?ca=1_10

    # Éléments qui se répètent avec espacement FIXE:
    # parallax.add_layer("bush.png", depth=0.8, x_position=0, y_position=0.3, repeat=True, repeat_spacing=6)

    # Éléments uniques positionnés (repeat=False):
    # parallax.add_layer("big_tree.png", depth=0.6, x_position=-8, y_position=1, repeat=False)

    print("💡 Pour ajouter des arrière-plans, décommentez les lignes add_layer() dans main.py")
    print("   - depth: 0.0=lointain, 1.0=proche")
    print("   - x_position: point de départ horizontal (0=centre)")
    print("   - y_position: position verticale en mètres (0=sol)")
    print("   - repeat: True=répète, False=image unique")
    print("   - repeat_spacing: None=collé, nombre=fixe, (min,max)=aléatoire")

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



        # ===== MISE À JOUR CAMÉRA =====
        # En mode suivi automatique, la caméra suit le corps du quadrupède
        if display.follow_mode:
            body_pos = quadruped.body.body.position
            display.follow_target(body_pos, smoothness=0.08)

        # === AFFICHAGE ===
        display.clear()

        # 1. Dessiner les arrière-plans parallaxe (depth < 0.9)
        parallax.draw_background(display)

        # 2. Dessiner le sol
        display.draw_ground(physics_world.ground)

        # 3. Dessiner les premier plans parallaxe (depth >= 0.9) - DEVANT le sol
        parallax.draw_foreground(display)

        # 4. Dessiner le quadrupède
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