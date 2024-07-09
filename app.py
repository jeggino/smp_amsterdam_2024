import streamlit as st
from streamlit_option_menu import option_menu

import geopandas as gpd
import pandas as pd

import pydeck as pdk

# --- CONFIGURATION ---
st.set_page_config(
    page_title="❌❌❌",
    page_icon="🦇",
    layout="centered",
    menu_items={
        'About': "https://www.ecoloogamsterdam.nl/"
    }
    
)


# --- CONNECT TO DETA ---
# deta = Deta(st.secrets["deta_key"])
# db = deta.Base("df_amsterdam_bat")

# --- COSTANTS ---


### FUNCTIONS ###
def load_point:
  df_raw = pd.read_csv(r"C:\Users\Luigi\Downloads\amserdam.csv")
  df_raw[['lat', 'lng']] = df_raw["geometry"].apply(lambda st: st[st.find("(")+1:st.find(")")]).str.split(' ', n=1, expand=True).astype("float")
  df_raw.drop('geometry',axis=1,inplace=True)   
  df_raw['date'].apply(pd.to_datetime).dt.date
  df_raw = df_raw.replace({"Alko 18":"Alko"})
  df_raw['species'] = "Pipistrellus pipistrellus"
  df_raw['nl_naam'] = "gewone dwergvleermuis"
  
  gdf_raw = gpd.GeoDataFrame(df_raw, geometry=gpd.points_from_xy(df_raw['lat'], df_raw['lng']), crs="EPSG:4326")

  return gdf_raw

def load_buurt(gdf_raw): 
  columns = ['Buurtnaam', 'Oppervlakte_m2','Oppervlakte_Km2','geometry']
  
  gdf_buurt = gpd.read_file("https://maps.amsterdam.nl/open_geodata/geojson_lnglat.php?KAARTLAAG=GEBIED_BUURTEN_EXWATER&THEMA=gebiedsindeling")
  gdf_buurt = gdf_buurt[gdf_buurt.Stadsdeelcode=="F"]
  gdf_buurt["Oppervlakte_Km2"] = gdf_buurt["Oppervlakte_m2"].apply(lambda x: x / 1000000)
  gdf_buurt = gdf_buurt[columns]
  
  gdf_buurt_join = gpd.sjoin(gdf_buurt, gdf_raw.to_crs(gdf_buurt.crs))
  gdf_buurt['antall'] = gdf_buurt["Buurtnaam"].map(gdf_buurt_join["Buurtnaam"].value_counts().to_dict())
  gdf_buurt["n_Km2"] = round(gdf_buurt['antall'] / gdf_buurt['Oppervlakte_Km2'])
  gdf_buurt["antallNORM"] = gdf_buurt['antall'].apply(lambda x: (255+((x - gdf_buurt['antall'].min())*(255)))/(gdf_buurt['antall'].max() - gdf_buurt['antall'].min()))

  return gdf_buurt

def map_buurt(gdf_buurt):
  
  
  INITIAL_VIEW_STATE = pdk.ViewState(latitude=gdf_raw["lng"].mean(), 
                                     longitude=gdf_raw["lat"].mean(), 
                                     zoom=11, max_zoom=16, pitch=60, bearing=20)
  
  
  polygon_layer = pdk.Layer(
      "GeoJsonLayer",
      gdf_buurt,
      opacity=0.9,
      stroked=True,
      filled=True,
      extruded=True,
      wireframe=True,
      pickable=True,
      get_elevation="antall * 300",
      get_fill_color="[antallNORM+95, antallNORM+95, antallNORM+95]",
      get_line_color="[antallNORM+70, antallNORM+70, antallNORM+70]",
  )
  
  tooltip = {"html": "<b>Buurt:</b> {Buurtnaam}""<br />""<b>Aantal kraamverblijven:</b> {antall}"}
  
  r = pdk.Deck(
      [polygon_layer],
      initial_view_state=INITIAL_VIEW_STATE,
      tooltip=tooltip,
  )
  
  return r

### APP ###

# load dataset
gdf_point = load_point()
gdf_buurt = load_buurt(gdf_point)

# map
map_buurt(gdf_buurt)




