import random
import math

import pygame
# Import depuis physics.py
from physics import PhysicsWorld, Quadruped
# Import depuis display.py
from display import Display
# Import du système d'overlay AMÉLIORÉ
from overlay import VisualOverlay
# Import du système de parallaxe
from parallax import ParallaxManager

# ===== IMPORTS POUR L'IA =====
from ia_gen import GeneticAlgorithm, AIController
from config_ia import HUMAN_CONTROL, DISPLAY_ENABLED, GA_CONFIG, TRAINING_CONFIG, STATS_CONFIG, FITNESS_CONFIG


def main():
    # Initialiser les systèmes
    physics_world = PhysicsWorld(gravity=(0, -10))

    # ===== GESTION DE L'AFFICHAGE =====
    display = Display(width=1200, height=700, title="Quadrupède muscles - Chat texture")

    quadruped = Quadruped(physics_world, x=6, y=3)

    # Initialiser le système d'overlay visuel avec l'image du chat
    overlay = VisualOverlay(display, parts_folder="img", global_scale=0.3)

    # Initialiser le système de parallaxe
    parallax = ParallaxManager()

    # Ajouter des couches d'arrière-plan
    parallax.add_layer("img/cloud.png", depth=0.07, x_position=-1, y_position=6, repeat=True, repeat_spacing=(9, 12),
                       scale=0.4)
    parallax.add_layer("img/cloud2.png", depth=0.05, x_position=5, y_position=5, repeat=True, repeat_spacing=(5, 7),
                       scale=0.3)

    parallax.add_layer("img/mountain2.png", depth=0.1, x_position=0, y_position=0, repeat=True, repeat_spacing=(9, 12),
                       scale=1.3)

    parallax.add_layer("img/hill1.png", depth=0.15, x_position=-4, y_position=-0.16, repeat=True,
                       repeat_spacing=(6, 10), scale=1.4)
    parallax.add_layer("img/hill2.png", depth=0.14, x_position=15, y_position=-0.16, repeat=True,
                       repeat_spacing=(5, 10))
    parallax.add_layer("img/hill3.png", depth=0.19, x_position=-15, y_position=-0.16, repeat=True,
                       repeat_spacing=(4, 8))
    parallax.add_layer("img/hill4.png", depth=0.23, x_position=8, y_position=-0.16, repeat=True, repeat_spacing=(6, 8))
    parallax.add_layer("img/hill1.png", depth=0.15, x_position=-6, y_position=-0.16, repeat=True,
                       repeat_spacing=(6, 10))
    parallax.add_layer("img/hill2.png", depth=0.14, x_position=20, y_position=-0.16, repeat=True,
                       repeat_spacing=(5, 10))
    parallax.add_layer("img/hill3.png", depth=0.19, x_position=-19, y_position=-0.16, repeat=True,
                       repeat_spacing=(5, 6))
    parallax.add_layer("img/hill4.png", depth=0.23, x_position=14, y_position=-0.16, repeat=True, repeat_spacing=(6, 8))

    parallax.add_layer("img/tree3.png", depth=0.7, x_position=0, y_position=0, repeat=True, repeat_spacing=(4, 10))
    parallax.add_layer("img/tree3.png", depth=0.7, x_position=3, y_position=0, repeat=True, repeat_spacing=(4, 10),
                       scale=1.1)

    parallax.add_layer("img/tree4.png", depth=0.6, x_position=-2, y_position=0, repeat=True, repeat_spacing=(4, 10),
                       scale=0.9)
    parallax.add_layer("img/tree5.png", depth=0.5, x_position=-6, y_position=0, repeat=True, repeat_spacing=(4, 10))

    parallax.add_layer("img/bush.png", depth=0.8, x_position=-2, y_position=0.35, repeat=True, repeat_spacing=(4, 10),
                       scale=0.25)
    parallax.add_layer("img/bush2.png", depth=0.83, x_position=-5, y_position=0.35, repeat=True, repeat_spacing=(4, 10),
                       scale=0.15)
    parallax.add_layer("img/bush3.png", depth=0.84, x_position=-7, y_position=0.34, repeat=True, repeat_spacing=(4, 10),
                       scale=0.2)
    parallax.add_layer("img/bush4.png", depth=0.87, x_position=-9, y_position=0.33, repeat=True, repeat_spacing=(4, 10),
                       scale=0.1)

    parallax.add_layer("img/bush.png", depth=0.92, x_position=-2, y_position=0.2, repeat=True, repeat_spacing=(4, 6),
                       scale=0.4)
    parallax.add_layer("img/bush2.png", depth=0.93, x_position=-5, y_position=0.15, repeat=True, repeat_spacing=(4, 7),
                       scale=0.45)
    parallax.add_layer("img/bush3.png", depth=0.97, x_position=-7, y_position=0.1, repeat=True, repeat_spacing=(3, 8),
                       scale=0.2)
    parallax.add_layer("img/bush4.png", depth=0.99, x_position=-9, y_position=0.1, repeat=True, repeat_spacing=(2, 9),
                       scale=0.3)

    print("💡 Pour ajouter des arrière-plans, décommentez les lignes add_layer() dans main.py")
    print("   - depth: 0.0=lointain, 1.0=proche")
    print("   - x_position: point de départ horizontal (0=centre)")
    print("   - y_position: position verticale en mètres (0=sol)")
    print("   - repeat: True=répète, False=image unique")
    print("   - repeat_spacing: None=collé, nombre=fixe, (min,max)=aléatoire")

    print("\n🔍 Appuyez sur P pour afficher les angles des os")

    # Afficher le mode d'affichage
    if DISPLAY_ENABLED:
        print("🖥️  Mode AFFICHAGE ACTIVÉ")
    else:
        print("⚡ Mode RAPIDE (sans affichage)")

    print("\n💡 Appuyez sur F2 pour basculer l'affichage pendant l'exécution")

    # Variable pour gérer l'affichage dynamique
    display_active = DISPLAY_ENABLED

    # ===== INITIALISATION DE L'IA =====
    if not HUMAN_CONTROL:
        print("🤖 Mode IA ACTIVÉ")

        # Créer la configuration complète avec FITNESS_CONFIG
        ga_config_complete = {**GA_CONFIG, 'fitness_config': FITNESS_CONFIG}
        ga = GeneticAlgorithm(**ga_config_complete)

        loaded = ga.load(TRAINING_CONFIG['save_file'])
        if loaded:
            print(f"   IA chargée: Training #{ga.training_number}, Génération {ga.generation}")
        else:
            print(f"   Nouvel entraînement: Training #{ga.training_number}")

        ai_controller = AIController(ga, save_all_individuals=TRAINING_CONFIG['save_all_individuals'])

        # Initialiser le premier individu
        start_x = quadruped.body.body.position.x
        ai_controller.reset_for_individual(0, start_x)
    else:
        print("👤 Mode CONTRÔLE HUMAIN")

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
                # Basculer l'affichage avec F2
                elif event.key == pygame.K_F2:
                    display_active = not display_active
                    if display_active:
                        print("🖥️  AFFICHAGE ACTIVÉ")
                    else:
                        print("⚡ AFFICHAGE DÉSACTIVÉ (mode rapide)")
                # Sauvegarder manuellement avec S
                elif event.key == pygame.K_s and not HUMAN_CONTROL:
                    ga.save(TRAINING_CONFIG['save_file'])
                    print(f"💾 Sauvegarde manuelle effectuée")

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

        # ===== CONTRÔLE DES MUSCLES =====
        # Relâcher tous les muscles
        for i in range(8):
            quadruped.control_muscles(i, 'relax')

        if HUMAN_CONTROL:
            # ===== MODE HUMAIN: Contrôle par clavier =====
            if keys[pygame.K_t]:
                quadruped.control_muscles(0, 'contract')
            elif keys[pygame.K_g]:
                quadruped.control_muscles(0, 'extend')

            if keys[pygame.K_y]:
                quadruped.control_muscles(1, 'contract')
            elif keys[pygame.K_h]:
                quadruped.control_muscles(1, 'extend')

            if keys[pygame.K_u]:
                quadruped.control_muscles(2, 'contract')
            elif keys[pygame.K_j]:
                quadruped.control_muscles(2, 'extend')

            if keys[pygame.K_i]:
                quadruped.control_muscles(3, 'contract')
            elif keys[pygame.K_k]:
                quadruped.control_muscles(3, 'extend')

            if keys[pygame.K_r]:
                quadruped.control_muscles(4, 'contract')
            elif keys[pygame.K_f]:
                quadruped.control_muscles(4, 'extend')

            if keys[pygame.K_e]:
                quadruped.control_muscles(5, 'contract')
            elif keys[pygame.K_d]:
                quadruped.control_muscles(5, 'extend')

            if keys[pygame.K_z]:
                quadruped.control_muscles(6, 'contract')
            elif keys[pygame.K_s]:
                quadruped.control_muscles(6, 'extend')

            if keys[pygame.K_a]:
                quadruped.control_muscles(7, 'contract')
            elif keys[pygame.K_q]:
                quadruped.control_muscles(7, 'extend')
        else:
            # ===== MODE IA: Contrôle automatique =====
            ai_action = ai_controller.get_action_keys()

            # L'IA retourne {'muscle': 0-7 ou None, 'action': 'contract'/'extend'/'relax'}
            if ai_action['muscle'] is not None:
                quadruped.control_muscles(ai_action['muscle'], ai_action['action'])

        if quadruped.is_upside_down():
            if display_active:
                display.draw_text("RETOURNÉ!", (display.width // 2 - 50, 50), (255, 0, 0))

        # Mettre à jour la physique
        quadruped.update()
        physics_world.step(TIME_STEP)

        # ===== ÉVALUATION DE L'IA =====
        if not HUMAN_CONTROL:
            # Récupérer les informations nécessaires
            current_x = quadruped.body.body.position.x
            is_fallen = quadruped.is_upside_down()

            # Évaluer l'individu actuel
            if ai_controller.evaluate_individual(current_x, is_fallen):
                # Cet individu a terminé son évaluation
                if ai_controller.next_individual():
                    # Passer à l'individu suivant
                    # Réinitialiser seulement la physique
                    del physics_world
                    del quadruped

                    physics_world = PhysicsWorld(gravity=(0, -10))
                    quadruped = Quadruped(physics_world, x=6, y=3)

                    start_x = quadruped.body.body.position.x
                    ai_controller.reset_for_individual(ai_controller.current_individual_index, start_x)
                else:
                    # Tous les individus ont été évalués, génération terminée
                    if STATS_CONFIG['show_progress'] and (ga.generation % STATS_CONFIG['print_every'] == 0):
                        ga.print_stats()

                    # Sauvegarde périodique
                    if (ga.generation + 1) % TRAINING_CONFIG['save_every'] == 0:
                        ga.save(TRAINING_CONFIG['save_file'])

                    # Évoluer vers la nouvelle génération
                    ga.evolve()
                    ai_controller.current_individual_index = 0

                    # Réinitialiser pour le premier individu de la nouvelle génération
                    del physics_world
                    del quadruped

                    physics_world = PhysicsWorld(gravity=(0, -10))
                    quadruped = Quadruped(physics_world, x=6, y=3)

                    start_x = quadruped.body.body.position.x
                    ai_controller.reset_for_individual(0, start_x)

                    # Vérifier si on a atteint le nombre max de générations
                    if ga.generation >= TRAINING_CONFIG['max_generations']:
                        print(f"\n✅ Training #{ga.training_number} terminé: {ga.generation} générations")
                        ga.save(TRAINING_CONFIG['save_file'])

                        # Générer le résumé final pour ce training
                        ga._generate_training_summary()

                        # Vérifier si on continue automatiquement
                        if TRAINING_CONFIG['auto_continue']:
                            # Vérifier s'il y a une limite de trainings
                            max_trainings = TRAINING_CONFIG.get('max_trainings', None)
                            if max_trainings is None or ga.training_number < max_trainings:
                                print(f"\n🔄 Démarrage du Training #{ga.training_number + 1}...")

                                # Réinitialiser pour un nouvel entraînement
                                ga_config_complete = {**GA_CONFIG, 'fitness_config': FITNESS_CONFIG}
                                ga = GeneticAlgorithm(**ga_config_complete)
                                ai_controller = AIController(ga, save_all_individuals=TRAINING_CONFIG[
                                    'save_all_individuals'])

                                # Réinitialiser la physique
                                del physics_world
                                del quadruped

                                physics_world = PhysicsWorld(gravity=(0, -10))
                                quadruped = Quadruped(physics_world, x=6, y=3)

                                start_x = quadruped.body.body.position.x
                                ai_controller.reset_for_individual(0, start_x)
                            else:
                                print(f"\n🏁 Nombre maximum de trainings atteint ({max_trainings})")
                                running = False
                        else:
                            print(f"\n🛑 Arrêt (auto_continue désactivé)")
                            running = False

        # ===== MISE À JOUR CAMÉRA =====
        # En mode suivi automatique, la caméra suit le corps du quadrupède
        if display.follow_mode:
            body_pos = quadruped.body.body.position
            display.follow_target(body_pos, smoothness=0.08)

        # ===== AFFICHAGE (seulement si display_active) =====
        if display_active:
            display.clear()

            # 1. Dessiner les arrière-plans parallaxe (depth < 0.9)
            parallax.draw_background(display)

            # 2. Dessiner le sol
            display.draw_ground(physics_world.ground)

            # 3. Dessiner les premier plans parallaxe (depth >= 0.9) - DEVANT le sol
            parallax.draw_foreground(display)

            # 4. Dessiner le quadrupède
            overlay.draw_quadruped(quadruped)

            display.draw_instructions()
            display.draw_camera_info()
            overlay.draw_status()

            # Ajouter l'instruction pour afficher les angles
            display.draw_text("P: Afficher angles des os", (10, display.height - 105), (200, 200, 200))

            # Instruction pour basculer l'affichage
            display.draw_text("F2: Basculer affichage", (10, display.height - 80), (200, 200, 200))

            # Afficher les infos de l'IA (optionnel)
            if not HUMAN_CONTROL:
                font = pygame.font.Font(None, 24)
                train_num = ga.training_number
                gen = ga.generation
                ind = ai_controller.current_individual_index
                total = ga.population_size

                text = f"Training {train_num} | Gen {gen} | Individu {ind + 1}/{total}"

                surface = font.render(text, True, (255, 255, 255))
                bg_surf = pygame.Surface((surface.get_width() + 10, surface.get_height() + 5))
                bg_surf.fill((0, 0, 0))
                bg_surf.set_alpha(150)
                display.screen.blit(bg_surf, (5, 5))
                display.screen.blit(surface, (10, 5))

            display.update()

        # Toujours gérer le FPS (même sans affichage)
        if display_active:
            display.tick(TARGET_FPS)
        else:
            display.tick(TARGET_FPS * TRAINING_CONFIG['speed_multiplier'])

    # Sauvegarde finale
    if not HUMAN_CONTROL:
        ga.save(TRAINING_CONFIG['save_file'])
        print(f"\n💾 Sauvegarde finale effectuée")
        print(f"📊 Données CSV: {ga.csv_file}")

    # Fermer proprement Pygame
    display.quit()


if __name__ == "__main__":
    main()