# A program to brute-force solve the traveling salesman problem.
# Will be used to compare the speed of other heuristics

from itertools import permutations

# NOTE: it's possible to remove half of the paths since they're 
# inverses of each other but that's not implemented yet

# a 2d tuple to store a graph, with its connections. Hard-coded for now
matrix = ((0, 20, 40, 15, 29, 10),
          (20, 0, 62, 43, 9, 8),
          (40, 62, 0, 21, 5, 21),
          (15, 43, 21, 0, 42, 17),
          (29, 9, 5, 42, 0, 15),
          (10, 8, 21, 17, 15, 0))

numCities = 6

# find all possible path permutations
possiblePaths = list(permutations(range(1, numCities), r=numCities-1))
# stores the length of all paths for sorting later
pathLength = []

for i in possiblePaths:
    currentLength = 0
    # add the lengths of the first and last path
    currentLength += matrix[0][i[0]] + matrix[0][i[-1]]
    # add the lengths of all other paths
    for j in range(numCities-2):
        currentLength += matrix[i[j]][i[j+1]]
    pathLength.append(currentLength)

# find the shortest path
shortestPathIndex = min(range(len(pathLength)), key=pathLength.__getitem__)
# convert shortest path to string
shortestPath = ",".join(str(x) for x in possiblePaths[shortestPathIndex])
print(f'The shortest path is 0,{shortestPath},0 with a cost of {pathLength[shortestPathIndex]}')