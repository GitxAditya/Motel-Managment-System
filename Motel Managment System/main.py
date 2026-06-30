import mysql.connector
from datetime import datetime, date
import os

# ---------------- CONFIGURATION ----------------
DB_NAME = "motel"
DB_PASSWORD = "sqlXaditya"   # <-- your MySQL root password

# ---------------- DATABASE CONNECTIONS ----------------
def connect_root():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASSWORD
    )

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=DB_PASSWORD,
        database=DB_NAME
    )

# ---------------- SETUP DATABASE ----------------
def setup():
    """Create database and tables. Run once."""
    # connect to server and create DB
    conn = connect_root()
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    conn.commit()
    conn.close()

    # connect to DB and create tables
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Customers(
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            phone VARCHAR(20),
            email VARCHAR(255),
            address VARCHAR(255),
            total_stays INT DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Rooms(
            room_no INT PRIMARY KEY,
            type VARCHAR(50),
            price DECIMAL(10,2),
            status VARCHAR(20)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS Bookings(
            booking_id INT AUTO_INCREMENT PRIMARY KEY,
            cust_id INT,
            cust_name VARCHAR(255),
            room_no INT,
            check_in DATE,
            check_out DATE,
            total DECIMAL(10,2),
            status VARCHAR(20)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS GuestInvoices(
            invoice_id INT AUTO_INCREMENT PRIMARY KEY,
            guest_id INT,
            guest_name VARCHAR(255),
            room_number INT,
            nights INT,
            rate_per_night DECIMAL(10,2),
            total_amount DECIMAL(10,2),
            date DATE
        )
    """)

    # Insert sample rooms if not present
    sample_rooms = [
        (101, "Standard", 1500.00, "Available"),
        (102, "Standard", 1500.00, "Available"),
        (103, "Deluxe", 2500.00, "Available"),
        (104, "Deluxe", 2500.00, "Available"),
        (105, "Suite", 4000.00, "Available")
    ]
    for r in sample_rooms:
        try:
            cur.execute("INSERT INTO Rooms (room_no, type, price, status) VALUES (%s,%s,%s,%s)", r)
        except mysql.connector.IntegrityError:
            # room already exists
            pass

    conn.commit()
    conn.close()
    print("\nDatabase and tables created (or already existed). Sample rooms inserted.\n")

# ---------------- CORE FUNCTIONS ----------------
def add_customer_and_book():
    print("\n--- Add Customer & Book Room ---")
    name = input("Enter Name: ").strip()
    phone = input("Phone: ").strip()
    email = input("Email: ").strip()
    address = input("Address: ").strip()

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Customers(name, phone, email, address) VALUES (%s,%s,%s,%s)",
        (name, phone, email, address)
    )
    cust_id = cur.lastrowid
    conn.commit()
    print(f"\nCustomer added. ID = {cust_id}")

    # show available rooms
    cur.execute("SELECT room_no, type, price FROM Rooms WHERE status='Available' ORDER BY room_no")
    rooms = cur.fetchall()
    if not rooms:
        print("No rooms available.")
        conn.close()
        return

    print("\nAvailable Rooms:")
    print(f"{'Room':<6} {'Type':<10} {'Price'}")
    print("-"*30)
    for r in rooms:
        print(f"{r[0]:<6} {r[1]:<10} ₹{float(r[2]):.2f}")

    try:
        room_no = int(input("\nEnter room number to book: ").strip())
    except ValueError:
        print("Invalid room number.")
        conn.close()
        return

    cur.execute("SELECT price FROM Rooms WHERE room_no=%s AND status='Available'", (room_no,))
    price_row = cur.fetchone()
    if not price_row:
        print("Invalid or unavailable room.")
        conn.close()
        return

    price = float(price_row[0])

    check_in = input("Check-in date (YYYY-MM-DD): ").strip()
    check_out = input("Check-out date (YYYY-MM-DD): ").strip()
    try:
        d1 = datetime.strptime(check_in, "%Y-%m-%d").date()
        d2 = datetime.strptime(check_out, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
        conn.close()
        return

    nights = (d2 - d1).days
    if nights <= 0:
        nights = 1

    total = round(nights * price, 2)

    cur.execute("""
        INSERT INTO Bookings (cust_id, cust_name, room_no, check_in, check_out, total, status)
        VALUES (%s,%s,%s,%s,%s,%s,'Active')
    """, (cust_id, name, room_no, check_in, check_out, total))

    cur.execute("UPDATE Rooms SET status='Occupied' WHERE room_no=%s", (room_no,))
    conn.commit()
    conn.close()

    print("\nRoom booked successfully!")
    print(f"Total Amount: ₹{total:.2f}\n")

def view_customers():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, name, phone, email, address, total_stays FROM Customers ORDER BY name")
    rows = cur.fetchall()
    print("\n--- Customer List ---")
    if not rows:
        print("No customers found.\n")
        conn.close()
        return
    print(f"{'ID':<4} {'Name':<20} {'Phone':<12} {'Email':<20} {'Address':<20} {'Stays'}")
    print("-"*90)
    for r in rows:
        print(f"{r[0]:<4} {r[1]:<20} {r[2] or '-':<12} {r[3] or '-':<20} {r[4] or '-':<20} {r[5]}")
    conn.close()
    print("")

def view_rooms():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT room_no, type, price, status FROM Rooms ORDER BY room_no")
    rows = cur.fetchall()
    print("\n--- Room List ---")
    if not rows:
        print("No rooms found.\n")
        conn.close()
        return
    print(f"{'Room':<6} {'Type':<10} {'Price':<10} {'Status'}")
    print("-"*40)
    for r in rows:
        print(f"{r[0]:<6} {r[1]:<10} ₹{float(r[2]):<8.2f} {r[3]}")
    conn.close()
    print("")

def view_bookings():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT booking_id, cust_id, cust_name, room_no, check_in, check_out, total, status FROM Bookings ORDER BY booking_id DESC")
    rows = cur.fetchall()
    print("\n--- Bookings ---")
    if not rows:
        print("No bookings found.\n")
        conn.close()
        return
    print(f"{'BID':<5} {'CID':<5} {'Name':<20} {'Room':<6} {'Check-in':<12} {'Check-out':<12} {'Total':<10} {'Status'}")
    print("-"*100)
    for b in rows:
        print(f"{b[0]:<5} {b[1] or '-':<5} {b[2]:<20} {b[3]:<6} {str(b[4]):<12} {str(b[5]):<12} ₹{float(b[6]):<8.2f} {b[7]}")
    conn.close()
    print("")

def search_customer():
    kw = input("Enter Customer ID or Name to search: ").strip()
    if not kw:
        print("Empty search.\n")
        return
    conn = connect_db()
    cur = conn.cursor()
    if kw.isdigit():
        cur.execute("SELECT customer_id, name, phone, email FROM Customers WHERE customer_id=%s", (int(kw),))
    else:
        cur.execute("SELECT customer_id, name, phone, email FROM Customers WHERE name LIKE %s", (f"%{kw}%",))
    rows = cur.fetchall()
    if not rows:
        print("No matching customers found.\n")
        conn.close()
        return
    print("\nSearch Results:")
    for r in rows:
        print(f"ID:{r[0]} | Name:{r[1]} | Phone:{r[2] or '-'} | Email:{r[3] or '-'}")
    conn.close()
    print("")

def checkout():
    try:
        bid = int(input("Enter Booking ID to checkout: ").strip())
    except ValueError:
        print("Invalid booking ID.\n")
        return

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT booking_id, cust_id, cust_name, room_no, check_in, check_out, total, status FROM Bookings WHERE booking_id=%s", (bid,))
    b = cur.fetchone()
    if not b:
        print("Booking not found.\n")
        conn.close()
        return
    if b[7] and b[7].lower() in ('checked-out', 'checked_out', 'checked out'):
        print("Booking already checked out.\n")
        conn.close()
        return

    # compute nights (dates returned as datetime.date)
    try:
        ci = b[4]
        co = b[5]
        if not isinstance(ci, date) or not isinstance(co, date):
            # convert if they are strings
            ci = datetime.strptime(str(ci), "%Y-%m-%d").date()
            co = datetime.strptime(str(co), "%Y-%m-%d").date()
    except Exception:
        # fallback: use stored total
        ci = None
        co = None

    nights = 1
    if ci and co:
        nights = (co - ci).days
        if nights <= 0:
            nights = 1

    # fetch room price (fresh)
    cur.execute("SELECT price FROM Rooms WHERE room_no=%s", (b[3],))
    price_row = cur.fetchone()
    price = float(price_row[0]) if price_row else float(b[6]) / max(nights,1)

    base = round(price * nights, 2)
    gst = round(base * 0.12, 2)
    final = round(base + gst, 2)

    # store invoice
    today = date.today().strftime("%Y-%m-%d")
    cur.execute("""
    INSERT INTO GuestInvoices (guest_id, guest_name, room_number, nights, rate_per_night, total_amount, date)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (b[1], b[2], b[3], nights, price, final, today))
    invoice_id = cur.lastrowid

    # update room and booking and customer
    cur.execute("UPDATE Rooms SET status='Available' WHERE room_no=%s", (b[3],))
    cur.execute("UPDATE Bookings SET status='Checked-Out' WHERE booking_id=%s", (bid,))
    if b[1]:
        cur.execute("SELECT total_stays FROM Customers WHERE customer_id=%s", (b[1],))
        ts = cur.fetchone()
        new_stays = (ts[0] if ts and ts[0] is not None else 0) + 1
        cur.execute("UPDATE Customers SET total_stays=%s WHERE customer_id=%s", (new_stays, b[1]))

    conn.commit()
    conn.close()

    # write invoice file
    if not os.path.exists("invoices"):
        os.makedirs("invoices")
    safe_name = (b[2].replace(" ", "") if b[2] else "guest")
    fname = f"invoices/invoice_{invoice_id}_booking{bid}_{safe_name}.txt"
    with open(fname, "w", encoding="utf-8") as f:
        f.write("----- Motel Invoice -----\n")
        f.write(f"Invoice ID: {invoice_id}\nDate: {today}\n")
        f.write(f"Guest: {b[2]}\nRoom: {b[3]}\n")
        f.write(f"Check-in: {b[4]}   Check-out: {b[5]}\n")
        f.write(f"Nights: {nights}\nBase: ₹{base:.2f}\nGST (12%): ₹{gst:.2f}\nTotal: ₹{final:.2f}\n")
        f.write("\nThank you for staying with us!\n")

    print(f"\nCheckout successful! Invoice saved as {fname}\n")

def remove_customer():
    print("\n--- Remove Customer ---")
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, name FROM Customers ORDER BY customer_id")
    rows = cur.fetchall()
    if not rows:
        print("No customers to remove.\n")
        conn.close()
        return
    for r in rows:
        print(f"{r[0]:<4} {r[1]}")
    try:
        cid = int(input("\nEnter Customer ID to remove (0 to cancel): ").strip())
    except ValueError:
        print("Invalid ID.\n")
        conn.close()
        return
    if cid == 0:
        conn.close()
        return
    cur.execute("SELECT name FROM Customers WHERE customer_id=%s", (cid,))
    name_row = cur.fetchone()
    if not name_row:
        print("Customer not found.\n")
        conn.close()
        return
    confirm = input(f"Are you sure you want to delete customer '{name_row[0]}' and their bookings? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.\n")
        conn.close()
        return

    # free rooms of active bookings
    cur.execute("SELECT room_no FROM Bookings WHERE cust_id=%s AND status='Active'", (cid,))
    for (room_no,) in cur.fetchall():
        cur.execute("UPDATE Rooms SET status='Available' WHERE room_no=%s", (room_no,))
    cur.execute("DELETE FROM Bookings WHERE cust_id=%s", (cid,))
    cur.execute("DELETE FROM Customers WHERE customer_id=%s", (cid,))
    conn.commit()
    conn.close()
    print("Customer and related bookings removed.\n")

# ---------------- MAIN MENU ----------------
def menu():
    
    while True:
        print("\n===== MOTEL MANAGEMENT SYSTEM =====")
        print("1. Add Customer & Book Room")
        print("2. View Customers")
        print("3. View Rooms")
        print("4. View Bookings")
        print("5. Checkout (Generate Invoice)")
        print("6. Remove Customer")
        print("7. Setup Database (Run Once)")
        print("0. Exit")
        ch = input("Enter choice: ").strip()
        if ch == "1":
            add_customer_and_book()
        elif ch == "2":
            view_customers()
        elif ch == "3":
            view_rooms()
        elif ch == "4":
            view_bookings()
        elif ch == "5":
            checkout()
        elif ch == "6":
            remove_customer()
        elif ch == "7":
            setup()
        elif ch == "0":
            print("Thank you for using the system!")
            break
        else:
            print("Invalid option. Try again.")

# ---------------- RUN PROGRAM ----------------
if __name__ == "__main__":
    # if DB password not replaced, warn user
    if DB_PASSWORD == "YOUR_MYSQL_PASSWORD":
        print("NOTE: Please edit DB_PASSWORD variable in the script to your MySQL root password before running.")
    menu()