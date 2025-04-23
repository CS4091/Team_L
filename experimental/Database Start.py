import socket
import mysql.connector

mydb = mysql.connector.connect(
    host = "localhost",
    user = "BRP_admin",
    password = "BRPtest123",
    database = "brp"
)\

mycursor = mydb.cursor()

def get_all_airports():
    sql = "SELECT Airport_ID FROM airports"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"
    
def get_all_pilots():
    sql = "SELECT Pilot_ID FROM pilots"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def get_all_planes():
    sql = "SELECT Plane_ID FROM planes"
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def insert_new_airport():
    sql = "INSERT INTO airports (Airport_ID, Runway_Length, Fuel_Price) VALUES (%s, %s, %s)"
    #grab next airport id
    airport_list = get_all_airports()
    airport_id = airport_list[-1]
    airport_id = airport_id[0]
    airport_id = airport_id + 1
    airport_length = input("What is the length of the airports runway? ")
    fuel_price = input("What is the price of fuel at the runway? ")
    val = (airport_id, airport_length, fuel_price, )
    mycursor.execute(sql, val)
    mydb.commit()

def insert_new_pilot():
    sql = "INSERT INTO pilots (Pilot_ID, Available) VALUES (%s, %s)"
    #grab next pilot id
    pilot_list = get_all_pilots()
    pilot_id = pilot_list[-1]
    pilot_id = pilot_id[0]
    pilot_id = pilot_id + 1
    available = input("Is the pilot available? (0 for no, 1 for yes) ")
    val = (pilot_id, available, )
    mycursor.execute(sql, val)
    mydb.commit()

def insert_new_plane():
    sql = "INSERT INTO planes (Plane_ID, Fuel_Use, Maintenance_Cost, Location) VALUES (%s, %s, %s, %s)"
    #grab next plane id
    plane_list = get_all_planes()
    plane_id = plane_list[-1]
    plane_id = plane_id[0]
    plane_id = plane_id + 1
    fuel_use = input("What is the fuel use of this plane? ")
    maintenance_cost = input("What is the maintenance cost of this plane? ")
    location = input("What is the location of this plane? ")
    val = (plane_id, fuel_use, maintenance_cost, location, )
    mycursor.execute(sql, val)
    mydb.commit()

def get_runway_length(airport_id):
    sql = "SELECT Runway_Length FROM airports WHERE Airport_ID = %s"
    airport_id = (airport_id, )
    mycursor.execute(sql, airport_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def get_fuel_price(airport_id):
    sql = "SELECT Fuel_Price FROM airports WHERE Airport_ID = %s"
    airport_id = (airport_id, )
    mycursor.execute(sql, airport_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def get_pilot_availability(pilot_id):
    sql = "SELECT Available FROM pilots WHERE Pilot_ID = %s"
    pilot_id = (pilot_id, )
    mycursor.execute(sql, pilot_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def get_plane_fuel_use(plane_id):
    sql = "SELECT Fuel_Use FROM planes WHERE Plane_ID = %s"
    plane_id = (plane_id, )
    mycursor.execute(sql, plane_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def get_plane_maintenance_cost(plane_id):
    sql = "SELECT Maintenance_Cost FROM planes WHERE Plane_ID = %s"
    plane_id = (plane_id, )
    mycursor.execute(sql, plane_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"
    
def get_plane_location(plane_id):
    sql = "SELECT Location FROM planes WHERE Plane_ID = %s"
    plane_id = (plane_id, )
    mycursor.execute(sql, plane_id)
    myresult = mycursor.fetchall()
    if myresult:
        return myresult
    else:
        return "Fail"

def update_runway_length(airport_id):
    sql = "UPDATE airports SET Runway_Length = %s WHERE Airport_ID = %s"
    runway_length = input("What is the new runway length? ")
    val = (runway_length, airport_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def update_fuel_price(airport_id):
    sql = "UPDATE airports SET Fuel_Price = %s WHERE Airport_ID = %s"
    fuel_price = input("What is the new fuel price? ")
    val = (fuel_price, airport_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def update_pilot_availability(pilot_id):
    sql = "UPDATE pilots SET Available = %s WHERE Pilot_ID = %s"
    availability = input("What is the new availability? ")
    val = (availability, pilot_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def update_plane_fuel_use(plane_id):
    sql = "UPDATE planes SET Fuel_Use = %s WHERE Plane_ID = %s"
    fuel_use = input("What is the new fuel use? ")
    val = (fuel_use, plane_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def update_plane_maintenance_cost(plane_id):
    sql = "UPDATE planes SET Maintenance_Cost = %s WHERE Plane_ID = %s"
    maintenance_cost = input("What is the new maintenance cost? ")
    val = (maintenance_cost, plane_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def update_plane_location(plane_id):
    sql = "UPDATE planes SET Location = %s WHERE Plane_ID = %s"
    location = input("What is the new location? ")
    val = (location, plane_id, )
    mycursor.execute(sql, val)
    mydb.commit()

def main():
    # airport_id = 1
    # pilot_id = 1
    # plane_id = 1

    print ("END")
    # Working: #
    #airport_list = get_all_airports()
    #print(airport_list)
    #airport_id = airport_list[0] # airport_list is a 2d tuple so we have to do it again to get the value
    #airport_id = airport_id[0]
    #print(airport_id)

    #insert_new_airport()

    #pilot_list = get_all_pilots()
    #print(pilot_list)

    #insert_new_pilot()

    #plane_list = get_all_planes()
    #print(plane_list)

    #insert_new_plane()

    #runway_legth = get_runway_length(airport_id)
    #print(runway_legth)

    #fuel_price = get_fuel_price(airport_id)
    #print(fuel_price)

    #pilot_id = get_pilot_availability(pilot_id)
    #print(pilot_id)

    #plane_fuel = get_plane_fuel_use(plane_id)
    #print(plane_fuel)

    #plane_maintenance = get_plane_maintenance_cost(plane_id)
    #print(plane_maintenance)

    #location = get_plane_location(plane_id)
    #print(location)

    #update_runway_length(airport_id)
    
    #update_fuel_price(airport_id)

    #update_pilot_availability(pilot_id)

    #update_plane_fuel_use(plane_id)
    
    #update_plane_maintenance_cost(plane_id)
    
    #update_plane_location(plane_id)

main()
