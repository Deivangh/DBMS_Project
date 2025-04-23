# -*- coding: utf-8 -*-
"""
Created on Sat Apr 12 01:58:01 2025

@author: Deivangh
"""

from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Global connection variables
myConnection = None
cursor = None
userName = ""
password = ""

# Helper to connect to MySQL
def MYSQLconnectionCheck():
    global myConnection
    global cursor
    global userName
    global password
    userName = "root"
    password = "Deivangh26$"
    myConnection = mysql.connector.connect(
        host="localhost",
        user=userName,
        passwd=password,
        auth_plugin='mysql_native_password'
    )
    if myConnection:
        cursor = myConnection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS HMS")
        cursor.execute("COMMIT")
        return myConnection
    else:
        return None

def MYSQLconnection():
    global myConnection
    global cursor
    myConnection = mysql.connector.connect(
        host="localhost", user=userName, passwd=password, database="HMS", auth_plugin='mysql_native_password'
    )
    if myConnection:
        cursor = myConnection.cursor()
        return myConnection
    else:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/enter_customer', methods=['GET', 'POST'])
def enter_customer():
    if request.method == 'POST':
        cid = request.form['cid']
        name = request.form['name']
        address = request.form['address']
        age = request.form['age']
        nationality = request.form['nationality']
        phoneno = request.form['phoneno']
        email = request.form['email']

        # Insert customer data into MySQL
        if myConnection:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS C_DETAILS (
                    CID VARCHAR(20), 
                    C_NAME VARCHAR(30), 
                    C_ADDRESS VARCHAR(30), 
                    C_AGE VARCHAR(30),
                    C_COUNTRY VARCHAR(30),
                    P_NO VARCHAR(30),
                    C_EMAIL VARCHAR(30)
                )
            """)
            cursor.execute("""
                INSERT INTO C_DETAILS (CID, C_NAME, C_ADDRESS, C_AGE, C_COUNTRY, P_NO, C_EMAIL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (cid, name, address, age, nationality, phoneno, email))
            cursor.execute("COMMIT")
            return redirect(url_for('home'))
    return render_template('enter_customer.html')

@app.route('/book_room', methods=['GET', 'POST'])
def book_room():
    if request.method == 'POST':
        cid = request.form['cid']
        room_type = request.form['room_type']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        
        # Insert booking data into MySQL
        if myConnection:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS BOOKINGS (
                    CID VARCHAR(20),
                    ROOM_TYPE VARCHAR(20),
                    CHECK_IN DATE,
                    CHECK_OUT DATE,
                    FOREIGN KEY (CID) REFERENCES C_DETAILS(CID)
                )
            """)
            cursor.execute("""
                INSERT INTO BOOKINGS (CID, ROOM_TYPE, CHECK_IN, CHECK_OUT)
                VALUES (%s, %s, %s, %s)
            """, (cid, room_type, check_in, check_out))
            cursor.execute("COMMIT")
            return redirect(url_for('home'))
    return render_template('book_room.html')

@app.route('/calculate_room_rent', methods=['GET', 'POST'])
def calculate_room_rent():
    if request.method == 'POST':
        room_type = request.form['room_type']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        
        # Calculate number of nights
        from datetime import datetime
        
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        days_stayed = (check_out_date - check_in_date).days

        # Define room prices
        room_prices = {
            'Single': 1000,
            'Double': 2000,
            'Suite': 5000
        }
        
        if room_type in room_prices:
            room_price = room_prices[room_type]
            total_rent = room_price * days_stayed
            return render_template('room_rent_result.html', total_rent=total_rent, room_type=room_type, days_stayed=days_stayed)
        else:
            return "Invalid room type"
    return render_template('calculate_room_rent.html')


@app.route('/generate_bill', methods=['GET', 'POST'])
def generate_bill():
    if request.method == 'POST':
        cid = request.form['cid']
        room_type = request.form['room_type'].capitalize()  # suite → Suite
        days_stayed = int(request.form['days_stayed'])
        restaurant_bill = float(request.form['restaurant_bill'])
        gaming_bill = float(request.form['gaming_bill'])

        room_prices = {
            'Single': 1000,
            'Double': 2000,
            'Suite': 5000
        }

        if room_type in room_prices:
            room_price = room_prices[room_type]
            room_rent = room_price * days_stayed
            total_bill = room_rent + restaurant_bill + gaming_bill

            if myConnection:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS BILL_DETAILS (
                        CID VARCHAR(20),
                        ROOM_RENT FLOAT,
                        RESTAURANT_BILL FLOAT,
                        GAMING_BILL FLOAT,
                        TOTAL_BILL FLOAT,
                        FOREIGN KEY (CID) REFERENCES C_DETAILS(CID)
                    )
                """)
                cursor.execute("SELECT * FROM BILL_DETAILS WHERE CID = %s", (cid,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute("""
                        INSERT INTO BILL_DETAILS (CID, ROOM_RENT, RESTAURANT_BILL, GAMING_BILL, TOTAL_BILL)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (cid, room_rent, restaurant_bill, gaming_bill, total_bill))
                    cursor.execute("COMMIT")

            return render_template('bill_result.html', total_bill=total_bill)
        else:
            return "Invalid room type"
    return render_template('generate_bill.html')


@app.route('/lookup_bill', methods=['GET', 'POST'])
def lookup_bill():
    if request.method == 'POST':
        cid = request.form['cid']
        con = mysql.connector.connect(
            host='localhost', user='root', password='Deivangh26$', database='HMS')
        cur = con.cursor()

        # Step 1: Get Booking Details
        cur.execute("SELECT cid, room_type, check_in, check_out FROM bookings WHERE cid = %s", (cid,))
        bookings = cur.fetchall()

        # Step 2: Get Bill Details directly from BILL_DETAILS
        cur.execute("SELECT cid, room_rent, restaurant_bill, gaming_bill, total_bill FROM bill_details WHERE cid = %s", (cid,))
        bill_details = cur.fetchall()

        con.close()

        return render_template('lookup_bill.html', bookings=bookings, bill_details=bill_details)

    return render_template('lookup_bill_form.html')

# Other routes for booking, bill calculations, etc. will be defined similarly

if __name__ == "__main__":
    myConnection = MYSQLconnectionCheck()
    if myConnection:
        MYSQLconnection()
        app.run(debug=True)
    else:
        print("ERROR ESTABLISHING MYSQL CONNECTION!")






















































'''
from flask import Flask, request, render_template, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Deivangh26$",  # Your MySQL password
    database="hotel_db"
)
cursor = conn.cursor()

# Functions for DB operations
def add_customer(name, phone, email):
    cursor.execute("INSERT INTO Customer (name, phone, email) VALUES (%s, %s, %s)", (name, phone, email))
    conn.commit()
    return cursor.lastrowid

def add_room(room_type, price):
    cursor.execute("INSERT INTO Room (room_type, price) VALUES (%s, %s)", (room_type, price))
    conn.commit()

def book_room(customer_id, room_type, check_in, check_out):
    cursor.execute("SELECT room_id FROM Room WHERE room_type=%s AND is_available=TRUE LIMIT 1", (room_type,))
    room = cursor.fetchone()

    if room:
        room_id = room[0]
        cursor.execute("INSERT INTO Booking (customer_id, room_id, check_in, check_out) VALUES (%s, %s, %s, %s)",
                       (customer_id, room_id, check_in, check_out))
        cursor.execute("UPDATE Room SET is_available=FALSE WHERE room_id=%s", (room_id,))
        conn.commit()
        return "Room booked successfully!"
    else:
        return "No available room for the selected type."

# Routes for frontend
@app.route("/")
def home():
    return render_template("add_room.html")

@app.route("/add-room", methods=["POST"])
def handle_add_room():
    room_type = request.form['room_type']
    price = request.form['price']
    add_room(room_type, price)
    return "Room added!"

@app.route("/book-room", methods=["POST"])
def handle_book_room():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    room_type = request.form['room_type']
    check_in = request.form['check_in']
    check_out = request.form['check_out']
    customer_id = add_customer(name, phone, email)
    result = book_room(customer_id, room_type, check_in, check_out)
    return result

@app.route("/bookings", methods=["GET"])
def bookings():
    cursor.execute("""
        SELECT b.booking_id, c.name, r.room_type, b.check_in, b.check_out
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        JOIN Room r ON b.room_id = r.room_id
    """)
    bookings = cursor.fetchall()
    return jsonify(bookings)

# Shutdown
@app.teardown_appcontext
def close_connection(exception):
    cursor.close()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)


'''

































'''
from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Deivangh26$",
    database="hotel_db"
)
cursor = conn.cursor()

# === Backend Functions ===
def add_customer(name, phone, email):
    cursor.execute("INSERT INTO Customer (name, phone, email) VALUES (%s, %s, %s)", (name, phone, email))
    conn.commit()
    return cursor.lastrowid

def add_room(room_type, price):
    cursor.execute("INSERT INTO Room (room_type, price) VALUES (%s, %s)", (room_type, price))
    conn.commit()

def book_room(customer_id, room_type, check_in, check_out):
    cursor.execute("SELECT room_id FROM Room WHERE room_type=%s AND is_available=TRUE LIMIT 1", (room_type,))
    room = cursor.fetchone()
    if room:
        room_id = room[0]
        cursor.execute("INSERT INTO Booking (customer_id, room_id, check_in, check_out) VALUES (%s, %s, %s, %s)",
                       (customer_id, room_id, check_in, check_out))
        cursor.execute("UPDATE Room SET is_available=FALSE WHERE room_id=%s", (room_id,))
        conn.commit()
        return True
    return False

def get_bookings():
    cursor.execute("""
        SELECT b.booking_id, c.name, r.room_type, b.check_in, b.check_out
        FROM Booking b
        JOIN Customer c ON b.customer_id = c.customer_id
        JOIN Room r ON b.room_id = r.room_id
    """)
    return cursor.fetchall()

# === Flask Routes ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-room', methods=['GET', 'POST'])
def add_room_route():
    if request.method == 'POST':
        room_type = request.form['room_type']
        price = float(request.form['price'])
        add_room(room_type, price)
        return redirect('/')
    return render_template('add_room.html')

@app.route('/book-room', methods=['GET', 'POST'])
def book_room_route():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        room_type = request.form['room_type']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        customer_id = add_customer(name, phone, email)
        success = book_room(customer_id, room_type, check_in, check_out)
        return render_template('book_room.html', success=success)
    return render_template('book_room.html')

@app.route('/bookings')
def bookings():
    all_bookings = get_bookings()
    return render_template('bookings.html', bookings=all_bookings)

if __name__ == '__main__':
    app.run(debug=True)
'''