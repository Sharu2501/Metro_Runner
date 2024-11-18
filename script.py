import networkx as nx
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Metro Surfer",
    page_icon="data/MetroSurfer.png"
)

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

# -------------------------------
# Construction du graphe
# -------------------------------
import networkx as nx

def verifie_connexite(graphe):
    """Vérifie si le graphe est connexe en utilisant le parcours en profondeur."""
    if not graphe.nodes:
        return True  # Un graphe sans nœuds est connexe

    # On commence la recherche en profondeur à partir d'un nœud
    depart_node = next(iter(graphe.nodes))

    # Utilisation du parcours en profondeur pour parcourir tous les nœuds accessibles
    visites = set()

    def dfs(node):
        visites.add(node)
        for voisin in graphe.neighbors(node):
            if voisin not in visites:
                dfs(voisin)

    # Faire le parcours en profondeur depuis le premier nœud
    dfs(depart_node)

    # Si tous les nœuds ont été visités, le graphe est connexe
    return len(visites) == len(graphe.nodes)

def ajoute_liaisons_manquantes(graphe, stations, liaisons):
    """Ajoute des arêtes pour rendre le graphe connexe si nécessaire."""
    if verifie_connexite(graphe):
        return graphe

    # Si le graphe n'est pas connexe, on ajoute des arêtes manquantes
    # On peut ajouter des arêtes entre stations non connectées
    # Exemple : on ajouter une arête entre des stations choisies pour rendre le graphe connexe
    for x in stations:
        for y in stations:
            if not graphe.has_edge(x, y):
                graphe.add_edge(x, y, weight=20)  # Ajout d'une arête avec un temps de 20s
    return graphe

def construire_graphe(stations, liaisons):
    """Construit un graphe NetworkX à partir des stations et des arêtes."""
    graphe = nx.Graph()
    for station_id, info in stations.items():
        graphe.add_node(station_id, **info)
    for x, y, temps in liaisons:
        graphe.add_edge(x, y, weight=temps / 60)    # conversion du temps en minutes
    return graphe

def bellman_ford(graphe, depart, arrivee):
    """Calcule le plus court chemin entre source et target avec l'algorithme de Bellman-Ford."""
    # Initialisation des distances
    distances = {node: float('inf') for node in graphe.nodes}
    distances[depart] = 0  # la distance du nœud départ à lui-même vaut 0
    predecesseurs = {node: None for node in graphe.nodes}  # Pour reconstruire le chemin

    # Étape 1 : Relaxation des arêtes, N-1 fois (N est le nombre de nœuds)
    for _ in range(len(graphe.nodes) - 1):
        for x, y, data in graphe.edges(data=True):
            temps = data['weight']  # Poids de l'arête, le temps
            if distances[x] + temps < distances[y]:
                distances[y] = distances[x] + temps
                predecesseurs[y] = x
            if distances[y] + temps < distances[x]:
                distances[x] = distances[y] + temps
                predecesseurs[x] = y

    # Vérification des cycles de poids négatifs
    for x, y, data in graphe.edges(data=True):
        temps = data['weight']
        if distances[x] + temps < distances[y]:
            raise ValueError("Le graphe contient un cycle de poids négatif")
        if distances[y] + temps < distances[x]:
            raise ValueError("Le graphe contient un cycle de poids négatif")

    # Étape 2 : Reconstruction du chemin le plus court
    chemin = []
    node_actuel = arrivee
    while node_actuel is not None:
        chemin.append(node_actuel)
        node_actuel = predecesseurs[node_actuel]

    chemin.reverse()  # Inverser le chemin pour obtenir la direction correcte

    # Si la distance au nœud d'arrivée est infinie, il n'y a pas de chemin
    if distances[arrivee] == float('inf'):
        return None, None

    return distances[arrivee], chemin



def display_route_info(chemin, stations, terminus):
    """Affiche les instructions pour l'itinéraire calculé en ne mentionnant que les changements de ligne avec le terminus."""
    route_instructions = []
    ligne_precedente = None
    direction_precedente = None

    for station_id in chemin:
        station = stations[station_id]
        ligne_numero = station['ligne_numero']
        direction_numero = station['direction_numero']

        if ligne_precedente != ligne_numero:
            # On cherche le terminus en fonction du branchement
            if direction_numero == 0:
                route_instructions.append(f"Changez de ligne et prenez la {ligne_numero}, direction {terminus[ligne_numero][1]}.")
            elif direction_numero == 1:
                route_instructions.append(f"Changez de ligne et prenez la {ligne_numero}, direction {terminus[ligne_numero][0]}.")
            else:
                route_instructions.append(f"Changez de ligne et prenez la {ligne_numero}, direction {terminus[ligne_numero][1]}.")

        ligne_precedente = ligne_numero
        direction_precedente = direction_numero

    return "\n".join(route_instructions)


# -------------------------------
# Visualisation graphique
# -------------------------------
LINE_COLORS = {
    "1": "blue", "2": "green", "3": "red","3bis": "olive", "4": "purple", "5": "orange",
    "6": "pink", "7": "brown", "7bis": "lightblue", "8": "yellow",
    "9": "cyan", "10": "lime", "11": "gray", "12": "gold",
    "13": "darkblue", "14": "darkred"
}

def plot_metro(graphe, stations, positions, chemin=None, titre="Carte du métro"):
    """
    Affiche une carte interactive avec Plotly, avec un zoom autour du chemin rouge si donné.

    Args:
        graphe (nx.Graph): Le graphe du métro.
        stations (dict): Dictionnaire des stations.
        positions (dict): Coordonnées des stations.
        chemin (list, optional): Chemin le plus court (liste des nœuds). Default: None.
        titre (str): Le titre de la carte.
    """
    fig = go.Figure()

    # Ajouter les arêtes
    for u, v, data in graphe.edges(data=True):
        x_coords = [positions[stations[u]['station_nom']][0], positions[stations[v]['station_nom']][0]]
        y_coords = [positions[stations[u]['station_nom']][1], positions[stations[v]['station_nom']][1]]
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords, mode='lines',
            line=dict(color='gray', width=1), hoverinfo='none'
        ))

    # Ajouter les nœuds
    for station_id, data in stations.items():
        if data['station_nom'] in positions:
            x, y = positions[data['station_nom']]
            line_color = LINE_COLORS.get(data['ligne_numero'], "black")  # Couleur par ligne
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode='markers+text',
                text=[data['station_nom']],
                textposition='top right',
                marker=dict(size=10, color=line_color),
                hoverinfo='text'
            ))

    # Ajouter le chemin le plus court
    if chemin:
        # Calculer les coordonnées du chemin
        chemin_x = []
        chemin_y = []
        for i in range(len(chemin) - 1):
            u, v = chemin[i], chemin[i + 1]
            x_coords = [positions[stations[u]['station_nom']][0], positions[stations[v]['station_nom']][0]]
            y_coords = [positions[stations[u]['station_nom']][1], positions[stations[v]['station_nom']][1]]
            chemin_x.extend(x_coords)
            chemin_y.extend(y_coords)
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords, mode='lines',
                line=dict(color='red', width=3), hoverinfo='none'
            ))

        # Ajuster les limites de la carte autour du chemin
        x_min, x_max = min(chemin_x), max(chemin_x)
        y_min, y_max = min(chemin_y), max(chemin_y)

        # Ajouter un petit padding autour du chemin
        padding_factor = 0.1  # 10% de marge autour du chemin
        x_range = [x_min - (x_max - x_min) * padding_factor, x_max + (x_max - x_min) * padding_factor]
        y_range = [y_min - (y_max - y_min) * padding_factor, y_max + (y_max - y_min) * padding_factor]

        # Appliquer les limites de zoom
        fig.update_layout(
            title=titre,
            xaxis=dict(range=x_range, visible=False),
            yaxis=dict(range=y_range, visible=False),
            showlegend=False,
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0),
        )
    else:
        # Si aucun chemin, afficher la carte entière
        fig.update_layout(
            title=titre,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0),
        )

    return fig


# -------------------------------
# Interface utilisateur
# -------------------------------
st.title("Metro Surfer :  Votre guide interactif du métro")
st.sidebar.title("Me déplacer")

# Charger les données
stations, terminus = recup_stations('data/station.txt')
liaisons = recup_laisons('data/liaison.txt')
positions = recup_positions('data/pospoints.txt')
metro_graphe = construire_graphe(stations, liaisons)

# Créer le dictionnaire des noms
station_noms = {id: info['station_nom'] for id, info in stations.items()}

# Enlever les doublons dans la liste des stations
station_unique = list(set(station_noms.values()))

# Sélection des stations de départ et d'arrivée
depart_station_nom = st.sidebar.selectbox("Station de départ", station_unique)
arrivee_station_nom = st.sidebar.selectbox("Station d’arrivée", station_unique)

# Valider les indices
try:
    deb_station = [id for id, name in station_noms.items() if name == depart_station_nom][0]
    fin_station = [id for id, name in station_noms.items() if name == arrivee_station_nom][0]
except IndexError:
    st.error("Station non trouvée. Veuillez vérifier les données.")

# Calcul du plus court chemin
if st.sidebar.button("Calculer le plus court chemin"):
    temps, chemin = bellman_ford(metro_graphe, deb_station, fin_station)
    if chemin:
        st.write(f"Durée estimée : {temps:.2f} minutes")
        route_info = display_route_info(chemin, stations, terminus)
        st.write(route_info)

        # Affichage du trajet sur la carte interactive
        fig = plot_metro(metro_graphe, stations, positions, chemin=chemin, titre="Plus Court Chemin")
        st.plotly_chart(fig)
    else:
        st.write("Aucun chemin trouvé entre les stations.")


# Calcul et affichage de l'ACPM pour tout le graphe
if st.sidebar.button("Afficher l'ACPM de tout le graphe"):
    acpm = nx.minimum_spanning_tree(metro_graphe, weight='temps')
    fig_acpm = plot_metro(acpm, stations, positions, titre="Arbre Couvrant de Poids Minimum (ACPM)")
    fig_acpm.update_layout(
        height=500,
        autosize=False,
        width=1500,
        title="Arbre Couvrant de Poids Minimum (ACPM)"
    )

    st.plotly_chart(fig_acpm)

# Affichage de la légende des lignes
st.sidebar.subheader("Légende des lignes")
for ligne_numero, couleur in LINE_COLORS.items():
    st.sidebar.markdown(
        f"<div style='display: inline-block; margin-right: 10px;'>"
        f"<div style='width: 20px; height: 20px; background-color: {couleur}; display: inline-block;'></div>"
        f"</div><span style='vertical-align: top; margin-left: 10px;'>Ligne {ligne_numero}</span>",
        unsafe_allow_html=True
    )
