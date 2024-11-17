import networkx as nx
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(
    page_title="Metro Surfer",
    page_icon="MetroSurfer.png"
)

# -------------------------------
# Chargement des données
# -------------------------------
def load_stations(file_path):
    """Charge les stations depuis un fichier formaté en un dictionnaire."""
    stations = {}
    terminus = {}  # Pour stocker les terminus de chaque ligne
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                main_part, terminus_part = line.split(';')
                main_parts = main_part.split(maxsplit=2)
                station_code = main_parts[0]
                station_number = int(main_parts[1])  # Identifiant unique de la station
                station_name, line_number = main_parts[2].rsplit(maxsplit=1)

                terminus_parts = terminus_part.split()
                is_terminus = terminus_parts[0].lower() == 'true'
                direction_number = int(terminus_parts[1])  # 0, 1, 2 pour le branchement
                terminus_name = terminus_parts[2] if len(terminus_parts) > 2 else None  # Nom du terminus si spécifié

                # Stocker les terminus pour chaque ligne
                if is_terminus and line_number not in terminus:
                    terminus[line_number] = [station_name]  # Si c'est le premier terminus pour cette ligne
                elif is_terminus:
                    terminus[line_number].append(station_name)  # Si c'est le second terminus pour cette ligne

                stations[station_number] = {
                    'station_code': station_code,
                    'station_name': station_name,
                    'line_number': line_number,  # Ligne conservée comme texte (peut être "7bis")
                    'is_terminus': is_terminus,
                    'direction_number': direction_number,
                    'terminus_name': terminus_name,  # Nom du terminus pour cette station
                }
            except Exception as e:
                print(f"Erreur lors de l'analyse de la ligne : {line}\n{e}")
    return stations, terminus



def load_edges(file_path):
    """Charge les arêtes (connexions) depuis un fichier formaté en une liste."""
    edges = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith("E"):
                parts = line.strip().split()
                u = int(parts[1])
                v = int(parts[2])
                weight = int(parts[3])  # Temps en secondes
                edges.append((u, v, weight))
    return edges


def load_positions(file_path):
    """Charge les coordonnées des stations depuis pospoints.txt et applique un facteur d'agrandissement."""
    scale_factor = 5
    positions = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            x, y, name = line.strip().split(';')
            positions[name.replace('@', ' ')] = (int(x) * scale_factor, int(y) * scale_factor)
    return positions


# -------------------------------
# Construction du graphe
# -------------------------------
import networkx as nx

def verifie_connexite(graph):
    """Vérifie si le graphe est connexe en utilisant le parcours en profondeur."""
    if not graph.nodes:
        return True  # Un graphe sans nœuds est connexe

    # On commence la recherche en profondeur à partir d'un nœud arbitraire
    start_node = next(iter(graph.nodes))

    # Utilisation de DFS pour parcourir tous les nœuds accessibles
    visited = set()

    def dfs(node):
        visited.add(node)
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                dfs(neighbor)

    # Lancer DFS depuis le premier nœud
    dfs(start_node)

    # Si tous les nœuds ont été visités, le graphe est connexe
    return len(visited) == len(graph.nodes)

def add_missing_edges(graph, stations, edges):
    """Ajoute des arêtes pour rendre le graphe connexe si nécessaire."""
    if verifie_connexite(graph):
        return graph

    # Si le graphe n'est pas connexe, ajouter des arêtes manquantes
    # On peut ajouter des arêtes entre stations non connectées
    # Exemple : Ajouter une arête entre des stations choisies pour rendre le graphe connexe
    for u in stations:
        for v in stations:
            if not graph.has_edge(u, v):
                graph.add_edge(u, v, weight=1)  # Ajout d'une arête avec un poids arbitraire
    return graph

def build_graph(stations, edges):
    """Construit un graphe NetworkX à partir des stations et des arêtes."""
    graph = nx.Graph()
    for station_id, info in stations.items():
        graph.add_node(station_id, **info)
    for u, v, weight in edges:
        graph.add_edge(u, v, weight=weight / 60)  # Convertir le poids en minutes
    return graph

def bellman_ford(graph, source, target):
    """Calcule le plus court chemin entre source et target avec l'algorithme de Bellman-Ford."""
    # Initialisation des distances
    distances = {node: float('inf') for node in graph.nodes}
    distances[source] = 0  # Distance du nœud source à lui-même est 0
    predecessors = {node: None for node in graph.nodes}  # Pour reconstruire le chemin

    # Étape 1 : Relaxation des arêtes, V-1 fois (V est le nombre de nœuds)
    for _ in range(len(graph.nodes) - 1):
        for u, v, data in graph.edges(data=True):
            weight = data['weight']  # Poids de l'arête
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                predecessors[v] = u
            if distances[v] + weight < distances[u]:
                distances[u] = distances[v] + weight
                predecessors[u] = v

    # Vérification des cycles de poids négatifs
    for u, v, data in graph.edges(data=True):
        weight = data['weight']
        if distances[u] + weight < distances[v]:
            raise ValueError("Le graphe contient un cycle de poids négatif")
        if distances[v] + weight < distances[u]:
            raise ValueError("Le graphe contient un cycle de poids négatif")

    # Étape 2 : Reconstruction du chemin le plus court
    path = []
    current_node = target
    while current_node is not None:
        path.append(current_node)
        current_node = predecessors[current_node]

    path.reverse()  # Inverser le chemin pour obtenir la direction correcte

    # Si la distance au nœud cible est infinie, il n'y a pas de chemin
    if distances[target] == float('inf'):
        return None, None

    return distances[target], path


def display_route_info(path, stations, terminus):
    """Affiche les instructions pour l'itinéraire calculé en ne mentionnant que les changements de ligne avec le terminus."""
    route_instructions = []
    previous_line = None
    previous_direction = None

    for station_id in path:
        station = stations[station_id]
        line_number = station['line_number']
        direction_number = station['direction_number']

        if previous_line != line_number:
            # On cherche le terminus en fonction du branchement
            if direction_number == 0:
                route_instructions.append(f"Changez de ligne et prenez la {line_number}, direction {terminus[line_number][1]}")
            elif direction_number == 1:
                route_instructions.append(f"Changez de ligne et prenez la {line_number}, direction {terminus[line_number][0]}")
            else:
                route_instructions.append(f"Changez de ligne et prenez la {line_number}, direction {terminus[line_number][1]}")

        previous_line = line_number
        previous_direction = direction_number

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

def plot_metro(graph, stations, positions, path=None, title="Carte du métro"):
    """
    Affiche une carte interactive avec Plotly, avec un zoom autour du chemin rouge si donné.

    Args:
        graph (nx.Graph): Le graphe du métro.
        stations (dict): Dictionnaire des stations.
        positions (dict): Coordonnées des stations.
        path (list, optional): Chemin le plus court (liste des nœuds). Default: None.
        title (str): Le titre de la carte.
    """
    fig = go.Figure()

    # Ajouter les arêtes
    for u, v, data in graph.edges(data=True):
        x_coords = [positions[stations[u]['station_name']][0], positions[stations[v]['station_name']][0]]
        y_coords = [positions[stations[u]['station_name']][1], positions[stations[v]['station_name']][1]]
        fig.add_trace(go.Scatter(
            x=x_coords, y=y_coords, mode='lines',
            line=dict(color='gray', width=1), hoverinfo='none'
        ))

    # Ajouter les nœuds
    for station_id, data in stations.items():
        if data['station_name'] in positions:
            x, y = positions[data['station_name']]
            line_color = LINE_COLORS.get(data['line_number'], "black")  # Couleur par ligne
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode='markers+text',
                text=[data['station_name']],
                textposition='top right',
                marker=dict(size=10, color=line_color),
                hoverinfo='text'
            ))

    # Ajouter le chemin le plus court
    if path:
        # Calculer les coordonnées du chemin
        path_x = []
        path_y = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            x_coords = [positions[stations[u]['station_name']][0], positions[stations[v]['station_name']][0]]
            y_coords = [positions[stations[u]['station_name']][1], positions[stations[v]['station_name']][1]]
            path_x.extend(x_coords)
            path_y.extend(y_coords)
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords, mode='lines',
                line=dict(color='red', width=3), hoverinfo='none'
            ))

        # Ajuster les limites de la carte autour du chemin
        x_min, x_max = min(path_x), max(path_x)
        y_min, y_max = min(path_y), max(path_y)

        # Ajouter un petit padding autour du chemin
        padding_factor = 0.1  # 10% de marge autour du chemin
        x_range = [x_min - (x_max - x_min) * padding_factor, x_max + (x_max - x_min) * padding_factor]
        y_range = [y_min - (y_max - y_min) * padding_factor, y_max + (y_max - y_min) * padding_factor]

        # Appliquer les limites de zoom
        fig.update_layout(
            title=title,
            xaxis=dict(range=x_range, visible=False),
            yaxis=dict(range=y_range, visible=False),
            showlegend=False,
            autosize=True,
            margin=dict(l=0, r=0, b=0, t=0),
        )
    else:
        # Si aucun chemin, afficher la carte entière
        fig.update_layout(
            title=title,
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
stations, terminus = load_stations('station.txt')
edges = load_edges('arete.txt')
positions = load_positions('pospoints.txt')
metro_graph = build_graph(stations, edges)

# Créer le dictionnaire des noms
station_names = {id: info['station_name'] for id, info in stations.items()}

# Enlever les doublons dans la liste des stations
unique_station_names = list(set(station_names.values()))

# Sélection des stations de départ et d'arrivée
start_station_name = st.sidebar.selectbox("Station de départ", unique_station_names)
end_station_name = st.sidebar.selectbox("Station d’arrivée", unique_station_names)

# Valider les indices
try:
    start_station = [id for id, name in station_names.items() if name == start_station_name][0]
    end_station = [id for id, name in station_names.items() if name == end_station_name][0]
except IndexError:
    st.error("Station non trouvée. Veuillez vérifier les données.")

# Calcul du chemin
# Calcul du plus court chemin
if st.sidebar.button("Calculer le plus court chemin"):
    length, path = bellman_ford(metro_graph, start_station, end_station)
    if path:
        st.write(f"Durée estimée : {length:.2f} minutes")
        route_info = display_route_info(path, stations, terminus)
        st.write(route_info)

        # Affichage du trajet sur la carte interactive
        fig = plot_metro(metro_graph, stations, positions, path=path, title="Plus Court Chemin")
        st.plotly_chart(fig)
    else:
        st.write("Aucun chemin trouvé entre les stations.")


# Calcul et affichage de l'ACPM pour tout le graphe
if st.sidebar.button("Afficher l'ACPM de tout le graphe"):
    acpm = nx.minimum_spanning_tree(metro_graph, weight='weight')
    fig_acpm = plot_metro(acpm, stations, positions, title="Arbre Couvrant de Poids Minimum (ACPM)")
    fig_acpm.update_layout(
        height=500,
        autosize=False,
        width=1500,
        title="Arbre Couvrant de Poids Minimum (ACPM)"
    )

    st.plotly_chart(fig_acpm)

# Affichage de la légende des lignes
st.sidebar.subheader("Légende des lignes")
for line_number, color in LINE_COLORS.items():
    st.sidebar.markdown(
        f"<div style='display: inline-block; margin-right: 10px;'>"
        f"<div style='width: 20px; height: 20px; background-color: {color}; display: inline-block;'></div>"
        f"</div><span style='vertical-align: top; margin-left: 10px;'>Ligne {line_number}</span>",
        unsafe_allow_html=True
    )
