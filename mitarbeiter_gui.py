import tkinter as tk
from tkinter import messagebox, ttk 
from datetime import datetime, timedelta
from database import connect_db

class MitarbeiterGUI:
    def __init__(self, root, mitarbeiter_id, vorname):
        self.mitarbeiter_id = mitarbeiter_id
        self.vorname = vorname if vorname else "Mitarbeiter"
        self.window = tk.Toplevel(root)
        self.window.title("Mitarbeiter | Arbeitszeiterfassung")
        self.window.geometry("400x250")

        # Style für ttk
        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 14))
        style.configure("TButton", font=("Arial", 12))

        # Frame für bessere Struktur
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Willkommens-Label
        ttk.Label(main_frame, text=f"Willkommen, {self.vorname}").pack(pady=10)

        # Timer-Label
        self.timer_label = ttk.Label(main_frame, text="00:00:00", font=("Arial", 16), foreground="red")
        self.timer_label.pack(pady=10)

        # Buttons mit ttk
        self.btn_start = ttk.Button(main_frame, text="🟢 Arbeitsbeginn", command=self.start_work)
        self.btn_start.pack(pady=5, fill="x")

        self.btn_pause = ttk.Button(main_frame, text="⏸️ Pause", command=self.pause_work)
        self.btn_pause.pack(pady=5, fill="x")

        self.btn_end = ttk.Button(main_frame, text="🔴 Arbeitsende", command=self.end_work)
        self.btn_end.pack(pady=5, fill="x")

        self.start_time = None
        self.pause_time = None
        self.eintrag_id = None
        self.total_pause_duration = timedelta()
        self.total_pause = 0
        self.running = False
        self.alert_shown = False

    def start_work(self):
        if self.start_time:
            messagebox.showwarning("Info", "Du hast deinen Arbeitstag bereits gestartet")
            return
        
        now = datetime.now()
        earliest_start = now.replace(hour=7, minute=0, second=0, microsecond=0)
        
        if now < earliest_start:
            messagebox.showerror("Fehler", "Arbeitsbeginn erst ab 07:00 Uhr möglich")
            return

        self.start_time = now
        formatted_start = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            sql = "INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit) VALUES (%s, 'Arbeit', %s)"
            try:
                cursor.execute(sql, (self.mitarbeiter_id, formatted_start))
                self.eintrag_id = cursor.lastrowid
                conn.commit()
                self.running = True
                self.update_timer()
                print(f"Arbeitsbeginn: {formatted_start}, Eintrag-ID: {self.eintrag_id}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()

    def update_timer(self):
        if self.running and self.start_time:
            now = datetime.now()
            start_date = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            latest_end = start_date.replace(hour=19, minute=0, second=0)
            
            # Automatisches Beenden um 19:00 Uhr
            if now >= latest_end:
                self.end_work()
                return

            elapsed_time = now - self.start_time - self.total_pause_duration
            hours = elapsed_time.total_seconds() / 3600
            
            if hours > 8 and not hasattr(self, 'overtime_notified'):
                messagebox.showinfo("Hinweis", "Du hast mehr als 8 Stunden gearbeitet")
                self.overtime_notified = True

            # Prüfung der Pausenzeit, während eine Pause läuft
        if self.paused and self.current_pause_start:
            current_pause_duration = now - self.current_pause_start
            pause_minutes = current_pause_duration.total_seconds() / 60
            if pause_minutes > 60 and not hasattr(self, 'pause_notified'):
                messagebox.showwarning("Warnung", "Deine aktuelle Pausenzeit beträgt mehr als 60 Minuten")
                self.pause_notified = True

            self.timer_label.config(text=str(elapsed_time).split('.')[0])
            self.window.after(1000, self.update_timer)

    def pause_work(self):
        if not self.start_time:
            messagebox.showwarning("Fehler", "Arbeitsbeginn muss zuerst erfasst werden")
            return
        if self.pause_time:  # Pause beenden
            pause_end = datetime.now()
            pause_duration = pause_end - self.pause_time
            self.total_pause_duration += pause_duration
            self.pause_time = None
            self.running = True
            self.update_timer()
            self.timer_label.config(foreground="red")
            pause_minutes = self.total_pause_duration.total_seconds() / 60
            if pause_minutes > 60 and not hasattr(self, 'pause_notified'):
                messagebox.showwarning("Warnung", "Deine Pausenzeit beträgt mehr als 60 Minuten")
                self.pause_notified = True
        else:  # Pause starten
            self.pause_time = datetime.now()
            self.running = False
            self.timer_label.config(text="Pause gestartet ⏸️", foreground="blue")

    def end_work(self):
        if not self.start_time:
            messagebox.showerror("Fehler", "Arbeitsbeginn wurde nicht erfasst")
            return
        if self.pause_time:
            messagebox.showwarning("Fehler", "Bitte beende die Pause, bevor du den Arbeitstag beendest")
            return
        
        now = datetime.now()
        start_date = self.start_time.replace(hour=0, minute=0, second=0, microsecond=0)
        latest_end = start_date.replace(hour=19, minute=0, second=0)
        
        # Wenn manuell nach 19:00 Uhr beendet wird (sollte durch update_timer verhindert werden)
        if now > latest_end:
            now = latest_end  # Setze Endzeit auf 19:00 Uhr
            messagebox.showinfo("Info", "Arbeitstag wurde automatisch um 19:00 Uhr beendet.")

        formatted_end = now.strftime("%Y-%m-%d %H:%M:%S")
        pause_hours = self.total_pause_duration.total_seconds() / 3600
        
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            try:
                sql_update = "UPDATE anwesenheiten SET end_zeit = %s, pause_in_stunden = %s WHERE eintrag_id = %s"
                cursor.execute(sql_update, (formatted_end, pause_hours, self.eintrag_id))
                conn.commit()

                self.running = False
                self.timer_label.config(text="00:00:00", foreground="red")
                self.start_time = None
                self.total_pause_duration = timedelta()
                self.eintrag_id = None
                if hasattr(self, 'pause_notified'):
                    del self.pause_notified
                if hasattr(self, 'overtime_notified'):
                    del self.overtime_notified
                print(f"Arbeitsende: {formatted_end}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()