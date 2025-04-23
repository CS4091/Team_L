import math
import random

def haversine_dist(c1, c2):
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371.0 # Earth radius in kilometers (mean radius)
    
    return R * c # Distance in kilometers
    
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
    
def get_dist_matrix(cities):
    return [[haversine_dist(cities[i], cities[j]) for j in range(len(cities))] for i in range(len(cities))]

class TSPHeuristic:
    def sim_ann_TSP(cities, init_temp, cool_rate, min_temp):
        num_cities = len(cities)
        dist_matrix = get_dist_matrix(cities)
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
        
    def brute_force(cities):
        from permutations import permutations
        # find all possible path permutations
        num_cities = len(cities)
        dist_matrix = get_dist_matrix(cities)
        
        possiblePaths = list(permutations(range(1, num_cities), r=num_cities-1))
        # stores the length of all paths for sorting later
        pathLength = []

        for i in possiblePaths:
            currentLength = 0
            # add the lengths of the first and last path
            currentLength += dist_matrix[0][i[0]] + dist_matrix[0][i[-1]]
            # add the lengths of all other paths
            for j in range(num_cities-2):
                currentLength += dist_matrix[i[j]][i[j+1]]
            pathLength.append(currentLength)

        # find the shortest path
        shortestPathIndex = min(range(len(pathLength)), key=pathLength.__getitem__)
        # convert shortest path to string
        shortestPath = possiblePaths[shortestPathIndex]
        cost = pathLength[shortestPathIndex]
        return shortestPath, cost
        
    def nearest_neighbor(cities):
        visitedCities = [0]
        currentCity = 0
        cost = 0
        num_cities = len(cities)
        dist_matrix = get_dist_matrix(cities)
        while len(visitedCities) < len(dist_matrix):
            minLength = max(dist_matrix[currentCity])
            for i in range(num_cities):
                if dist_matrix[currentCity][i] < minLength and i not in visitedCities:
                    minLength = dist_matrix[currentCity][i]
            cost += minLength
            currentCity = dist_matrix[currentCity].index(minLength)
            visitedCities.append(currentCity)
        cost += dist_matrix[0][visitedCities[-1]]
        visitedCities.pop(0)
        return visitedCities, cost