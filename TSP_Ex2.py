import geopandas as gpd
from geopy import location
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import math, random, sys
from geopy.geocoders import Nominatim

# Load a GeoDataFrame with real-world coordinates
world = gpd.read_file('geopandas_maps/ne_110m_admin_0_countries.shp')

# Example: List of real-world coordinates (latitude, longitude)
cities = []
list_prompt = ""
while list_prompt != "N" and list_prompt != "n":
    list_prompt = str(input("Please input a city name (or n/N to stop): "))
    if list_prompt != "N" and list_prompt != "n":
        geolocator = Nominatim(user_agent="TSP_annealing_example")
        location = geolocator.geocode(list_prompt)
        cities.append((location.latitude, location.longitude))

def euc_dist(c1, c2):
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def tot_dist(rt, dist_matrix):
    distance = 0
    for i in range(len(rt)):
        distance += dist_matrix[rt[i]][rt[(i+1) % len(rt)]]
    return distance

def neighbor(rt):
    neighbor_rt = rt[:]
    i, j = random.sample(range(len(rt)), 2)
    neighbor_rt[i], neighbor_rt[j] = neighbor_rt[j], neighbor_rt[i]
    return neighbor_rt

def sim_ann_TSP(cities, init_temp, cool_rate, min_temp):
    num_cities = len(cities)
    dist_matrix = [[euc_dist(cities[i], cities[j]) for j in range(num_cities)] for i in range(num_cities)]
    curr_rt = list(range(num_cities))
    #random.shuffle(curr_rt)
    curr_rt_cp = curr_rt[1:-1]
    random.shuffle(curr_rt_cp)
    curr_rt = [curr_rt[0]] + curr_rt_cp + [curr_rt[-1]]
    curr_dist = tot_dist(curr_rt, dist_matrix)
    temp = init_temp
    while temp > min_temp:
        neighbor_rt = neighbor(curr_rt)
        neighbor_dist= tot_dist(neighbor_rt, dist_matrix)
        delta= neighbor_dist - curr_dist
        if delta < 0 or random.random() < math.exp(-delta / temp):
            curr_rt = neighbor_rt
            curr_dist= neighbor_dist
        temp *= cool_rate
    return curr_rt, curr_dist

# Convert to Cartesian coordinates for TSP
def latlon_to_cartesian(lat, lon):
    R = 6371  # Earth radius in kilometers
    x = R * math.cos(math.radians(lat)) * math.cos(math.radians(lon))
    y = R * math.cos(math.radians(lat)) * math.sin(math.radians(lon))
    return (x, y)

cartesian_cities = [latlon_to_cartesian(lat, lon) for lat, lon in cities]

# Run the TSP algorithm
init_temp = 1000
cool_rate = 0.995
min_temp = 1e-3
best_rt, best_dist = sim_ann_TSP(cartesian_cities, init_temp, cool_rate, min_temp)

# Convert the best route back to latitude and longitude
best_route_coords = [cities[i] for i in best_rt]

# Create a GeoDataFrame for the route
route_line = LineString([Point(lon, lat) for lat, lon in best_route_coords])
route_gdf = gpd.GeoDataFrame(geometry=[route_line])

# Plot the world map and the route
fig, ax = plt.subplots(1, 1, figsize=(15, 10))
world.plot(ax=ax, color='lightgrey')
route_gdf.plot(ax=ax, color='blue', linewidth=2)
plt.scatter([lon for lat, lon in cities], [lat for lat, lon in cities], color='red')
plt.show()
