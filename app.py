import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from shapely.wkt import loads

# Init
debug = False
ApiKeyStreetView = "YOUR_STREET_VIEW_API_KEY"
budget = initial_budget = 3000000

#localisation des fichiers sources
file_path_zones = "./zones.csv"
file_path_houses = "./points_of_interest.csv"

start_coordinates = [34.05, -118.25] # centrage de la carte sur les coordonnées de Los Angeles
start_zoom_level = 11 # niveau de zoom approprié pour voir la carte de Los Angeles

st.set_page_config(layout="wide")

# Appliquer du CSS pour modifier la taille du texte et la largeur de l'input
st.markdown("""
    <style>
        .custom-label {
            font-size: 20px !important;
            font-weight: bold;
            min-height:1.5rem;
            font-size: 0.875rem;
            color: rgb(250, 250, 250);
            display: flex;
            visibility: visible;
            margin-bottom: 0.25rem;
            height: auto;
            min-height: 1.5rem;
            vertical-align: middle;
            flex-direction: row;
            -webkit-box-align: center;
            align-items: center;
        }
        div[data-testid="stNumberInput"] input {
            font-size: 25px !important;
            width: 10ch !important; /* Ajuste la largeur (10-15 caractères) */
            text-align: right; /* Alignement du texte */
        }
            body {
            background-color: #110c4b !important; /* Gris clair */
        }
        
        /* Modifier la couleur des titres */
        h1, h2, h3, h4, h5, h6 {
            color: #ff9807; /* orange */
        }

    </style>
""", unsafe_allow_html=True)


# Création d'une ligne avec le label à gauche et l'input à droite
col1, col2, col3 = st.columns([5,1,1])  # Ajuste les colonnes pour contrôler la largeur
with col1:
    st.title(f"Maisons à Vendre et quartiers à risque dans Los Angeles")
with col2:
    st.title(f"💰Budget")
with col3:
    budget = st.number_input("", min_value=0, value=initial_budget, step=100000, format="%d")




# Affichage amélioré des données monétaires (en dollars)
def format_currency(amount):
    return '${:,.2f}'.format(amount)


# Obtenir l'URL d'une image Street View à partir des coordonnées
def get_street_view_image_url(lat, lon, api_key=ApiKeyStreetView):
    """Génère une URL pour une image Google Street View à partir des coordonnées."""
    return f"https://maps.googleapis.com/maps/api/streetview?size=400x300&location={lat},{lon}&key={api_key}"


# Chargement dans un dataframe des données des zones et mise en cache
@st.cache_data
def load_zones(file_path):
    try:
        df = pd.read_csv(file_path)
        # vérification de la colonne 'geometry' et conversion en objets géométriques Shapely
        df["geometry_obj"] = df["geometry"].apply(lambda x: loads(x) if isinstance(x, str) else None)
        if debug:
            st.success("✅ Fichier chargé avec succès !")
        return df
    except Exception as e:
        if debug:
            st.error(f"❌ Erreur lors du chargement du CSV : {e}")
        return None


# Chargement dans un dataframe des données des maisons et mise en cache
@st.cache_data
def load_houses(file_path):
    try:
        df = pd.read_csv(file_path)
        # Elimination des coordonnées incomplètes (lat/lon)
        if "lat" in df.columns and "lon" in df.columns:
            df = df.dropna(subset=["lat", "lon"])
            if debug:
                st.success("✅ Maisons à vendre chargées avec succès !")
            return df
        else:
            if debug:
                st.error("❌ Les colonnes 'lat' et 'lon' sont manquantes dans le fichier des maisons.")
            return None
    except Exception as e:
        if debug:
            st.error(f"❌ Erreur lors du chargement du fichier des maisons : {e}")
        return None


# Définir la couleur d'une zone en fonction du score de criminalité
def get_zone_color(crime_score):
    if crime_score >= 90:
        return "red"
    elif crime_score >= 85:
        return "orange"
    else:
        return "green"

# Créer une carte avec les zones et les maisons
def create_map(df_zones, df_houses, budget, start_coordinates=start_coordinates, start_zoom_level=start_zoom_level):
    m = folium.Map(location=start_coordinates, zoom_start=start_zoom_level, tiles="cartodbpositron", control_scale=True)
    
    #Création des zones sur la carte avec les couleurs correspondantes
    for _, row in df_zones.iterrows():
        if row["geometry_obj"] is not None:
            try:
                #Extraction des polygons geolocalisés des quartiers (champ geometry) et des propriétés des quartiers
                geojson_feature = {
                    "type": "Feature",
                    "geometry": row["geometry_obj"].__geo_interface__,
                    "properties": {
                        "neighborhood": row["neighborhood"],
                        "crime_gravity": row["crime_gravity"]
                    }
                }
                #Ajout des polygons sur la carte avec les couleurs correspondantes
                folium.GeoJson(
                    geojson_feature,
                    style_function=lambda feature, crime_score=row["crime_gravity"]: {
                        "fillColor": get_zone_color(crime_score),
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.6,
                    },
                    tooltip=f"<h1><b>{row['neighborhood']}</b></h1><h4>{int(row['crime_gravity'])} (Crime Score)</h4>"
                ).add_to(m)
            except Exception as e:
                if debug:
                    st.warning(f"⚠️ Erreur sur {row['neighborhood']}: {e}")
    
    #Création des marqueurs pour chaque maison, de l'extrait des infos au survol (tooltip) et placement sur la carte
    if df_houses is not None:
        for _, row in df_houses.iterrows():
            house_id = row.get("house_id", "ID inconnu")
            house_surfacem2 = int(row.get("superficie_metres", "Surface inconnue"))
            house_totalprice = row.get("total_value", "Prix inconnu")
            house_rooms = row.get("nb_rooms", "Nombre de pièces inconnu")
            house_bathrooms = row.get("nb_bathrooms", "Nombre de salles de bain inconnu")
            house_bedrooms = row.get("nb_bedrooms", "Nombre de chambres")
            house_landvalue = row.get("land_value", "Valeur du terrain inconnue")
            house_type = row.get("p_use_type", "Type d'usage inconnu")
            house_pricem2 = int(row.get("square_metres_price", "Prix/m²"))
            pin_color = "blue" if house_totalprice <= budget else "lightgray"
            house_imageurl= get_street_view_image_url(row["lat"], row["lon"])
            house_neighborhood = row.get("neighborhood", "Quartier inconnu")
            #placement du marqueur sur la carte et de son tooltip associé
            folium.Marker(
                location=[row["lat"], row["lon"]],
                tooltip=f"<h4>Maison à {house_neighborhood} ID#{house_id}</h4><br><img src='{house_imageurl}' width='500'><br><h1><b>Prix : {house_totalprice:,} $ (Terrain: {house_landvalue:,} $)</b></h1><h4>{house_surfacem2} m² <br>{house_rooms} pièces ({house_bedrooms} chambres, {house_bathrooms} salles de bains) <br>{house_pricem2:,} $/m²</h4>",
                opacity=1,
                icon=folium.Icon(color=pin_color, icon="home")
            ).add_to(m)     
    return m


#Chargement des données des quartiers et des maisons (en local)
df_zones = load_zones(file_path_zones)
df_houses = load_houses(file_path_houses)
if df_zones is not None:
    if debug:
        st.write("Aperçu du CSV des quartiers :", df_zones.head(10))
    if df_houses is not None:
        if debug:
            st.write("Aperçu du CSV des maisons :", df_houses.head(10))
    
    #Création de la carte des quartiers et des maisons en résolution 2300x900, selon les datas des 2 CSV df_zones et df_houses
    map_object = create_map(df_zones, df_houses, budget)
    st_folium(map_object, width=2300, height=900)
else:
    if debug:
        st.error("❌ Le fichier CSV des quartiers n'a pas pu être chargé. Vérifiez le chemin.")
