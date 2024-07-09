import streamlit as st
from streamlit_option_menu import option_menu

import random

import geopandas as gpd
import pandas as pd

from deta import Deta

import pydeck as pdk

import altair as alt


# --- CONFIGURATION ---
st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("""
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob, .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137, .viewerBadge_text__1JaDK{ display: none; } #MainMenu{ visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True)

reduce_header_height_style = """
<style>
    div.block-container {padding-top: 0em; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem; margin-top: -5em; margin-bottom: 2em;}
</style>
"""

st.set_page_config(
    page_title="❌❌❌",
    page_icon="🦇",
    layout="centered",
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
LOGO = "pictures/Untitled.png"

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
selected = option_menu(None, ['📊','📋','📷/📹'], 
                       icons=None,
                       default_index=0,
                       orientation="horizontal",
                       )

st.logo(image=LOGO,link="https://www.ecoloogamsterdam.nl/")

# load dataset
gdf_point = load_point()
gdf_buurt = load_buurt(gdf_point)



if selected == '📊':
    # map
    st.pydeck_chart(pydeck_obj=map_buurt(gdf_buurt,gdf_point), use_container_width=True)
    
    "---"
    
    size_scale = st.number_input("Set size scale", min_value=1, max_value=10, value="min", step=1, key="size_scale")
    st.pydeck_chart(pydeck_obj=map_point(gdf_point,size_scale), use_container_width=True)
    
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
    chart_date = alt.Chart(gdf_point.drop('geometry',axis=1)).mark_circle(
        opacity=0.8,
        stroke='black',
        strokeWidth=1,
        strokeOpacity=0.4
    ).encode(
        x=alt.X('date:T', title=None,scale=alt.Scale(domain=['05-01-2024','08-01-2024']) ),
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
    
    "---"
    
    import itertools
    
    
    LOCATION = 15
    DISTANCE = 1000
    
    
    c = list(set(itertools.combinations(range(len(gdf_point)), 2)))
    
    dict_distances = {}
    distance_total = []
    
    gdf_dist = gdf_point.copy()
    gdf_dist.to_crs(epsg=3310, inplace=True)
    
    for comb in c:
        distance = round(gdf_dist.loc[comb[0],"geometry"].distance(gdf_dist.loc[comb[1],"geometry"]))
        distance_total.append(distance)
        
        if distance<DISTANCE:
            dict_distances[comb] = distance
            
    df_network = pd.DataFrame(dict_distances.items(),columns=["combination","distance"])
    df_network["path"] = df_network["combination"].apply(lambda x: [[gdf_point.loc[x[0],"lat"],gdf_point.loc[x[0],"lng"]],
                                                                    [gdf_point.loc[x[1],"lat"],gdf_point.loc[x[1],"lng"]]])
    
    
    if LOCATION is None:
        df_path_2 = df_network
        
    else:
        list_now = []
    
        for i in df_network.combination:
            if LOCATION in i:
                list_now.append(i)
    
        df_path_2 = df_network[df_network.combination.isin(list_now)]
    
    
    data = gdf_point
    data["antallNORM"] = data['antaal']\
    .apply(lambda x: (255+((x - data['antaal'].min())*(255)))/(data['antaal'].max() - data['antaal'].min()))
    
    
    
    
    column_layer = pdk.Layer(
        "ColumnLayer",
        data=data,
        get_position=["lat", "lng"],
        get_elevation="antaal",
        elevation_scale=10,
        radius=3,
        get_fill_color="[antallNORM+95, antallNORM+95, antallNORM+95]",
        pickable=True,
        auto_highlight=True,
    )
    
    
    df = df_path_2
    
    layer = pdk.Layer(
        type="PathLayer",
        data=df,
        pickable=False,
        get_color="[255,255,255]",
        width_scale=1,
        width_min_pixls=1,
        get_path="path",
        get_width=5,
    )
    
    tooltip = {"html": "<b>Aantal:</b> {antaal}"}
    
    view_state = pdk.ViewState(latitude=gdf_point["lng"].mean(), 
                                       longitude=gdf_point["lat"].mean(), 
                                       zoom=10, max_zoom=18,pitch=90, bearing=20)
    
    r = pdk.Deck(layers=[column_layer,layer], initial_view_state=view_state, tooltip=tooltip, map_style='dark')
    
    list_number_connections = []
    
    for location in range(29):
    
        list_now = []
    
        for i in df_network.combination:
            if location in i:
                list_now.append(i)
    
        df_path_2 = df_network[df_network.combination.isin(list_now)]
        list_number_connections.append(len(df_path_2))
    
    st.write(f"Number of connections for that location: {list_number_connections[LOCATION]}")
    st.write(f"Average number of connections: {pd.Series(list_number_connections).mean().round()}")
    st.write(f"Average distance total: {pd.Series(distance_total).mean().round()}")
    
    st.pydeck_chart(pydeck_obj=r, use_container_width=True)


elif selected == '📋':
    st.dataframe(gdf_point.drop('geometry',axis=1))
    

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
