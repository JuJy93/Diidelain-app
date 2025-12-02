import flet as ft
import sqlite3
from datetime import datetime

# --- ASETUKSET (RETRO SUMMER TEEMA) ---
DB_FILENAME = "tasks.db"

# Väripaletti
COLOR_BG = "#FAECB6"        # Vanilla (Tausta)
COLOR_PRIMARY = "#2BBAA5"   # Keppel (Pääväri)
COLOR_TEXT = "#333333"      # Tummanharmaa (Teksti)
COLOR_CARD = "#FFFDF0"      # Korttiväri
COLOR_DELETE = "#F96635"    # Giants orange (Poisto)

CAT_COLORS = {
    "Työ": "#F96635",
    "Koulu": "#F9A822",
    "Muu": "#93D3AE",
    "Yleinen": "#2BBAA5"
}

# --- PÄIVÄMÄÄRÄMUUNTIMET ---
def date_db_to_fi(db_date):
    try:
        parts = db_date.split("-")
        if len(parts) == 3:
            return f"{parts[2]}.{parts[1]}.{parts[0]}"
    except:
        pass
    return db_date

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

class TaskManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILENAME, check_same_thread=False)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            category TEXT,
            deadline TEXT,
            completed INTEGER DEFAULT 0
        )
        """)
        self.conn.commit()

    def add_task(self, content, category, deadline):
        db_date = date_fi_to_db(deadline)
        self.conn.execute("INSERT INTO tasks (content, category, deadline) VALUES (?, ?, ?)", 
                          (content, category, db_date))
        self.conn.commit()

    def update_task(self, task_id, content, category, deadline):
        db_date = date_fi_to_db(deadline)
        self.conn.execute("UPDATE tasks SET content=?, category=?, deadline=? WHERE id=?", 
                          (content, category, db_date, task_id))
        self.conn.commit()

    def get_tasks(self, category_filter=None):
        cursor = self.conn.execute("SELECT id, content, category, deadline, completed FROM tasks ORDER BY deadline ASC")
        all_tasks = cursor.fetchall()
        if category_filter and category_filter != "Kaikki":
            return [t for t in all_tasks if t[2] == category_filter]
        return all_tasks

    def toggle_task(self, task_id, current_status):
        new_status = 0 if current_status else 1
        self.conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))
        self.conn.commit()
    
    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

db = TaskManager()

def main(page: ft.Page):
    page.title = "Retro Taskmaster"
    page.bgcolor = COLOR_BG
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {"Retro": "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"}
    page.theme = ft.Theme(font_family="Retro")
    page.locale = "fi-FI"

    editing_task_id = ft.Ref[int]()
    editing_task_id.current = None

    # --- UI ELEMENTIT ---
    today_fi = datetime.now().strftime("%d.%m.%Y")
    
    date_input = ft.TextField(
        label="Pvm (pp.kk.vvvv)", 
        value=today_fi,
        border_color=COLOR_PRIMARY,
        color=COLOR_TEXT,
        width=180,
        text_size=14
    )

    def change_date(e):
        if date_picker.value:
            fi_date = date_picker.value.strftime("%d.%m.%Y")
            date_input.value = fi_date
            date_input.update()

    date_picker = ft.DatePicker(
        on_change=change_date,
        first_date=datetime(2023, 1, 1),
        last_date=datetime(2030, 12, 31)
    )
    
    def open_calendar(e):
        page.open(date_picker)

    calendar_icon_btn = ft.IconButton(
        icon=ft.Icons.CALENDAR_MONTH,
        icon_color=COLOR_PRIMARY,
        tooltip="Avaa kalenteri",
        on_click=open_calendar
    )

    new_task_name = ft.TextField(label="Tehtävä", border_color=COLOR_PRIMARY, color=COLOR_TEXT, expand=True)
    
    new_task_cat = ft.Dropdown(
        label="Kategoria",
        options=[
            ft.dropdown.Option("Työ"),
            ft.dropdown.Option("Koulu"),
            ft.dropdown.Option("Muu")
        ],
        value="Muu",
        border_color=COLOR_PRIMARY,
        color=COLOR_TEXT,
        width=200 
    )

    tasks_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    def render_tasks(category_filter="Kaikki"):
        tasks_column.controls.clear()
        tasks = db.get_tasks(category_filter)

        if not tasks:
            tasks_column.controls.append(ft.Container(
                content=ft.Text("Ei tehtäviä tässä kategoriassa!", color=COLOR_TEXT),
                padding=20, alignment=ft.alignment.center
            ))
        
        for t in tasks:
            t_id = t[0]
            t_completed = t[4]
            t_deadline_db = t[3]
            display_date = date_db_to_fi(t_deadline_db)
            
            cat_color = CAT_COLORS.get(t[2], COLOR_PRIMARY)
            decor = ft.TextDecoration.LINE_THROUGH if t_completed else ft.TextDecoration.NONE
            opacity = 0.6 if t_completed else 1.0
            bg_color = "#EAE0B0" if t_completed else COLOR_CARD

            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DELETE, on_click=lambda e, x=t_id: delete_task_click(x))
            edit_btn = ft.IconButton(icon=ft.Icons.EDIT, icon_color=COLOR_PRIMARY, on_click=lambda e, x=t: open_edit_dialog(x))

            task_card = ft.Container(
                content=ft.Row([
                    ft.Container(width=10, bgcolor=cat_color, border_radius=ft.border_radius.only(top_left=10, bottom_left=10)),
                    ft.Checkbox(value=bool(t_completed), fill_color=COLOR_PRIMARY, on_change=lambda e, x=t_id, y=t_completed: toggle_status(x, y)),
                    ft.Column([
                        ft.Text(t[1], style=ft.TextStyle(decoration=decor, color=COLOR_TEXT, size=14, weight=ft.FontWeight.BOLD)),
                        ft.Text(f"{t[2]} | {display_date}", size=10, color=COLOR_TEXT),
                    ], expand=True),
                    edit_btn,
                    delete_btn
                ]),
                bgcolor=bg_color,
                height=70,
                border_radius=10,
                opacity=opacity,
                shadow=ft.BoxShadow(blur_radius=2, color="#33000000"), 
                animate=300
            )
            tasks_column.controls.append(task_card)
        page.update()

    def refresh_list():
        current_tab_index = tabs.selected_index if tabs.selected_index else 0
        tab_name = tabs.tabs[current_tab_index].text
        render_tasks(tab_name)

    def toggle_status(t_id, current_val):
        db.toggle_task(t_id, current_val)
        refresh_list()

    def delete_task_click(t_id):
        db.delete_task(t_id)
        refresh_list()

    def save_task(e):
        if not new_task_name.value:
            new_task_name.error_text = "Nimi puuttuu!"
            new_task_name.update()
            return
        
        if editing_task_id.current is not None:
            db.update_task(editing_task_id.current, new_task_name.value, new_task_cat.value, date_input.value)
            msg = "Päivitetty!"
        else:
            db.add_task(new_task_name.value, new_task_cat.value, date_input.value)
            msg = "Luotu!"
        
        page.close(add_dialog)
        page.update()
        refresh_list()
        page.open(ft.SnackBar(ft.Text(msg, color=COLOR_BG), bgcolor=COLOR_TEXT))

    def close_dialog(e):
        page.close(add_dialog)

    # --- DIALOGI (POPUP) ---
    add_dialog = ft.AlertDialog(
        title=ft.Text("Tehtävä", color=COLOR_TEXT),
        bgcolor=COLOR_BG,
        content=ft.Column([
            ft.Row([new_task_name], expand=True),
            ft.Row([new_task_cat], expand=True),
            ft.Text("Deadline:", size=12, color=COLOR_TEXT),
            ft.Row([date_input, calendar_icon_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ], height=250, width=320),
        actions=[
            ft.TextButton(content=ft.Text("Peruuta", color=COLOR_TEXT), on_click=close_dialog),
            ft.ElevatedButton(content=ft.Text("Tallenna", color=COLOR_BG), on_click=save_task, bgcolor=COLOR_PRIMARY)
        ]
    )

    def open_new_dialog(e):
        editing_task_id.current = None
        new_task_name.value = ""
        new_task_cat.value = "Muu"
        date_input.value = datetime.now().strftime("%d.%m.%Y")
        add_dialog.title = ft.Text("Uusi tehtävä", color=COLOR_TEXT)
        page.open(add_dialog)

    def open_edit_dialog(task_data):
        editing_task_id.current = task_data[0]
        new_task_name.value = task_data[1]
        new_task_cat.value = task_data[2]
        date_input.value = date_db_to_fi(task_data[3])
        add_dialog.title = ft.Text("Muokkaa", color=COLOR_TEXT)
        page.open(add_dialog)

    # --- PÄÄRAKENNE ---
    def tab_changed(e):
        render_tasks(e.control.tabs[e.control.selected_index].text)

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Kaikki", icon=ft.Icons.LIST),
            ft.Tab(text="Työ", icon=ft.Icons.WORK),
            ft.Tab(text="Koulu", icon=ft.Icons.SCHOOL),
            ft.Tab(text="Muu", icon=ft.Icons.CIRCLE),
        ],
        on_change=tab_changed,
        label_color=COLOR_BG,
        indicator_color=COLOR_BG,
        divider_color="transparent"
    )

    page.appbar = ft.AppBar(title=ft.Text("DIIDELAINIT", color=COLOR_BG, font_family="Retro"), center_title=True, bgcolor=COLOR_PRIMARY)
    
    # KORJAUS: color -> foreground_color
    page.floating_action_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD, 
        bgcolor=COLOR_PRIMARY, 
        foreground_color=COLOR_BG, 
        on_click=open_new_dialog
    )

    page.add(
        ft.Column([
            ft.Container(content=tabs, bgcolor=COLOR_PRIMARY),
            ft.Container(content=tasks_column, padding=10, expand=True)
        ], expand=True)
    )

    render_tasks("Kaikki")

ft.app(target=main, view=ft.AppView.WEB_BROWSER)