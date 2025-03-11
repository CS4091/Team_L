import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import math
from TSP_Ex import sim_ann_TSP

# Load a GeoDataFrame with real-world coordinates
world = gpd.read_file('geopandas_maps/ne_110m_admin_0_countries.shp')

# Example: List of real-world coordinates (latitude, longitude)
cities = [
    (48.8566, 2.3522),  # Paris
    (51.5074, -0.1278), # London
    (40.7128, -74.0060),# New York
    (35.6895, 139.6917),# Tokyo
    (55.7558, 37.6173), # Moscow
    (45.3279, 14.4410), # Rijeka
    (41.2141, 13.5710), # Gaeta
    (37.5665, 126.9780),# Seoul
    (37.7749, -122.4194),# San Francisco
    (31.2304, 121.4737)  # Shanghai
    # Add more cities as needed
]

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
