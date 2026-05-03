"""
ai_system.py - Système d'IA modulaire pour l'apprentissage de la marche
Permet de basculer facilement entre différentes méthodes d'apprentissage
"""

import numpy as np
import math
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
import json
import os


# ============================================================================
# EXTRACTION DES ENTRÉES POUR LE RÉSEAU DE NEURONES
# ============================================================================

def get_neural_network_inputs(creature) -> np.ndarray:
    """
    Extrait toutes les entrées pour le réseau de neurones
    """
    inputs = []

    # Angles des articulations (sin/cos pour éviter discontinuité)
    for joint_name in ['hip_front', 'knee_front', 'ankle_front', 'ear_front',
                       'hip_back', 'knee_back', 'ankle_back', 'ear_back']:
        joint = creature.joints[joint_name]
        angle = joint.angle
        inputs.append(math.sin(angle))
        inputs.append(math.cos(angle))

    # Vitesses angulaires
    for joint_name in ['hip_front', 'knee_front', 'ankle_front', 'ear_front',
                       'hip_back', 'knee_back', 'ankle_back', 'ear_back']:
        joint = creature.joints[joint_name]
        angular_velocity = joint.GetJointSpeed()
        inputs.append(np.clip(angular_velocity / 10.0, -1, 1))

    # États des muscles
    for muscle_name in ['hip_front', 'knee_front', 'ankle_front', 'ear_front',
                        'hip_back', 'knee_back', 'ankle_back', 'ear_back']:
        muscle = creature.muscles[muscle_name]
        inputs.append(muscle.contraction)

    # Orientation du torse
    torso_angle = creature.torso.angle
    inputs.append(math.sin(torso_angle))
    inputs.append(math.cos(torso_angle))

    # Vitesse angulaire du torse
    inputs.append(np.clip(creature.torso.angularVelocity / 5.0, -1, 1))

    # Vélocité
    velocity = creature.torso.linearVelocity
    inputs.append(np.clip(velocity.x / 10.0, -1, 1))
    inputs.append(np.clip(velocity.y / 10.0, -1, 1))

    # Hauteur
    inputs.append(np.clip((creature.torso.position.y - 3.0) / 2.0, -1, 1))

    # Contact avec le sol
    for foot_name in ['foot_front', 'foot_back']:
        foot = creature.bodies[foot_name]
        is_touching = False
        for contact_edge in foot.contacts:
            contact = contact_edge.contact
            if contact.touching:
                is_touching = True
                break
        inputs.append(1.0 if is_touching else 0.0)

    # Forces de contact
    for foot_name in ['foot_front', 'foot_back']:
        foot = creature.bodies[foot_name]
        contact_force = 0.0
        for contact_edge in foot.contacts:
            contact = contact_edge.contact
            if contact.touching:
                manifold = contact.manifold
                contact_force += manifold.pointCount
        inputs.append(np.clip(contact_force / 5.0, 0, 1))

    # Position horizontale
    inputs.append(np.clip(creature.torso.position.x / 50.0, -1, 1))

    return np.array(inputs, dtype=np.float32)


# ============================================================================
# CLASSE DE BASE POUR LES IAs
# ============================================================================

class BaseAI(ABC):
    """
    Classe abstraite de base pour toutes les méthodes d'apprentissage
    """

    def __init__(self, name: str):
        self.name = name
        self.input_size = 43  # Nombre d'entrées du réseau
        self.output_size = 8  # Nombre de muscles à contrôler
        self.episode_count = 0
        self.total_reward = 0.0

    @abstractmethod
    def get_actions(self, creature, time: float) -> np.ndarray:
        """
        Retourne les actions à effectuer pour les 8 muscles
        Returns: array de 8 valeurs entre 0 et 1
        """
        pass

    @abstractmethod
    def update(self, creature, reward: float, done: bool):
        """
        Met à jour l'IA avec le résultat de l'action
        """
        pass

    @abstractmethod
    def save(self, filepath: str):
        """
        Sauvegarde l'état de l'IA
        """
        pass

    @abstractmethod
    def load(self, filepath: str):
        """
        Charge l'état de l'IA
        """
        pass

    @abstractmethod
    def reset(self):
        """
        Réinitialise l'IA pour un nouvel épisode
        """
        pass

    def calculate_reward(self, creature, prev_x: float) -> float:
        """
        Calcule la récompense basée sur la performance
        """
        current_x = creature.torso.position.x
        current_y = creature.torso.position.y

        # Récompense pour la distance parcourue
        distance_reward = (current_x - prev_x) * 10.0

        # Pénalité si trop bas (tombé)
        height_penalty = -5.0 if current_y < 1.0 else 0.0

        # Pénalité si trop incliné
        angle = abs(creature.torso.angle % (2 * math.pi))
        if angle > math.pi:
            angle = 2 * math.pi - angle
        tilt_penalty = -abs(angle) * 0.5

        # Bonus pour rester stable
        stability_bonus = 1.0 if current_y > 2.0 else 0.0

        return distance_reward + height_penalty + tilt_penalty + stability_bonus

    def get_stats(self) -> Dict:
        """Retourne les statistiques de l'IA"""
        return {
            'name': self.name,
            'episode_count': self.episode_count,
            'total_reward': self.total_reward
        }


# ============================================================================
# MÉTHODE 1 : SÉLECTION NATURELLE
# ============================================================================

class NaturalSelectionAI(BaseAI):
    """
    IA basée sur la sélection naturelle avec des chorégraphies pré-définies
    """

    def __init__(self, population_size: int = 20, mutation_rate: float = 0.1):
        super().__init__("Natural Selection")
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.sequence_length = 100  # Nombre de frames dans une chorégraphie

        # Population de chorégraphies
        self.population = self._create_initial_population()
        self.current_individual = 0
        self.current_sequence = self.population[0]
        self.generation = 0

        # Fitness tracking
        self.fitness_scores = [0.0] * population_size
        self.best_fitness = -float('inf')
        self.best_sequence = None
        self.best_distance = 0.0

    def _create_initial_population(self) -> List[np.ndarray]:
        """Crée la population initiale de chorégraphies aléatoires"""
        return [np.random.uniform(0, 1, (self.sequence_length, self.output_size))
                for _ in range(self.population_size)]

    def get_actions(self, creature, time: float) -> np.ndarray:
        """Retourne les actions selon la chorégraphie actuelle"""
        frame = int(time * 60) % self.sequence_length  # 60 FPS
        return self.current_sequence[frame]

    def update(self, creature, reward: float, done: bool):
        """Met à jour le fitness de l'individu actuel"""
        self.fitness_scores[self.current_individual] += reward
        self.total_reward += reward

        if done:
            # Enregistre la distance finale
            final_distance = creature.torso.position.x
            if final_distance > self.best_distance:
                self.best_distance = final_distance

            # Passe à l'individu suivant
            self.current_individual += 1
            self.episode_count += 1

            # Si toute la population a été évaluée
            if self.current_individual >= self.population_size:
                self._evolve_population()
                self.current_individual = 0
                self.generation += 1

    def _evolve_population(self):
        """Fait évoluer la population par sélection naturelle"""
        # Trouve le meilleur individu
        best_idx = np.argmax(self.fitness_scores)
        if self.fitness_scores[best_idx] > self.best_fitness:
            self.best_fitness = self.fitness_scores[best_idx]
            self.best_sequence = self.population[best_idx].copy()

        # Sélection par tournoi
        new_population = []

        # Garde le meilleur (élitisme)
        new_population.append(self.population[best_idx].copy())

        # Génère le reste par sélection et mutation
        for _ in range(self.population_size - 1):
            # Sélection par tournoi
            parent = self._tournament_selection()

            # Mutation
            child = self._mutate(parent)
            new_population.append(child)

        self.population = new_population
        self.fitness_scores = [0.0] * self.population_size

    def _tournament_selection(self, tournament_size: int = 3) -> np.ndarray:
        """Sélection par tournoi"""
        indices = np.random.choice(self.population_size, tournament_size, replace=False)
        best_idx = indices[np.argmax([self.fitness_scores[i] for i in indices])]
        return self.population[best_idx].copy()

    def _mutate(self, sequence: np.ndarray) -> np.ndarray:
        """Applique une mutation à une séquence"""
        mutated = sequence.copy()
        mask = np.random.random(sequence.shape) < self.mutation_rate
        mutated[mask] = np.random.uniform(0, 1, np.sum(mask))
        return mutated

    def reset(self):
        """Réinitialise pour un nouvel épisode"""
        self.current_sequence = self.population[self.current_individual]

    def save(self, filepath: str):
        """Sauvegarde la population et les statistiques"""
        data = {
            'population': [seq.tolist() for seq in self.population],
            'fitness_scores': self.fitness_scores,
            'best_fitness': self.best_fitness,
            'best_sequence': self.best_sequence.tolist() if self.best_sequence is not None else None,
            'generation': self.generation,
            'best_distance': self.best_distance
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load(self, filepath: str):
        """Charge la population et les statistiques"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.population = [np.array(seq) for seq in data['population']]
        self.fitness_scores = data['fitness_scores']
        self.best_fitness = data['best_fitness']
        self.best_sequence = np.array(data['best_sequence']) if data['best_sequence'] else None
        self.generation = data['generation']
        self.best_distance = data.get('best_distance', 0.0)

    def get_stats(self) -> Dict:
        """Retourne les statistiques détaillées"""
        stats = super().get_stats()
        stats.update({
            'generation': self.generation,
            'individual': f"{self.current_individual + 1}/{self.population_size}",
            'best_fitness': self.best_fitness,
            'best_distance': self.best_distance,
            'current_fitness': self.fitness_scores[self.current_individual]
        })
        return stats


# ============================================================================
# MÉTHODE 2 : PPO (PROXIMAL POLICY OPTIMIZATION) - À COMPLÉTER
# ============================================================================

class PPOAI(BaseAI):
    """
    IA basée sur PPO (Proximal Policy Optimization)
    Utilise un réseau de neurones qui apprend par reinforcement learning

    TODO: Implémenter le réseau de neurones et l'algorithme PPO
    Nécessite: PyTorch ou TensorFlow + Stable-Baselines3
    """

    def __init__(self, learning_rate: float = 3e-4):
        super().__init__("PPO")
        self.learning_rate = learning_rate

        # Placeholders pour le réseau de neurones
        self.policy_network = None  # TODO: Créer le réseau Actor
        self.value_network = None  # TODO: Créer le réseau Critic

        # Buffers pour stocker les expériences
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.values_buffer = []
        self.log_probs_buffer = []

        print("⚠️  PPO AI initialisé mais non implémenté. À compléter avec PyTorch/TF.")

    def get_actions(self, creature, time: float) -> np.ndarray:
        """
        TODO: Utiliser le réseau de neurones pour prédire les actions
        Pour l'instant, retourne des actions aléatoires
        """
        # Récupère l'état actuel
        state = get_neural_network_inputs(creature)

        # TODO: Passer state dans le policy_network
        # action, log_prob, value = self.policy_network(state)

        # Pour l'instant: actions aléatoires
        actions = np.random.uniform(0, 1, self.output_size)

        # Stocke pour l'apprentissage
        self.states_buffer.append(state)
        self.actions_buffer.append(actions)

        return actions

    def update(self, creature, reward: float, done: bool):
        """
        TODO: Implémenter la mise à jour PPO
        """
        self.rewards_buffer.append(reward)
        self.total_reward += reward

        if done:
            self.episode_count += 1
            # TODO: Calculer les avantages et mettre à jour les réseaux
            # self._update_networks()
            self._clear_buffers()

    def _clear_buffers(self):
        """Vide les buffers d'expérience"""
        self.states_buffer = []
        self.actions_buffer = []
        self.rewards_buffer = []
        self.values_buffer = []
        self.log_probs_buffer = []

    def reset(self):
        """Réinitialise pour un nouvel épisode"""
        pass  # Pas besoin de reset particulier pour PPO

    def save(self, filepath: str):
        """TODO: Sauvegarder les poids du réseau"""
        print("⚠️  Sauvegarde PPO non implémentée")

    def load(self, filepath: str):
        """TODO: Charger les poids du réseau"""
        print("⚠️  Chargement PPO non implémenté")


# ============================================================================
# MÉTHODE 3 : TEMPLATE POUR FUTURES IAs
# ============================================================================

class TemplateAI(BaseAI):
    """
    Template pour ajouter facilement de nouvelles méthodes d'apprentissage
    Exemples possibles:
    - Genetic Algorithm (AG pur)
    - Deep Q-Network (DQN)
    - Actor-Critic (A2C/A3C)
    - Soft Actor-Critic (SAC)
    - NEAT (NeuroEvolution of Augmenting Topologies)
    """

    def __init__(self):
        super().__init__("Template AI")
        print("⚠️  Template AI - À personnaliser selon votre méthode")

    def get_actions(self, creature, time: float) -> np.ndarray:
        return np.random.uniform(0, 1, self.output_size)

    def update(self, creature, reward: float, done: bool):
        self.total_reward += reward
        if done:
            self.episode_count += 1

    def reset(self):
        pass

    def save(self, filepath: str):
        pass

    def load(self, filepath: str):
        pass


# ============================================================================
# GESTIONNAIRE D'IA
# ============================================================================

class AIManager:
    """
    Gestionnaire qui permet de basculer facilement entre différentes IAs
    """

    def __init__(self):
        self.available_ais = {
            'natural_selection': NaturalSelectionAI,
            'ppo': PPOAI,
            'template': TemplateAI
        }
        self.current_ai = None
        self.ai_type = None

    def set_ai(self, ai_type: str, **kwargs):
        """
        Change l'IA active

        Args:
            ai_type: 'natural_selection', 'ppo', ou 'template'
            **kwargs: Arguments spécifiques à l'IA choisie
        """
        if ai_type not in self.available_ais:
            raise ValueError(f"AI type '{ai_type}' non reconnu. Disponibles: {list(self.available_ais.keys())}")

        self.ai_type = ai_type
        self.current_ai = self.available_ais[ai_type](**kwargs)
        print(f"✓ IA activée: {self.current_ai.name}")

    def get_actions(self, creature, time: float) -> np.ndarray:
        """Délègue à l'IA active"""
        if self.current_ai is None:
            raise RuntimeError("Aucune IA n'est active. Appelez set_ai() d'abord.")
        return self.current_ai.get_actions(creature, time)

    def update(self, creature, reward: float, done: bool):
        """Délègue à l'IA active"""
        if self.current_ai:
            self.current_ai.update(creature, reward, done)

    def reset(self):
        """Délègue à l'IA active"""
        if self.current_ai:
            self.current_ai.reset()

    def save(self, filename: str = None):
        """Sauvegarde l'IA active"""
        if self.current_ai:
            if filename is None:
                filename = f"saves/{self.ai_type}_save.json"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            self.current_ai.save(filename)
            print(f"✓ IA sauvegardée: {filename}")

    def load(self, filename: str):
        """Charge une IA depuis un fichier"""
        if self.current_ai:
            self.current_ai.load(filename)
            print(f"✓ IA chargée: {filename}")

    def register_ai(self, name: str, ai_class: type):
        """
        Permet d'enregistrer une nouvelle IA custom

        Usage:
            class MyCustomAI(BaseAI):
                ...

            ai_manager.register_ai('my_custom', MyCustomAI)
            ai_manager.set_ai('my_custom')
        """
        self.available_ais[name] = ai_class
        print(f"✓ Nouvelle IA enregistrée: {name}")

    def get_stats(self) -> Dict:
        """Retourne les statistiques de l'IA active"""
        if self.current_ai:
            return self.current_ai.get_stats()
        return {}