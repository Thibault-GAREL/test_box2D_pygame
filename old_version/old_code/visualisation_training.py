"""
Script simple pour analyser les données CSV d'entraînement
Affiche uniquement des statistiques textuelles, pas de graphiques
"""

import pandas as pd
import os


def analyze_training_data(csv_file='training_data.csv'):
    """Analyse le fichier CSV des entraînements"""
    if not os.path.exists(csv_file):
        print(f"❌ Fichier {csv_file} non trouvé!")
        return

    df = pd.read_csv(csv_file)

    print("\n" + "=" * 70)
    print("ANALYSE DES DONNÉES D'ENTRAÎNEMENT")
    print("=" * 70)

    # Informations générales
    print(f"\n📊 Informations générales:")
    print(f"   Nombre total de générations: {len(df)}")
    print(f"   Nombre d'entraînements: {df['training_number'].nunique()}")

    # Par entraînement
    print(f"\n📈 Détails par entraînement:")
    for train_num in sorted(df['training_number'].unique()):
        train_df = df[df['training_number'] == train_num]

        print(f"\n   === Training #{train_num} ===")
        print(f"   Générations: {len(train_df)}")
        print(f"   Première date: {train_df.iloc[0]['timestamp']}")
        print(f"   Dernière date: {train_df.iloc[-1]['timestamp']}")

        # Progression du fitness
        first_fitness = train_df.iloc[0]['best_fitness']
        last_fitness = train_df.iloc[-1]['best_fitness']
        best_ever = train_df['absolute_best_fitness'].max()

        print(f"   Premier fitness: {first_fitness:.2f}")
        print(f"   Dernier fitness: {last_fitness:.2f}")
        print(f"   Meilleur fitness absolu: {best_ever:.2f}")
        print(
            f"   Amélioration: {last_fitness - first_fitness:.2f} ({((last_fitness / first_fitness - 1) * 100):.1f}%)")

        # Distance
        best_distance = train_df['absolute_best_distance'].max()
        print(f"   Meilleure distance: {best_distance:.2f}m")

        # Stabilité moyenne
        avg_stability = train_df['avg_stability'].mean()
        print(f"   Stabilité moyenne: {avg_stability:.2f}")

    # Comparaison entre entraînements
    if df['training_number'].nunique() > 1:
        print(f"\n🔄 Comparaison entre entraînements:")
        for train_num in sorted(df['training_number'].unique()):
            train_df = df[df['training_number'] == train_num]
            best = train_df['absolute_best_fitness'].max()
            print(f"   Training #{train_num}: Meilleur fitness = {best:.2f}")

    print("\n" + "=" * 70 + "\n")


def analyze_individuals_data(csv_file='individuals_data.csv'):
    """Analyse le fichier CSV des individus"""
    if not os.path.exists(csv_file):
        print(f"ℹ️  Fichier {csv_file} non trouvé (normal si save_all_individuals=False)")
        return

    df = pd.read_csv(csv_file)

    print("\n" + "=" * 70)
    print("ANALYSE DES INDIVIDUS")
    print("=" * 70)

    print(f"\n📊 Informations générales:")
    print(f"   Nombre total d'individus évalués: {len(df)}")
    print(f"   Entraînements: {df['training_number'].nunique()}")

    # Actions les plus utilisées
    action_cols = [col for col in df.columns if col.startswith('action_') and col.endswith('_percent')]

    print(f"\n🎮 Actions moyennes (tous individus):")
    for col in sorted(action_cols):
        action_name = col.replace('action_', '').replace('_percent', '')
        avg_percent = df[col].mean()
        print(f"   {action_name:10s}: {avg_percent:5.2f}%")

    print("\n" + "=" * 70 + "\n")


def export_summary(csv_file='training_data.csv', output_file='training_summary.csv'):
    """Crée un résumé condensé des entraînements"""
    if not os.path.exists(csv_file):
        print(f"❌ Fichier {csv_file} non trouvé!")
        return

    df = pd.read_csv(csv_file)

    # Créer un résumé par entraînement
    summary = []
    for train_num in sorted(df['training_number'].unique()):
        train_df = df[df['training_number'] == train_num]

        summary.append({
            'training_number': train_num,
            'total_generations': len(train_df),
            'start_date': train_df.iloc[0]['timestamp'],
            'end_date': train_df.iloc[-1]['timestamp'],
            'first_fitness': train_df.iloc[0]['best_fitness'],
            'final_fitness': train_df.iloc[-1]['best_fitness'],
            'best_fitness_ever': train_df['absolute_best_fitness'].max(),
            'best_distance_ever': train_df['absolute_best_distance'].max(),
            'avg_fitness_improvement': train_df['best_fitness'].diff().mean(),
            'avg_stability': train_df['avg_stability'].mean(),
            'avg_energy': train_df['avg_energy'].mean(),
        })

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_file, index=False)
    print(f"✅ Résumé sauvegardé dans: {output_file}")


def main():
    """Fonction principale"""
    print("🦊 ANALYSE DES DONNÉES CSV")

    # Analyser les données d'entraînement
    analyze_training_data('../old_data/training1/training_data.csv')

    # Analyser les données individuelles
    analyze_individuals_data('individuals_data.csv')

    # Créer un résumé
    export_summary('../old_data/training1/training_data.csv', 'old_data/training_summary.csv')


if __name__ == "__main__":
    main()