import mysql.connector
from mysql.connector import Error


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "root"
DB_NAME = "meditrack_db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():

    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

    return connection


# ==========================================================
# INSERT / UPDATE / DELETE
# ==========================================================

def execute(query, params=None):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        query,
        params or ()
    )

    connection.commit()

    cursor.close()
    connection.close()


# ==========================================================
# GET ONE RECORD
# ==========================================================

def fetch_one(query, params=None):

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        query,
        params or ()
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result


# ==========================================================
# GET ALL RECORDS
# ==========================================================

def fetch_all(query, params=None):

    connection = get_connection()
    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        query,
        params or ()
    )

    result = cursor.fetchall()

    cursor.close()
    connection.close()

    return result


# ==========================================================
# TEST DATABASE CONNECTION
# ==========================================================

def test_connection():

    try:

        connection = get_connection()

        connection.close()

        return True, "Connected"

    except Error as error:

        return False, str(error)