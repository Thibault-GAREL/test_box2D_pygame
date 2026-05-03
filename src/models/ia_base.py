"""
Module de base pour toutes les intelligences artificielles.
Définit l'interface commune que toutes les IA doivent implémenter.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json


class IABase(ABC):
    """
    Classe abstraite de base pour toutes les intelligences artificielles.

    Architecture:
    - Chaque IA doit hériter de cette classe
    - Les méthodes abstraites DOIVENT être implémentées
    - Les méthodes concrètes peuvent être surchargées si besoin

    Attributs:
        config: Configuration de l'IA (POPULATION_SIZE, MUTATION_RATE, etc.)
        generation: Numéro de génération actuelle
        best_distance: Meilleure distance parcourue
        current_individual: Index de l'individu actuellement testé
    """

    def __init__(self, config):
        """
        Initialise l'IA avec sa configuration.

        Args:
            config: Objet de configuration (ex: ConfigIA)
        """
        self.config = config
        self.generation = 0
        self.best_distance = 0.0
        self.current_individual = 0

    # ========== MÉTHODES ABSTRAITES (OBLIGATOIRES) ==========

    @abstractmethod
    def get_action(self, time: float, dog_state: Dict[str, Any]) -> List[float]:
        """
        Calcule les activations musculaires pour le temps donné.

        Args:
            time: Temps écoulé depuis le début de l'épisode (en secondes)
            dog_state: État du chien (position, vitesse, angles, etc.)
                      Format: {
                          'position': (x, y),
                          'velocity': (vx, vy),
                          'angle': float,
                          'joints_angles': [angle1, angle2, ...]
                      }

        Returns:
            Liste des activations musculaires [0.0 - 1.0] pour chaque muscle
            Longueur = nombre de muscles du chien
        """
        pass

    @abstractmethod
    def on_episode_end(self, distance: float, time_survived: float, dog_state: Dict[str, Any]):
        """
        Appelée à la fin d'un épisode pour mettre à jour l'IA.

        Args:
            distance: Distance parcourue par le chien (en mètres)
            time_survived: Temps de survie (en secondes)
            dog_state: État final du chien
        """
        pass

    @abstractmethod
    def should_reset_simulation(self) -> bool:
        """
        Détermine si la simulation doit être réinitialisée.

        Returns:
            True si un nouvel individu doit être testé (reset simulation)
            False si on continue avec le même individu
        """
        pass

    @abstractmethod
    def save(self, filepath: str):
        """
        Sauvegarde le modèle de l'IA.

        Args:
            filepath: Chemin du fichier de sauvegarde
        """
        pass

    @abstractmethod
    def load(self, filepath: str):
        """
        Charge un modèle d'IA sauvegardé.

        Args:
            filepath: Chemin du fichier à charger
        """
        pass

    # ========== MÉTHODES CONCRÈTES (OPTIONNELLES) ==========

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques actuelles de l'IA.
        Peut être surchargée pour ajouter des stats spécifiques.

        Returns:
            Dictionnaire avec les statistiques
        """
        return {
            'generation': self.generation,
            'best_distance': self.best_distance,
            'current_individual': self.current_individual,
            'ia_type': self.__class__.__name__
        }

    def on_generation_start(self):
        """
        Appelée au début d'une nouvelle génération.
        Peut être surchargée pour initialiser des variables.
        """
        pass

    def on_generation_end(self):
        """
        Appelée à la fin d'une génération.
        Peut être surchargée pour faire des logs, sauvegardes, etc.
        """
        pass

    def reset_episode(self):
        """
        Réinitialise les variables liées à l'épisode actuel.
        Peut être surchargée si besoin de réinitialisation spécifique.
        """
        pass

    def _save_metadata(self, filepath: str, additional_data: Optional[Dict] = None):
        """
        Sauvegarde les métadonnées communes à toutes les IA.
        Méthode utilitaire pour les classes filles.

        Args:
            filepath: Chemin du fichier de métadonnées
            additional_data: Données supplémentaires à sauvegarder
        """
        metadata = {
            'ia_type': self.__class__.__name__,
            'generation': self.generation,
            'best_distance': self.best_distance,
            'config': {
                'POPULATION_SIZE': self.config.GA_CONFIG['population_size'],
                'MUTATION_RATE': getattr(self.config, 'MUTATION_RATE', None),
            }
        }

        if additional_data:
            metadata.update(additional_data)

        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_metadata(self, filepath: str) -> Dict[str, Any]:
        """
        Charge les métadonnées communes.
        Méthode utilitaire pour les classes filles.

        Args:
            filepath: Chemin du fichier de métadonnées

        Returns:
            Dictionnaire des métadonnées
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    def __repr__(self):
        """Représentation textuelle de l'IA."""
        return f"{self.__class__.__name__}(gen={self.generation}, best={self.best_distance:.2f}m)"