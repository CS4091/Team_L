
# nearestNeighbor: as a parameter, takes the filepath of a text file where line 1 is the 
#   number of cities 'n' and lines 2 - n+1 are a space-separated matrix of city-to-city travel costs
# Returns a tuple (shortestPath, cost)
def nearestNeighbor(filepath: str):
    matrix = []
    input = open(filepath, 'r')
    # takes the first line of the file as the number of cities
    numCities = int(input.readline())
    # stores the matrix in the file as a list of tuples
    for line in input.readlines():
        matrix.append([int(item) for item in line.split()])

    visitedCities = [0]
    currentCity = 0
    cost = 0
    # travels through the graph, adding last visited city's nearest neighbor
    while len(visitedCities) < len(matrix):
        minLength = max(matrix[currentCity])
        for i in range(numCities):
            if matrix[currentCity][i] < minLength and i not in visitedCities:
                minLength = matrix[currentCity][i]
        cost += minLength
        currentCity = matrix[currentCity].index(minLength)
        visitedCities.append(currentCity)
    cost += matrix[0][visitedCities[-1]]
    visitedCities.pop(0)
    return tuple(visitedCities), cost


print(nearestNeighbor('test_matrix.txt'))