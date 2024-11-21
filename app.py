import streamlit as st
from utils.algorithmes import bellman_ford, prim
from utils.chargement_donnees import recup_stations, recup_laisons, recup_positions
from utils.visualisation import plot_metro, affiche_route_info, sidebar_bg
from utils.algorithmes import verifie_connexite, ajoute_liaisons_manquantes
from utils.algorithmes import construire_graphe, format_temps
from utils.visualisation import LIGNE_COULEURS
from utils.visualisation import set_bg_hack_url

st.set_page_config(page_title="Metro Surfer", page_icon="images/MetroSurfer.png", layout="wide")

# -------------------------------
# Chargement des données
# -------------------------------
stations, terminus = recup_stations('data/station.txt')
liaisons = recup_laisons('data/liaison.txt')
positions = recup_positions('data/pospoints.txt')

# Construction du graphe
metro_graphe = construire_graphe(stations, liaisons)

# -------------------------------
# Interface utilisateur
# -------------------------------
set_bg_hack_url("images/MetroSurfer.png")
sidebar_bg("images/MetroSurfer.png")

st.title("Bienvenue sur Metro Surfer, votre guide du métro !")
st.sidebar.title("Me déplacer")

# Affichage de la carte de métro
if "graphe_actif" not in st.session_state:
    st.session_state.graphe_actif = "complet"

# Création du dictionnaire des noms de stations
station_noms = {id: info['station_nom'] for id, info in stations.items()}

# Suppression des doublons dans la liste des stations
station_unique = ["Aucune sélection"] + list(set(station_noms.values()))

with st.sidebar:
    st.subheader("Sélectionnez les stations")
    # Initialisation des stations sélectionnées
    if "depart_station" not in st.session_state:
        st.session_state.depart_station = "Aucune sélection"
    if "arrivee_station" not in st.session_state:
        st.session_state.arrivee_station = "Aucune sélection"

    # Listes de sélection
    depart_station_nom = st.selectbox("Station de départ", station_unique, key="depart_station")
    arrivee_station_nom = st.selectbox("Station d’arrivée", station_unique, key="arrivee_station")

# Vérification avant le clic sur le bouton
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

    # Calcul du plus court chemin avec Bellman-Ford
    if st.sidebar.button("Calculer le plus court chemin"):
        temps, chemin = bellman_ford(metro_graphe, deb_station, fin_station)
        if chemin:
            # Affichage du temps en minutes et secondes
            temps_formatte = format_temps(temps)
            st.markdown(f"""
                <div style="background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #41288a;">
                    <h3 style="color: white;">Durée estimée :</h3>
                    <p style="color: white;">{temps_formatte}</p>
                </div>
                <br><br>
            """, unsafe_allow_html=True)
            route_info = affiche_route_info(chemin, stations, terminus, temps_formatte)

            st.markdown(f"""
                <div style="background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #41288a;">
                    <h3 style="color: white;">Itinéraire :</h3>
                    <p style="color: white;">{route_info}</p>
                </div>
                <br><br>
            """, unsafe_allow_html=True)

            # Mise à jour de la carte avec le plus court chemin avec l'itinéraire
            st.session_state.graphe_actif = "plus_court_chemin"
        else:
            st.write("Aucun chemin trouvé entre les stations.")

# Calcul et affichage de l'ACPM
if st.sidebar.button("Afficher l'ACPM"):
    acpm_prim, temps_total = prim(metro_graphe)
    temps_formatte = format_temps(temps_total)
    
    # Mise à jour de la carte avec Prim et le temps total
    st.session_state.graphe_actif = "acpm"
    st.markdown(f"""
                <div style="background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #41288a;">
                    <h3 style="color: white;">Durée totale :</h3>
                    <p style="color: white;">{temps_formatte}</p>
                </div>
                <br><br>
            """, unsafe_allow_html=True)

# Vérification de la connexité du graphe
if st.sidebar.button("Vérifier la connexité"):
    est_connexe = verifie_connexite(metro_graphe)
    if est_connexe:
        st.markdown(f"""
                <div style="background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #41288a;">
                    <h3 style="color: white;">Vérification de la connexité</h3>
                    <p style="color: white;">Le graphe est connexe : toutes les stations sont accessibles !</p>
                </div>
                <br><br>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
                <div style="background-color: #000000; padding: 15px; border-radius: 10px; border: 2px solid #41288a;">
                    <h3 style="color: white;">Vérification de la connexité</h3>
                    <p style="color: white;">Le graphe n'est pas connexe : certaines stations ne sont pas accessibles !</p>
                </div>
                <br><br>
            """, unsafe_allow_html=True)

# Affichage du graphe en fonction des clics des boutons
if st.session_state.graphe_actif == "plus_court_chemin" and 'chemin' in locals():
    st.session_state.fig = plot_metro(metro_graphe, stations, positions, chemin=chemin, titre=f"Plus Court Chemin : {temps_formatte}")
    st.plotly_chart(st.session_state.fig, use_container_width=True)
elif st.session_state.graphe_actif == "acpm":
    st.session_state.fig = plot_metro(metro_graphe, stations, positions, titre="Arbre Couvrant de Poids Minimum (Prim)")
    st.plotly_chart(st.session_state.fig, use_container_width=True)
else:
    # Affichage du graphe complet
    st.session_state.fig = plot_metro(metro_graphe, stations, positions, titre="Réseau Métro Complet")
    st.plotly_chart(st.session_state.fig, use_container_width=True)

# Affichage des lignes du métro avec son code couleur
st.sidebar.subheader("Lignes du métro")
for ligne_numero, couleur in LIGNE_COULEURS.items():
    st.sidebar.markdown(
        f"<div style='display: inline-block; margin-right: 10px;'>"
        f"<div style='width: 20px; height: 20px; background-color: {couleur}; display: inline-block;'></div>"
        f"</div><span style='vertical-align: top; margin-left: 10px;'>Ligne {ligne_numero}</span>",
        unsafe_allow_html=True
    )

st.image("images/metro.gif")