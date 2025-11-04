import numpy as np
import pickle
import os
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple
from datetime import datetime


@dataclass
class Individual:
    """Représente un individu avec son génome et son fitness"""
    genome: np.ndarray
    fitness: float = 0.0
    distance: float = 0.0
    stability: float = 0.0
    energy: float = 0.0
    time_alive: int = 0


class GeneticAlgorithm:
    """Algorithme génétique pour apprendre à marcher"""

    def __init__(self,
                 population_size=50,
                 genome_length=500,
                 mutation_rate=0.1,
                 crossover_rate=0.7,
                 elite_size=5,
                 csv_file='training_data.csv',
                 adaptive_time=True,
                 base_time=500,
                 max_time=2000,
                 fitness_config=None):

        self.population_size = population_size
        self.genome_length = genome_length
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size

        self.population: List[Individual] = []
        self.generation = 0
        self.best_individual = None

        # Gestion du CSV
        self.csv_file = csv_file
        self.training_number = self._get_next_training_number()

        # Gestion du temps adaptatif
        self.adaptive_time = adaptive_time
        self.base_time = base_time
        self.max_time = max_time
        self.current_time_limit = base_time

        # Configuration du fitness
        self.fitness_config = fitness_config if fitness_config else {
            'distance_weight': 100.0,
            'stability_weight': 50.0,
            'fallen_penalty': -100.0,
            'energy_penalty': 0.1,
            'time_bonus': 0.5
        }

        # Timestamp pour mesurer la durée de chaque génération
        self.generation_start_time = None

        self.num_actions = 17

        self._initialize_population()

    def _get_next_training_number(self):
        """Détermine le numéro d'entraînement suivant"""
        os.makedirs('data', exist_ok=True)

        if not os.path.exists(self.csv_file):
            return 1

        try:
            df = pd.read_csv(self.csv_file, decimal='.')
            if 'training_number' in df.columns and len(df) > 0:
                return int(df['training_number'].max()) + 1
            return 1
        except:
            return 1

    def _initialize_population(self):
        """Initialise la population avec des génomes aléatoires"""
        self.population = []
        for _ in range(self.population_size):
            genome = np.random.randint(0, self.num_actions, size=self.genome_length)
            self.population.append(Individual(genome=genome))

    def get_action(self, individual: Individual, frame: int) -> int:
        """Récupère l'action à effectuer pour une frame donnée"""
        if frame >= len(individual.genome):
            return 0
        return individual.genome[frame]

    def action_to_keys(self, action: int) -> dict:
        """Convertit une action en dictionnaire de contrôle des muscles"""
        if action == 0:
            return {'muscle': None, 'action': 'relax'}

        muscle_index = (action - 1) // 2
        is_contract = (action - 1) % 2 == 0

        return {
            'muscle': muscle_index,
            'action': 'contract' if is_contract else 'extend'
        }

    def calculate_fitness(self, individual: Individual, distance: float,
                          stability: float, energy: float, time_alive: int):
        """Calcule le fitness d'un individu selon la configuration"""
        fitness = 0.0

        fitness += distance * self.fitness_config['distance_weight']

        if stability > 0.5:
            fitness += self.fitness_config['stability_weight']
        else:
            fitness += self.fitness_config['fallen_penalty']

        fitness -= energy * self.fitness_config['energy_penalty']
        fitness += time_alive * self.fitness_config['time_bonus']

        individual.fitness = fitness
        individual.distance = distance
        individual.stability = stability
        individual.energy = energy
        individual.time_alive = time_alive

        return individual.fitness

    def selection(self) -> List[Individual]:
        """Sélection par tournoi"""
        selected = []

        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        selected.extend(sorted_pop[:self.elite_size])

        tournament_size = 3
        while len(selected) < self.population_size:
            tournament = np.random.choice(self.population, tournament_size, replace=False)
            winner = max(tournament, key=lambda x: x.fitness)
            selected.append(Individual(genome=winner.genome.copy(), fitness=0.0))

        return selected

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Croisement à un point"""
        if np.random.random() > self.crossover_rate:
            return (Individual(genome=parent1.genome.copy()),
                    Individual(genome=parent2.genome.copy()))

        point = np.random.randint(1, self.genome_length - 1)

        child1_genome = np.concatenate([parent1.genome[:point], parent2.genome[point:]])
        child2_genome = np.concatenate([parent2.genome[:point], parent1.genome[point:]])

        return (Individual(genome=child1_genome),
                Individual(genome=child2_genome))

    def mutate(self, individual: Individual):
        """Mutation aléatoire des gènes"""
        for i in range(len(individual.genome)):
            if np.random.random() < self.mutation_rate:
                individual.genome[i] = np.random.randint(0, self.num_actions)

    def evolve(self):
        """Fait évoluer la population d'une génération"""
        # Sauvegarder les stats de la génération qui vient de se terminer
        self._save_generation_stats()

        # Marquer le début de la PROCHAINE génération
        self.generation_start_time = datetime.now()

        # Adapter le temps si activé
        if self.adaptive_time:
            self._update_time_limit()

        # Sélection
        selected = self.selection()

        # Créer la nouvelle génération
        new_population = selected[:self.elite_size]

        # Croisement et mutation
        while len(new_population) < self.population_size:
            parent1, parent2 = np.random.choice(selected, 2, replace=False)
            child1, child2 = self.crossover(parent1, parent2)

            self.mutate(child1)
            self.mutate(child2)

            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)

        self.population = new_population[:self.population_size]
        self.generation += 1

        # Mise à jour du meilleur individu
        best = max(self.population, key=lambda x: x.fitness)
        if self.best_individual is None or best.fitness > self.best_individual.fitness:
            self.best_individual = Individual(
                genome=best.genome.copy(),
                fitness=best.fitness,
                distance=best.distance,
                stability=best.stability,
                energy=best.energy,
                time_alive=best.time_alive
            )

    def _update_time_limit(self):
        """Met à jour la limite de temps en fonction des performances"""
        avg_distance = np.mean([ind.distance for ind in self.population])
        best_distance = max([ind.distance for ind in self.population])

        if best_distance > 1.0:
            new_time = int(self.base_time + (best_distance * 50))
            self.current_time_limit = min(new_time, self.max_time)
        else:
            self.current_time_limit = self.base_time

        self.genome_length = self.current_time_limit

    def _calculate_muscle_usage_stats(self):
        """Calcule les statistiques d'utilisation des muscles pour toute la génération"""
        # Compter l'utilisation de chaque muscle à travers toute la population
        muscle_usage_counts = {
            'muscle0_contract': 0,
            'muscle0_extend': 0,
            'muscle1_contract': 0,
            'muscle1_extend': 0,
            'muscle2_contract': 0,
            'muscle2_extend': 0,
            'muscle3_contract': 0,
            'muscle3_extend': 0,
            'muscle4_contract': 0,
            'muscle4_extend': 0,
            'muscle5_contract': 0,
            'muscle5_extend': 0,
            'muscle6_contract': 0,
            'muscle6_extend': 0,
            'muscle7_contract': 0,
            'muscle7_extend': 0,
            'nothing': 0
        }

        total_actions = 0

        # Parcourir tous les individus de la génération
        for individual in self.population:
            unique, counts = np.unique(individual.genome, return_counts=True)
            action_counts = dict(zip(unique, counts))

            # Action 0 = nothing
            muscle_usage_counts['nothing'] += action_counts.get(0, 0)

            # Actions 1-16 pour les 8 muscles (contract/extend)
            for action_id, count in action_counts.items():
                if action_id > 0 and action_id <= 16:
                    muscle_index = (action_id - 1) // 2
                    is_contract = (action_id - 1) % 2 == 0

                    muscle_name = f'muscle{muscle_index}_{"contract" if is_contract else "extend"}'
                    muscle_usage_counts[muscle_name] += count

            total_actions += len(individual.genome)

        # Calculer les pourcentages
        muscle_usage_percent = {}
        for muscle_name, count in muscle_usage_counts.items():
            percent = (count / total_actions * 100) if total_actions > 0 else 0
            muscle_usage_percent[f'usage_{muscle_name}_percent'] = round(percent, 2)

        # Calculer aussi l'utilisation totale par muscle (contract + extend)
        for i in range(8):
            contract_key = f'usage_muscle{i}_contract_percent'
            extend_key = f'usage_muscle{i}_extend_percent'
            total_muscle = muscle_usage_percent.get(contract_key, 0) + muscle_usage_percent.get(extend_key, 0)
            muscle_usage_percent[f'usage_muscle{i}_total_percent'] = round(total_muscle, 2)

        return muscle_usage_percent

    def _save_generation_stats(self):
        """Sauvegarde les statistiques détaillées de la génération dans le CSV"""
        generation_end_time = datetime.now()

        # Calculer la durée de la génération
        if self.generation_start_time:
            duration = (generation_end_time - self.generation_start_time).total_seconds()
        else:
            duration = 0
            self.generation_start_time = generation_end_time

        # Extraire toutes les valeurs
        fitnesses = [ind.fitness for ind in self.population]
        distances = [ind.distance for ind in self.population]
        stabilities = [ind.stability for ind in self.population]
        energies = [ind.energy for ind in self.population]
        times_alive = [ind.time_alive for ind in self.population]

        # Calculer l'utilisation moyenne des muscles pour toute la génération
        muscle_usage = self._calculate_muscle_usage_stats()

        data = {
            # Informations générales
            'training_number': self.training_number,
            'generation': self.generation,
            'generation_start_timestamp': self.generation_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'generation_end_timestamp': generation_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'generation_duration_seconds': duration,

            # Fitness (reward) - statistiques complètes
            'fitness_best': np.max(fitnesses),
            'fitness_worst': np.min(fitnesses),
            'fitness_avg': np.mean(fitnesses),
            'fitness_median': np.median(fitnesses),
            'fitness_std': np.std(fitnesses),

            # Distance - statistiques complètes
            'distance_best': np.max(distances),
            'distance_worst': np.min(distances),
            'distance_avg': np.mean(distances),
            'distance_median': np.median(distances),
            'distance_std': np.std(distances),

            # Stabilité - statistiques complètes
            'stability_best': np.max(stabilities),
            'stability_worst': np.min(stabilities),
            'stability_avg': np.mean(stabilities),
            'stability_median': np.median(stabilities),
            'stability_std': np.std(stabilities),

            # Énergie - statistiques complètes (best = minimum car moins c'est mieux)
            'energy_best': np.min(energies),
            'energy_worst': np.max(energies),
            'energy_avg': np.mean(energies),
            'energy_median': np.median(energies),
            'energy_std': np.std(energies),

            # Temps de vie - statistiques complètes
            'time_alive_best': np.max(times_alive),
            'time_alive_worst': np.min(times_alive),
            'time_alive_avg': np.mean(times_alive),
            'time_alive_median': np.median(times_alive),
            'time_alive_std': np.std(times_alive),

            # Records absolus
            'absolute_best_fitness': self.best_individual.fitness if self.best_individual else 0,
            'absolute_best_distance': self.best_individual.distance if self.best_individual else 0,

            # Paramètres
            'population_size': self.population_size,
            'genome_length': self.genome_length,
            'current_time_limit': self.current_time_limit,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'elite_size': self.elite_size
        }

        # Ajouter les statistiques d'utilisation des muscles
        data.update(muscle_usage)

        df = pd.DataFrame([data])

        if os.path.exists(self.csv_file):
            df.to_csv(self.csv_file, mode='a', header=False, index=False, decimal=',', sep=';')
        else:
            df.to_csv(self.csv_file, mode='w', header=True, index=False, decimal=',', sep=';')

    def save_individual_stats(self, individual_index: int):
        """Sauvegarde les statistiques d'un individu spécifique"""
        os.makedirs('data', exist_ok=True)
        csv_file = 'data/individuals_data.csv'

        individual = self.population[individual_index]

        unique, counts = np.unique(individual.genome, return_counts=True)
        action_counts = dict(zip(unique, counts))

        action_names = ['nothing',
                        'muscle0_contract', 'muscle0_extend',
                        'muscle1_contract', 'muscle1_extend',
                        'muscle2_contract', 'muscle2_extend',
                        'muscle3_contract', 'muscle3_extend',
                        'muscle4_contract', 'muscle4_extend',
                        'muscle5_contract', 'muscle5_extend',
                        'muscle6_contract', 'muscle6_extend',
                        'muscle7_contract', 'muscle7_extend']

        data = {
            'training_number': self.training_number,
            'generation': self.generation,
            'individual_index': individual_index,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fitness': individual.fitness,
            'distance': individual.distance,
            'stability': individual.stability,
            'energy': individual.energy,
            'time_alive': individual.time_alive,
        }

        for i, name in enumerate(action_names):
            data[f'action_{name}_count'] = action_counts.get(i, 0)
            data[f'action_{name}_percent'] = (action_counts.get(i, 0) / len(individual.genome)) * 100

        df = pd.DataFrame([data])

        if os.path.exists(csv_file):
            df.to_csv(csv_file, mode='a', header=False, index=False, decimal=',', sep=';')
        else:
            df.to_csv(csv_file, mode='w', header=True, index=False, decimal=',', sep=';')

    def save(self, filename='data/fox_ai.pkl'):
        """Sauvegarde l'état de l'algorithme génétique"""
        os.makedirs('data', exist_ok=True)

        data = {
            'population': self.population,
            'generation': self.generation,
            'best_individual': self.best_individual,
            'training_number': self.training_number,
            'parameters': {
                'population_size': self.population_size,
                'genome_length': self.genome_length,
                'mutation_rate': self.mutation_rate,
                'crossover_rate': self.crossover_rate,
                'elite_size': self.elite_size
            }
        }
        with open(filename, 'wb') as f:
            pickle.dump(data, f)

    def load(self, filename='data/fox_ai.pkl'):
        """Charge l'état de l'algorithme génétique"""
        if not os.path.exists(filename):
            return False

        with open(filename, 'rb') as f:
            data = pickle.load(f)

        # ✅ Charger directement le training sauvegardé
        self.population = data['population']
        self.generation = data['generation']
        self.best_individual = data['best_individual']
        self.training_number = data.get('training_number', 1)

        params = data['parameters']
        self.population_size = params['population_size']
        self.genome_length = params['genome_length']
        self.mutation_rate = params['mutation_rate']
        self.crossover_rate = params['crossover_rate']
        self.elite_size = params['elite_size']

        return True

    def _generate_training_summary(self):
        """Génère un fichier de résumé pour chaque training"""
        if not os.path.exists(self.csv_file):
            return

        try:
            df = pd.read_csv(self.csv_file, decimal=',', sep=';')

            summary = []
            for train_num in sorted(df['training_number'].unique()):
                train_df = df[df['training_number'] == train_num]

                summary.append({
                    'training_number': train_num,
                    'total_generations': len(train_df),
                    'start_date': train_df.iloc[0]['generation_start_timestamp'],
                    'end_date': train_df.iloc[-1]['generation_end_timestamp'],
                    'total_duration_seconds': train_df['generation_duration_seconds'].sum(),
                    'avg_generation_duration_seconds': train_df['generation_duration_seconds'].mean(),
                    'first_best_fitness': train_df.iloc[0]['fitness_best'],
                    'final_best_fitness': train_df.iloc[-1]['fitness_best'],
                    'best_fitness_ever': train_df['absolute_best_fitness'].max(),
                    'best_distance_ever': train_df['absolute_best_distance'].max(),
                    'avg_fitness': train_df['fitness_avg'].mean(),
                    'avg_distance': train_df['distance_avg'].mean(),
                    'avg_stability': train_df['stability_avg'].mean(),
                    'avg_energy': train_df['energy_avg'].mean(),
                    'final_time_limit': train_df.iloc[-1]['current_time_limit'],
                })

            summary_df = pd.DataFrame(summary)
            summary_df.to_csv('data/training_summary.csv', index=False, decimal=',', sep=';')

        except Exception as e:
            print(f"⚠️ Erreur lors de la génération du résumé: {e}")

    def print_stats(self):
        """Affiche les statistiques dans la console"""
        if not self.population:
            return

        best = max(self.population, key=lambda x: x.fitness)
        avg = np.mean([ind.fitness for ind in self.population])
        record = self.best_individual.fitness if self.best_individual else 0.0

        print(f"[T{self.training_number}] Gen {self.generation}: "
              f"Best={best.fitness:.2f}, "
              f"Avg={avg:.2f}, "
              f"Record={record:.2f}, "
              f"Time={self.current_time_limit}frames")


class AIController:
    """Contrôleur pour l'IA qui utilise l'algorithme génétique"""

    def __init__(self, genetic_algorithm: GeneticAlgorithm, save_all_individuals: bool = False):
        self.ga = genetic_algorithm
        self.current_individual_index = 0
        self.frame = 0
        self.start_position = None
        self.energy_used = 0
        self.is_stable = True
        self.time_alive = 0
        self.save_all_individuals = save_all_individuals

    def reset_for_individual(self, index: int, start_x: float):
        """Réinitialise pour évaluer un nouvel individu"""
        self.current_individual_index = index
        self.frame = 0
        self.start_position = start_x
        self.energy_used = 0
        self.is_stable = True
        self.time_alive = 0

    def get_current_individual(self) -> Individual:
        """Retourne l'individu actuel"""
        return self.ga.population[self.current_individual_index]

    def get_action_keys(self) -> dict:
        """Retourne l'action à effectuer pour la frame actuelle"""
        individual = self.get_current_individual()
        action = self.ga.get_action(individual, self.frame)

        if action != 0:
            self.energy_used += 1

        self.frame += 1
        self.time_alive += 1

        return self.ga.action_to_keys(action)

    def evaluate_individual(self, current_x: float, is_fallen: bool):
        """Évalue l'individu actuel et retourne True si terminé"""
        individual = self.get_current_individual()

        distance = current_x - self.start_position if self.start_position else 0
        stability = 1.0 if not is_fallen else 0.0

        is_done = is_fallen or self.frame >= self.ga.current_time_limit

        if is_done:
            self.ga.calculate_fitness(
                individual,
                distance,
                stability,
                self.energy_used,
                self.time_alive
            )

            if self.save_all_individuals:
                self.ga.save_individual_stats(self.current_individual_index)

        return is_done

    def next_individual(self) -> bool:
        """Passe à l'individu suivant. Retourne False si c'est le dernier"""
        self.current_individual_index += 1
        return self.current_individual_index < self.ga.population_size

    def is_generation_complete(self) -> bool:
        """Vérifie si tous les individus ont été évalués"""
        return self.current_individual_index >= self.ga.population_size