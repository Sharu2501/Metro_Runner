import networkx as nx
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Metro Surfer",
    page_icon="images/MetroSurfer.png"
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
    # Exemple : on ajoute une arête entre des stations choisies pour rendre le graphe connexe
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

def prim(graphe):
    """
    Implémente l'algorithme de Prim pour calculer l'ACPM.
    Args:
        graphe (nx.Graph): Graphe non orienté avec des poids sur les arêtes.
    Returns:
        nx.Graph: L'arbre couvrant de poids minimum.
    """
    from heapq import heappop, heappush

    acpm = nx.Graph()  # Graphe pour stocker l'ACPM
    visites = set()  # Ensemble des nœuds visités
    liaisons = []  # Min-heap pour gérer les arêtes

    # Choisir un nœud de départ
    start_node = next(iter(graphe.nodes))
    visites.add(start_node)

    # Ajouter les arêtes du nœud de départ dans le tas
    for neighbor, attributes in graphe[start_node].items():
        heappush(liaisons, (attributes['weight'], start_node, neighbor))

    while liaisons:
        weight, x, y = heappop(liaisons)  # Extraire l'arête de poids minimum
        if y not in visites:
            # Ajouter l'arête à l'ACPM
            acpm.add_edge(x, y, weight=weight)
            visites.add(y)

            # Ajouter les nouvelles arêtes accessibles depuis y
            for neighbor, attributes in graphe[y].items():
                if neighbor not in visites:
                    heappush(liaisons, (attributes['weight'], y, neighbor))

    return acpm

def display_route_info(chemin, stations, terminus):
    """
    Affiche les instructions pour l'itinéraire calculé en mentionnant les changements de ligne
    avec le terminus basé sur le sens du trajet.
    """
    route_instructions = []
    ligne_precedente = None
    terminus_direction = None

    for i in range(len(chemin) - 1):
        # Station actuelle et suivante
        current_station_id = chemin[i]
        next_station_id = chemin[i + 1]
        current_station = stations[current_station_id]
        next_station = stations[next_station_id]

        current_line = current_station['ligne_numero']

        if ligne_precedente != current_line:
            # Changement de ligne, déterminer le terminus basé sur le sens du déplacement
            ligne_terminus = terminus[current_line]
            current_name = current_station['station_nom']
            next_name = next_station['station_nom']

            # Si le terminus de la ligne existe, choisir celui vers lequel on se dirige
            if next_name in ligne_terminus:
                terminus_direction = next_name
            else:
                # Sinon, choisir l'autre terminus comme direction
                terminus_direction = (
                    ligne_terminus[1] if ligne_terminus[0] == current_name else ligne_terminus[0]
                )

            route_instructions.append(
                f"Prenez la ligne {current_line}, direction {terminus_direction}."
            )

        ligne_precedente = current_line

    # Ajouter la dernière station
    last_station = stations[chemin[-1]]
    route_instructions.append(f"Descendez à {last_station['station_nom']}.")

    return "\n".join(route_instructions)



# -------------------------------
# Visualisation graphique
# -------------------------------
LINE_COLORS = {
    "1": "blue", "2": "green", "3": "red","3bis": "olive", "4": "violet", "5": "orange",
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

def format_temps(minutes_float):
    """Convertit un temps en minutes (float) au format minutes:secondes."""
    minutes = int(minutes_float)
    secondes = round((minutes_float - minutes) * 60)
    return f"{minutes} min {secondes} sec"


# -------------------------------
# Interface utilisateur
# -------------------------------
st.title("Metro Surfer : Votre guide interactif du métro :)")
st.sidebar.title("Me déplacer")

# Charger les données
stations, terminus = recup_stations('data/station.txt')
liaisons = recup_laisons('data/liaison.txt')
positions = recup_positions('data/pospoints.txt')
metro_graphe = construire_graphe(stations, liaisons)

# Créer le dictionnaire des noms
station_noms = {id: info['station_nom'] for id, info in stations.items()}

# Enlever les doublons dans la liste des stations
station_unique = ["Aucune sélection"] + list(set(station_noms.values()))

# Ajout d'un conteneur pour gérer l'inversion des stations
with st.sidebar:
    st.subheader("Sélectionnez les stations")
    # Initialisation des stations sélectionnées
    if "depart_station" not in st.session_state:
        st.session_state.depart_station = "Aucune sélection"
    if "arrivee_station" not in st.session_state:
        st.session_state.arrivee_station = "Aucune sélection"

    # Composants de sélection
    depart_station_nom = st.selectbox("Station de départ", station_unique, key="depart_station")
    arrivee_station_nom = st.selectbox("Station d’arrivée", station_unique, key="arrivee_station")

    # Bouton pour inverser les stations
    if st.button("🔄 Inverser"):
    # Inverser les stations dans session_state
        st.session_state.depart_station, st.session_state.arrivee_station = st.session_state.arrivee_station, st.session_state.depart_station


# Vérifier que les stations sont différentes
if depart_station_nom == "Aucune sélection" or arrivee_station_nom == "Aucune sélection":
    st.error("Veuillez sélectionner une station de départ et une station d’arrivée.")
elif depart_station_nom == arrivee_station_nom:
    st.error("La station de départ doit être différente de la station d’arrivée.")
else:
    try:
        deb_station = [id for id, name in station_noms.items() if name == depart_station_nom][0]
        fin_station = [id for id, name in station_noms.items() if name == arrivee_station_nom][0]
    except IndexError:
        st.error("Station non trouvée. Veuillez vérifier les données.")

    # Calcul du plus court chemin
    if st.sidebar.button("Calculer le plus court chemin"):
        temps, chemin = bellman_ford(metro_graphe, deb_station, fin_station)
        if chemin:
            # Formatage du temps
            temps_formatte = format_temps(temps)
            st.write(f"Durée estimée : {temps_formatte}")
            route_info = display_route_info(chemin, stations, terminus)
            st.write(route_info)

            # Affichage du trajet sur la carte interactive
            fig = plot_metro(metro_graphe, stations, positions, chemin=chemin, titre="Plus Court Chemin")
            st.plotly_chart(fig)
        else:
            st.write("Aucun chemin trouvé entre les stations.")


# Calcul et affichage de l'ACPM pour tout le graphe
if st.sidebar.button("Afficher l'ACPM"):
    acpm_prim = prim(metro_graphe)
    fig_acpm_prim = plot_metro(acpm_prim, stations, positions, titre="Arbre Couvrant de Poids Minimum (Prim)")
    fig_acpm_prim.update_layout(
        height=500,
        autosize=False,
        width=1500,
    )
    st.plotly_chart(fig_acpm_prim)

acpm_methode = st.sidebar.radio(
    "Choisissez l'algorithme pour l'ACPM :",
    options=["Prim", "NetworkX"]
)

if acpm_methode == "Prim":
    acpm_prim = prim(metro_graphe)
    fig_acpm_prim = plot_metro(acpm_prim, stations, positions, titre="ACPM avec Prim")
    st.plotly_chart(fig_acpm_prim)
else:
    acpm_networkx = nx.minimum_spanning_tree(metro_graphe, weight='weight')
    fig_acpm_networkx = plot_metro(acpm_networkx, stations, positions, titre="ACPM avec Kruskal")
    st.plotly_chart(fig_acpm_networkx)

# Affichage de la légende des lignes
st.sidebar.subheader("Légende des lignes")
for ligne_numero, couleur in LINE_COLORS.items():
    st.sidebar.markdown(
        f"<div style='display: inline-block; margin-right: 10px;'>"
        f"<div style='width: 20px; height: 20px; background-color: {couleur}; display: inline-block;'></div>"
        f"</div><span style='vertical-align: top; margin-left: 10px;'>Ligne {ligne_numero}</span>",
        unsafe_allow_html=True
    )
