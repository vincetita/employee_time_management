import bcrypt
import mysql.connector as dbconnection
from tkinter import messagebox

def connect_db():
    # Verbindung zur Datenbank herstellen
    try:
        conn = dbconnection.connect(
            host="localhost",
            user="root",
            password="root",
            database="mitarbeiter_verwaltung"
        )
        return conn
    except:
        messagebox.showerror("Fehler", "Keine Verbindung zur Datenbank")
        return None

def fetch_user_data(username):
    # Benutzerdaten aus Datenbank holen
    conn = connect_db()
    if conn is None:
        return None
    cursor = conn.cursor()
    query = "SELECT b.password_hash, b.rolle, b.mitarbeiter_id, m.vorname, m.status, b.passwort_typ FROM benutzer b JOIN mitarbeiter m ON b.mitarbeiter_id = m.mitarbeiter_id WHERE b.username = %s"
    cursor.execute(query, (username,))
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    if data:
        return data
    else:
        messagebox.showerror("Fehler", "Benutzer nicht gefunden")
        return None

def start_work(mitarbeiter_id, start_time):
    # Arbeitsbeginn speichern
    conn = connect_db()
    if conn is None:
        return False, "Keine Verbindung"
    cursor = conn.cursor()
    query = "SELECT eintrag_id FROM anwesenheiten WHERE mitarbeiter_id = %s AND end_zeit IS NULL"
    cursor.execute(query, (mitarbeiter_id,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False, "Arbeit schon gestartet"
    
    query = "INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit) VALUES (%s, 'Arbeit', %s)"
    cursor.execute(query, (mitarbeiter_id, start_time))
    conn.commit()
    cursor.close()
    conn.close()
    return True, "Arbeit gestartet"

def end_work(mitarbeiter_id, end_time):
    # Arbeitsende speichern
    conn = connect_db()
    if conn is None:
        return False, "Keine Verbindung"
    cursor = conn.cursor()
    query = "SELECT eintrag_id FROM anwesenheiten WHERE mitarbeiter_id = %s AND end_zeit IS NULL"
    cursor.execute(query, (mitarbeiter_id,))
    result = cursor.fetchone()

    if result:
        eintrag_id = result[0]
        query = "UPDATE anwesenheiten SET end_zeit = %s WHERE eintrag_id = %s"
        cursor.execute(query, (end_time, eintrag_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Arbeit beendet"
    else:
        cursor.close()
        conn.close()
        return False, "Kein offener Eintrag"