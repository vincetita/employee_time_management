-- Erstellung von Datenbank und Tabellen
CREATE DATABASE IF NOT EXISTS mitarbeiter_verwaltung;
USE mitarbeiter_verwaltung;

-- Mitarbeitertabelle
CREATE TABLE IF NOT EXISTS mitarbeiter (
    mitarbeiter_id INT PRIMARY KEY AUTO_INCREMENT,
    abteilung ENUM('Geschäftsführung', 'Kundensupport & Office-Management', 'Marketing', 'Technik', 'Vertrieb', 'Verwaltung') NOT NULL,
    position ENUM(
        'Geschäftsführung', 'Kundenservice', 'Kundenservice-Leitung', 'Office-Management',
        'Marketing-Management', 'Online-Marketing-Spezialist', 'Social-Media-Management',
        'Datenbankadministration', 'IT-Infrastrukturleitung', 'IT-Projektmanagement',
        'IT-Support', 'IT-Support-Leitung', 'IT-Support-Spezialist', 'Netzwerkadministration',
        'Senior IT-Beratung', 'Systemadministration', 'Key-Account-Management',
        'Vertriebsaußendienst', 'Vertriebsinnendienst', 'Vertriebsleitung',
        'Vertriebsunterstützung', 'Controlling & Finanzanalyse', 'Gehaltsbuchhaltung',
        'HR- & Finanzleitung', 'Personalreferenz'
    ) NOT NULL,
    vorname VARCHAR(50) NOT NULL,
    nachname VARCHAR(50) NOT NULL,
    strasse TEXT,
    hausnummer VARCHAR(10) NOT NULL,
    plz VARCHAR(10) NOT NULL,
    stadt VARCHAR(50) NOT NULL,
    telefon VARCHAR(20),
    email VARCHAR(50) UNIQUE NOT NULL,
    geburtsdatum DATE,
    vertrag_beginn DATE NOT NULL,
    vertrag_ende DATE DEFAULT NULL,
    vertrag_typ ENUM('befristet', 'unbefristet') NOT NULL DEFAULT 'unbefristet',
    arbeitszeit ENUM('Vollzeit', 'Teilzeit') NOT NULL DEFAULT 'Vollzeit',
    urlaubstage INT DEFAULT 0,
    gehalt DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('aktiv', 'inaktiv') NOT NULL DEFAULT 'inaktiv'
);

-- Tabelle für Logindaten
CREATE TABLE IF NOT EXISTS benutzer (
    benutzer_id INT AUTO_INCREMENT PRIMARY KEY,
    mitarbeiter_id INT NOT NULL UNIQUE,
    username VARCHAR(30) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    passwort_typ ENUM('generiert', 'festgelegt', 'abgelaufen') DEFAULT 'festgelegt',
    rolle ENUM('Admin', 'HR', 'Mitarbeiter') NOT NULL DEFAULT 'Mitarbeiter',
    FOREIGN KEY (mitarbeiter_id) REFERENCES mitarbeiter(mitarbeiter_id) ON DELETE CASCADE
);

-- Tabelle für An- und Abwesenheiten
CREATE TABLE anwesenheiten (
    eintrag_id INT AUTO_INCREMENT PRIMARY KEY,
    mitarbeiter_id INT NOT NULL,
    typ ENUM('Arbeit', 'Urlaub', 'Krank') NOT NULL,
    start_zeit DATETIME,
    end_zeit DATETIME,
    pause_in_stunden DECIMAL(3,2) DEFAULT NULL,
    arbeitsstunden DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN typ = 'Arbeit' THEN IFNULL(TIMESTAMPDIFF(SECOND, start_zeit, end_zeit) / 3600 - COALESCE(pause_in_stunden, 0), 0)
             ELSE 0 END
    ) STORED,
    ueberstunden DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE WHEN typ = 'Arbeit' AND arbeitsstunden > 8 
             THEN GREATEST(arbeitsstunden - 8 - GREATEST(pause_in_stunden - 1, 0), 0)
             ELSE 0 END
    ) STORED,
    entschuldigt BOOLEAN,
    bestaetigt BOOLEAN DEFAULT FALSE,
    kommentar VARCHAR(255),
    FOREIGN KEY (mitarbeiter_id) REFERENCES mitarbeiter(mitarbeiter_id) ON DELETE CASCADE
);

-- Tabelle für Export-Protokolle
CREATE TABLE IF NOT EXISTS export_protokoll (
    export_id INT AUTO_INCREMENT PRIMARY KEY,
    export_typ ENUM('täglich', 'woechentlich', 'monatlich'),
    filter_von DATE DEFAULT NULL,
    filter_bis DATE DEFAULT NULL,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    erstellt_von INT,
    FOREIGN KEY (erstellt_von) REFERENCES mitarbeiter(mitarbeiter_id)
);