import math
import random

def haversine_dist(c1, c2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # Earth radius in kilometers (mean radius)
    R = 6371.0
    
    # Distance in kilometers
    return R * c
    
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
    dist_matrix = [[haversine_dist(cities[i], cities[j]) for j in range(num_cities)] for i in range(num_cities)]
    curr_rt = list(range(num_cities))
    random.shuffle(curr_rt)
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