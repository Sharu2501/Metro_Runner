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
            line_color = LIGNE_COULEURS.get(data['ligne_numero'], "black")  # Couleur par ligne
            fig.add_trace(go.Scatter(
                x=[x], y=[y], mode='markers+text',
                text=[data['station_nom']],
                textposition='top right',  
                textfont=dict(size=4), 
                marker=dict(size=6, color=line_color),
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
            width=1200,
            height=1000,
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
            width=1200,
            height=1000,
            margin=dict(l=0, r=0, b=0, t=0),
        )

    return fig

def affiche_route_info(chemin, stations, terminus):
    """
    Affiche les instructions pour l'itinéraire calculé en mentionnant les changements de ligne
    avec le terminus basé sur le sens du trajet.
    """
    route_instructions = []
    ligne_precedente = None
    terminus_direction = None

    for i in range(len(chemin) - 1):
        # Station actuelle et suivante
        station_actuelle_id = chemin[i]
        station_suivante_id = chemin[i + 1]
        station_actuelle = stations[station_actuelle_id]
        station_suivante = stations[station_suivante_id]

        ligne_actuelle = station_actuelle['ligne_numero']

        if ligne_precedente != ligne_actuelle:
            # Changement de ligne, déterminer le terminus basé sur le sens du déplacement
            ligne_terminus = terminus[ligne_actuelle]
            nom_actuel = station_actuelle['station_nom']
            nom_suivant = station_suivante['station_nom']

            # Si le terminus de la ligne existe, choisir celui vers lequel on se dirige
            if nom_suivant in ligne_terminus:
                terminus_direction = nom_suivant
            else:
                # Sinon, choisir l'autre terminus comme direction
                terminus_direction = (
                    ligne_terminus[1] if ligne_terminus[0] == nom_actuel else ligne_terminus[0]
                )

            route_instructions.append(
                f"A {nom_actuel}, prenez la ligne {ligne_actuelle}, direction {terminus_direction}."
            )

        ligne_precedente = ligne_actuelle

    # Ajouter la dernière station
    last_station = stations[chemin[-1]]
    route_instructions.append(f"Descendez à {last_station['station_nom']}.")

    return "\n".join(route_instructions)

def set_bg_hack_url(image_path):
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''

    # Open the image file in binary mode
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()

    # Encode the image in base64
    img_base64 = base64.b64encode(img_data).decode()

    # Create the image URL in data URI format
    img_url = f"data:image/png;base64,{img_base64}"

    # Use markdown to set the background style
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
    """
    Set the background image of the sidebar by reading the image,
    converting it into base64 and applying it as the background.
    """
    # Get the image in base64 format
    with open(side_bg, "rb") as img_file:
        img_data = img_file.read()

    img_base64 = base64.b64encode(img_data).decode()

    # Apply the image as the sidebar background
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
def gif_bg(gif_bg):
    """
    Set the background image of the sidebar using a GIF file,
    converting it into Base64 and applying it as the background.
    """
    gif_bg_ext = 'gif'  # File extension for GIF images

    # Open the GIF image in binary mode and encode it as base64
    with open(gif_bg, "rb") as img_file:
        img_data = img_file.read()

    img_base64 = base64.b64encode(img_data).decode()

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] > div:first-child {{
            background: url(data:image/{gif_bg_ext};base64,{img_base64});
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
