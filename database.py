import mysql.connector # Required to connect to the database

# Create a class for connecting to MySQL database
class MySql:
    # Establish a connection to the MySQL database with provided credentials
    mydb = mysql.connector.connect(
        host="localhost",   # Database host name
        user="root",        # Database user name
        password="",        # Database user password
        database="store_monitoring"     # Name of the database to connect to
    )
