import streamlit as st
from streamlit_option_menu import option_menu

import geopandas as gpd
import pandas as pd

import pydeck as pdk

import altair as alt

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
def load_point():
  df_raw = pd.read_csv("dataset/df_raw.csv")
  df_raw['date'].apply(pd.to_datetime).dt.date
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

def map_buurt(gdf_buurt,gdf_raw):
  
  
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

def map_point(gdf_raw,size_scale):
    # Data from OpenStreetMap, accessed via osmpy
    ICON_URL = "https://images.vexels.com/media/users/3/135975/isolated/preview/cfd8bb70033550adc52ef910d92397db-flying-bats-circle-icon.png"
    
    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }
    
    data = gdf_raw
    data["icon_data"] = None
    for i in data.index:
        data["icon_data"][i] = icon_data
    
    view_state = pdk.ViewState(latitude=gdf_raw["lng"].mean(), 
                                       longitude=gdf_raw["lat"].mean(), 
                                       zoom=10, max_zoom=18,pitch=0, bearing=20)
    
    icon_layer = pdk.Layer(
        type="IconLayer",
        data=data,
        get_icon="icon_data",
        get_size="antaal",
        size_scale=size_scale,
        get_position=["lat", "lng"],
        pickable=True,
    )
    
    
    tooltip = {"html": "<b>Aantal:</b> {antaal}"}
    
    r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip=tooltip, map_style='road')
    
    return r

### APP ###

# load dataset
gdf_point = load_point()
gdf_buurt = load_buurt(gdf_point)

# map
st.pydeck_chart(pydeck_obj=map_buurt(gdf_buurt,gdf_point), use_container_width=True)

"---"

size_scale = st.number_input("Set size scale", min_value=1, max_value=10, value="min", step=1, key="size_scale")
st.pydeck_chart(pydeck_obj=map_point(gdf_point,size_scale), use_container_width=True)

"---"

total = alt.Chart(gdf_point.drop('geometry',axis=1)).mark_boxplot(extent='min-max').encode(
    y='antaal:Q'
)

buurt = alt.Chart(gdf_point.drop('geometry',axis=1)).mark_boxplot(extent='min-max').encode(
    y='antaal:Q',
    x = 'area:N'
)

chart_number_1 = st.altair_chart(total, use_container_width=True, theme="streamlit", key="chart_number_1",on_select="rerun",selection_mode=None)
chart_number_2 = st.altair_chart(buurt, use_container_width=True, theme="streamlit", key="chart_number_2", on_select="rerun", selection_mode=None)

chart_number_1




