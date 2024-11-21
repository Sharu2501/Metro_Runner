import networkx as nx

def verifie_connexite(graphe):
    """Vérifie si le graphe est connexe en utilisant le parcours en profondeur."""
    if not graphe.nodes:
        return True  # Un graphe sans nœuds est connexe

    depart_node = next(iter(graphe.nodes))

    visites = set()

    def parcours_profondeur(node):
        visites.add(node)
        for voisin in graphe.neighbors(node):
            if voisin not in visites:
                parcours_profondeur(voisin)

    # Faire le parcours en profondeur depuis le premier nœud
    parcours_profondeur(depart_node)

    # Si toutes les stations ont été visités, le graphe est connexe
    return len(visites) == len(graphe.nodes)

def ajoute_liaisons_manquantes(graphe, stations, liaisons):
    """Ajoute des arêtes pour rendre le graphe connexe si nécessaire."""
    if verifie_connexite(graphe):
        return graphe

    # Si le graphe n'est pas connexe, on ajoute des arêtes manquantes
    for x in stations:
        for y in stations:
            if not graphe.has_edge(x, y):
                graphe.add_edge(x, y, weight=20)  # temps de 20 secondes
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
    distances = {node: float('inf') for node in graphe.nodes}
    distances[depart] = 0  # la distance du nœud départ à lui-même vaut 0
    predecesseurs = {node: None for node in graphe.nodes}

    for _ in range(len(graphe.nodes) - 1):
        for x, y, data in graphe.edges(data=True):
            temps = data['weight']  # Poids de l'arête ici le temps
            if distances[x] + temps < distances[y]:
                distances[y] = distances[x] + temps
                predecesseurs[y] = x
            if distances[y] + temps < distances[x]:
                distances[x] = distances[y] + temps
                predecesseurs[x] = y

    # Cycles de poids négatifs
    for x, y, data in graphe.edges(data=True):
        temps = data['weight']
        if distances[x] + temps < distances[y]:
            raise ValueError("Le graphe contient un cycle de poids négatif")
        if distances[y] + temps < distances[x]:
            raise ValueError("Le graphe contient un cycle de poids négatif")

    # on reconstruit le chemin le plus court
    chemin = []
    node_actuel = arrivee
    while node_actuel is not None:
        chemin.append(node_actuel)
        node_actuel = predecesseurs[node_actuel]

    chemin.reverse()

    # Pas de chemin si la distance au nœud d'arrivée est infinie
    if distances[arrivee] == float('inf'):
        return None, None

    return distances[arrivee], chemin

def prim(graphe):
    """
    Implémente l'algorithme de Prim pour calculer l'ACPM.
    Args:
        graphe (nx.Graph): Graphe non orienté avec des poids sur les arêtes.
    Returns:
        tuple: (nx.Graph, float) L'arbre couvrant de poids minimum et le temps total en minutes.
    """
    from heapq import heappop, heappush

    acpm = nx.Graph()
    visites = set()
    liaisons = []

    start_node = next(iter(graphe.nodes))
    visites.add(start_node)

    # On ajoute les liaisons de la station de départ
    for neighbor, attributes in graphe[start_node].items():
        heappush(liaisons, (attributes['weight'], start_node, neighbor))

    total_temps = 0

    while liaisons:
        temps, x, y = heappop(liaisons)  # arête de poid minimum
        if y not in visites:
            acpm.add_edge(x, y, weight=temps)
            visites.add(y)
            total_temps += temps

            # On ajoute les nouvelles arêtes accessibles depuis la station y
            for neighbor, attributes in graphe[y].items():
                if neighbor not in visites:
                    heappush(liaisons, (attributes['weight'], y, neighbor))

    return acpm, total_temps


def format_temps(minutes_float):
    """
    Convertit un temps en minutes (float) au format heures, minutes et secondes.
    """
    total_seconds = int(minutes_float * 60)
    heures = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secondes = total_seconds % 60

    if heures > 0:
        return f"{heures} h {minutes} min {secondes} sec"
    elif minutes > 0:
        return f"{minutes} min {secondes} sec"
    else:
        return f"{secondes} sec"

