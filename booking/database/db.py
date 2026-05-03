import sqlite3


def create_db():
    conn = sqlite3.connect('restaurant_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS bookings
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id    INTEGER,
                       username   TEXT,
                       date       TEXT,
                       time       TEXT,
                       guests     INTEGER,
                       preference TEXT,
                       status     TEXT DEFAULT 'pending'
                   )
                   ''')

    conn.commit()
    conn.close()


def add_booking(user_id, username, date, time, guests, preference, status='confirmed'):
    conn = sqlite3.connect('restaurant_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO bookings(user_id, username, date, time, guests, preference, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ''', (user_id, username, date, time, guests, preference, status))

    conn.commit()
    conn.close()


def get_user_bookings(user_id):
    conn = sqlite3.connect('restaurant_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT id, date, time, guests, preference, status
                   FROM bookings
                   WHERE user_id = ?
                   ''', (user_id,))

    bookings = cursor.fetchall()
    conn.close()

    return bookings


def delete_booking(booking_id):
    conn = sqlite3.connect('restaurant_bot.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM bookings WHERE id = ?',
                   (booking_id,))

    conn.commit()
    conn.close()
