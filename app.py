import flet as ft
import os
import psycopg2
from datetime import datetime

# --- ASETUKSET ---

# TÄMÄ ON TURVALLINEN VERSIO GITHUBIIN.
# Render syöttää osoitteen tähän automaattisesti taustalla.
DATABASE_URL = os.getenv("DATABASE_URL")

# Teeman värit
COLOR_BG = "#FAECB6"
COLOR_PRIMARY = "#2BBAA5"
COLOR_TEXT = "#333333"
COLOR_CARD = "#FFFDF0"
COLOR_DELETE = "#F96635"

# Ikonit
AVAILABLE_ICONS = {
    "Työ": ft.Icons.WORK,
    "Koulu": ft.Icons.SCHOOL,
    "Koti": ft.Icons.HOME,
    "Harrastus": ft.Icons.SPORTS_SOCCER,
    "Tärkeä": ft.Icons.STAR,
    "Kauppa": ft.Icons.SHOPPING_CART,
    "Matka": ft.Icons.FLIGHT,
    "Raha": ft.Icons.ATTACH_MONEY,
    "Idea": ft.Icons.LIGHTBULB,
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
    "Harmaa": "#90A4AE"
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
            # Tämä virhe tulee vain jos Renderin asetukset puuttuvat
            raise Exception("DATABASE_URL puuttuu! Aseta se Renderin Environment Variables -kohtaan.")
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
                CREATE TABLE IF NOT EXISTS categories (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE,
                    color TEXT,
                    icon_name TEXT
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

    def get_categories(self):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, color, icon_name FROM categories ORDER BY id ASC")
                return cur.fetchall()
        finally:
            conn.close()

    def add_category(self, name, color, icon_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO categories (name, color, icon_name) VALUES (%s, %s, %s)", (name, color, icon_name))
            conn.commit()
        finally:
            conn.close()

    def update_category(self, old_name, new_name, color, icon_name):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE categories SET name=%s, color=%s, icon_name=%s WHERE name=%s", 
                           (new_name, color, icon_name, old_name))
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

    def add_task(self, content, category, deadline):
        db_date = date_fi_to_db(deadline)
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO tasks (content, category, deadline) VALUES (%s, %s, %s)", (content, category, db_date))
            conn.commit()
        finally:
            conn.close()

    def update_task(self, task_id, content, category, deadline):
        db_date = date_fi_to_db(deadline)
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE tasks SET content=%s, category=%s, deadline=%s WHERE id=%s", (content, category, db_date, task_id))
            conn.commit()
        finally:
            conn.close()

    def get_tasks(self, category_filter=None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, content, category, deadline, completed FROM tasks ORDER BY deadline ASC")
                all_tasks = cur.fetchall()
            
            if category_filter and category_filter != "Kaikki":
                return [t for t in all_tasks if t[2] == category_filter]
            return all_tasks
        finally:
            conn.close()

    def toggle_task(self, task_id, current_status):
        new_status = not current_status
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE tasks SET completed = %s WHERE id = %s", (new_status, task_id))
            conn.commit()
        finally:
            conn.close()
    
    def delete_task(self, task_id):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
        finally:
            conn.close()

db = TaskManager()

def main(page: ft.Page):
    page.title = "Retro Taskmaster"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {"Retro": "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"}
    page.theme = ft.Theme(font_family="Retro")
    page.locale = "fi-FI"

    try:
        db.create_tables()
    except Exception as e:
        page.add(ft.Text(f"Tietokantavirhe: {e}", color="red"))
        return

    editing_task_id = ft.Ref[int]()
    editing_task_id.current = None
    
    current_categories = [] 

    # --- UI RAKENNE ---
    tasks_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    
    tabs_control = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[ft.Tab(text="Kaikki", icon=ft.Icons.LIST)], 
        label_color=COLOR_BG,
        indicator_color=COLOR_BG,
        divider_color="transparent"
    )

    # --- TOIMINNOT ---

    def load_categories():
        nonlocal current_categories
        try:
            current_categories = db.get_categories()
        except:
            current_categories = []

    def get_cat_color(cat_name):
        for c in current_categories:
            if c[1] == cat_name:
                return c[2]
        return COLOR_PRIMARY

    def rebuild_tabs():
        # Tarkistetaan onko kontrolli sivulla
        if not tabs_control.page:
            return

        selected_text = "Kaikki"
        if tabs_control.tabs and tabs_control.selected_index is not None and tabs_control.selected_index < len(tabs_control.tabs):
            selected_text = tabs_control.tabs[tabs_control.selected_index].text
        
        new_tabs = [ft.Tab(text="Kaikki", icon=ft.Icons.LIST)]
        
        for cat in current_categories:
            c_name = cat[1]
            c_icon_key = cat[3]
            real_icon = AVAILABLE_ICONS.get(c_icon_key, ft.Icons.CIRCLE)
            new_tabs.append(ft.Tab(text=c_name, icon=real_icon))
            
        tabs_control.tabs = new_tabs
        
        found_index = 0
        for i, t in enumerate(new_tabs):
            if t.text == selected_text:
                found_index = i
                break
        tabs_control.selected_index = found_index
        tabs_control.update()

    def render_tasks(category_filter="Kaikki"):
        tasks_column.controls.clear()
        try:
            tasks = db.get_tasks(category_filter)
        except Exception as e:
            tasks_column.controls.append(ft.Text(f"Yhteysvirhe: {e}", color="red"))
            page.update()
            return

        if not tasks:
            tasks_column.controls.append(ft.Container(
                content=ft.Text("Ei tehtäviä!", color=COLOR_TEXT),
                padding=20, alignment=ft.alignment.center
            ))
        
        for t in tasks:
            t_id, t_content, t_cat, t_deadline_db, t_completed = t[0], t[1], t[2], t[3], t[4]
            display_date = date_db_to_fi(t_deadline_db)
            cat_color = get_cat_color(t_cat)
            
            decor = ft.TextDecoration.LINE_THROUGH if t_completed else ft.TextDecoration.NONE
            opacity = 0.6 if t_completed else 1.0
            bg_color = "#EAE0B0" if t_completed else COLOR_CARD

            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DELETE, on_click=lambda e, x=t_id: delete_task_click(x))
            edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=COLOR_PRIMARY, on_click=lambda e, x=t: open_edit_dialog(x))

            tasks_column.controls.append(ft.Container(
                content=ft.Row([
                    ft.Container(width=10, bgcolor=cat_color, border_radius=ft.border_radius.only(top_left=10, bottom_left=10)),
                    ft.Checkbox(value=bool(t_completed), fill_color=COLOR_PRIMARY, on_change=lambda e, x=t_id, y=t_completed: toggle_status(x, y)),
                    ft.Column([
                        ft.Text(t_content, style=ft.TextStyle(decoration=decor, color=COLOR_TEXT, size=14, weight=ft.FontWeight.BOLD)),
                        ft.Text(f"{t_cat} | {display_date}", size=10, color=COLOR_TEXT),
                    ], expand=True),
                    edit_btn, delete_btn
                ]),
                bgcolor=bg_color, height=70, border_radius=10, opacity=opacity, shadow=ft.BoxShadow(blur_radius=2, color="#33000000"), animate=300
            ))
        page.update()

    def refresh_main_view():
        load_categories()
        rebuild_tabs()
        current_tab_text = "Kaikki"
        if tabs_control.tabs and tabs_control.selected_index is not None:
             current_tab_text = tabs_control.tabs[tabs_control.selected_index].text
        render_tasks(current_tab_text)

    # --- DIALOGIT ---
    
    new_task_name = ft.TextField(label="Tehtävä", border_color=COLOR_PRIMARY, color=COLOR_TEXT, expand=True)
    new_task_cat_dropdown = ft.Dropdown(label="Kategoria", border_color=COLOR_PRIMARY, color=COLOR_TEXT, width=200)
    date_input = ft.TextField(label="Pvm", value=datetime.now().strftime("%d.%m.%Y"), border_color=COLOR_PRIMARY, color=COLOR_TEXT, width=150)
    
    def change_date(e):
        if date_picker.value:
            date_input.value = date_picker.value.strftime("%d.%m.%Y")
            date_input.update()
    
    date_picker = ft.DatePicker(on_change=change_date)
    calendar_btn = ft.IconButton(icon=ft.Icons.CALENDAR_MONTH, icon_color=COLOR_PRIMARY, on_click=lambda _: page.open(date_picker))

    add_dialog = ft.AlertDialog(
        title=ft.Text("Tehtävä", color=COLOR_TEXT),
        bgcolor=COLOR_BG,
        content=ft.Column([new_task_name, new_task_cat_dropdown, ft.Row([date_input, calendar_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], height=200, width=320),
        actions=[
            ft.TextButton(content=ft.Text("Peruuta", color=COLOR_TEXT), on_click=lambda e: page.close(add_dialog)),
            ft.ElevatedButton(content=ft.Text("Tallenna", color=COLOR_BG), bgcolor=COLOR_PRIMARY, on_click=lambda e: save_task(e))
        ]
    )

    cat_edit_name = ft.TextField(label="Nimi", border_color=COLOR_PRIMARY, color=COLOR_TEXT)
    cat_edit_color = ft.Dropdown(label="Väri", border_color=COLOR_PRIMARY, options=[ft.dropdown.Option(k) for k in AVAILABLE_COLORS.keys()])
    cat_edit_icon = ft.Dropdown(label="Ikoni", border_color=COLOR_PRIMARY, options=[ft.dropdown.Option(k) for k in AVAILABLE_ICONS.keys()])
    categories_list_view = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, height=200)

    settings_dialog = ft.AlertDialog(
        title=ft.Text("Kategoriat", color=COLOR_TEXT),
        bgcolor=COLOR_BG,
        content=ft.Column([
            ft.Text("Lisää/Muokkaa:", size=12, color=COLOR_TEXT),
            cat_edit_name,
            ft.Row([cat_edit_color, cat_edit_icon]),
            ft.ElevatedButton(content=ft.Text("Tallenna", color=COLOR_BG), bgcolor=COLOR_PRIMARY, on_click=lambda e: save_category(e)),
            ft.Divider(),
            categories_list_view
        ], height=400, width=350),
        actions=[ft.TextButton(content=ft.Text("Sulje", color=COLOR_TEXT), on_click=lambda e: close_settings(e))]
    )

    # --- TAPAHTUMAKÄSITTELIJÄT ---

    def save_task(e):
        if not new_task_name.value: return
        try:
            if editing_task_id.current:
                db.update_task(editing_task_id.current, new_task_name.value, new_task_cat_dropdown.value, date_input.value)
                msg = "Päivitetty!"
            else:
                db.add_task(new_task_name.value, new_task_cat_dropdown.value, date_input.value)
                msg = "Luotu!"
            page.close(add_dialog)
            refresh_main_view()
            page.open(ft.SnackBar(ft.Text(msg, color=COLOR_BG), bgcolor=COLOR_TEXT))
        except Exception as ex:
            print(ex)

    def delete_task_click(t_id):
        try:
            db.delete_task(t_id)
            refresh_main_view()
        except: pass

    def toggle_status(t_id, current):
        try:
            db.toggle_task(t_id, current)
            refresh_main_view()
        except: pass

    def open_new_dialog(e):
        editing_task_id.current = None
        new_task_name.value = ""
        date_input.value = datetime.now().strftime("%d.%m.%Y")
        opts = [ft.dropdown.Option(c[1]) for c in current_categories]
        new_task_cat_dropdown.options = opts
        if opts: new_task_cat_dropdown.value = opts[0].key
        add_dialog.title = ft.Text("Uusi tehtävä", color=COLOR_TEXT)
        page.open(add_dialog)

    def open_edit_dialog(t):
        editing_task_id.current = t[0]
        new_task_name.value = t[1]
        opts = [ft.dropdown.Option(c[1]) for c in current_categories]
        new_task_cat_dropdown.options = opts
        new_task_cat_dropdown.value = t[2]
        date_input.value = date_db_to_fi(t[3])
        add_dialog.title = ft.Text("Muokkaa", color=COLOR_TEXT)
        page.open(add_dialog)

    def render_categories_list():
        categories_list_view.controls.clear()
        for c in current_categories:
            c_name, c_color, c_icon = c[1], c[2], c[3]
            row = ft.Container(
                content=ft.Row([
                    ft.Container(width=15, height=15, bgcolor=c_color, border_radius=5),
                    ft.Text(c_name, color=COLOR_TEXT, expand=True),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color=COLOR_DELETE, on_click=lambda e, x=c_name: delete_category(x))
                ]),
                bgcolor="#FFFFFF", padding=5, border_radius=5,
                on_click=lambda e, x=c: prefill_cat_form(x)
            )
            categories_list_view.controls.append(row)
        
        if categories_list_view.page:
            categories_list_view.update()

    def prefill_cat_form(cat_data):
        cat_edit_name.value = cat_data[1]
        cat_edit_name.data = cat_data[1] 
        found_color = next((k for k, v in AVAILABLE_COLORS.items() if v == cat_data[2]), None)
        cat_edit_color.value = found_color
        cat_edit_icon.value = cat_data[3]
        settings_dialog.update()

    def save_category(e):
        if not cat_edit_name.value: return
        real_color = AVAILABLE_COLORS.get(cat_edit_color.value, COLOR_PRIMARY)
        icon_name = cat_edit_icon.value or "Muu"
        
        try:
            if hasattr(cat_edit_name, 'data') and cat_edit_name.data:
                db.update_category(cat_edit_name.data, cat_edit_name.value, real_color, icon_name)
                cat_edit_name.data = None
            else:
                db.add_category(cat_edit_name.value, real_color, icon_name)
            
            cat_edit_name.value = ""
            load_categories()
            render_categories_list()
            page.open(ft.SnackBar(ft.Text("Tallennettu", color=COLOR_BG), bgcolor=COLOR_TEXT))
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"Virhe: {ex}"), bgcolor="red"))

    def delete_category(name):
        if name == "Muu": return
        try:
            db.delete_category(name)
            load_categories()
            render_categories_list()
        except: pass

    def open_settings(e):
        load_categories()
        render_categories_list()
        page.open(settings_dialog)

    def close_settings(e):
        page.close(settings_dialog)
        refresh_main_view()

    def tab_changed(e):
        render_tasks(e.control.tabs[e.control.selected_index].text)

    tabs_control.on_change = tab_changed

    # --- SIVUN ALUSTUS (KORJATTU JÄRJESTYS) ---
    
    page.appbar = ft.AppBar(
        title=ft.Text("DIIDELAINIT", color=COLOR_BG, font_family="Retro"), 
        center_title=True, 
        bgcolor=COLOR_PRIMARY,
        actions=[ft.IconButton(icon=ft.Icons.SETTINGS, icon_color=COLOR_BG, on_click=open_settings)]
    )
    
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, 
        bgcolor=COLOR_PRIMARY, 
        foreground_color=COLOR_BG, 
        on_click=open_new_dialog
    )

    page.add(
        ft.Column([
            ft.Container(content=tabs_control, bgcolor=COLOR_PRIMARY),
            ft.Container(content=tasks_column, padding=10, expand=True)
        ], expand=True)
    )

    # Vasta nyt päivitetään data
    load_categories()
    rebuild_tabs()
    render_tasks("Kaikki")

port = int(os.environ.get("PORT", 8080))
ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port, host="0.0.0.0")
