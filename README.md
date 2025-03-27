# StreamlitMap
A simple page that runs under python with streamlit/folium to display zones and points on a map.

# Usage
- Create and activate your virtual environment
- install requirements (pip install -r requirements.txt)
- run app.py (streamlit run app.py)

# source files
- zones.csv : zones to display. Important row "geometry" contains polygon shapes to display as L.A. neighborhoods
- points_of_interest.csv : data for your points on the map. lat/lon fields used to geolocalisation