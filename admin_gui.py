import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import bcrypt
from reportlab.lib import colors
from reportlab.lib.pagesizes import TABLOID, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from datetime import datetime, timedelta
from database import start_work, end_work, connect_db
import csv
from tkcalendar import DateEntry

class AdminGUI:
    def __init__(self, root, mitarbeiter_id, vorname):
        self.mitarbeiter_id = mitarbeiter_id
        self.vorname = vorname
        self.window = tk.Toplevel(root)
        self.window.title("Administrator Dashboard")
        self.window.geometry("800x500")

        style = ttk.Style()
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12))

        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill="both", expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="y", padx=10)

        ttk.Label(left_frame, text=f"Willkommen, {self.vorname}", font=("Arial", 14)).pack(pady=10)
        self.timer_label = ttk.Label(left_frame, text="00:00:00", font=("Arial", 16), foreground="red")
        self.timer_label.pack(pady=10)
        self.btn_start = ttk.Button(left_frame, text="🟢 Arbeitsbeginn", command=self.start_work)
        self.btn_start.pack(pady=5, fill="x")
        self.btn_pause = ttk.Button(left_frame, text="⏸️ Pause", command=self.pause_work)
        self.btn_pause.pack(pady=5, fill="x")
        self.btn_end = ttk.Button(left_frame, text="🔴 Arbeitsende", command=self.end_work)
        self.btn_end.pack(pady=5, fill="x")
        self.btn_search = ttk.Button(left_frame, text="Mitarbeiter suchen", command=self.mitarbeiter_suchen)
        self.btn_search.pack(pady=5, fill="x")
        self.btn_edit = ttk.Button(left_frame, text="Mitarbeiter bearbeiten", command=self.mitarbeiter_bearbeiten)
        self.btn_edit.pack(pady=5, fill="x")
        self.btn_add = ttk.Button(left_frame, text="Mitarbeiter hinzufügen", command=self.mitarbeiter_hinzufuegen)
        self.btn_add.pack(pady=5, fill="x")
        self.btn_activate = ttk.Button(left_frame, text="Mitarbeiter aktivieren", command=self.mitarbeiter_aktivieren)
        self.btn_activate.pack(pady=5, fill="x")
        self.btn_deactivate = ttk.Button(left_frame, text="Mitarbeiter deaktivieren", command=self.mitarbeiter_deaktivieren)
        self.btn_deactivate.pack(pady=5, fill="x")
        self.btn_reset_password = ttk.Button(left_frame, text="Passwort zurücksetzen", command=self.passwort_zuruecksetzen)
        self.btn_reset_password.pack(pady=5, fill="x")
        self.btn_zeiterfassung = ttk.Button(left_frame, text="⏱️ Zeiterfassung", command=self.zeiterfassung)
        self.btn_zeiterfassung.pack(pady=5, fill="x")

        self.right_frame = ttk.Frame(main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10)

        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = timedelta()
        self.running = False

        menue = tk.Menu(self.window)
        self.window.config(menu=menue)
        datei_m = tk.Menu(menue, tearoff=0)
        menue.add_cascade(label="Datei", menu=datei_m)
        datei_m.add_command(label="Import CSV", command=self.browse_file)
        datei_m.add_command(label="Export", command=self.export_datei)
        
        self.refresh_table()

    # Suche nach *.csv Datei
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="CSV-Datei auswählen",
            filetypes=[("CSV-Dateien", "*.csv")]
        )
        if file_path:
            self.insert_from_csv(file_path)

    # Tabelle aus *.csv importieren
    def insert_from_csv(self, csv_datei):
        dbconnector = connect_db()
        if dbconnector is None:
            return
        datatable_insert = dbconnector.cursor()

        sql_insert_mitarbeiter = "INSERT INTO mitarbeiter (abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, urlaubstage, gehalt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        
        sql_insert_benutzer = "INSERT INTO benutzer (mitarbeiter_id, username, password_hash, passwort_typ) VALUES (%s, %s, %s, %s)"

        try:
            with open(csv_datei, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file, delimiter=";")
                next(reader)  # Überspringt die Kopfzeile
                for row in reader:
                    # Mitarbeiter einfügen
                    datatable_insert.execute(sql_insert_mitarbeiter, row)
                    
                    # Die zuletzt eingefügte mitarbeiter_id abrufen
                    datatable_insert.execute("SELECT LAST_INSERT_ID()")
                    mitarbeiter_id = datatable_insert.fetchone()[0]

                    # Benutzername generieren (vorname.nachname, kleingeschrieben)
                    vorname = row[2]  # Index 2 - 'vorname' in der CSV
                    nachname = row[3]  # Index 3 - 'nachname' in der CSV
                    username = f"{vorname.lower()}.{nachname.lower()}"
                    default_password = f"{vorname.lower()}.{nachname.lower()}123"
                    passwort_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

                    # Benutzer einfügen
                    values_benutzer = (mitarbeiter_id, username, passwort_hash, "abgelaufen")
                    datatable_insert.execute(sql_insert_benutzer, values_benutzer)

            dbconnector.commit()
            messagebox.showinfo("Erfolg", "CSV-Daten erfolgreich eingefügt")
        except Exception as e:
            dbconnector.rollback()  # Rückgängig machen bei Fehlern
            messagebox.showerror("Fehler", f"Fehler beim Importieren der CSV-Datei: {str(e)}")
        finally:
            datatable_insert.close()
            dbconnector.close()

    # Tabelle mit Mitarbeiterdaten exportieren als *.xlsx oder *.pdf
    def export_datei(self):
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            messagebox.showwarning("Warnung", "Keine Daten zum Exportieren vorhanden")
            return

        columns = self.tree["columns"]
        if not columns:
            messagebox.showwarning("Warnung", "Keine Spalten zum Exportieren vorhanden")
            return

        data = []
        for item in self.tree.get_children():
            row = self.tree.item(item, "values")
            data.append(row)

        if not data:
            messagebox.showwarning("Warnung", "Keine Datenreihen zum Exportieren vorhanden")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel-Datei", "*.xlsx"), ("PDF-Datei", "*.pdf")],
            title="Daten exportieren als"
        )
        if not file_path:
            return

        if file_path.endswith(".xlsx"):
            try:
                df = pd.DataFrame(data, columns=columns)
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Erfolg", f"Daten erfolgreich als XLSX exportiert: {file_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren als XLSX: {str(e)}")

        elif file_path.endswith(".pdf"):
            try:
                custom_size = (1800, 500)
                doc = SimpleDocTemplate(file_path, pagesize=custom_size)
                elements = []

                table_data = [columns] + data
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))

                elements.append(table)
                doc.build(elements)
                messagebox.showinfo("Erfolg", f"Daten erfolgreich als PDF exportiert: {file_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren als PDF: {str(e)}")

    # Startet Timer für Arbeitsbeginn
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

    # Aktualisiert den Timer und überprüft die Arbeitszeit
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
            
            # Zeigt ein Hinweis, wenn ein Mitarbeiter mehr als 8 Stunden am Tag gearbeitet hat
            if hours > 8 and not hasattr(self, 'overtime_notified'):
                messagebox.showinfo("Hinweis", "Du hast mehr als 8 Stunden gearbeitet")
                self.overtime_notified = True
            # Zeigt eine Warnung, wenn die Pause mehr als 60 Minuten am Tag beträgt
            pause_minutes = self.total_pause_duration.total_seconds() / 60
            if pause_minutes > 60 and not hasattr(self, 'pause_notified'):
                messagebox.showwarning("Warnung", "Deine Pausenzeit beträgt mehr als 60 Minuten")
                self.pause_notified = True

            self.timer_label.config(text=str(elapsed_time).split('.')[0])
            self.window.after(1000, self.update_timer)
    # Pause starten oder beenden
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
    # Beendet den Arbeitstag und speichert die Daten in Datenbank
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
    # Neuer Mitarbeiter hinzufügen
    def mitarbeiter_hinzufuegen(self):
        add_window = tk.Toplevel(self.window)
        add_window.title("Mitarbeiter hinzufügen")
        add_window.geometry("600x450")

        add_frame = ttk.Frame(add_window, padding="10")
        add_frame.pack(fill="both", expand=True)

        fields = [
            ("Abteilung", "entry_abteilung", "combobox"),
            ("Position", "entry_position", "combobox"),
            ("Vorname", "entry_vorname", "entry"),
            ("Nachname", "entry_nachname", "entry"),
            ("Straße", "entry_strasse", "entry"),
            ("Hausnummer", "entry_hausnummer", "entry"),
            ("PLZ", "entry_plz", "entry"),
            ("Stadt", "entry_stadt", "entry"),
            ("Telefon", "entry_telefon", "entry"),
            ("Email", "entry_email", "entry"),
            ("Geburtsdatum)", "entry_geburtsdatum", "calendar"),
            ("Vertrag Beginn)", "entry_vertrag_beginn", "calendar"),
            ("Vertrag Ende", "entry_vertrag_ende", "calendar"),
            ("Vertrag Typ", "entry_vertrag_typ", "combobox"),
            ("Arbeitszeit", "entry_arbeitszeit", "combobox"),
            ("Urlaubstage", "entry_urlaubstage", "entry"),
            ("Gehalt", "entry_gehalt", "entry"),
        ]

        abteilung_options = ["Geschäftsführung", "Kundensupport & Office-Management", "Marketing", "Technik", "Vertrieb", "Verwaltung"]
        position_options = ["Geschäftsführung", "Kundenservice", "Kundenservice-Leitung", "Office-Management", "Marketing-Management", "Online-Marketing-Spezialist", "Social-Media-Management", "Datenbankadministration", "IT-Infrastrukturleitung", "IT-Projektmanagement", "IT-Support", "IT-Support-Leitung", "IT-Support-Spezialist", "Netzwerkadministration", "Senior IT-Beratung", "Systemadministration", "Key-Account-Management", "Vertriebsaußendienst", "Vertriebsinnendienst", "Vertriebsleitung", "Vertriebsunterstützung", "Controlling & Finanzanalyse", "Gehaltsbuchhaltung", "HR- & Finanzleitung", "Personalreferenz"]
        vertrag_typ_options = ["Unbefristet", "Befristet"]
        arbeitszeit_options = ["Vollzeit", "Teilzeit"]

        for i, (label_text, attr, widget_type) in enumerate(fields):
            if i < 8:
                col = 0
                row = i
            else:
                col = 2
                row = i - 8

            ttk.Label(add_frame, text=label_text).grid(row=row, column=col, pady=5, sticky="w")
            if widget_type == "entry":
                widget = ttk.Entry(add_frame)
            elif widget_type == "combobox":
                if attr == "entry_abteilung":
                    widget = ttk.Combobox(add_frame, values=abteilung_options, state="readonly")
                    widget.set(abteilung_options[0])
                elif attr == "entry_position":
                    widget = ttk.Combobox(add_frame, values=position_options, state="readonly")
                    widget.set(position_options[0])
                elif attr == "entry_vertrag_typ":
                    widget = ttk.Combobox(add_frame, values=vertrag_typ_options, state="readonly")
                    widget.set(vertrag_typ_options[0])
                elif attr == "entry_arbeitszeit":
                    widget = ttk.Combobox(add_frame, values=arbeitszeit_options, state="readonly")
                    widget.set(arbeitszeit_options[0])
            elif widget_type == "calendar":
                widget = DateEntry(add_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
            
            widget.grid(row=row, column=col + 1, pady=5, padx=5, sticky="ew")
            setattr(self, attr, widget)

        add_frame.grid_columnconfigure(1, weight=1)
        add_frame.grid_columnconfigure(3, weight=1)
        # Mitarbeiter speichern
        def save_mitarbeiter():
            abteilung = self.entry_abteilung.get()
            position = self.entry_position.get()
            vorname = self.entry_vorname.get()
            nachname = self.entry_nachname.get()
            strasse = self.entry_strasse.get()
            hausnummer = self.entry_hausnummer.get()
            plz = self.entry_plz.get()
            stadt = self.entry_stadt.get()
            telefon = self.entry_telefon.get()
            email = self.entry_email.get()
            geburtsdatum = self.entry_geburtsdatum.get()
            vertrag_beginn = self.entry_vertrag_beginn.get()
            vertrag_ende = self.entry_vertrag_ende.get() or None
            vertrag_typ = self.entry_vertrag_typ.get()
            arbeitszeit = self.entry_arbeitszeit.get()
            urlaubstage = self.entry_urlaubstage.get()
            gehalt = self.entry_gehalt.get()

            if all([abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_typ, arbeitszeit, urlaubstage, gehalt]):
                try:
                    self.datenbank_mitarbeiter_hinzufuegen(abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, int(urlaubstage), float(gehalt))
                    messagebox.showinfo("Erfolg", f"Mitarbeiter {vorname} {nachname} wurde hinzugefügt")
                    add_window.destroy()
                except ValueError as e:
                    messagebox.showerror("Fehler", f"Eingabefehler: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            else:
                messagebox.showwarning("Fehler", "Bitte alle Pflichtfelder ausfüllen")
            
            self.refresh_table()
        ttk.Button(add_frame, text="Speichern ✅", command=save_mitarbeiter).grid(row=9, column=0, columnspan=4, pady=15, sticky="ew")
    # Suche nach Mitarbeitern. Neben relevanten Informationen muss ein checkbox aktiviert werden
    def mitarbeiter_suchen(self):
        search_window = tk.Toplevel(self.window)
        search_window.title("Mitarbeiter suchen")
        search_window.geometry("700x500")

        search_frame = ttk.Frame(search_window, padding="10")
        search_frame.pack(fill="both", expand=True)

        search_fields = [
            ("Abteilung", "search_abteilung", "combobox", "check_abteilung"),
            ("Position", "search_position", "combobox", "check_position"),
            ("Vorname", "search_vorname", "entry", "check_vorname"),
            ("Nachname", "search_nachname", "entry", "check_nachname"),
            ("Straße", "search_strasse", "entry", "check_strasse"),
            ("Hausnummer", "search_hausnummer", "entry", "check_hausnummer"),
            ("PLZ", "search_plz", "entry", "check_plz"),
            ("Stadt", "search_stadt", "entry", "check_stadt"),
            ("Telefon", "search_telefon", "entry", "check_telefon"),
            ("Email", "search_email", "entry", "check_email"),
            ("Geburtsdatum", "search_geburtsdatum", "calendar", "check_geburtsdatum"),
            ("Vertrag Beginn", "search_vertrag_beginn", "calendar", "check_vertrag_beginn"),
            ("Vertrag Ende", "search_vertrag_ende", "calendar", "check_vertrag_ende"),
            ("Vertrag Typ", "search_vertrag_typ", "combobox", "check_vertrag_typ"),
            ("Arbeitszeit", "search_arbeitszeit", "combobox", "check_arbeitszeit"),
            ("Urlaubstage", "search_urlaubstage", "entry", "check_urlaubstage"),
            ("Gehalt", "search_gehalt", "entry", "check_gehalt"),
            ("Status", "search_status", "combobox", "check_status"),
        ]

        abteilung_options = ["Geschäftsführung", "Kundensupport & Office-Management", "Marketing", "Technik", "Vertrieb", "Verwaltung"]
        position_options = ["Geschäftsführung", "Kundenservice", "Kundenservice-Leitung", "Office-Management", "Marketing-Management", "Online-Marketing-Spezialist", "Social-Media-Management", "Datenbankadministration", "IT-Infrastrukturleitung", "IT-Projektmanagement", "IT-Support", "IT-Support-Leitung", "IT-Support-Spezialist", "Netzwerkadministration", "Senior IT-Beratung", "Systemadministration", "Key-Account-Management", "Vertriebsaußendienst", "Vertriebsinnendienst", "Vertriebsleitung", "Vertriebsunterstützung", "Controlling & Finanzanalyse", "Gehaltsbuchhaltung", "HR- & Finanzleitung", "Personalreferenz"]
        vertrag_typ_options = ["Unbefristet", "Befristet"]
        arbeitszeit_options = ["Vollzeit", "Teilzeit"]
        status_options = ["aktiv", "inaktiv"]

        for i, (label_text, attr, widget_type, check_attr) in enumerate(search_fields):
            if i < 9:
                col = 0
                row = i
            else:
                col = 3
                row = i - 9

            ttk.Label(search_frame, text=label_text).grid(row=row, column=col, pady=5, sticky="w")
            if widget_type == "entry":
                widget = ttk.Entry(search_frame)
            elif widget_type == "combobox":
                if attr == "search_abteilung":
                    widget = ttk.Combobox(search_frame, values=abteilung_options, state="readonly")
                    widget.set(abteilung_options[0])
                elif attr == "search_position":
                    widget = ttk.Combobox(search_frame, values=position_options, state="readonly")
                    widget.set(position_options[0])
                elif attr == "search_vertrag_typ":
                    widget = ttk.Combobox(search_frame, values=vertrag_typ_options, state="readonly")
                    widget.set(vertrag_typ_options[0])
                elif attr == "search_arbeitszeit":
                    widget = ttk.Combobox(search_frame, values=arbeitszeit_options, state="readonly")
                    widget.set(arbeitszeit_options[0])
                elif attr == "search_status":
                    widget = ttk.Combobox(search_frame, values=status_options, state="readonly")
                    widget.set(status_options[0])
            elif widget_type == "calendar":
                widget = DateEntry(search_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)

            widget.grid(row=row, column=col + 1, pady=5, padx=5, sticky="ew")
            setattr(self, attr, widget)

            check_var = tk.BooleanVar(value=False)
            check = ttk.Checkbutton(search_frame, variable=check_var)
            check.grid(row=row, column=col + 2, padx=5)
            setattr(self, check_attr, check_var)

        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_columnconfigure(4, weight=1)

        def search_and_display():
            conditions = []
            values = []
            field_mapping = {
                "search_abteilung": ("abteilung", "check_abteilung"),
                "search_position": ("position", "check_position"),
                "search_vorname": ("vorname", "check_vorname"),
                "search_nachname": ("nachname", "check_nachname"),
                "search_strasse": ("strasse", "check_strasse"),
                "search_hausnummer": ("hausnummer", "check_hausnummer"),
                "search_plz": ("plz", "check_plz"),
                "search_stadt": ("stadt", "check_stadt"),
                "search_telefon": ("telefon", "check_telefon"),
                "search_email": ("email", "check_email"),
                "search_geburtsdatum": ("geburtsdatum", "check_geburtsdatum"),
                "search_vertrag_beginn": ("vertrag_beginn", "check_vertrag_beginn"),
                "search_vertrag_ende": ("vertrag_ende", "check_vertrag_ende"),
                "search_vertrag_typ": ("vertrag_typ", "check_vertrag_typ"),
                "search_arbeitszeit": ("arbeitszeit", "check_arbeitszeit"),
                "search_urlaubstage": ("urlaubstage", "check_urlaubstage"),
                "search_gehalt": ("gehalt", "check_gehalt"),
                "search_status": ("status", "check_status"),
            }

            for attr, (db_field, check_attr) in field_mapping.items():
                check_var = getattr(self, check_attr)
                if check_var.get():
                    value = getattr(self, attr).get()
                    if value:
                        conditions.append(f"{db_field} = %s")
                        values.append(value)

            query = "SELECT * FROM mitarbeiter"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()
            cursor.execute(query, values)
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()

            for widget in self.right_frame.winfo_children():
                widget.destroy()

            self.tree = ttk.Treeview(self.right_frame, height=20)
            scrollbar_vert = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
            scrollbar_horiz = ttk.Scrollbar(self.right_frame, orient="horizontal", command=self.tree.xview)

            self.tree.configure(yscrollcommand=scrollbar_vert.set, xscrollcommand=scrollbar_horiz.set)

            self.tree.grid(row=0, column=0, sticky="nsew")
            scrollbar_vert.grid(row=0, column=1, sticky="ns")
            scrollbar_horiz.grid(row=1, column=0, sticky="ew")

            self.right_frame.columnconfigure(0, weight=1)
            self.right_frame.rowconfigure(0, weight=1)

            self.tree["columns"] = column_names
            self.tree.column("#0", width=0, stretch=tk.NO)
            for col in column_names:
                self.tree.column(col, anchor="w", width=100)
                self.tree.heading(col, text=col.capitalize(), anchor="w")

            for row in results:
                self.tree.insert("", tk.END, values=row)

            search_window.destroy()

        ttk.Button(search_frame, text="Suchen 🔍", command=search_and_display).grid(row=9, column=0, columnspan=6, pady=15, sticky="ew")
    # Mitarbeiter in Datenbank hinzufügen
    def datenbank_mitarbeiter_hinzufuegen(self, abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, urlaubstage, gehalt):
        conn = connect_db()
        if conn is None:
            return
        cursor = conn.cursor()

        # SQL-Statement für die mitarbeiter-Tabelle
        sql_insert_mitarbeiter = "INSERT INTO mitarbeiter (abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, urlaubstage, gehalt) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        values_mitarbeiter = (abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, urlaubstage, gehalt)

        sql_insert_benutzer = "INSERT INTO benutzer (mitarbeiter_id, username, password_hash, passwort_typ) VALUES (%s, %s, %s, %s)"
        # Benutzername und Passwort generieren
        username = f"{vorname.lower()}.{nachname.lower()}"
        default_password = f"{vorname.lower()}.{nachname.lower()}123"
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())
        try:
            # Mitarbeiter einfügen
            cursor.execute(sql_insert_mitarbeiter, values_mitarbeiter)
            
            # Die zuletzt eingefügte mitarbeiter_id abrufen
            cursor.execute("SELECT LAST_INSERT_ID()")
            mitarbeiter_id = cursor.fetchone()[0]

            # Benutzername generieren (vorname.nachname, kleingeschrieben)
            username = f"{vorname.lower()}.{nachname.lower()}"

            # SQL-Statement für die benutzer-Tabelle
            values_benutzer = (mitarbeiter_id, username, password_hash, "abgelaufen")

            # Benutzer einfügen
            cursor.execute(sql_insert_benutzer, values_benutzer)

            # Beide Änderungen committen
            conn.commit()

        except Exception as e:
            # Bei einem Fehler rollback durchführen
            conn.rollback()
            raise Exception(f"Datenbankfehler: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    # Status auf "aktiv" setzen       
    def mitarbeiter_aktivieren(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus der Tabelle aus")
            return

        mitarbeiter_id = self.tree.item(selected_item, "values")[0]
        self.update_status(mitarbeiter_id, "aktiv")
        self.refresh_table()
    # Status auf "inaktiv" setzen  
    def mitarbeiter_deaktivieren(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus der Tabelle aus")
            return

        mitarbeiter_id = self.tree.item(selected_item, "values")[0]
        self.update_status(mitarbeiter_id, "inaktiv")
        self.refresh_table()
    # status in Datenbank updaten
    def update_status(self, mitarbeiter_id, status):
        conn = connect_db()
        if conn is None:
            return
        cursor = conn.cursor()

        sql_update = "UPDATE mitarbeiter SET status = %s WHERE mitarbeiter_id = %s"
        values = (status, mitarbeiter_id)

        try:
            cursor.execute(sql_update, values)
            conn.commit()
            messagebox.showinfo("Erfolg", f"Mitarbeiter wurde auf '{status}' gesetzt")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Aktualisieren des Status: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    # Aktualisiert die Tabelle
    def refresh_table(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        conn = connect_db()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mitarbeiter")
        results = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        self.tree = ttk.Treeview(self.right_frame)
        self.tree.pack(fill="both", expand=True)

        self.tree["columns"] = column_names
        self.tree.column("#0", width=0, stretch=tk.NO)
        for col in column_names:
            self.tree.column(col, anchor="w", width=100)
            self.tree.heading(col, text=col.capitalize(), anchor="w")

        for row in results:
            self.tree.insert("", tk.END, values=row)
    # Ausgewählten Mitarbeiter bearbeiten
    def mitarbeiter_bearbeiten(self):
        selected_item = self.tree.selection()
        if not selected_item: # Fehlermeldung, falls kein Mitarbeiter ausgewählt ist
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus der Tabelle aus")
            return

        mitarbeiter_id = self.tree.item(selected_item, "values")[0]
        conn = connect_db()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mitarbeiter WHERE mitarbeiter_id = %s", (mitarbeiter_id,))
        mitarbeiter = cursor.fetchone()
        column_names = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        if not mitarbeiter:
            messagebox.showerror("Fehler", "Mitarbeiter konnte nicht gefunden werden")
            return

        edit_window = tk.Toplevel(self.window)
        edit_window.title("Mitarbeiter bearbeiten")
        edit_window.geometry("600x450")

        edit_frame = ttk.Frame(edit_window, padding="10")
        edit_frame.pack(fill="both", expand=True)

        fields = [
            ("Abteilung", "entry_abteilung", "combobox"),
            ("Position", "entry_position", "combobox"),
            ("Vorname", "entry_vorname", "entry"),
            ("Nachname", "entry_nachname", "entry"),
            ("Straße", "entry_strasse", "entry"),
            ("Hausnummer", "entry_hausnummer", "entry"),
            ("PLZ", "entry_plz", "entry"),
            ("Stadt", "entry_stadt", "entry"),
            ("Telefon", "entry_telefon", "entry"),
            ("Email", "entry_email", "entry"),
            ("Geburtsdatum)", "entry_geburtsdatum", "calendar"),
            ("Vertrag Beginn)", "entry_vertrag_beginn", "calendar"),
            ("Vertrag Ende", "entry_vertrag_ende", "calendar"),
            ("Vertrag Typ", "entry_vertrag_typ", "combobox"),
            ("Arbeitszeit", "entry_arbeitszeit", "combobox"),
            ("Urlaubstage", "entry_urlaubstage", "entry"),
            ("Gehalt", "entry_gehalt", "entry"),
        ]

        abteilung_options = ["Geschäftsführung", "Kundensupport & Office-Management", "Marketing", "Technik", "Vertrieb", "Verwaltung"]
        position_options = ["Geschäftsführung", "Kundenservice", "Kundenservice-Leitung", "Office-Management", "Marketing-Management", "Online-Marketing-Spezialist", "Social-Media-Management", "Datenbankadministration", "IT-Infrastrukturleitung", "IT-Projektmanagement", "IT-Support", "IT-Support-Leitung", "IT-Support-Spezialist", "Netzwerkadministration", "Senior IT-Beratung", "Systemadministration", "Key-Account-Management", "Vertriebsaußendienst", "Vertriebsinnendienst", "Vertriebsleitung", "Vertriebsunterstützung", "Controlling & Finanzanalyse", "Gehaltsbuchhaltung", "HR- & Finanzleitung", "Personalreferenz"]
        vertrag_typ_options = ["Unbefristet", "Befristet"]
        arbeitszeit_options = ["Vollzeit", "Teilzeit"]

        mitarbeiter_dict = dict(zip(column_names, mitarbeiter))

        for i, (label_text, attr, widget_type) in enumerate(fields):
            if i < 8:
                col = 0
                row = i
            else:
                col = 2
                row = i - 8

            ttk.Label(edit_frame, text=label_text).grid(row=row, column=col, pady=5, sticky="w")
            if widget_type == "entry":
                widget = ttk.Entry(edit_frame)
                widget.insert(0, mitarbeiter_dict.get(attr.split('_')[1], ""))
            elif widget_type == "combobox":
                if attr == "entry_abteilung":
                    widget = ttk.Combobox(edit_frame, values=abteilung_options, state="readonly")
                    widget.set(mitarbeiter_dict.get("abteilung", abteilung_options[0]))
                elif attr == "entry_position":
                    widget = ttk.Combobox(edit_frame, values=position_options, state="readonly")
                    widget.set(mitarbeiter_dict.get("position", position_options[0]))
                elif attr == "entry_vertrag_typ":
                    widget = ttk.Combobox(edit_frame, values=vertrag_typ_options, state="readonly")
                    widget.set(mitarbeiter_dict.get("vertrag_typ", vertrag_typ_options[0]))
                elif attr == "entry_arbeitszeit":
                    widget = ttk.Combobox(edit_frame, values=arbeitszeit_options, state="readonly")
                    widget.set(mitarbeiter_dict.get("arbeitszeit", arbeitszeit_options[0]))
            elif widget_type == "calendar":
                widget = DateEntry(edit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
                if mitarbeiter_dict.get(attr.split('_')[1]):
                    widget.set_date(mitarbeiter_dict.get(attr.split('_')[1]))

            widget.grid(row=row, column=col + 1, pady=5, padx=5, sticky="ew")
            setattr(self, attr, widget)

        edit_frame.grid_columnconfigure(1, weight=1)
        edit_frame.grid_columnconfigure(3, weight=1)
        # Speichert die geänderten Daten in Datenbank
        def save_edited_mitarbeiter():
            abteilung = self.entry_abteilung.get()
            position = self.entry_position.get()
            vorname = self.entry_vorname.get()
            nachname = self.entry_nachname.get()
            strasse = self.entry_strasse.get()
            hausnummer = self.entry_hausnummer.get()
            plz = self.entry_plz.get()
            stadt = self.entry_stadt.get()
            telefon = self.entry_telefon.get()
            email = self.entry_email.get()
            geburtsdatum = self.entry_geburtsdatum.get()
            vertrag_beginn = self.entry_vertrag_beginn.get()
            vertrag_ende = self.entry_vertrag_ende.get() or None
            vertrag_typ = self.entry_vertrag_typ.get()
            arbeitszeit = self.entry_arbeitszeit.get()
            urlaubstage = self.entry_urlaubstage.get()
            gehalt = self.entry_gehalt.get()

            if all([abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_typ, arbeitszeit, urlaubstage, gehalt]):
                try:
                    conn = connect_db()
                    if conn is None:
                        return
                    cursor = conn.cursor()
                    sql_update = "UPDATE mitarbeiter SET abteilung = %s, position = %s, vorname = %s, nachname = %s, strasse = %s, hausnummer = %s, plz = %s, stadt = %s, telefon = %s, email = %s, geburtsdatum = %s, vertrag_beginn = %s, vertrag_ende = %s, vertrag_typ = %s, arbeitszeit = %s, urlaubstage = %s, gehalt = %s WHERE mitarbeiter_id = %s"
                    values = (abteilung, position, vorname, nachname, strasse, hausnummer, plz, stadt, telefon, email, geburtsdatum, vertrag_beginn, vertrag_ende, vertrag_typ, arbeitszeit, int(urlaubstage), float(gehalt), mitarbeiter_id)
                    cursor.execute(sql_update, values)
                    conn.commit()
                    cursor.close()
                    conn.close()
                    messagebox.showinfo("Erfolg", f"Mitarbeiter {vorname} {nachname} wurde aktualisiert")
                    edit_window.destroy()
                    self.refresh_table()
                except ValueError as e:
                    messagebox.showerror("Fehler", f"Eingabefehler: {str(e)}")
                except Exception as e:
                    messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            else:
                messagebox.showwarning("Fehler", "Bitte alle Pflichtfelder ausfüllen")
            self.refresh_table()
        ttk.Button(edit_frame, text="Speichern ✅", command=save_edited_mitarbeiter).grid(row=9, column=0, columnspan=4, pady=15, sticky="ew")
    # Setzt Passwort auf "abgelaufen"
    def passwort_zuruecksetzen(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus der Tabelle aus")
            return

        mitarbeiter_id = self.tree.item(selected_item, "values")[0]
        conn = connect_db()
        if conn is None:
            return
        cursor = conn.cursor()

        sql_update = "UPDATE benutzer SET passwort_typ = %s WHERE mitarbeiter_id = %s"
        values = ("abgelaufen", mitarbeiter_id)

        try:
            cursor.execute(sql_update, values)
            conn.commit()
            messagebox.showinfo("Erfolg", "Passwort wurde auf 'abgelaufen' gesetzt")
            self.refresh_table()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Zurücksetzen des Passworts: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    # Öffnet das Fenster für die Zeiterfassung
    def zeiterfassung(self):
        zeiterfassung_window = tk.Toplevel(self.window)
        zeiterfassung_window.title("Zeiterfassung")
        zeiterfassung_window.geometry("1600x600")

        zeit_frame = ttk.Frame(zeiterfassung_window, padding="10")
        zeit_frame.pack(fill="both", expand=True)

        ttk.Label(zeit_frame, text="Von:").grid(row=0, column=0, pady=5, sticky="w")
        von_datum = DateEntry(zeit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        von_datum.grid(row=0, column=1, pady=5, padx=5, sticky="w")

        ttk.Label(zeit_frame, text="Bis:").grid(row=0, column=2, pady=5, sticky="w")
        bis_datum = DateEntry(zeit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        bis_datum.grid(row=0, column=3, pady=5, padx=5, sticky="w")

        ttk.Label(zeit_frame, text="Mitarbeiter:").grid(row=0, column=4, pady=5, sticky="w")
        conn = connect_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mitarbeiter_id, CONCAT(vorname, ' ', nachname) AS name FROM mitarbeiter")
            mitarbeiter_list = [(row[0], row[1]) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
        mitarbeiter_combo = ttk.Combobox(zeit_frame, values=[f"{id} - {name}" for id, name in mitarbeiter_list], state="readonly")
        mitarbeiter_combo.grid(row=0, column=5, pady=5, padx=5, sticky="w")

        tree = ttk.Treeview(zeit_frame, height=15)
        scrollbar_vert = ttk.Scrollbar(zeit_frame, orient="vertical", command=tree.yview)
        scrollbar_horiz = ttk.Scrollbar(zeit_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_vert.set, xscrollcommand=scrollbar_horiz.set)
        tree.grid(row=2, column=0, columnspan=6, pady=10, sticky="nsew")
        scrollbar_vert.grid(row=2, column=6, sticky="ns")
        scrollbar_horiz.grid(row=3, column=0, columnspan=6, sticky="ew")
        
        for col in range(6):  # Spalten 0 bis 5
            zeit_frame.columnconfigure(col, weight=1, minsize=100)
        zeit_frame.rowconfigure(2, weight=1)
        
        columns = ("eintrag_id", "typ", "start_zeit", "end_zeit", "pause_in_stunden", "arbeitsstunden", "ueberstunden", "entschuldigt", "bestaetigt", "kommentar", "restliche_urlaubstage")
        tree["columns"] = columns
        tree.column("#0", width=0, stretch=tk.NO)
        for col in columns:
            tree.column(col, anchor="w", width=100)
            tree.heading(col, text=col.capitalize().replace("_", " "), anchor="w")

        stats_frame = ttk.LabelFrame(zeit_frame, text="Statistik", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=6, pady=10, sticky="ew")
        ttk.Label(stats_frame, text="Genutzte Urlaubstage:").grid(row=0, column=0, pady=5, sticky="w")
        self.urlaubstage_label = ttk.Label(stats_frame, text="0")
        self.urlaubstage_label.grid(row=0, column=1, pady=5, padx=5)
        ttk.Label(stats_frame, text="Restliche Urlaubstage:").grid(row=0, column=2, pady=5, sticky="w")
        self.restliche_urlaubstage_label = ttk.Label(stats_frame, text="0")
        self.restliche_urlaubstage_label.grid(row=0, column=3, pady=5, padx=5)
        ttk.Label(stats_frame, text="Kranktage:").grid(row=0, column=4, pady=5, sticky="w")
        self.kranktage_label = ttk.Label(stats_frame, text="0")
        self.kranktage_label.grid(row=0, column=5, pady=5, padx=5)
        ttk.Label(stats_frame, text="Arbeitsstunden:").grid(row=0, column=6, pady=5, sticky="w")
        self.arbeitsstunden_label = ttk.Label(stats_frame, text="0")
        self.arbeitsstunden_label.grid(row=0, column=7, pady=5, padx=5)
        ttk.Label(stats_frame, text="Pausen (h):").grid(row=0, column=8, pady=5, sticky="w")
        self.pausen_label = ttk.Label(stats_frame, text="0")
        self.pausen_label.grid(row=0, column=9, pady=5, padx=5)
        ttk.Label(stats_frame, text="Überstunden:").grid(row=0, column=10, pady=5, sticky="w")
        self.ueberstunden_label = ttk.Label(stats_frame, text="0")
        self.ueberstunden_label.grid(row=0, column=11, pady=5, padx=5)

        ttk.Button(zeit_frame, text="Suchen 🔍", command=lambda: self.search_zeiterfassung(von_datum, bis_datum, mitarbeiter_combo, tree)).grid(row=1, column=0, columnspan=6, pady=10, sticky="ew")
        ttk.Button(zeit_frame, text="Krankmeldung 🤒", command=lambda: self.add_krankmeldung(mitarbeiter_combo)).grid(row=5, column=0, pady=5, sticky="ew")
        ttk.Button(zeit_frame, text="Urlaub 🏖️", command=lambda: self.add_urlaub(mitarbeiter_combo)).grid(row=5, column=1, pady=5, sticky="ew")
        ttk.Button(zeit_frame, text="Anwesenheit ⏱️", command=lambda: self.add_anwesenheit(mitarbeiter_combo)).grid(row=5, column=2, pady=5, sticky="ew")
        ttk.Button(zeit_frame, text="Bearbeiten ✏️", command=lambda: self.edit_eintrag(tree, mitarbeiter_combo, von_datum, bis_datum)).grid(row=5, column=3, pady=5, sticky="ew")
        ttk.Button(zeit_frame, text="Löschen 🗑️", command=lambda: self.delete_eintrag(tree, mitarbeiter_combo, von_datum, bis_datum)).grid(row=5, column=4, pady=5, sticky="ew")
        ttk.Button(zeit_frame, text="Export 📤", command=lambda: self.export_to_xlsx(tree)).grid(row=5, column=5, pady=5, sticky="ew")
    # Sucht in Datenbank nach Einträgen für bestimmten Zeitraum und Mitarbeiter
    def search_zeiterfassung(self, von_datum, bis_datum, mitarbeiter_combo, tree):
        start_date = von_datum.get()
        end_date = bis_datum.get()
        mitarbeiter = mitarbeiter_combo.get()
        if not mitarbeiter:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus")
            return
        mitarbeiter_id = mitarbeiter.split(" - ")[0]

        conn = connect_db()
        if conn is None:
            messagebox.showerror("Fehler", "Datenbankverbindung fehlgeschlagen")
            return
        cursor = conn.cursor()

        cursor.execute("SELECT urlaubstage FROM mitarbeiter WHERE mitarbeiter_id = %s", (mitarbeiter_id,))
        total_urlaubstage = cursor.fetchone()[0] or 0  # Falls NULL, dann 0

        query = "SELECT eintrag_id, typ, start_zeit, end_zeit, pause_in_stunden, arbeitsstunden, ueberstunden, entschuldigt, bestaetigt, kommentar FROM anwesenheiten WHERE mitarbeiter_id = %s AND start_zeit BETWEEN %s AND %s"
        cursor.execute(query, (mitarbeiter_id, f"{start_date} 00:00:00", f"{end_date} 23:59:59"))
        results = cursor.fetchall()

        if not results:
            messagebox.showinfo("Info", "Keine Einträge für diesen Zeitraum und Mitarbeiter gefunden.")

        urlaubstage_genutzt = 0
        kranktage = 0
        arbeitsstunden = 0
        pausen = 0
        ueberstunden = 0

        for row in results:
            start = datetime.strptime(str(row[2]), "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S") if row[3] else start
            days = (end - start).days + 1

            if row[1] == "Urlaub" and row[8]:  # Nur bestätigte Urlaubstage zählen
                urlaubstage_genutzt += days
            elif row[1] == "Krank" and row[7]:
                kranktage += days
            elif row[1] == "Arbeit":
                arbeitsstunden += row[5] or 0
                pausen += row[4] or 0
                ueberstunden += row[6] or 0

        restliche_urlaubstage = total_urlaubstage - urlaubstage_genutzt

        self.urlaubstage_label.config(text=str(urlaubstage_genutzt))
        self.restliche_urlaubstage_label.config(text=str(restliche_urlaubstage))
        self.kranktage_label.config(text=str(kranktage))
        self.arbeitsstunden_label.config(text=f"{arbeitsstunden:.2f}")
        self.pausen_label.config(text=f"{pausen:.2f}")
        self.ueberstunden_label.config(text=f"{ueberstunden:.2f}")

        for item in tree.get_children():
            tree.delete(item)
        for row in results:
            entschuldigt = "Ja" if row[7] else "Nein" if row[7] is not None else ""
            bestaetigt = "Ja" if row[8] else "Nein"
            kommentar = row[9] if row[9] is not None else ""
            formatted_row = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], entschuldigt, bestaetigt, kommentar, restliche_urlaubstage)
            tree.insert("", tk.END, values=formatted_row)

        cursor.close()
        conn.close()
    # Export von Daten als *.xslx
    def export_to_xlsx(self, tree):
        # Daten aus der Treeview holen
        data = []
        columns = ["Eintrag ID", "Typ", "Startzeit", "Endzeit", "Pause (hh:mm)", "Arbeitsstunden (hh:mm)", "Überstunden (hh:mm)", "Entschuldigt", "Bestätigt", "Kommentar", "Restliche Urlaubstage"]
        for item in tree.get_children():
            data.append(tree.item(item, 'values'))

        # Pandas DataFrame erstellen
        df = pd.DataFrame(data, columns=columns)

        # Datei speichern mit filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel-Dateien", "*.xlsx"), ("Alle Dateien", "*.*")],
            title="Speichere die Excel-Datei"
        )
        
        if file_path:
            try:
                # DataFrame in Excel schreiben
                with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name="Anwesenheiten", index=False)
                messagebox.showinfo("Erfolg", f"Daten wurden erfolgreich nach {file_path} exportiert")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren: {str(e)}")
    # Krankmeldung hinzufügen
    def add_krankmeldung(self, mitarbeiter_combo):
        mitarbeiter = mitarbeiter_combo.get()
        if not mitarbeiter:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus")
            return
        mitarbeiter_id = mitarbeiter.split(" - ")[0]

        krank_window = tk.Toplevel(self.window)
        krank_window.title("Krankmeldung hinzufügen")
        krank_window.geometry("300x280")

        krank_frame = ttk.Frame(krank_window, padding="10")
        krank_frame.pack(fill="both", expand=True)

        ttk.Label(krank_frame, text="Startdatum:").grid(row=0, column=0, pady=5, sticky="w")
        start_datum = DateEntry(krank_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        start_datum.grid(row=0, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(krank_frame, text="Startzeit (HH:MM):").grid(row=1, column=0, pady=5, sticky="w")
        start_stunde = ttk.Spinbox(krank_frame, from_=0, to=23, width=5, format="%02.0f")
        start_stunde.grid(row=1, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(krank_frame, text=":").grid(row=1, column=1, pady=5, padx=(65, 0), sticky="w")
        start_minute = ttk.Spinbox(krank_frame, from_=0, to=59, width=5, format="%02.0f")
        start_minute.grid(row=1, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(krank_frame, text="Enddatum:").grid(row=2, column=0, pady=5, sticky="w")
        end_datum = DateEntry(krank_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        end_datum.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(krank_frame, text="Endzeit (HH:MM):").grid(row=3, column=0, pady=5, sticky="w")
        end_stunde = ttk.Spinbox(krank_frame, from_=0, to=23, width=5, format="%02.0f")
        end_stunde.grid(row=3, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(krank_frame, text=":").grid(row=3, column=1, pady=5, padx=(65, 0), sticky="w")
        end_minute = ttk.Spinbox(krank_frame, from_=0, to=59, width=5, format="%02.0f")
        end_minute.grid(row=3, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(krank_frame, text="Entschuldigt:").grid(row=4, column=0, pady=5, sticky="w")
        entschuldigt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(krank_frame, variable=entschuldigt_var).grid(row=4, column=1, pady=5, sticky="w")

        ttk.Label(krank_frame, text="Kommentar:").grid(row=5, column=0, pady=5, sticky="w")
        kommentar_entry = ttk.Entry(krank_frame)
        kommentar_entry.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        # Krankmeldung speichern
        def save_krankmeldung():
            start_date = start_datum.get()
            start_time = f"{start_stunde.get()}:{start_minute.get()}:00"
            end_date = end_datum.get()
            end_time = f"{end_stunde.get()}:{end_minute.get()}:00"
            start = f"{start_date} {start_time}"
            end = f"{end_date} {end_time}"
            entschuldigt = entschuldigt_var.get()
            kommentar = kommentar_entry.get() or None

            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            sql_insert = "INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit, end_zeit, pause_in_stunden, arbeitsstunden, ueberstunden, entschuldigt, kommentar) VALUES (%s, 'Krank', %s, %s, NULL, NULL, NULL, %s, %s)"
            values = (mitarbeiter_id, start, end, entschuldigt, kommentar)

            try:
                cursor.execute(sql_insert, values)
                conn.commit()
                messagebox.showinfo("Erfolg", f"Krankmeldung für Mitarbeiter {mitarbeiter_id} hinzugefügt")
                krank_window.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()

        ttk.Button(krank_frame, text="Speichern ✅", command=save_krankmeldung).grid(row=6, column=0, columnspan=2, pady=15, sticky="ew")
    # Urlaub hinzufügen
    def add_urlaub(self, mitarbeiter_combo):
        mitarbeiter = mitarbeiter_combo.get()
        if not mitarbeiter:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus")
            return
        mitarbeiter_id = mitarbeiter.split(" - ")[0]

        urlaub_window = tk.Toplevel(self.window)
        urlaub_window.title("Urlaub hinzufügen")
        urlaub_window.geometry("300x280")

        urlaub_frame = ttk.Frame(urlaub_window, padding="10")
        urlaub_frame.pack(fill="both", expand=True)

        ttk.Label(urlaub_frame, text="Startdatum:").grid(row=0, column=0, pady=5, sticky="w")
        start_datum = DateEntry(urlaub_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        start_datum.grid(row=0, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(urlaub_frame, text="Startzeit (HH:MM):").grid(row=1, column=0, pady=5, sticky="w")
        start_stunde = ttk.Spinbox(urlaub_frame, from_=0, to=23, width=5, format="%02.0f")
        start_stunde.grid(row=1, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(urlaub_frame, text=":").grid(row=1, column=1, pady=5, padx=(65, 0), sticky="w")
        start_minute = ttk.Spinbox(urlaub_frame, from_=0, to=59, width=5, format="%02.0f")
        start_minute.grid(row=1, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(urlaub_frame, text="Enddatum:").grid(row=2, column=0, pady=5, sticky="w")
        end_datum = DateEntry(urlaub_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        end_datum.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(urlaub_frame, text="Endzeit (HH:MM):").grid(row=3, column=0, pady=5, sticky="w")
        end_stunde = ttk.Spinbox(urlaub_frame, from_=0, to=23, width=5, format="%02.0f")
        end_stunde.grid(row=3, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(urlaub_frame, text=":").grid(row=3, column=1, pady=5, padx=(65, 0), sticky="w")
        end_minute = ttk.Spinbox(urlaub_frame, from_=0, to=59, width=5, format="%02.0f")
        end_minute.grid(row=3, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(urlaub_frame, text="Genehmigt:").grid(row=4, column=0, pady=5, sticky="w")
        bestaetigt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(urlaub_frame, variable=bestaetigt_var).grid(row=4, column=1, pady=5, sticky="w")

        ttk.Label(urlaub_frame, text="Kommentar:").grid(row=5, column=0, pady=5, sticky="w")
        kommentar_entry = ttk.Entry(urlaub_frame)
        kommentar_entry.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        # Urlaub speichern
        def save_urlaub():
            start_date = start_datum.get()
            start_time = f"{start_stunde.get()}:{start_minute.get()}:00"
            end_date = end_datum.get()
            end_time = f"{end_stunde.get()}:{end_minute.get()}:00"
            start = f"{start_date} {start_time}"
            end = f"{end_date} {end_time}"
            bestaetigt = bestaetigt_var.get()
            kommentar = kommentar_entry.get() or None

            start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            urlaubstage_beantragt = (end_dt - start_dt).days + 1

            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            cursor.execute("SELECT urlaubstage FROM mitarbeiter WHERE mitarbeiter_id = %s", (mitarbeiter_id,))
            total_urlaubstage = cursor.fetchone()[0] or 0
            cursor.execute("SELECT SUM(DATEDIFF(end_zeit, start_zeit) + 1) FROM anwesenheiten WHERE mitarbeiter_id = %s AND typ = 'Urlaub' AND bestaetigt = 1", (mitarbeiter_id,))
            urlaubstage_genutzt = cursor.fetchone()[0] or 0
            restliche_urlaubstage = total_urlaubstage - urlaubstage_genutzt
            # Prüft ob der Mitarbeiter noch genug Urlaubstage hat
            if urlaubstage_beantragt > restliche_urlaubstage:
                messagebox.showwarning("Fehler", f"Nicht genügend Urlaubstage verfügbar. Verbleibend: {restliche_urlaubstage} Tage")
                cursor.close()
                conn.close()
                return

            sql_insert = "INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit, end_zeit, pause_in_stunden, arbeitsstunden, ueberstunden, bestaetigt, kommentar) VALUES (%s, 'Urlaub', %s, %s, NULL, NULL, NULL, %s, %s)"
            values = (mitarbeiter_id, start, end, bestaetigt, kommentar)

            try:
                cursor.execute(sql_insert, values)
                if bestaetigt:
                    new_urlaubstage = restliche_urlaubstage - urlaubstage_beantragt
                    cursor.execute("UPDATE mitarbeiter SET urlaubstage = %s WHERE mitarbeiter_id = %s", (new_urlaubstage, mitarbeiter_id))
                conn.commit()
                messagebox.showinfo("Erfolg", f"Urlaub für Mitarbeiter {mitarbeiter_id} hinzugefügt")
                urlaub_window.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()

        ttk.Button(urlaub_frame, text="Speichern ✅", command=save_urlaub).grid(row=6, column=0, columnspan=2, pady=15, sticky="ew")
    # Anwesenheit manuell hinzufügen
    def add_anwesenheit(self, mitarbeiter_combo):
        mitarbeiter = mitarbeiter_combo.get()
        if not mitarbeiter:
            messagebox.showwarning("Fehler", "Bitte wähle einen Mitarbeiter aus")
            return
        mitarbeiter_id = mitarbeiter.split(" - ")[0]

        anwesenheit_window = tk.Toplevel(self.window)
        anwesenheit_window.title("Anwesenheit manuell hinzufügen")
        anwesenheit_window.geometry("310x280")

        anwesenheit_frame = ttk.Frame(anwesenheit_window, padding="10")
        anwesenheit_frame.pack(fill="both", expand=True)

        ttk.Label(anwesenheit_frame, text="Startdatum:").grid(row=0, column=0, pady=5, sticky="w")
        start_datum = DateEntry(anwesenheit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        start_datum.grid(row=0, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(anwesenheit_frame, text="Startzeit (HH:MM):").grid(row=1, column=0, pady=5, sticky="w")
        start_stunde = ttk.Spinbox(anwesenheit_frame, from_=0, to=23, width=5, format="%02.0f")
        start_stunde.grid(row=1, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(anwesenheit_frame, text=":").grid(row=1, column=1, pady=5, padx=(65, 0), sticky="w")
        start_minute = ttk.Spinbox(anwesenheit_frame, from_=0, to=59, width=5, format="%02.0f")
        start_minute.grid(row=1, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(anwesenheit_frame, text="Enddatum:").grid(row=2, column=0, pady=5, sticky="w")
        end_datum = DateEntry(anwesenheit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        end_datum.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(anwesenheit_frame, text="Endzeit (HH:MM):").grid(row=3, column=0, pady=5, sticky="w")
        end_stunde = ttk.Spinbox(anwesenheit_frame, from_=0, to=23, width=5, format="%02.0f")
        end_stunde.grid(row=3, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(anwesenheit_frame, text=":").grid(row=3, column=1, pady=5, padx=(65, 0), sticky="w")
        end_minute = ttk.Spinbox(anwesenheit_frame, from_=0, to=59, width=5, format="%02.0f")
        end_minute.grid(row=3, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(anwesenheit_frame, text="Pausen (in Stunden):").grid(row=4, column=0, pady=5, sticky="w")
        pause_entry = ttk.Entry(anwesenheit_frame)
        pause_entry.insert(0, "1.00")
        pause_entry.grid(row=4, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(anwesenheit_frame, text="Kommentar:").grid(row=5, column=0, pady=5, sticky="w")
        kommentar_entry = ttk.Entry(anwesenheit_frame)
        kommentar_entry.grid(row=5, column=1, pady=5, padx=5, sticky="ew")
        # Anwesenheit speichern
        def save_anwesenheit():
            start_date = start_datum.get()
            start_time = f"{start_stunde.get()}:{start_minute.get()}:00"
            end_date = end_datum.get()
            end_time = f"{end_stunde.get()}:{end_minute.get()}:00"
            start = f"{start_date} {start_time}"
            end = f"{end_date} {end_time}"
            pause = float(pause_entry.get())
            kommentar = kommentar_entry.get() or None

            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            sql_insert = "INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit, end_zeit, pause_in_stunden, kommentar) VALUES (%s, 'Arbeit', %s, %s, %s, %s)"
            values = (mitarbeiter_id, start, end, pause, kommentar)

            try:
                cursor.execute(sql_insert, values)
                conn.commit()
                messagebox.showinfo("Erfolg", f"Anwesenheit für Mitarbeiter {mitarbeiter_id} hinzugefügt")
                anwesenheit_window.destroy()
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()

        ttk.Button(anwesenheit_frame, text="Speichern ✅", command=save_anwesenheit).grid(row=6, column=0, columnspan=2, pady=15, sticky="ew")
    # Ein Eintrag bearbeiten
    def edit_eintrag(self, tree, mitarbeiter_combo, von_datum, bis_datum):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Fehler", "Bitte wähle einen Eintrag zum Bearbeiten aus")
            return
        
        item_values = tree.item(selected_item[0], "values")
        eintrag_id = item_values[0]
        typ = item_values[1]
        start_zeit = datetime.strptime(item_values[2], "%Y-%m-%d %H:%M:%S")
        end_zeit = None
        if item_values[3] and item_values[3] != "None" and item_values[3].strip():
            end_zeit = datetime.strptime(item_values[3], "%Y-%m-%d %H:%M:%S")
        pause = float(item_values[4]) if item_values[4] and item_values[4] != "None" else 0
        entschuldigt = item_values[7] == "Ja"
        bestaetigt = item_values[8] == "Ja"
        kommentar = item_values[9] if item_values[9] != "None" else ""

        edit_window = tk.Toplevel(self.window)
        edit_window.title("Datensatz bearbeiten")
        edit_window.geometry("300x280")

        edit_frame = ttk.Frame(edit_window, padding="10")
        edit_frame.pack(fill="both", expand=True)

        ttk.Label(edit_frame, text="Startdatum:").grid(row=0, column=0, pady=5, sticky="w")
        start_datum = DateEntry(edit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        start_datum.set_date(start_zeit.date())
        start_datum.grid(row=0, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(edit_frame, text="Startzeit (HH:MM):").grid(row=1, column=0, pady=5, sticky="w")
        start_stunde = ttk.Spinbox(edit_frame, from_=0, to=23, width=5, format="%02.0f")
        start_stunde.set(start_zeit.hour)
        start_stunde.grid(row=1, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(edit_frame, text=":").grid(row=1, column=1, pady=5, padx=(65, 0), sticky="w")
        start_minute = ttk.Spinbox(edit_frame, from_=0, to=59, width=5, format="%02.0f")
        start_minute.set(start_zeit.minute)
        start_minute.grid(row=1, column=1, pady=5, padx=(80, 0), sticky="w")

        ttk.Label(edit_frame, text="Enddatum:").grid(row=2, column=0, pady=5, sticky="w")
        end_datum = DateEntry(edit_frame, date_pattern="yyyy-mm-dd", width=12, background="darkblue", foreground="white", borderwidth=2)
        end_datum.set_date(end_zeit.date() if end_zeit else start_zeit.date())
        end_datum.grid(row=2, column=1, pady=5, padx=5, sticky="ew")

        ttk.Label(edit_frame, text="Endzeit (HH:MM):").grid(row=3, column=0, pady=5, sticky="w")
        end_stunde = ttk.Spinbox(edit_frame, from_=0, to=23, width=5, format="%02.0f")
        end_stunde.set(end_zeit.hour if end_zeit else 0)
        end_stunde.grid(row=3, column=1, pady=5, padx=5, sticky="w")
        ttk.Label(edit_frame, text=":").grid(row=3, column=1, pady=5, padx=(65, 0), sticky="w")
        end_minute = ttk.Spinbox(edit_frame, from_=0, to=59, width=5, format="%02.0f")
        end_minute.set(end_zeit.minute if end_zeit else 0)
        end_minute.grid(row=3, column=1, pady=5, padx=(80, 0), sticky="w")

        row_idx = 4
        if typ == "Arbeit":
            ttk.Label(edit_frame, text="Pausen (in Stunden):").grid(row=row_idx, column=0, pady=5, sticky="w")
            pause_entry = ttk.Entry(edit_frame)
            pause_entry.insert(0, f"{pause:.2f}")
            pause_entry.grid(row=row_idx, column=1, pady=5, padx=5, sticky="ew")
            row_idx += 1

        if typ == "Krank":
            ttk.Label(edit_frame, text="Entschuldigt:").grid(row=row_idx, column=0, pady=5, sticky="w")
            entschuldigt_var = tk.BooleanVar(value=entschuldigt)
            ttk.Checkbutton(edit_frame, variable=entschuldigt_var).grid(row=row_idx, column=1, pady=5, sticky="w")
            row_idx += 1

        if typ == "Urlaub":
            ttk.Label(edit_frame, text="Genehmigt:").grid(row=row_idx, column=0, pady=5, sticky="w")
            bestaetigt_var = tk.BooleanVar(value=bestaetigt)
            ttk.Checkbutton(edit_frame, variable=bestaetigt_var).grid(row=row_idx, column=1, pady=5, sticky="w")
            row_idx += 1

        ttk.Label(edit_frame, text="Kommentar:").grid(row=row_idx, column=0, pady=5, sticky="w")
        kommentar_entry = ttk.Entry(edit_frame)
        kommentar_entry.insert(0, kommentar)
        kommentar_entry.grid(row=row_idx, column=1, pady=5, padx=5, sticky="ew")
        row_idx += 1
        # Änderungen speichern
        def save_edit():
            start_date = start_datum.get()
            start_time = f"{start_stunde.get()}:{start_minute.get()}:00"
            end_date = end_datum.get()
            end_time = f"{end_stunde.get()}:{end_minute.get()}:00"
            start = f"{start_date} {start_time}"
            end = f"{end_date} {end_time}"

            conn = connect_db()
            if conn is None:
                return
            cursor = conn.cursor()

            if typ == "Arbeit":
                pause = float(pause_entry.get())
                sql_update = "UPDATE anwesenheiten SET start_zeit = %s, end_zeit = %s, pause_in_stunden = %s, kommentar = %s WHERE eintrag_id = %s"
                values = (start, end, pause, kommentar_entry.get() or None, eintrag_id)
            elif typ == "Krank":
                sql_update = "UPDATE anwesenheiten SET start_zeit = %s, end_zeit = %s, arbeitsstunden = NULL, ueberstunden = NULL, entschuldigt = %s, kommentar = %s WHERE eintrag_id = %s"
                values = (start, end, entschuldigt_var.get(), kommentar_entry.get() or None, eintrag_id)
            elif typ == "Urlaub":
                sql_update = "UPDATE anwesenheiten SET start_zeit = %s, end_zeit = %s, arbeitsstunden = NULL, ueberstunden = NULL, bestaetigt = %s, kommentar = %s WHERE eintrag_id = %s"
                values = (start, end, bestaetigt_var.get(), kommentar_entry.get() or None, eintrag_id)

            try:
                cursor.execute(sql_update, values)
                conn.commit()
                messagebox.showinfo("Erfolg", f"Eintrag {eintrag_id} erfolgreich bearbeitet")
                edit_window.destroy()
                self.search_zeiterfassung(von_datum, bis_datum, mitarbeiter_combo, tree)
            except Exception as e:
                messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
            finally:
                cursor.close()
                conn.close()

        ttk.Button(edit_frame, text="Speichern ✅", command=save_edit).grid(row=row_idx, column=0, columnspan=2, pady=15, sticky="ew")
    # Ein Eintrag löschen
    def delete_eintrag(self, tree, mitarbeiter_combo, von_datum, bis_datum):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Fehler", "Bitte wähle einen Eintrag zum Löschen aus")
            return
        
        item_values = tree.item(selected_item[0], "values")
        eintrag_id = item_values[0]
        typ = item_values[1]
        start_zeit = item_values[2]

        if not messagebox.askyesno("Bestätigung", f"Möchtest du den Eintrag '{typ}' vom {start_zeit} wirklich löschen?"):
            return

        conn = connect_db()
        if conn is None:
            messagebox.showerror("Fehler", "Datenbankverbindung fehlgeschlagen")
            return
        cursor = conn.cursor()

        sql_delete = "DELETE FROM anwesenheiten WHERE eintrag_id = %s"
        try:
            cursor.execute(sql_delete, (eintrag_id,))
            conn.commit()
            messagebox.showinfo("Erfolg", f"Eintrag {eintrag_id} erfolgreich gelöscht")
            self.search_zeiterfassung(von_datum, bis_datum, mitarbeiter_combo, tree)
        except Exception as e:
            messagebox.showerror("Fehler", f"Datenbankfehler: {str(e)}")
        finally:
            cursor.close()
            conn.close()