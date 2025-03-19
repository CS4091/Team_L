
import math
import random
import tkinter as tk
import time

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

def sim_ann_TSP(cities, init_temp, cool_rate, min_temp, globe=False):
    num_cities = len(cities)
    func = haversine_dist if globe else euc_dist
    dist_matrix = [[func(cities[i], cities[j]) for j in range(num_cities)] for i in range(num_cities)]
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

def draw_route(canvas, cities, rt):
    canvas.delete("all")
    for i in range(len(rt)):
        c1 = cities[rt[i]]
        c2 = cities[rt[(i+1) % len(rt)]]
        canvas.create_line(c1[0]*5, c1[1]*5, c2[0]*5, c2[1]*5, fill='blue')
        canvas.create_oval(c1[0]*5-5, c1[1]*5-5, c1[0]*5+5, c1[1]*5+5, fill='red')

if __name__ == "__main__":
    num_cities = 10
    cities = [(random.randint(0, 100), random.randint(0, 100)) for _ in range(num_cities)]
    
    init_temp = 1000
    cool_rate = 0.995
    min_temp = 1e-3
    start = time.time()

    best_rt, best_dist = sim_ann_TSP(cities, init_temp, cool_rate, min_temp)

    end = time.time()

    print("Best route: ", best_rt)
    print("Best distance: ", best_dist)
    print("City Coords: ", cities)
    print(f"Execution time: {end - start} s")

    root = tk.Tk()
    root.title("TSP - Annealing")

    canvas = tk.Canvas(root, width=600, height=600, bg='white')
    canvas.pack()

    draw_route(canvas, cities, best_rt)

    root.mainloop()