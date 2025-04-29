import random
from datetime import datetime, timedelta

# Parameter
start_date = datetime(2025, 3, 1)
end_date = datetime(2025, 4, 15)
num_mitarbeiter = 34
vollzeit_stunden = 8
teilzeit_stunden = 4
teilzeit_mitarbeiter = {16, 24, 30, 34}  # Teilzeit-Mitarbeiter-IDs

# Funktion zur Generierung eines zufälligen Datums
def random_date(start, end):
    delta = end - start
    random_days = random.randrange(delta.days + 1)
    return start + timedelta(days=random_days)

# Funktion zur Generierung von Start- und Endzeiten
def generate_work_times(date, hours):
    start_hour = random.randint(7, 9)  # Start zwischen 7:00 und 9:00
    start_time = datetime(date.year, date.month, date.day, start_hour, 0)
    end_time = start_time + timedelta(hours=hours)
    return start_time, end_time

# Funktion zur Generierung von Urlaub über mehrere Tage
def generate_multi_day_vacation(start_date, mitarbeiter_id, sql_statements):
    duration = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]  # 1, 2 oder 3 Tage
    for i in range(duration):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() < 5 and current_date <= end_date:  # Nur Arbeitstage
            start_zeit = datetime(current_date.year, current_date.month, current_date.day, 8, 0)
            end_zeit = start_zeit + timedelta(hours=vollzeit_stunden if mitarbeiter_id not in teilzeit_mitarbeiter else teilzeit_stunden)
            sql = f"""
            INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit, end_zeit, pause_in_stunden, entschuldigt, bestaetigt, kommentar)
            VALUES ({mitarbeiter_id}, 'Urlaub', '{start_zeit.strftime('%Y-%m-%d %H:%M:%S')}', 
                    '{end_zeit.strftime('%Y-%m-%d %H:%M:%S')}', {1.00 if mitarbeiter_id not in teilzeit_mitarbeiter else 0.75}, TRUE, TRUE, 'Urlaub ganzer Tag');
            """
            sql_statements.append(sql.strip())

# SQL-Insert-Statements generieren
sql_statements = []
current_date = start_date
mitarbeiter_vacation = {i: False for i in range(1, num_mitarbeiter + 1)}  # Verfolgt, ob Mitarbeiter im Urlaub ist

while current_date <= end_date:
    if current_date.weekday() < 5:  # Nur Arbeitstage (Montag bis Freitag)
        for mitarbeiter_id in range(1, num_mitarbeiter + 1):
            # Prüfen, ob Mitarbeiter bereits in einem mehrtägigen Urlaub ist
            if mitarbeiter_vacation[mitarbeiter_id]:
                continue  # Überspringen, wenn im Urlaub

            # Typauswahl mit realistischer Verteilung
            typ = random.choices(['Arbeit', 'Urlaub', 'Krank'], weights=[80, 10, 10], k=1)[0]
            
            if typ == 'Arbeit':
                # Teilzeit oder Vollzeit
                if mitarbeiter_id in teilzeit_mitarbeiter:
                    stunden = teilzeit_stunden
                else:
                    # Überstunden in 20% der Fälle für Vollzeit
                    if random.random() < 0.2:
                        stunden = vollzeit_stunden + random.uniform(0.5, 2)
                    else:
                        stunden = vollzeit_stunden
                start_zeit, end_zeit = generate_work_times(current_date, stunden)
                pause = round(random.uniform(0.75, 1.00), 2) if mitarbeiter_id not in teilzeit_mitarbeiter else 0.75
                entschuldigt = 'NULL'
                kommentar = random.choices([None, f"'Überstunden abgerechnet'"], weights=[80, 20], k=1)[0]

            elif typ == 'Urlaub':
                # Urlaub: Einzelner Tag (ganz oder halb) oder mehrtägig
                urlaub_typ = random.choices(['ganz', 'halb', 'mehrere'], weights=[50, 30, 20], k=1)[0]
                if urlaub_typ == 'mehrere':
                    generate_multi_day_vacation(current_date, mitarbeiter_id, sql_statements)
                    mitarbeiter_vacation[mitarbeiter_id] = True  # Markiert als im Urlaub
                    continue  # Nächster Mitarbeiter
                elif urlaub_typ == 'ganz':
                    stunden = vollzeit_stunden if mitarbeiter_id not in teilzeit_mitarbeiter else teilzeit_stunden
                    kommentar = "'Urlaub ganzer Tag'"
                else:  # halb
                    stunden = teilzeit_stunden  # Halber Tag ist immer 4 Stunden
                    kommentar = "'Urlaub halber Tag'"
                start_zeit, end_zeit = generate_work_times(current_date, stunden)
                pause = 1.00 if stunden == vollzeit_stunden else 0.75
                entschuldigt = 'TRUE'
                bestaetigt = 'TRUE'  # Urlaub immer bestätigt

            elif typ == 'Krank':
                # Krank: Ganzer oder halber Tag
                krank_typ = random.choices(['ganz', 'halb'], weights=[70, 30], k=1)[0]
                stunden = vollzeit_stunden if krank_typ == 'ganz' and mitarbeiter_id not in teilzeit_mitarbeiter else teilzeit_stunden
                start_zeit, end_zeit = generate_work_times(current_date, stunden)
                pause = 1.00 if stunden == vollzeit_stunden else 0.75
                entschuldigt = random.choice(['TRUE', 'FALSE'])
                kommentar = f"'Krankmeldung {'ganzer Tag' if krank_typ == 'ganz' else 'halber Tag'}'"

            # Für Arbeit und Krank: Bestätigung zufällig, für Urlaub immer TRUE
            if typ != 'Urlaub':
                bestaetigt = random.choices([True, False], weights=[90, 10], k=1)[0]
            else:
                bestaetigt = True

            kommentar_sql = kommentar if kommentar else 'NULL'

            sql = f"""
            INSERT INTO anwesenheiten (mitarbeiter_id, typ, start_zeit, end_zeit, pause_in_stunden, entschuldigt, bestaetigt, kommentar)
            VALUES ({mitarbeiter_id}, '{typ}', '{start_zeit.strftime('%Y-%m-%d %H:%M:%S')}', 
                    '{end_zeit.strftime('%Y-%m-%d %H:%M:%S')}', {pause}, {entschuldigt}, {str(bestaetigt).upper()}, {kommentar_sql});
            """
            sql_statements.append(sql.strip())

    # Reset für mehrtägigen Urlaub nach jedem Tag
    for mitarbeiter_id in range(1, num_mitarbeiter + 1):
        if mitarbeiter_vacation[mitarbeiter_id]:
            if random.random() < 0.33:  # 33% Chance, dass Urlaub endet
                mitarbeiter_vacation[mitarbeiter_id] = False

    current_date += timedelta(days=1)

# SQL-Datei schreiben
with open("anwesenheiten_musterdaten.sql", "w", encoding="utf-8") as f:
    f.write("SET FOREIGN_KEY_CHECKS=0;\n")
    f.write("TRUNCATE TABLE anwesenheiten;\n")
    for stmt in sql_statements:
        f.write(stmt + "\n")
    f.write("SET FOREIGN_KEY_CHECKS=1;\n")

print(f"Generated {len(sql_statements)} INSERT statements.")