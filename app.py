import streamlit as st
from utils.algorithmes import bellman_ford, prim
from utils.chargement_donnees import recup_stations, recup_laisons, recup_positions
from utils.visualisation import plot_metro, affiche_route_info
from utils.algorithmes import verifie_connexite, ajoute_liaisons_manquantes
from utils.algorithmes import construire_graphe, format_temps
from utils.visualisation import LIGNE_COULEURD;
import networkx as nx

st.set_page_config(page_title="Metro Surfer", page_icon="images/MetroSurfer.png")

# -------------------------------
# Chargement des données
# -------------------------------
stations, terminus = recup_stations('data/station.txt')
liaisons = recup_laisons('data/liaison.txt')
positions = recup_positions('data/pospoints.txt')

# Construction du graphe
metro_graphe = construire_graphe(stations, liaisons)# -------------------------------
# Interface utilisateur
# -------------------------------
st.title("Metro Surfer : Votre guide interactif du métro :)")
st.sidebar.title("Me déplacer")


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
            route_info = affiche_route_info(chemin, stations, terminus)
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
for ligne_numero, couleur in LIGNE_COULEURD.items():
    st.sidebar.markdown(
        f"<div style='display: inline-block; margin-right: 10px;'>"
        f"<div style='width: 20px; height: 20px; background-color: {couleur}; display: inline-block;'></div>"
        f"</div><span style='vertical-align: top; margin-left: 10px;'>Ligne {ligne_numero}</span>",
        unsafe_allow_html=True
    )
