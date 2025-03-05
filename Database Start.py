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

def main():
    airport_list = get_all_airports()
    print(airport_list)
    airport_id = airport_list[0] # airport_list is a 2d tuple so we have to do it again to get the value
    airport_id = airport_id[0]
    print(airport_id)
    runway_legth = get_runway_length(airport_id)
    print(runway_legth)
    fuel_price = get_fuel_price(airport_id)
    print(fuel_price)

main()

# Needed Functions
'''
get all planes
get all pilots
'''
#Note:
'''def set_key(username, key, password):
    sql = "SELECT Username FROM users WHERE Username = %s"
    username1 = (username, )
    mycursor.execute(sql, username1)
    myresult = mycursor.fetchall()
    if myresult:
        sql = "SELECT Password FROM users WHERE Username = %s"
        mycursor.execute(sql, username1)
        password2 = mycursor.fetchall()
        if password2[0][0] == password:
            print("Password matched")
            sql = "UPDATE users SET RSA_Key = %s WHERE Username = %s"
            key1 = (key, username, )
            mycursor.execute(sql, key1)
            mydb.commit()
    else:
        sql = "INSERT INTO users (Username, RSA_Key, Password) VALUES (%s, %s, %s)"
        val = (username, key, password, )
        mycursor.execute(sql, val)
        mydb.commit()
'''