# -------------------------------
# Chargement des données
# -------------------------------
def recup_stations(chemin_fichier):
    """Charge les stations depuis un fichier formaté en un dictionnaire."""
    stations = {}
    terminus = {}  # Pour stocker les terminus de chaque ligne
    with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            if not ligne:
                continue
            try:
                main_part, terminus_part = ligne.split(';')
                main_parts = main_part.split(maxsplit=2)
                station_code = main_parts[0]
                station_numero = int(main_parts[1])  # Identifiant unique de la station
                station_nom, ligne_numero = main_parts[2].rsplit(maxsplit=1)

                terminus_parts = terminus_part.split()
                est_terminus = terminus_parts[0].lower() == 'true'
                direction_numero = int(terminus_parts[1])  # 0, 1, 2... pour le branchement
                terminus_nom = terminus_parts[2] if len(terminus_parts) > 2 else None  # Nom du terminus si spécifié

                # Stocker les terminus pour chaque ligne
                if est_terminus and ligne_numero not in terminus:
                    terminus[ligne_numero] = [station_nom]  # Si c'est le premier terminus pour cette ligne
                elif est_terminus:
                    terminus[ligne_numero].append(station_nom)  # Si c'est le second terminus pour cette ligne

                stations[station_numero] = {
                    'station_code': station_code,
                    'station_nom': station_nom,
                    'ligne_numero': ligne_numero,  # Ligne conservée comme texte (peut être "7bis")
                    'est_terminus': est_terminus,
                    'direction_numero': direction_numero,
                    'terminus_nom': terminus_nom,  # Nom du terminus pour cette station
                }
            except Exception as e:
                print(f"Erreur lors de l'analyse de la ligne : {ligne}\n{e}")
    return stations, terminus


def recup_laisons(chemin_fichier):
    """Charge les arêtes (connexions) depuis un fichier formaté en une liste."""
    laisons = []
    with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
        for ligne in fichier:
            if ligne.startswith("E"):
                parts = ligne.strip().split()
                x = int(parts[1])
                y = int(parts[2])
                temps = int(parts[3])  # Temps en secondes
                laisons.append((x, y, temps))
    return laisons


def recup_positions(chemin_fichier):
    """Charge les coordonnées des stations depuis pospoints.txt et applique un facteur d'agrandissement."""
    scale_factor = 5
    positions = {}
    with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
        for ligne in fichier:
            x, y, name = ligne.strip().split(';')
            positions[name.replace('@', ' ')] = (int(x) * scale_factor, int(y) * scale_factor)
    return positions