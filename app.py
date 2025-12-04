import flet as ft
import os
import psycopg2
from datetime import datetime

# --- ASETUKSET ---
DATABASE_URL = os.getenv("DATABASE_URL")

# Teeman värit
COLOR_BG = "#FAECB6"
COLOR_PRIMARY = "#2BBAA5"
COLOR_TEXT = "#333333"
COLOR_CARD = "#FFFDF0"
COLOR_DELETE = "#F96635"

# Laajennettu ikonivalikoima
AVAILABLE_ICONS = {
    "Kansio": ft.Icons.FOLDER,
    "Nainen": ft.Icons.WOMAN,
    "Mies": ft.Icons.MAN,
    "Työ": ft.Icons.WORK,
    "Koulu": ft.Icons.SCHOOL,
    "Koti": ft.Icons.HOME,
    "Harrastus": ft.Icons.SPORTS_SOCCER,
    "Pelaaminen": ft.Icons.GAMEPAD,
    "Kuntosali": ft.Icons.FITNESS_CENTER,
    "Lemmikki": ft.Icons.PETS,
    "Auto": ft.Icons.DIRECTIONS_CAR,
    "Tärkeä": ft.Icons.STAR,
    "Kauppa": ft.Icons.SHOPPING_CART,
    "Ruoka": ft.Icons.RESTAURANT,
    "Matka": ft.Icons.FLIGHT,
    "Raha": ft.Icons.ATTACH_MONEY,
    "Idea": ft.Icons.LIGHTBULB,
    "Musiikki": ft.Icons.MUSIC_NOTE,
    "Lahja": ft.Icons.CARD_GIFTCHARD,
    "Muu": ft.Icons.CIRCLE
}

# Värit
AVAILABLE_COLORS = {
    "Turkoosi": "#2BBAA5",
    "Oranssi": "#F96635",
    "Keltainen": "#F9A822",
    "Vihreä": "#93D3AE",
    "Punainen": "#E57373",
    "Sininen": "#64B5F6",
    "Violetti": "#BA68C8",
    "Harmaa": "#90A4AE",
    "Musta": "#333333"
}

# --- APUFUNKTIOT ---
def date_db_to_fi(db_date):
    try:
        if db_date:
            if isinstance(db_date, str):
                parts = db_date.split("-")
                if len(parts) == 3:
                    return f"{parts[2]}.{parts[1]}.{parts[0]}"
            else:
                return db_date.strftime("%d.%m.%Y")
    except:
        pass
    return str(db_date) if db_date else ""

def date_fi_to_db(fi_date):
    try:
        parts = fi_date.split(".")
        if len(parts) == 3:
            d = parts[0].zfill(2)
            m = parts[1].zfill(2)
            y = parts[2]
            return f"{y}-{m}-{d}"
    except:
        pass
    return fi_date 

# --- TIETOKANTA ---
class TaskManager:
    def get_connection(self):
        if not DATABASE_URL:
            raise Exception("DATABASE_URL puuttuu!")
        return psycopg2.connect(DATABASE_URL, sslmode='require')

    def create_tables(self):
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    category TEXT,
                    deadline DATE,
                    completed BOOLEAN DEFAULT FALSE
                )
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS master_categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    color TEXT,
                    icon_name TEXT
                )
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    color TEXT,
                    icon_name TEXT,
                    master_id INTEGER REFERENCES master_categories(id)
                )
                """)
                
                cur.execute("SELECT count(*) FROM categories")
                if cur.fetchone()[0] == 0:
                    defaults = [
                        ("Työ", "#F96635", "Työ"),
                        ("Koulu", "#F9A822", "Koulu"),
                        ("Muu", "#93D3AE", "Muu")
                    ]
                    for name, color, icon in defaults:
                        cur.execute("INSERT INTO categories (name, color, icon_name) VALUES (%s, %s, %s)", (name, color, icon))
            conn.commit()
        except Exception as e:
            print("Virhe taulujen luonnissa:", e)
        finally:
            if conn: conn.close()

    # --- PÄÄKATEGORIA METODIT ---
    def get_master_categories(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, color, icon_name FROM master_categories ORDER BY id ASC")
                return cur.fetchall()
        finally:
            conn.close()

    def add_master_category(self, name, color, icon_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO master_categories (name, color, icon_name) VALUES (%s, %s, %s)", (name, color, icon_name))
            conn.commit()
        finally:
            conn.close()

    def update_master_category(self, m_id, name, color, icon_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE master_categories SET name=%s, color=%s, icon_name=%s WHERE id=%s", (name, color, icon_name, m_id))
            conn.commit()
        finally:
            conn.close()
            
    def delete_master_category(self, m_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE categories SET master_id = NULL WHERE master_id = %s", (m_id,))
                cur.execute("DELETE FROM master_categories WHERE id = %s", (m_id,))
            conn.commit()
        finally:
            conn.close()

    # --- ALIKATEGORIA METODIT ---
    def get_categories(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, color, icon_name, master_id FROM categories ORDER BY id ASC")
                return cur.fetchall()
        finally:
            conn.close()

    def add_category(self, name, color, icon_name, master_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO categories (name, color, icon_name, master_id) VALUES (%s, %s, %s, %s)", 
                           (name, color, icon_name, master_id))
            conn.commit()
        finally:
            conn.close()

    def update_category(self, old_name, new_name, color, icon_name, master_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE categories SET name=%s, color=%s, icon_name=%s, master_id=%s WHERE name=%s", 
                           (new_name, color, icon_name, master_id, old_name))
                if old_name != new_name:
                    cur.execute("UPDATE tasks SET category=%s WHERE category=%s", (new_name, old_name))
            conn.commit()
        finally:
            conn.close()

    def delete_category(self, name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE tasks SET category='Muu' WHERE category=%s", (name,))
                cur.execute("DELETE FROM categories WHERE name=%s", (name,))
            conn.commit()
        finally:
            conn.close()

    # --- TEHTÄVÄT ---
    def add_task(self, content, category, deadline):
        db_date = date_fi_to_db(deadline)
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO tasks (content, category, deadline) VALUES (%s, %s, %s)", (content, category, db_date))
            conn.commit()
        finally:
            conn.close()

    def update_task(self, task
