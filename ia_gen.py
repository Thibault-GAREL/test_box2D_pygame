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
        self.base_time = base_time  # Temps de base (frames)
        self.max_time = max_time  # Temps maximum (frames)
        self.current_time_limit = base_time

        # Configuration du fitness
        self.fitness_config = fitness_config if fitness_config else {
            'distance_weight': 100.0,
            'stability_weight': 50.0,
            'fallen_penalty': -100.0,
            'energy_penalty': 0.1,
            'time_bonus': 0.5
        }

        # Actions possibles (16 actions pour contrôler 8 muscles)
        # 0: rien
        # 1-2: muscle 0 (contract/extend)
        # 3-4: muscle 1 (contract/extend)
        # 5-6: muscle 2 (contract/extend)
        # 7-8: muscle 3 (contract/extend)
        # 9-10: muscle 4 (contract/extend)
        # 11-12: muscle 5 (contract/extend)
        # 13-14: muscle 6 (contract/extend)
        # 15-16: muscle 7 (contract/extend)
        self.num_actions = 17

        self._initialize_population()

    def _get_next_training_number(self):
        """Détermine le numéro d'entraînement suivant"""
        # Créer le dossier data s'il n'existe pas
        os.makedirs('data', exist_ok=True)

        if not os.path.exists(self.csv_file):
            return 1

        try:
            df = pd.read_csv(self.csv_file)
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
        # Retourne quel muscle contrôler et comment
        # Format: {'muscle': numéro (0-7), 'action': 'contract'/'extend'/'relax'}

        if action == 0:
            return {'muscle': None, 'action': 'relax'}

        # Actions 1-16 contrôlent les 8 muscles
        # 1-2: muscle 0, 3-4: muscle 1, etc.
        muscle_index = (action - 1) // 2
        is_contract = (action - 1) % 2 == 0

        return {
            'muscle': muscle_index,
            'action': 'contract' if is_contract else 'extend'
        }

    def calculate_fitness(self, individual: Individual, distance: float,
                          stability: float, energy: float, time_alive: int):
        """
        Calcule le fitness d'un individu selon la configuration
        """
        fitness = 0.0

        # Récompense pour la distance parcourue
        fitness += distance * self.fitness_config['distance_weight']

        # Récompense si stable OU pénalité si tombé
        if stability > 0.5:  # Pas tombé
            fitness += self.fitness_config['stability_weight']
        else:  # Tombé
            fitness += self.fitness_config['fallen_penalty']  # C'est négatif

        # Pénalité pour l'énergie utilisée
        fitness -= energy * self.fitness_config['energy_penalty']

        # Bonus pour le temps de survie
        fitness += time_alive * self.fitness_config['time_bonus']

        individual.fitness = fitness  # Peut être négatif maintenant
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
        # Statistiques avant évolution
        self._save_generation_stats()

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
        # Calculer la distance moyenne de la génération
        avg_distance = np.mean([ind.distance for ind in self.population])
        best_distance = max([ind.distance for ind in self.population])

        # Si l'IA progresse bien, on augmente le temps disponible
        # Formule: temps = base_time + (distance_moyenne * facteur)
        # Plus l'IA va loin, plus elle a de temps pour explorer

        if best_distance > 1.0:  # Si le meilleur a parcouru au moins 1 mètre
            # Augmenter progressivement le temps
            new_time = int(self.base_time + (best_distance * 50))
            self.current_time_limit = min(new_time, self.max_time)
        else:
            # Rester au temps de base
            self.current_time_limit = self.base_time

        # Mettre à jour genome_length pour la prochaine génération
        self.genome_length = self.current_time_limit

    def _save_generation_stats(self):
        """Sauvegarde les statistiques de la génération dans le CSV"""
        fitnesses = [ind.fitness for ind in self.population]
        distances = [ind.distance for ind in self.population]
        stabilities = [ind.stability for ind in self.population]
        energies = [ind.energy for ind in self.population]
        times_alive = [ind.time_alive for ind in self.population]

        best_ind = max(self.population, key=lambda x: x.fitness)
        worst_ind = min(self.population, key=lambda x: x.fitness)

        data = {
            'training_number': self.training_number,
            'generation': self.generation,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'best_fitness': best_ind.fitness,
            'worst_fitness': worst_ind.fitness,
            'avg_fitness': np.mean(fitnesses),
            'median_fitness': np.median(fitnesses),
            'std_fitness': np.std(fitnesses),
            'best_distance': best_ind.distance,
            'avg_distance': np.mean(distances),
            'median_distance': np.median(distances),
            'best_stability': best_ind.stability,
            'avg_stability': np.mean(stabilities),
            'best_energy': best_ind.energy,
            'avg_energy': np.mean(energies),
            'best_time_alive': best_ind.time_alive,
            'avg_time_alive': np.mean(times_alive),
            'absolute_best_fitness': self.best_individual.fitness if self.best_individual else 0,
            'absolute_best_distance': self.best_individual.distance if self.best_individual else 0,
            'population_size': self.population_size,
            'genome_length': self.genome_length,
            'current_time_limit': self.current_time_limit,
            'mutation_rate': self.mutation_rate,
            'crossover_rate': self.crossover_rate,
            'elite_size': self.elite_size
        }

        df = pd.DataFrame([data])

        if os.path.exists(self.csv_file):
            df.to_csv(self.csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(self.csv_file, mode='w', header=True, index=False)

    def save_individual_stats(self, individual_index: int):
        """Sauvegarde les statistiques d'un individu spécifique"""
        # Créer le dossier data s'il n'existe pas
        os.makedirs('data', exist_ok=True)

        csv_file = 'data/individuals_data.csv'

        individual = self.population[individual_index]

        unique, counts = np.unique(individual.genome, return_counts=True)
        action_counts = dict(zip(unique, counts))

        # Noms des actions pour les 8 muscles
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
            df.to_csv(csv_file, mode='a', header=False, index=False)
        else:
            df.to_csv(csv_file, mode='w', header=True, index=False)

    def save(self, filename='data/fox_ai.pkl'):
        """Sauvegarde l'état de l'algorithme génétique"""
        # Créer le dossier data s'il n'existe pas
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

        # Récupérer le training_number de la sauvegarde
        saved_training_number = data.get('training_number', 1)

        # Si le training_number actuel est différent, c'est un nouvel entraînement
        # Dans ce cas, on ne charge PAS la génération (on repart de 0)
        if saved_training_number != self.training_number:
            # Nouvel entraînement : on garde generation = 0 et on ne charge rien d'autre
            print(f"   Nouvel entraînement détecté (Training #{self.training_number})")
            return False

        # Même training_number : on continue l'entraînement existant
        self.population = data['population']
        self.generation = data['generation']
        self.best_individual = data['best_individual']
        self.training_number = saved_training_number

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
            df = pd.read_csv(self.csv_file)

            # Créer un résumé par training
            summary = []
            for train_num in sorted(df['training_number'].unique()):
                train_df = df[df['training_number'] == train_num]

                summary.append({
                    'training_number': train_num,
                    'total_generations': len(train_df),
                    'start_date': train_df.iloc[0]['timestamp'],
                    'end_date': train_df.iloc[-1]['timestamp'],
                    'first_best_fitness': train_df.iloc[0]['best_fitness'],
                    'final_best_fitness': train_df.iloc[-1]['best_fitness'],
                    'best_fitness_ever': train_df['absolute_best_fitness'].max(),
                    'best_distance_ever': train_df['absolute_best_distance'].max(),
                    'avg_fitness': train_df['avg_fitness'].mean(),
                    'avg_distance': train_df['avg_distance'].mean(),
                    'avg_stability': train_df['avg_stability'].mean(),
                    'avg_energy': train_df['avg_energy'].mean(),
                    'final_time_limit': train_df.iloc[-1]['current_time_limit'],
                })

            summary_df = pd.DataFrame(summary)
            summary_df.to_csv('data/training_summary.csv', index=False)

        except Exception as e:
            print(f"⚠️  Erreur lors de la génération du résumé: {e}")

    def print_stats(self):
        """Affiche les statistiques dans la console"""
        if not self.population:
            return

        best = max(self.population, key=lambda x: x.fitness)
        avg = np.mean([ind.fitness for ind in self.population])
        record = self.best_individual.fitness if self.best_individual else 0.0

        print(f"[T{self.training_number}] Gen {self.generation}: "
              f"Best={best.fitness:.2f}m, "
              f"Avg={avg:.2f}m, "
              f"Record={record:.2f}m, "
              f"Time={self.current_time_limit}frames")

    def _generate_training_summary(self):
        """Génère un fichier de résumé pour chaque training"""
        if not os.path.exists(self.csv_file):
            return

        try:
            df = pd.read_csv(self.csv_file)

            # Créer un résumé par training
            summary = []
            for train_num in sorted(df['training_number'].unique()):
                train_df = df[df['training_number'] == train_num]

                summary.append({
                    'training_number': train_num,
                    'total_generations': len(train_df),
                    'start_date': train_df.iloc[0]['timestamp'],
                    'end_date': train_df.iloc[-1]['timestamp'],
                    'first_best_fitness': train_df.iloc[0]['best_fitness'],
                    'final_best_fitness': train_df.iloc[-1]['best_fitness'],
                    'best_fitness_ever': train_df['absolute_best_fitness'].max(),
                    'best_distance_ever': train_df['absolute_best_distance'].max(),
                    'avg_fitness': train_df['avg_fitness'].mean(),
                    'avg_distance': train_df['avg_distance'].mean(),
                    'avg_stability': train_df['avg_stability'].mean(),
                    'avg_energy': train_df['avg_energy'].mean(),
                    'final_time_limit': train_df.iloc[-1]['current_time_limit'],
                })

            summary_df = pd.DataFrame(summary)
            summary_df.to_csv('data/training_summary.csv', index=False)

        except Exception as e:
            print(f"⚠️  Erreur lors de la génération du résumé: {e}")


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

        # Terminer si tombé OU si on atteint la limite de temps actuelle
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