# Metro_Runner

lien vers le site : https://sharu2501-metro-runner-app-ohogzy.streamlit.app/

Vas-y dans le métro - DURAND Ugo, GUERIN Nam Luân, SASIKUMAR Sahkana
Projet en théorie des graphes pour Efrei Paris, 2024

Ce projet applique les concepts de théorie des graphes pour explorer le réseau du métro parisien.
Il permet de vérifier la connexité, de calculer le plus court chemin entre deux stations et de générer
un arbre couvrant de poids minimal. Le projet inclut une interface console et une interface graphique pour l’interaction.

## Lancement du Projet
Allez sur le site https://sharu2501-metro-runner-app-ohogzy.streamlit.app/ (qui se trouve également dans le à propos du repos)


Fonctionnalités des Interfaces :

- Interface Console (Main) : Permet de calculer le plus court chemin, de vérifier la connexité du graphe et d'afficher l'arbre couvrant minimal.
- Interface Graphique :
  - Carte du métro de paris navigable (zoom, dezoom, déplacement sur la carte,...)
  - Bouton "Afficher le chemin" : Affiche le plus court chemin entre deux stations
  - Bouton "Arbre couvrant du graphe" : Affiche l’arbre couvrant minimal du réseau.


Remarques :

- Données : Les fichiers station.txt, liaison.txt et pospoints.txt dans le dossier data sont nécessaires pour le bon fonctionnement des calculs et de l’affichage graphique.


Scénario :

Afficher le chemin le plus court entre 2 stations (de votre choix) :
- dans la liste déroulante à gauche choisissez la stations de départ et d'arriver de votre choix
- ensuite cliquez sur "Calculer le plus court chemin"
- Le plus court chemin entre ces 2 stations en rouge s'affiche sur la carte

Afficher l'APCM :
- cliquez sur "Afficher l'APCM"
- l'arbre couvrant minimal s'affiche sur la carte et le temps total s'affiche au dessus
