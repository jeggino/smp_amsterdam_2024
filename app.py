import streamlit as st
from streamlit_option_menu import option_menu
import base64

import random
import itertools

import geopandas as gpd
import pandas as pd

from deta import Deta

import pydeck as pdk

import altair as alt


# --- CONFIGURATION ---
st.set_page_config(
    page_title="❌❌❌",
    page_icon="🦇",
    layout="wide",
    menu_items={
        'About': "https://www.ecoloogamsterdam.nl/"
    }
    
)

# --- CONNECT TO DETA ---
deta = Deta(st.secrets["deta_key"])
db_infopictures = deta.Base("df_infopictures")
drive = deta.Drive("df_pictures")

db_content_infopictures = pd.DataFrame(db_infopictures.fetch().items)

# --- COSTANTS ---
ICON_URL = "https://images.vexels.com/media/users/3/135975/isolated/preview/cfd8bb70033550adc52ef910d92397db-flying-bats-circle-icon.png"
LOGO = "pictures/logo.png"

### FUNCTIONS ###
def password_generator():
    password_length = 12

    characters = "abcde12345"

    password = ""   

    for index in range(password_length):
        password = password + random.choice(characters)
        
    return password

def insert_info(pict_name,info):

  return db_infopictures.put({"pict_name":pict_name,"info":info})
def load_point():
  df_raw = pd.read_csv("dataset/df_raw.csv")
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


def map_heatmap(gdf_raw,opacity,threshold):
    view_state = pdk.ViewState(latitude=gdf_raw["lng"].mean(), 
                                       longitude=gdf_raw["lat"].mean(), 
                                       zoom=11, max_zoom=12,pitch=0, bearing=20)
    layer = pdk.Layer(
        "HeatmapLayer",
        data=gdf_raw,
        opacity=opacity,
        get_position=["lat", "lng"],
        threshold=threshold,
    )
    
    r = pdk.Deck(layers=[layer], initial_view_state=view_state)
    
    return r

### APP ###
with st.sidebar:
    st.image(LOGO)
    selected = option_menu("", ['📊','📋','📷/📹'], 
                           menu_icon="cast",
                           default_index=0,
                           orientation="vertical",
                           )


# load dataset
gdf_point = load_point()
gdf_buurt = load_buurt(gdf_point)



if selected == '📊':
    col_1,col_2 = st.columns([1,3])
    col_1.image("pictures/Observation.jpg")

    "---"
    # map
    st.pydeck_chart(pydeck_obj=map_buurt(gdf_buurt,gdf_point), use_container_width=True)
    
    "---"

    on = st.toggle("Activate size scale")

    if on:
        size_scale = st.number_input("Set size scale", min_value=1, max_value=10, value="min", step=1, key="size_scale")
        get_size = "antaal"

    else:
        get_size = 7
        size_scale = 3
    
    icon_data = {
        "url": ICON_URL,
        "width": 242,
        "height": 242,
        "anchorY": 242,
    }
    
    data = gdf_point
    data["icon_data"] = None
    for i in data.index:
        data["icon_data"][i] = icon_data
    
    view_state = pdk.ViewState(latitude=data["lng"].mean(), 
                               longitude=data["lat"].mean(), 
                               zoom=11, max_zoom=18,pitch=50, bearing=20)
    
    icon_layer = pdk.Layer(
        type="IconLayer",
        data=data,
        get_icon="icon_data",
        get_size=get_size,
        size_scale=size_scale,
        get_position=["lat", "lng"],
        pickable=True,
    )
    
    tooltip = {"html": "<b>Aantal:</b> {antaal}"}
    
    r = pdk.Deck(layers=[icon_layer], initial_view_state=view_state, tooltip=tooltip, map_style='road')
    
    st.pydeck_chart(pydeck_obj=r, use_container_width=True)
    
    "---"
    opacity = st.number_input("Set opacity", min_value=0.1, max_value=1.0, value=0.5, key="opacity")
    threshold = st.number_input("Set threshold", min_value=0.1, max_value=1.0, value=0.8, key="threshold")

    
    st.pydeck_chart(pydeck_obj=map_heatmap(gdf_point,opacity,threshold), use_container_width=True)
    
    "---"
    
    total = alt.Chart(gdf_point.drop('geometry',axis=1)).mark_boxplot(extent='min-max').encode(
        y='antaal:Q'
    )
    
    buurt = alt.Chart(gdf_point.drop('geometry',axis=1)).mark_boxplot(extent='min-max').encode(
        y='antaal:Q',
        x = 'area:N'
    )
    
    chart = total|buurt
    st.altair_chart(chart, use_container_width=True, theme=None, key="chart_number_1")
    
    "---"
    df_chart_date = gdf_point.drop('geometry',axis=1)
    # df_chart_date['date'] = df_chart_date['date'].apply(pd.to_datetime).dt.date
    chart_date = alt.Chart(df_chart_date).mark_circle(
        opacity=0.8,
        stroke='black',
        strokeWidth=1,
        strokeOpacity=0.4
    ).encode(
        x=alt.X('date:T', title=None,
                # scale=alt.Scale(domain=['05-01-2024','08-01-2024']) 
               ),
        y=alt.Y(
            'area:N',
            sort=alt.EncodingSortField(field="antaal", op="sum", order='descending'),
            title=None
        ),
        size=alt.Size('antaal:Q',
            legend=alt.Legend(title='antaal', clipHeight=30, format='s')
        ),
        color=alt.Color('area:N', legend=None),
        tooltip=[
            "area:N",
            alt.Tooltip("date:T"),
            alt.Tooltip("species:N"),
            alt.Tooltip("antaal:Q", format='~s')
        ],
    ).configure_axisY(
        domain=False,
        ticks=False,
        offset=5
    ).configure_axisX(
        grid=False,
    ).configure_view(
        stroke=None
    ).interactive()
    
    st.altair_chart(chart_date, use_container_width=True, theme=None, key="chart_date")
    

elif selected == '📋':
    st.dataframe(gdf_point.drop(['geometry'],axis=1), use_container_width=True)
    

elif selected == '📷/📹':
    tab1, tab2 = st.tabs(["🎞️","📂"])

    with tab1:    
        try:
            list_names = db_content_infopictures["pict_name"].to_list()
            for file in drive.list()["names"]:
                if file in list_names:
                    res = drive.get(file).read()
                    try:
                        st.image(res)
                    except:
                        st.video(res)
                    st.write(db_content_infopictures.loc[db_content_infopictures["pict_name"]==file,"info"].iloc[0])
                "---"
        except:
            st.warning("Nog geen foto's")

    with tab2:
        
        uploaded_file = st.file_uploader("Een afbeelding uploaded",label_visibility="hidden")
        if uploaded_file:
            with st.container(border=True):
                info = st.text_input("Schrijf wat informatie over de foto...",value=None,placeholder="Schrijf wat informatie over de foto...", label_visibility="hidden")
                try:
                    st.image(uploaded_file)
                except:
                    st.video(uploaded_file)
                    
                # Every form must have a submit button.
                submitted = st.button("Gegevens opslaan")
                if submitted:
                    if info==None:
                        st.warning("Provide  infos")
                        st.stop()
                    pict_name = password_generator()
                    bytes_data = uploaded_file.getvalue()
                    drive.put(f"{pict_name}", data=bytes_data)
                    insert_info(pict_name,info)
                    st.rerun()
