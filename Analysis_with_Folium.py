import folium
import pandas as pd
# Import folium MarkerCluster plugin
from folium.plugins import MarkerCluster
# Import folium MousePosition plugin
from folium.plugins import MousePosition
# Import folium DivIcon plugin
from folium.features import DivIcon

# Download and read the `spacex_launch_geo.csv`
from js import fetch
import io

URL = 'https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/datasets/spacex_launch_geo.csv'
resp = await fetch(URL)
spacex_csv_file = io.BytesIO((await resp.arrayBuffer()).to_py())
spacex_df=pd.read_csv(spacex_csv_file)

# Select relevant sub-columns: `Launch Site`, `Lat(Latitude)`, `Long(Longitude)`, `class`
spacex_df = spacex_df[['Launch Site', 'Lat', 'Long', 'class']]
launch_sites_df = spacex_df.groupby(['Launch Site'], as_index=False).first()
launch_sites_df = launch_sites_df[['Launch Site', 'Lat', 'Long']]

# Start location is NASA Johnson Space Center
nasa_coordinate = [29.559684888503615, -95.0830971930759]
site_map = folium.Map(location=nasa_coordinate, zoom_start=10)

# Create a blue circle at NASA Johnson Space Center's coordinate with a popup label showing its name
circle = folium.Circle(nasa_coordinate, radius=1000, color='#d35400', fill=True).add_child(folium.Popup('NASA Johnson Space Center'))
# Create a blue circle at NASA Johnson Space Center's coordinate with a icon showing its name
marker = folium.map.Marker(
    nasa_coordinate,
    # Create an icon as a text label
    icon=DivIcon(
        icon_size=(20,20),
        icon_anchor=(0,0),
        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % 'NASA JSC',
        )
    )
site_map.add_child(circle)
site_map.add_child(marker)

# Initial the map
site_map = folium.Map(location=nasa_coordinate, zoom_start=5)
# For each launch site, add a Circle object based on its coordinate (Lat, Long) values. In addition, add Launch site name as a popup label
for _, row in launch_sites_df.iterrows():
    circle = folium.Circle([row['Lat'], row['Long']], radius=1000, color='#d35400', fill=True).add_child(folium.Popup(row['Launch Site']))
    marker = folium.map.Marker([row['Lat'], row['Long']], icon=DivIcon(icon_size=(20,20),icon_anchor=(0,0), \
                                                        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % row['Launch Site'], ))
    site_map.add_child(circle)
    site_map.add_child(marker)

#Mark the success/failed launches for each site on the map
#Marker clusters can be a good way to simplify a map containing many markers having the same coordinate.
marker_cluster = MarkerCluster()
# Apply a function to check the value of `class` column
# If class=1, marker_color value will be green
# If class=0, marker_color value will be red
spacex_df['marker_color'] = spacex_df['class'].apply(lambda x: 'green' if x==1 else 'red')
# Add marker_cluster to current site_map
site_map.add_child(marker_cluster)

# for each row in spacex_df data frame
# create a Marker object with its coordinate
# and customize the Marker's icon property to indicate if this launch was successed or failed, 
# e.g., icon=folium.Icon(color='white', icon_color=row['marker_color']
for index, record in spacex_df.iterrows():
    # TODO: Create and add a Marker cluster to the site map
    # marker = folium.Marker(...)
    marker = folium.map.Marker([record['Lat'], record['Long']], \
                               icon=folium.Icon(icon_size=(20,20),icon_anchor=(0,0), color='white', icon_color=record['marker_color'],\
                                            html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % record['Launch Site'], ))
    marker_cluster.add_child(marker)
# Add Mouse Position to get the coordinate (Lat, Long) for a mouse over on the map
formatter = "function(num) {return L.Util.formatNum(num, 5);};"
mouse_position = MousePosition(
    position='topright',
    separator=' Long: ',
    empty_string='NaN',
    lng_first=False,
    num_digits=20,
    prefix='Lat:',
    lat_formatter=formatter,
    lng_formatter=formatter,
)

site_map.add_child(mouse_position)

from math import sin, cos, sqrt, atan2, radians

def calculate_distance(lat1, lon1, lat2, lon2):
    # approximate radius of earth in km
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance
# find coordinate of the closet coastline
# e.g.,: Lat: 28.56367  Lon: -80.57163
# distance_coastline = calculate_distance(launch_site_lat, launch_site_lon, coastline_lat, coastline_lon)
distance_coastline = calculate_distance(28.563197, -80.576820, 28.56302, -80.56782)
distance_marker = folium.Marker(
    [28.56302, -80.56782],
    icon=DivIcon(
        icon_size=(20,20),
        icon_anchor=(0,0),
        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % "{:10.2f} KM".format(distance_coastline),
        )
    )
# Create a `folium.PolyLine` object using the coastline coordinates and launch site coordinate
# lines=folium.PolyLine(locations=coordinates, weight=1)
lines=folium.PolyLine(locations=[(28.563197, -80.576820), (28.56302, -80.56782)], weight=1)
site_map.add_child(distance_marker)
site_map.add_child(lines)

# Create a marker with distance to a closest city, railway, highway, etc.
# Draw a line between the marker to the launch site
site_loc = (28.563197, -80.576820)
railway_loc = (28.56364, -80.58686)
distance_railway = calculate_distance(site_loc[0], site_loc[1], railway_loc[0], railway_loc[1])
distance_marker = folium.Marker(
    list(railway_loc),
    icon=DivIcon(
        icon_size=(20,20),
        icon_anchor=(0,0),
        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % "{:10.2f} KM".format(distance_railway),
        )
    )
lines=folium.PolyLine(locations=[site_loc, railway_loc], weight=1)
site_map.add_child(distance_marker)
site_map.add_child(lines)

site_loc = (28.563197, -80.576820)
highway_loc = (28.56312, -80.57067)
distance_highway = calculate_distance(site_loc[0], site_loc[1], highway_loc[0], highway_loc[1])
distance_marker = folium.Marker(
    list(highway_loc),
    icon=DivIcon(
        icon_size=(20,20),
        icon_anchor=(0,0),
        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % "{:10.2f} KM".format(distance_highway),
        )
    )
lines=folium.PolyLine(locations=[site_loc, highway_loc], weight=1)
site_map.add_child(distance_marker)
site_map.add_child(lines)

site_loc = (28.563197, -80.576820)
city_loc = (28.1035, -80.64274)
distance_city = calculate_distance(site_loc[0], site_loc[1], city_loc[0], city_loc[1])
distance_marker = folium.Marker(
    list(city_loc),
    icon=DivIcon(
        icon_size=(20,20),
        icon_anchor=(0,0),
        html='<div style="font-size: 12; color:#d35400;"><b>%s</b></div>' % "{:10.2f} KM".format(distance_city),
        )
    )
lines=folium.PolyLine(locations=[site_loc, city_loc], weight=1)
site_map.add_child(distance_marker)
site_map.add_child(lines)










