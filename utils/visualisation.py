import plotly.graph_objects as go
import streamlit as st
import base64

LIGNE_COULEURS = {
    "1": "blue", "2": "green", "3": "red", "4": "violet", "5": "orange", "6": "pink",
    "7": "brown", "8": "yellow", "9": "cyan", "10": "lime", "11": "gray", "12": "gold",
    "13": "darkblue", "14": "darkred"
}

def plot_metro(graphe, stations, positions, chemin=None, titre="Carte du métro"):
    """
    Affiche une carte interactive avec Plotly, avec un zoom autour du chemin rouge si donné.
    """
    fig = go.Figure()
    messages = []

    # Ajout des liaisons entre les stations
    for u, v, data in graphe.edges(data=True):
        station_u = stations[u]['station_nom']
        station_v = stations[v]['station_nom']
        if station_u in positions and station_v in positions:
            # Vérification de l'existence des positions des stations
            x_coords = [positions[station_u][0], positions[station_v][0]]
            y_coords = [positions[station_u][1], positions[station_v][1]]
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords, mode='lines',
                line=dict(color='gray', width=1), hoverinfo='none'
            ))
        else:
            messages.append(f"Impossible de relier les stations suivantes : {station_u}, {station_v}")

    # Ajout des stations
    for station_id, data in stations.items():
        station_nom = data['station_nom']
        if station_nom in positions:
            x, y = positions[station_nom]
            line_color = LIGNE_COULEURS.get(data['ligne_numero'], "black")
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode='markers+text',
                text=[station_nom],
                textposition='top right',
                textfont=dict(size=10),
                marker=dict(size=10, color=line_color),
                hoverinfo='text'
            ))
        else:
            messages.append(f"Position non connu pour la station : {station_nom}")

    # Ajout du chemin le plus court
    if chemin:
        # Calcul les coordonnées du chemin
        chemin_x = []
        chemin_y = []
        for i in range(len(chemin) - 1):
            u, v = chemin[i], chemin[i + 1]
            station_u = stations[u]['station_nom']
            station_v = stations[v]['station_nom']
            if station_u in positions and station_v in positions:
                x_coords = [positions[station_u][0], positions[station_v][0]]
                y_coords = [positions[station_u][1], positions[station_v][1]]
                chemin_x.extend(x_coords)
                chemin_y.extend(y_coords)
                fig.add_trace(go.Scatter(
                    x=x_coords, y=y_coords, mode='lines',
                    line=dict(color='red', width=3), hoverinfo='none'
                ))
            else:
                messages.append(f"Positions manquantes : {station_u}, {station_v}")

        if chemin_x and chemin_y:
            x_min, x_max = min(chemin_x), max(chemin_x)
            y_min, y_max = min(chemin_y), max(chemin_y)

            # Ajout d'un petit padding autour du chemin
            padding_factor = 0.1  # 10% de marge autour du chemin
            x_range = [x_min - (x_max - x_min) * padding_factor, x_max + (x_max - x_min) * padding_factor]
            y_range = [y_min - (y_max - y_min) * padding_factor, y_max + (y_max - y_min) * padding_factor]

            # Limites de zoom
            fig.update_layout(
                title=titre,
                xaxis=dict(range=x_range, visible=False),
                yaxis=dict(range=y_range, visible=False),
                showlegend=False,
                autosize=True,
                width=1200,
                height=800,
                margin=dict(l=0, r=0, b=0, t=0),
            )
    else:
        # Affiche la carte entière si il y a aucun chemin
        fig.update_layout(
            title=titre,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
            autosize=True,
            width=1200,
            height=1000,
            margin=dict(l=0, r=0, b=0, t=0),
        )

    # Affichage des messages dans l'application
    if messages:
        with st.sidebar:
            st.sidebar.title("Informations")
            st.sidebar.info("Certaines données sont manquantes. Voici les détails :")
            for msg in messages:
                st.sidebar.write(f"- {msg}")

    return fig


def affiche_route_info(chemin, stations, terminus, temps):
    """
    Affiche les instructions pour l'itinéraire calculé en mentionnant les changements de ligne
    avec le terminus basé sur le sens du trajet.
    """
    route_instructions = []
    ligne_precedente = None
    terminus_direction = None

    station_depart = stations[chemin[0]]
    route_instructions.append(f"Vous êtes à {station_depart['station_nom']}.")

    for i in range(len(chemin) - 1):
        # Station actuelle et suivante
        station_actuelle_id = chemin[i]
        station_suivante_id = chemin[i + 1]
        station_actuelle = stations[station_actuelle_id]
        station_suivante = stations[station_suivante_id]

        ligne_actuelle = station_actuelle['ligne_numero']

        if ligne_precedente != ligne_actuelle:
            # Changement de ligne
            ligne_terminus = terminus[ligne_actuelle]
            nom_actuel = station_actuelle['station_nom']
            nom_suivant = station_suivante['station_nom']

            # Recherche de terminus
            if nom_suivant in ligne_terminus:
                terminus_direction = nom_suivant
            else:
                terminus_direction = (
                    ligne_terminus[1] if ligne_terminus[0] == nom_actuel else ligne_terminus[0]
                )

            if ligne_precedente is not None:
                route_instructions.append(
                    f"- À {nom_actuel}, changez et prenez la ligne {ligne_actuelle} direction {terminus_direction}."
                )
            else:
                route_instructions.append(
                    f"- Prenez la ligne {ligne_actuelle} direction {terminus_direction}."
                )

        ligne_precedente = ligne_actuelle

    derniere_station = stations[chemin[-1]]
    route_instructions.append(f"- Vous devriez arriver à {derniere_station['station_nom']} dans environ {temps} !")

    return "\n".join(route_instructions)

def set_bg_hack_url(image_path):
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()

    img_base64 = base64.b64encode(img_data).decode()

    img_url = f"data:image/png;base64,{img_base64}"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url("{img_url}");
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def sidebar_bg(side_bg):
    with open(side_bg, "rb") as img_file:
        img_data = img_file.read()

    img_base64 = base64.b64encode(img_data).decode()

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] > div:first-child {{
            background: url(data:image/png;base64,{img_base64});
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def gif_bg_top(gif_bg):
    gif_bg_ext = 'gif'  

    # Ouvre l'image GIF
    with open(gif_bg, "rb") as img_file:
        img_data = img_file.read()

    img_base64 = base64.b64encode(img_data).decode()

    st.markdown(
        f"""
        <style>
        .bottom-gif {{
            position: fixed;  
            bottom: 0; 
            left: 50%;  
            transform: translateX(-50%);  
            width: 100%; 
            height: auto; 
            background: url(data:image/{gif_bg_ext};base64,{img_base64});
            background-size: contain;  
            background-position: center center;
            z-index: 9999; 
        }}
        
        .main-content {{
            padding-bottom: 80px; 
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Ajoute un div contenant le GIF dans la page
    st.markdown('<div class="bottom-gif"></div>', unsafe_allow_html=True)
    st.markdown('<div class="main-content"></div>', unsafe_allow_html=True)

