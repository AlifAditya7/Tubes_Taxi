import pandas as pd 
import datetime , calendar
import folium
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import lxml


# Scrapping Data
url = "https://dinarna.github.io/100-taxis-running-in-Portugal/"
res = requests.get(url)
soup = BeautifulSoup(res.content,'lxml')
table = soup.find_all('table')[0] 
data = pd.read_html(str(table))[0]

# Data Preprocess
data.TRIP_PATH = data.TRIP_PATH.apply(eval)

extract_starting_point = lambda list_ : list_[0]
extract_ending_point = lambda list_ : list_[-1]

data["START_LOC"] = data.TRIP_PATH.apply(extract_starting_point)
data["END_LOC"] = data.TRIP_PATH.apply(extract_ending_point)

# Memetakan ulang nilai kolom CALL_TYPE lebih detail
CALL_TYPES = {
              "A":"PUSAT",
              "B":"LANGSUNG",
              "C":"LAINNYA"
             }

data.CALL_TYPE = data.CALL_TYPE.map(CALL_TYPES)

# Wilayah di kota ini yang menjadi tujuan paling umum di hari Senin
day_names = list(calendar.day_name)
get_day = lambda timestamp: day_names[datetime.datetime.fromtimestamp(timestamp).weekday()]
data["week_day"] = data.TIMESTAMP.apply(get_day)

# Di mana titik awal dan akhir yang paling umum pada Senin Pagi dari jam 6 pagi sampai jam 9 pagi
extract_hour = lambda timestamp : datetime.datetime.fromtimestamp(timestamp).hour

data["hour"] = data.TIMESTAMP.apply(extract_hour)

Q5_data = data[(data.week_day=="Monday") & (data.hour > 6) & (data.hour < 9)]

# Visualisasi Streamlit
view = "Titik Jemput"

APP_TITLE = 'Taxis Running In Portugal🗺️'

def main():
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)

if __name__ == "__main__":
    main()

if "view" not in view:
    view = "Titik Jemput"

if "visibility" not in st.session_state:
    st.session_state.visibility = "visible"
    st.session_state.disabled = False

with st.sidebar:
    st.header('MAIN MENU')
    view = st.selectbox(
        "What\'s View Would You See?",
        key="view",
        options=['Titik penjemputan terbaik', 'Titik penjemputan terbaik untuk perjalanan berdasarkan cara untuk memintal layanan taksi', 'Wilayah di kota ini yang menjadi tujuan paling umum di hari Senin','Titik awal dan akhir yang paling umum pada Senin Pagi dari jam 6 pagi sampai jam 9 pagi','Jalan yang memiliki lalu lintas lebih padat pada jam sibuk']
    )

if view == 'Titik penjemputan terbaik':
    tab1, tab2 = st.tabs(["Map Jemput Terbaik", "Rate Order Taksi"])
    with tab1:
        st.write('Wilayah kota mana yang merupakan titik penjemputan terbaik')
        Map = folium.Map(location=[41.15, -8.62], zoom_start=14)
        for point in data.START_LOC:
            folium.CircleMarker(location=point, radius=1, color="red",weight = 2).add_to(Map)
        st_map = st_folium(Map, width=700, height=450)
    with tab2:
        st.write('Cara paling umum untuk mendapatkan taksi di Porto')
        q1_data = data.CALL_TYPE.value_counts(sort=False)
        st.bar_chart(q1_data)

elif view == 'Titik penjemputan terbaik untuk perjalanan berdasarkan cara untuk memintal layanan taksi':
    st.write('Wilayah kota mana yang merupakan titik penjemputan terbaik untuk perjalanan berdasarkan cara untuk memintal layanan taksi')
    Q3_Map = folium.Map(location=[41.15,-8.62],zoom_start=14)

    colors = {
        "PUSAT":"blue",
        "LANGSUNG":"red",
        "LAINNYA":"purple"
    }
    Q3_data = data [["CALL_TYPE","START_LOC"]]
    for index, row in Q3_data.iterrows():
        folium.CircleMarker(location=row["START_LOC"], radius=1, color=colors[row["CALL_TYPE"]],weight = 2).add_to(Q3_Map)
    st_map = st_folium(Q3_Map, width=700, height=450)

    with st.sidebar:
        st.subheader('Keterangan')
        st.color_picker('Blue : PUSAT','#0000FF')
        st.color_picker('Red : LANGSUNG','#FF0000')
        st.color_picker('Purple : LAINNYA','#800080')

elif view == 'Wilayah di kota ini yang menjadi tujuan paling umum di hari Senin':
    st.write('Wilayah di kota ini yang menjadi tujuan paling umum di hari Senin')
    Q4_data = data[data.week_day == "Monday"]
    Q4_map = folium.Map(location=[41.15,-8.62], zoom_start=15)
    for loc in Q4_data.END_LOC:
        folium.CircleMarker(location=loc, radius=1, color="red",weight = 2).add_to(Q4_map)
    st_map = st_folium(Q4_map, width=700, height=450)
        
elif view == 'Titik awal dan akhir yang paling umum pada Senin Pagi dari jam 6 pagi sampai jam 9 pagi':
    st.write('Di mana titik awal dan akhir yang paling umum pada Senin Pagi dari jam 6 pagi sampai jam 9 pagi')
    Q5_map = folium.Map(location=[41.15,-8.62],zoom_start=14)
    put_start_loc = lambda loc : folium.CircleMarker(loc,color="red",radius=1,weight= 2).add_to(Q5_map)
    put_end_loc = lambda loc : folium.CircleMarker(loc,color="blue",radius=1,weight= 2).add_to(Q5_map)

    Q5_data.START_LOC.apply(put_start_loc)
    Q5_data.END_LOC.apply(put_end_loc)
    st_map = st_folium(Q5_map, width=700, height=450)

    with st.sidebar:
        st.subheader('Keterangan')
        st.color_picker('Red : Titik Awal','#FF0000')
        st.color_picker('Blue : Titik Akhir','#0000FF')

elif view == 'Jalan yang memiliki lalu lintas lebih padat pada jam sibuk' :
    tab1, tab2 = st.tabs(["Map Rute Terpadat", "Jam Sibuk Porto"])
    with tab1:
        st.write('Jalan yang memiliki lalu lintas lebih padat pada jam sibuk')
        Q7_data = data[data.hour == 16]
        coords = Q7_data.TRIP_PATH.iloc[0]
        Q7_map = folium.Map(location=[41.15,-8.62],zoom_start=14)
        for coords in Q7_data.TRIP_PATH:
            folium.PolyLine(coords,color="red",weight=2,opacity=0.05).add_to(Q7_map)
        st_map = st_folium(Q7_map, width=700, height=450)
    with tab2:
        st.write('Jam Sibuk Di Porto')
        data7 = data.hour.value_counts().sort_index()
        st.bar_chart(data7)
