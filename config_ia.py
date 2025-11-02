# config_ia.py
"""Configuration pour l'entraînement de l'IA"""

# ============ OPTIONS PRINCIPALES ============

# Mode de contrôle
HUMAN_CONTROL = False  # True = contrôle humain, False = contrôle IA

# Affichage
DISPLAY_ENABLED = False  # True = afficher l'écran, False = mode rapide sans affichage

# ============ PARAMÈTRES DE L'ALGORITHME GÉNÉTIQUE ============

GA_CONFIG = {
    'population_size': 50,  # Nombre d'individus par génération
    'genome_length': 500,  # Temps de base (frames) - sera adapté automatiquement
    'mutation_rate': 0.1,  # Taux de mutation (0.0 à 1.0)
    'crossover_rate': 0.7,  # Taux de croisement (0.0 à 1.0)
    'elite_size': 5,  # Nombre d'élites conservés
    'csv_file': 'data/training_data.csv',  # Fichier CSV pour les données

    # Temps adaptatif
    'adaptive_time': True,  # True = le temps augmente avec les performances
    'base_time': 500,  # Temps de départ (frames)
    'max_time': 2000,  # Temps maximum (frames)
}

# ============ PARAMÈTRES D'ENTRAÎNEMENT ============

TRAINING_CONFIG = {
    'max_generations': 100,  # Nombre maximum de générations par training
    'save_every': 5,  # Sauvegarder tous les N générations
    'save_file': 'data/fox_ai.pkl',  # Fichier de sauvegarde
    'max_frames_per_individual': 500,  # Durée max d'évaluation
    'speed_multiplier': 10 if not DISPLAY_ENABLED else 1,  # Vitesse en mode rapide
    'save_all_individuals': False,  # True = sauvegarder chaque individu dans individuals_data.csv

    # Continuer automatiquement vers le prochain training
    'auto_continue': True,  # True = passe au training suivant, False = s'arrête
    'max_trainings': None,  # Nombre max de trainings (None = illimité)
}

# ============ CRITÈRES DE FITNESS ============

FITNESS_CONFIG = {
    'distance_weight': 100.0,  # Récompense pour la distance parcourue (en mètres)
    'stability_weight': 50.0,  # Récompense si pas retourné (bonus)
    'fallen_penalty': -100.0,  # Pénalité si retourné (négatif)
    'energy_penalty': 0.1,  # Pénalité pour chaque action utilisée
    'time_bonus': 0.5,  # Bonus pour chaque frame de survie
}

# Formule du fitness:
# Fitness = (distance × distance_weight)
#         + (stability × stability_weight) OU (fallen_penalty si tombé)
#         - (energy × energy_penalty)
#         + (time_alive × time_bonus)

# ============ AFFICHAGE CONSOLE ============

STATS_CONFIG = {
    'print_every': 1,  # Afficher stats tous les N générations
    'show_progress': True  # Afficher progression pendant entraînement
}