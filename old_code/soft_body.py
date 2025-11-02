# ============================================
# soft_body.py - Système de soft body pour le quadrupède
# ============================================

import pygame
import math
from Box2D import b2Vec2


class SoftBodyPart:
    """Représente une partie du soft body (body, head, thigh, etc.)"""

    def __init__(self, world, bone, num_points=15, part_name="part"):
        """
        Crée un soft body pour une partie du squelette

        Args:
            world: Monde Box2D
            bone: Os du squelette à suivre
            num_points: Nombre de points sur le contour
            part_name: Nom de la partie (pour debug)
        """
        self.world = world
        self.bone = bone
        self.part_name = part_name
        self.num_points = num_points
        self.points = []
        self.relative_positions = []
        self.connections = []

        # Paramètres physiques (identiques à test4_soft_body.py)
        self.spring_strength = 1.0
        self.spring_damping = 1.0
        self.shape_memory = 5
        self.collision_stiffness = 200.0
        self.collision_damping = 10.0
        self.attachment_strength = 1.0  # Force d'attachement au squelette

        # Créer les points autour de l'os
        self._create_points_from_bone()

    def _create_points_from_bone(self):
        """Crée les points du soft body autour de l'os"""
        # Récupérer les dimensions de l'os
        bone_width = self.bone.width
        bone_height = self.bone.height

        # Créer un contour rectangulaire autour de l'os avec marge
        margin = 0.15  # Marge autour de l'os
        half_width = (bone_width / 2) + margin
        half_height = (bone_height / 2) + margin

        # Calculer les positions relatives des points (contour rectangulaire)
        points_per_side = self.num_points // 4
        remainder = self.num_points % 4

        positions = []

        # Côté haut
        for i in range(points_per_side + (1 if remainder > 0 else 0)):
            t = i / max(1, points_per_side)
            x = -half_width + t * (2 * half_width)
            y = half_height
            positions.append((x, y))

        # Côté droit
        for i in range(points_per_side + (1 if remainder > 1 else 0)):
            t = i / max(1, points_per_side)
            x = half_width
            y = half_height - t * (2 * half_height)
            positions.append((x, y))

        # Côté bas
        for i in range(points_per_side + (1 if remainder > 2 else 0)):
            t = i / max(1, points_per_side)
            x = half_width - t * (2 * half_width)
            y = -half_height
            positions.append((x, y))

        # Côté gauche
        for i in range(points_per_side):
            t = i / max(1, points_per_side)
            x = -half_width
            y = -half_height + t * (2 * half_height)
            positions.append((x, y))

        # Créer les corps Box2D pour chaque point
        bone_pos = self.bone.body.position
        bone_angle = self.bone.body.angle

        for rel_x, rel_y in positions:
            # Rotation selon l'angle de l'os
            cos_a = math.cos(bone_angle)
            sin_a = math.sin(bone_angle)
            world_x = bone_pos.x + (rel_x * cos_a - rel_y * sin_a)
            world_y = bone_pos.y + (rel_x * sin_a + rel_y * cos_a)

            # Créer le corps physique
            body = self.world.CreateDynamicBody(
                position=(world_x, world_y),
                linearDamping=0.5,
                angularDamping=0.5
            )
            body.CreateCircleFixture(
                radius=0.15,
                density=0.5,
                friction=0.5,
                restitution=0.3
            )

            self.points.append(body)
            self.relative_positions.append(b2Vec2(rel_x, rel_y))

        # Créer les connexions entre points adjacents (périmètre)
        for i in range(self.num_points):
            next_i = (i + 1) % self.num_points
            original_length = (self.relative_positions[i] -
                               self.relative_positions[next_i]).length
            self.connections.append({
                'i': i,
                'j': next_i,
                'rest_length': original_length
            })

        # Connexions internes pour la stabilité (distance 2 et 3)
        for i in range(self.num_points):
            j = (i + 2) % self.num_points
            if j != i:
                original_length = (self.relative_positions[i] -
                                   self.relative_positions[j]).length
                self.connections.append({
                    'i': i,
                    'j': j,
                    'rest_length': original_length
                })

            if self.num_points > 5:
                j = (i + 3) % self.num_points
                if j != i and j != (i + 1) % self.num_points:
                    original_length = (self.relative_positions[i] -
                                       self.relative_positions[j]).length
                    self.connections.append({
                        'i': i,
                        'j': j,
                        'rest_length': original_length
                    })

    def update(self, ground_y=2.0):
        """Met à jour la physique du soft body"""
        # Récupérer la position et rotation de l'os
        bone_pos = self.bone.body.position
        bone_angle = self.bone.body.angle

        cos_angle = math.cos(bone_angle)
        sin_angle = math.sin(bone_angle)

        # Appliquer les forces de ressort entre points connectés
        for conn in self.connections:
            p1 = self.points[conn['i']]
            p2 = self.points[conn['j']]

            diff = p2.position - p1.position
            distance = diff.length

            if distance > 0.01:
                # Force de ressort
                force_magnitude = self.spring_strength * (distance - conn['rest_length'])
                force_direction = diff / distance
                force = force_direction * force_magnitude

                # Amortissement
                vel_diff = p2.linearVelocity - p1.linearVelocity
                damping_force = vel_diff * self.spring_damping

                total_force = force + damping_force

                p1.ApplyForce(total_force, p1.worldCenter, True)
                p2.ApplyForce(-total_force, p2.worldCenter, True)

        # Attacher les points au squelette avec shape memory
        for i, point in enumerate(self.points):
            # Position cible (relative à l'os, avec rotation)
            rel_x = self.relative_positions[i].x
            rel_y = self.relative_positions[i].y

            # Rotation de la forme de base
            rotated_x = rel_x * cos_angle - rel_y * sin_angle
            rotated_y = rel_x * sin_angle + rel_y * cos_angle

            target_position = bone_pos + b2Vec2(rotated_x, rotated_y)
            to_target = target_position - point.position

            # Force d'attachement au squelette
            attachment_force = to_target * self.attachment_strength
            point.ApplyForce(attachment_force, point.worldCenter, True)

            # Collision avec le sol
            point_y = point.position.y
            point_radius = 0.15

            penetration = (ground_y + point_radius) - point_y
            if penetration > 0:
                # Force de répulsion
                repulsion_force_magnitude = penetration * self.collision_stiffness

                # Amortissement
                velocity_y = point.linearVelocity.y
                damping_force = -velocity_y * self.collision_damping

                total_repulsion = repulsion_force_magnitude + damping_force

                # Appliquer la force verticale
                point.ApplyForce(b2Vec2(0, total_repulsion), point.worldCenter, True)

                # Friction horizontale
                friction_force = -point.linearVelocity.x * 5.0
                point.ApplyForce(b2Vec2(friction_force, 0), point.worldCenter, True)

    def draw(self, display):
        """Dessine le soft body"""
        # Dessiner les connexions
        for conn in self.connections:
            p1_pos = self.points[conn['i']].position
            p2_pos = self.points[conn['j']].position
            screen_p1 = display.to_screen(p1_pos)
            screen_p2 = display.to_screen(p2_pos)
            pygame.draw.line(display.screen, (100, 150, 255), screen_p1, screen_p2, 2)

        # Dessiner les points
        for point in self.points:
            pos = display.to_screen(point.position)
            pygame.draw.circle(display.screen, (50, 100, 200), pos, 6)
            pygame.draw.circle(display.screen, (150, 200, 255), pos, 4)


class SoftBodyQuadruped:
    """Gère tous les soft bodies du quadrupède"""

    def __init__(self, world, quadruped):
        """
        Crée le système de soft body pour le quadrupède entier

        Args:
            world: Monde Box2D
            quadruped: Instance du quadrupède avec squelette
        """
        self.world = world
        self.quadruped = quadruped
        self.parts = {}

        # Créer un soft body pour chaque partie du squelette
        self._create_soft_body_parts()

    def _create_soft_body_parts(self):
        """Crée les soft bodies pour toutes les parties"""
        # Nombre de points adapté à chaque partie
        parts_config = {
            # 'body': (self.quadruped.body, 20),
            # 'neck': (self.quadruped.neck, 12),
            'head': (self.quadruped.head, 2),
            # 'front_thigh': (self.quadruped.front_thigh, 12),
            # 'front_shin': (self.quadruped.front_shin, 10),
            # 'front_ankle': (self.quadruped.front_ankle, 8),
            # 'front_foot': (self.quadruped.front_foot, 8),
            # 'back_thigh': (self.quadruped.back_thigh, 12),
            # 'back_shin': (self.quadruped.back_shin, 10),
            # 'back_ankle': (self.quadruped.back_ankle, 8),
            # 'back_foot': (self.quadruped.back_foot, 8),
            # 'tail_bottom': (self.quadruped.tail_bottom, 12),
            # 'tail_mid': (self.quadruped.tail_mid, 10),
            # 'tail_high': (self.quadruped.tail_high, 10),
        }

        for part_name, (bone, num_points) in parts_config.items():
            self.parts[part_name] = SoftBodyPart(
                self.world, bone, num_points, part_name
            )
            print(f"✅ Soft body créé: {part_name} ({num_points} points)")

    def update(self):
        """Met à jour tous les soft bodies"""
        # Position Y du sol (à ajuster selon votre monde)
        ground_y = 0.5  # Ajustez selon la hauteur de votre sol

        for part in self.parts.values():
            part.update(ground_y)

    def draw(self, display):
        """Dessine tous les soft bodies"""
        # Ordre de dessin (du fond vers le premier plan)
        draw_order = [
            'tail_high', 'tail_mid', 'tail_bottom',
            'back_foot', 'back_ankle', 'back_shin', 'back_thigh',
            'front_foot', 'front_ankle', 'front_shin', 'front_thigh',
            'neck', 'head', 'body'
        ]

        for part_name in draw_order:
            if part_name in self.parts:
                self.parts[part_name].draw(display)