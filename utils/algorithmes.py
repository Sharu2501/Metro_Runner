import networkx as nx

def verifie_connexite(graphe):
    """Vérifie si le graphe est connexe en utilisant le parcours en profondeur."""
    if not graphe.nodes:
        return True  # Un graphe sans nœuds est connexe

    # On commence la recherche en profondeur à partir d'un nœud
    depart_node = next(iter(graphe.nodes))

    # Utilisation du parcours en profondeur pour parcourir tous les nœuds accessibles
    visites = set()

    def parcours_profondeur(node):
        visites.add(node)
        for voisin in graphe.neighbors(node):
            if voisin not in visites:
                parcours_profondeur(voisin)

    # Faire le parcours en profondeur depuis le premier nœud
    parcours_profondeur(depart_node)

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
                graphe.add_edge(x, y, weight=20)  # ajoute une arête avec un temps de 20s
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

def format_temps(minutes_float):
    """Convertis un temps en minutes (float) au format minutes:secondes."""
    minutes = int(minutes_float)
    secondes = round((minutes_float - minutes) * 60)
    return f"{minutes} min {secondes} sec"
