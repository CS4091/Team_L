# A program to brute-force solve the traveling salesman problem.
# Will be used to compare the speed of other heuristics

from itertools import permutations

# bruteForce: as a parameter, takes the filepath of a text file where line 1 is the 
#   number of cities 'n' and lines 2-n+1 are a space-separated matrix of city-to-city travel costs
# Returns a tuple (shortestPath, cost)
def bruteForce(filepath: str):
    matrix = []
    input = open(filepath, 'r')
    # takes the first line of the file as the number of cities
    numCities = int(input.readline())
    # stores the matrix in the file as a list of tuples
    for line in input.readlines():
        matrix.append([int(item) for item in line.split()])

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
    shortestPath = possiblePaths[shortestPathIndex]
    cost = pathLength[shortestPathIndex]
    return shortestPath, cost
#print(f'The shortest path is 0,{shortestPath},0 with a cost of {pathLength[shortestPathIndex]}')
print(bruteForce('test_matrix.txt'))