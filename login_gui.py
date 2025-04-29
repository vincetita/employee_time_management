import tkinter as tk
from tkinter import messagebox, ttk
import bcrypt
from database import fetch_user_data, connect_db
from mitarbeiter_gui import MitarbeiterGUI
from admin_gui import AdminGUI
from hr_gui import HRGUI

class BenutzerLoginGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Login | Arbeitszeiterfassung")
        self.root.geometry("350x290")

        # Style für ttk
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 14), padding=5)

        # Hauptframe
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Titel
        ttk.Label(main_frame, text="Anmeldung", font=("Arial", 16)).pack(pady=15)

        # Benutzername
        ttk.Label(main_frame, text="Benutzername:").pack()
        self.username_entry = ttk.Entry(main_frame, style="TEntry")
        self.username_entry.pack(pady=5, fill="x")

        # Passwort
        ttk.Label(main_frame, text="Passwort:").pack()
        self.password_entry = ttk.Entry(main_frame, style="TEntry", show="*")
        self.password_entry.pack(pady=5, fill="x")

        # Login-Button
        self.login_button = ttk.Button(main_frame, text="Login ➡️", command=self.login)
        self.login_button.pack(pady=15, fill="x")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning("Fehler", "Gib bitte Benutzername und Passwort ein")
            return

        user_data = fetch_user_data(username)
        if user_data:
            stored_hash, rolle, mitarbeiter_id, vorname, status, passwort_typ = user_data
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                if passwort_typ == "abgelaufen":
                    self.change_password_window(username, mitarbeiter_id, vorname)
                elif status == "aktiv":
                    # Rolle prüfen und entsprechendes GUI öffnen
                    gui_window = None
                    if rolle == "Admin":
                        gui_window = AdminGUI(self.root, mitarbeiter_id, vorname)
                    elif rolle == "HR":
                        gui_window = HRGUI(self.root, mitarbeiter_id, vorname)
                    elif rolle == "Mitarbeiter":
                        gui_window = MitarbeiterGUI(self.root, mitarbeiter_id, vorname)
                    else:
                        messagebox.showerror("Fehler", "Unbekannte Rolle!")
                        return

                    if gui_window:
                        # Wenn das GUI-Fenster geschlossen wird, Login-Fenster wieder einblenden
                        gui_window.window.protocol("WM_DELETE_WINDOW", lambda: self.on_gui_close(gui_window.window))
                        self.root.withdraw()  # Hauptfenster ausblenden
                else:
                    messagebox.showerror("Fehler", "Dein Konto ist inaktiv!")
            else:
                messagebox.showerror("Fehler", "Falsches Passwort!")

    def on_gui_close(self, window):
        # Wird aufgerufen, wenn ein GUI-Fenster geschlossen wird
        window.destroy()  # Das GUI-Fenster schließen
        self.root.deiconify()  # Login-Fenster wieder einblenden
        self.username_entry.delete(0, tk.END)  # Benutzername leeren
        self.password_entry.delete(0, tk.END)  # Passwort leeren

    def change_password_window(self, username, mitarbeiter_id, vorname):
        change_window = tk.Toplevel(self.root)
        change_window.title("Passwort ändern")
        change_window.geometry("350x290")

        change_frame = ttk.Frame(change_window, padding="20")
        change_frame.pack(fill="both", expand=True)

        ttk.Label(change_frame, text="Neues Passwort festlegen", font=("Arial", 16)).pack(pady=15)
        ttk.Label(change_frame, text="Neues Passwort:").pack()
        new_password_entry = ttk.Entry(change_frame, style="TEntry", show="*")
        new_password_entry.pack(pady=5, fill="x")
        ttk.Label(change_frame, text="Passwort bestätigen:").pack()
        confirm_password_entry = ttk.Entry(change_frame, style="TEntry", show="*")
        confirm_password_entry.pack(pady=5, fill="x")

        def save_new_password():
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()

            if not new_password or not confirm_password:
                messagebox.showwarning("Fehler", "Bitte beide Felder ausfüllen!")
                return
            if new_password != confirm_password:
                messagebox.showerror("Fehler", "Passwörter stimmen nicht überein!")
                return

            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute("UPDATE benutzer SET password_hash = %s, passwort_typ = 'festgelegt' WHERE username = %s", (new_hash, username))
            conn.commit()
            cursor.close()
            conn.close()

            messagebox.showinfo("Erfolg", "Passwort erfolgreich geändert. Bitte erneut einloggen.")
            change_window.destroy()

        ttk.Button(change_frame, text="Speichern ✅", command=save_new_password).pack(pady=15, fill="x")

if __name__ == "__main__":
    root = tk.Tk()
    app = BenutzerLoginGUI(root)
    root.mainloop()