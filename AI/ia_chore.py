"""
IA par algorithme génétique basé sur des chorégraphies musculaires.
VERSION AVEC LOGGING CSV
"""

import random
import pickle
import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any
from AI.ia_base import IABase


class Individual:
    """Classe compatible avec le format de ia_gen.py"""
    def __init__(self, genome=None, fitness=0.0, distance=0.0, stability=1.0, energy=0.0, time_alive=0):
        self.genome = genome if genome is not None else []
        self.fitness = fitness
        self.distance = distance
        self.stability = stability
        self.energy = energy
        self.time_alive = time_alive

class IAChoreography(IABase):
    """
    IA utilisant un algorithme génétique pour optimiser des chorégraphies.
    """

    def __init__(self, config):
        """
        Initialise l'IA chorégraphique.
        """
        super().__init__(config)

        # ✅ Définir num_actions AVANT de créer la population
        self.num_actions = 17  # 0 = relax, 1-16 = 8 muscles × 2 actions

        # État de l'épisode actuel
        self.episode_start_time = 0.0
        self.current_time = 0.0
        self.current_frame = 0

        # Logs pour statistiques
        self.generation_best = 0.0
        self.generation_avg = 0.0

        self.current_max_time = config.GA_CONFIG['base_time']
        self.best_reward_ever = 0.0

        # ✅ CSV logging
        self.csv_file = config.TRAINING_CONFIG.get('csv_file', 'data/training_data_choreography.csv')
        self.generation_start_time = datetime.now()

        # Population de chorégraphies (créée APRÈS num_actions)
        self.population = [self._create_random_choreography() for _ in range(config.GA_CONFIG['population_size'])]
        self.fitness_scores = [0.0] * config.GA_CONFIG['population_size']

    def _create_random_choreography(self) -> List[int]:
        """
        Crée une chorégraphie aléatoire avec des ACTIONS DISCRÈTES (0-16).
        """
        num_frames = self.config.GA_CONFIG['genome_length']
        choreography = [random.randint(0, self.num_actions - 1) for _ in range(num_frames)]
        return choreography

    def get_action(self, time: float, dog_state: Dict[str, Any]) -> int:
        """
        Retourne une ACTION DISCRÈTE (0-16).
        """
        choreography = self.population[self.current_individual]
        frame_index = min(self.current_frame, len(choreography) - 1)
        self.current_frame += 1
        return choreography[frame_index]

    def action_to_muscle_control(self, action: int) -> Dict[str, Any]:
        """
        Convertit une action (0-16) en commande musculaire.
        """
        if action == 0:
            return {'muscle': None, 'action': 'relax'}

        muscle_index = (action - 1) // 2
        is_contract = (action - 1) % 2 == 0

        return {
            'muscle': muscle_index,
            'action': 'contract' if is_contract else 'extend'
        }

    def on_episode_end(self, distance: float, frames_survived: int, dog_state: Dict[str, Any]):
        fitness = distance * 100 + frames_survived * 0.5
        self.fitness_scores[self.current_individual] = fitness

        if fitness > self.best_reward_ever:
            self.best_reward_ever = fitness
            self.current_max_time = self._calculate_max_time_from_reward()
            print(f"🏆 Nouveau record: {self.best_reward_ever:.2f}m → Temps: {self.current_max_time} frames")

        if fitness > self.best_distance:
            self.best_distance = fitness

        self.current_individual += 1

    def reset_episode(self):
        """
        Réinitialise le compteur de frames à chaque épisode.
        """
        self.current_frame = 0
        self.episode_start_time = 0.0
        self.current_time = 0.0

    def should_reset_simulation(self) -> bool:
        """
        Détermine si on doit reset (nouvelle génération).
        """
        if self.current_individual >= self.config.GA_CONFIG['population_size']:
            self._evolve_population()
            self.current_individual = 0
            self.generation += 1
            self._adapt_genome_length()
            return True
        return True

    def _adapt_genome_length(self):
        """
        Adapte la longueur du génome en fonction du current_max_time.
        """
        if self.config.GA_CONFIG['adaptive_time']:
            self.config.GA_CONFIG['genome_length'] = self.current_max_time

            for i in range(len(self.population)):
                current_length = len(self.population[i])
                target_length = self.current_max_time

                if current_length < target_length:
                    extension = [random.randint(0, self.num_actions - 1)
                                for _ in range(target_length - current_length)]
                    self.population[i].extend(extension)
                elif current_length > target_length:
                    self.population[i] = self.population[i][:target_length]

    def _evolve_population(self):
        """
        Fait évoluer la population via sélection, crossover et mutation.
        """
        self.generation_best = max(self.fitness_scores)
        self.generation_avg = sum(self.fitness_scores) / len(self.fitness_scores)

        self._save_generation_stats()

        sorted_indices = sorted(range(len(self.fitness_scores)),
                                key=lambda i: self.fitness_scores[i],
                                reverse=True)

        elite_count = max(1, self.config.GA_CONFIG['elite_size'])
        new_population = [self.population[i] for i in sorted_indices[:elite_count]]

        while len(new_population) < self.config.GA_CONFIG['population_size']:
            parent1 = self._tournament_selection(sorted_indices)
            parent2 = self._tournament_selection(sorted_indices)
            child = self._crossover(parent1, parent2)
            child = self._mutate(child)
            new_population.append(child)

        self.population = new_population
        self.fitness_scores = [0.0] * len(self.population)

    def _tournament_selection(self, sorted_indices: List[int]) -> List[int]:
        """Sélectionne un parent par tournoi."""
        tournament_size = 3
        tournament = random.sample(sorted_indices[:len(sorted_indices) // 2], tournament_size)
        winner = min(tournament)
        return self.population[winner]

    def _crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Croisement entre deux parents."""
        cutpoint = random.randint(0, len(parent1))
        child = parent1[:cutpoint] + parent2[cutpoint:]
        return child

    def _mutate(self, choreography: List[int]) -> List[int]:
        """Mute une chorégraphie."""
        mutated = []
        for action in choreography:
            if random.random() < self.config.GA_CONFIG['mutation_rate']:
                action = random.randint(0, self.num_actions - 1)
            mutated.append(action)
        return mutated

    def _save_generation_stats(self):
        """
        ✅ NOUVEAU: Sauvegarde les stats dans un CSV (comme l'ancien code).
        """
        os.makedirs('data', exist_ok=True)

        generation_end_time = datetime.now()
        duration = (generation_end_time - self.generation_start_time).total_seconds()

        data = {
            'generation': self.generation,
            'timestamp': generation_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'duration_seconds': duration,
            'fitness_best': self.generation_best,
            'fitness_avg': self.generation_avg,
            'fitness_worst': min(self.fitness_scores) if self.fitness_scores else 0,
            'fitness_std': pd.Series(self.fitness_scores).std() if self.fitness_scores else 0,
            'best_distance_ever': self.best_distance,
            'current_max_time': self.current_max_time,
            'population_size': len(self.population),
            'mutation_rate': self.config.GA_CONFIG['mutation_rate'],
            'elite_size': self.config.GA_CONFIG['elite_size'],
        }

        df = pd.DataFrame([data])

        if os.path.exists(self.csv_file):
            df.to_csv(self.csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.csv_file, mode='w', header=True, index=False)

        # Reset timer pour la prochaine génération
        self.generation_start_time = datetime.now()

    def save(self, filepath: str):
        """
        ✅ Sauvegarde au format de l'ANCIEN CODE (fox_ai.pkl compatible)
        Compatible avec ia_gen.py ET ia_chore.py
        """
        import os
        import numpy as np

        os.makedirs('data', exist_ok=True)

        # ✅ IMPORTANT : Convertir les génomes en numpy arrays pour compatibilité
        # L'ancien code utilise numpy arrays, pas des listes Python
        population_as_numpy = []
        for genome in self.population:
            if isinstance(genome, list):
                population_as_numpy.append(np.array(genome, dtype=int))
            else:
                population_as_numpy.append(genome)

        # Trouver le meilleur individu actuel
        best_idx = 0
        if self.fitness_scores and max(self.fitness_scores) > 0:
            best_idx = self.fitness_scores.index(max(self.fitness_scores))

        # ✅ MODIFIÉ : Utiliser la classe Individual du module (pas locale)
        best_genome = population_as_numpy[best_idx] if population_as_numpy else np.array([])
        best_fitness = self.best_distance if self.best_distance > 0 else self.generation_best

        best_individual = Individual(
            genome=best_genome,
            fitness=best_fitness,
            distance=self.best_distance,
            stability=1.0,
            energy=0.0,
            time_alive=len(best_genome)
        )

        # ✅ Format IDENTIQUE à l'ancien code
        save_data = {
            'population': population_as_numpy,  # Liste de numpy arrays
            'generation': self.generation,
            'best_individual': best_individual,  # Objet Individual
            'training_number': 1,
            'parameters': {
                'population_size': self.config.GA_CONFIG['population_size'],
                'genome_length': self.config.GA_CONFIG['genome_length'],
                'mutation_rate': self.config.GA_CONFIG['mutation_rate'],
                'crossover_rate': self.config.GA_CONFIG['crossover_rate'],
                'elite_size': self.config.GA_CONFIG['elite_size'],
            },
            'current_time_limit': self.current_max_time,
            'best_reward_ever': self.best_reward_ever,
        }

        with open(filepath, 'wb') as f:
            pickle.dump(save_data, f)

        print(f"✅ Sauvegarde réussie : {filepath}")

    def load(self, filepath: str):
        """
        ✅ Charge depuis le format de l'ANCIEN CODE (fox_ai.pkl compatible)
        Compatible avec ia_gen.py ET ia_chore.py
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fichier {filepath} introuvable")

        # ✅ AJOUT : Créer un module factice pour ia_gen si besoin
        import sys
        import types

        if 'AI.ia_gen' not in sys.modules:
            # Créer le module factice
            fake_module = types.ModuleType('ia_gen')

            # ✅ MODIFIÉ : Utiliser la classe Individual du module actuel
            fake_module.Individual = Individual

            sys.modules['AI.ia_gen'] = fake_module
            sys.modules['ia_gen'] = fake_module  # Alias au cas où

        # Charger le fichier
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        # Charger la population (gérer ancien et nouveau format)
        if isinstance(data['population'][0], list):
            # Nouveau format : liste de listes
            self.population = data['population']
        else:
            # Ancien format : liste d'objets Individual avec .genome
            self.population = []
            for individual in data['population']:
                if hasattr(individual, 'genome'):
                    # Convertir numpy array en list si nécessaire
                    import numpy as np
                    if isinstance(individual.genome, np.ndarray):
                        genome = individual.genome.tolist()
                    else:
                        genome = list(individual.genome)
                    self.population.append(genome)
                else:
                    self.population.append(individual)

        # Charger les métadonnées
        self.generation = data.get('generation', 0)

        if 'best_individual' in data and data['best_individual']:
            best_ind = data['best_individual']
            if hasattr(best_ind, 'distance'):
                self.best_distance = best_ind.distance
                self.best_reward_ever = best_ind.fitness if hasattr(best_ind, 'fitness') else best_ind.distance
            elif isinstance(best_ind, dict):
                self.best_distance = best_ind.get('distance', 0.0)
                self.best_reward_ever = best_ind.get('fitness', self.best_distance)

        self.current_max_time = data.get('current_time_limit', self.config.GA_CONFIG['base_time'])

        # Si best_reward_ever n'est pas dans les données, utiliser best_distance
        if 'best_reward_ever' in data:
            self.best_reward_ever = data['best_reward_ever']

        # Adapter la longueur des génomes
        self._adapt_genome_length()

        # Réinitialiser les fitness scores
        self.fitness_scores = [0.0] * len(self.population)

        print(
            f"✅ Chargement réussi : Gen {self.generation}, Best {self.best_distance:.2f}m, Time {self.current_max_time}f")


    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques."""
        stats = super().get_stats()
        stats.update({
            'generation_best': self.generation_best,
            'generation_avg': self.generation_avg,
            'population_size': len(self.population),
            'current_max_time': self.current_max_time
        })
        return stats

    def on_generation_end(self):
        """
        Appelée à la fin de chaque génération.
        """
        print(f"🧬 Génération {self.generation} | "
              f"Best: {self.generation_best:.2f}m | "
              f"Avg: {self.generation_avg:.2f}m | "
              f"All-time: {self.best_distance:.2f}m | "
              f"Time: {self.current_max_time}f ({self.current_max_time/60:.1f}s)")


        if (self.generation + 1) % self.config.TRAINING_CONFIG['save_every'] == 0:
            self.save(self.config.TRAINING_CONFIG['save_file'])
            print(f"💾 Sauvegarde périodique (Gen {self.generation})")

    def _calculate_max_time_from_reward(self) -> int:
        """
        Calcule le temps maximum alloué en fonction du meilleur reward.
        """
        reward_threshold = 5000.0
        progress = min(self.best_reward_ever / reward_threshold, 1.0)
        time_range = self.config.GA_CONFIG['max_time'] - self.config.GA_CONFIG['base_time']
        calculated_time = self.config.GA_CONFIG['base_time'] + int(progress * time_range)
        return calculated_time