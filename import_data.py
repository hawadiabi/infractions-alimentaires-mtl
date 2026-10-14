"""
Module d'importation des données de contraventions alimentaires de Montréal.
Télécharge le fichier CSV, détecte les nouvelles contraventions et
envoie un courriel automatique si de nouvelles infractions sont détectées.
"""
import csv
import os
import smtplib
import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests
import yaml

URL = (
    "https://donnees.montreal.ca/dataset/05a9e718-6810-4e73-8bb9-5955efeb91a0"
    "/resource/7f939a08-be8a-45e1-b208-d8744dca8fc6/download/violations.csv"
)
# Le site de la Ville refuse (erreur 403) l'en-tête par défaut de requests.
EN_TETES = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*",
}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "violations.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "db", "db.sql")
CONFIG_PATH = os.path.join(BASE_DIR, "config.yaml")

COLONNES = [
    "id_poursuite", "business_id", "date", "description", "adresse",
    "date_jugement", "etablissement", "montant", "proprietaire", "ville",
    "statut", "date_statut", "categorie",
]


def download_csv():
    """Télécharge le fichier CSV depuis la ville de Montréal."""
    response = requests.get(URL, headers=EN_TETES, timeout=60)
    response.raise_for_status()
    # utf-8-sig retire le BOM éventuel au début du fichier,
    # sinon la première colonne s'appelle "﻿id_poursuite".
    return response.content.decode("utf-8-sig")


def creer_tables(conn):
    """Crée les tables si elles n'existent pas encore."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def get_ids_existants(conn):
    """Retourne les ids des contraventions déjà dans la base de données."""
    cursor = conn.cursor()
    cursor.execute("SELECT id_poursuite FROM contrevenants")
    return set(row[0] for row in cursor.fetchall())


def lire_lignes(csv_text):
    """Lit le CSV et garde seulement les lignes avec un id valide."""
    reader = csv.DictReader(csv_text.splitlines())
    reader.fieldnames = [
        nom.strip().lstrip("﻿").lower()
        for nom in reader.fieldnames or []
    ]
    manquantes = [c for c in COLONNES if c not in reader.fieldnames]
    if manquantes:
        raise ValueError(f"Colonnes manquantes dans le CSV : {manquantes}")
    lignes = []
    for row in reader:
        try:
            row["id_poursuite"] = int(row["id_poursuite"])
        except (TypeError, ValueError):
            continue
        lignes.append(row)
    return lignes


def insert_data(csv_text):
    """Insère les nouvelles contraventions dans la base de données."""
    conn = sqlite3.connect(DB_PATH)
    creer_tables(conn)
    cursor = conn.cursor()

    ids_existants = get_ids_existants(conn)
    premiere_importation = len(ids_existants) == 0
    nouveaux = []

    for row in lire_lignes(csv_text):
        if row["id_poursuite"] in ids_existants:
            continue
        ids_existants.add(row["id_poursuite"])
        nouveaux.append(row)
        cursor.execute(
            "INSERT OR IGNORE INTO contrevenants VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            tuple(row[c] for c in COLONNES),
        )

    conn.commit()
    conn.close()
    print(f"Importation terminée ! {len(nouveaux)} nouvelle(s) "
          "contravention(s).")

    # À la première importation, toutes les lignes sont « nouvelles » :
    # on n'envoie pas un courriel de plusieurs milliers d'établissements.
    if nouveaux and not premiere_importation:
        try:
            envoyer_courriel(nouveaux)
        except (OSError, smtplib.SMTPException, KeyError) as e:
            # Un problème de courriel ne doit pas annuler l'importation.
            print(f"Courriel non envoyé : {e}")

    return nouveaux


def construire_corps_courriel(etablissements):
    """Construit le corps du courriel avec la liste des établissements."""
    corps = "Nouvelles contraventions détectées :\n\n"
    for nom in etablissements:
        corps += f"- {nom}\n"
    return corps


def lire_config():
    """Lit config.yaml. Le mot de passe peut venir d'une variable
    d'environnement pour ne pas être écrit dans le fichier."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    cfg = config["email"]
    mot_de_passe = os.environ.get("SMTP_MOT_DE_PASSE")
    if mot_de_passe:
        cfg["mot_de_passe"] = mot_de_passe
    return cfg


def envoyer_courriel(nouveaux):
    """Envoie un courriel avec les nouveaux établissements."""
    cfg = lire_config()
    etablissements = sorted(set(r["etablissement"] for r in nouveaux))
    corps = construire_corps_courriel(etablissements)

    msg = MIMEMultipart()
    msg["From"] = cfg["expediteur"]
    msg["To"] = cfg["destinataire"]
    msg["Subject"] = "Nouvelles contraventions - Montréal"
    msg.attach(MIMEText(corps, "plain", "utf-8"))

    with smtplib.SMTP(cfg["smtp_serveur"], cfg["smtp_port"],
                      timeout=30) as serveur:
        serveur.starttls()
        serveur.login(cfg["expediteur"], cfg["mot_de_passe"])
        serveur.send_message(msg)

    print("Courriel envoyé !")


if __name__ == "__main__":
    insert_data(download_csv())
