"""
Application Flask pour la gestion des contraventions alimentaires de Montréal.
Offre des services REST et des pages web pour consulter, rechercher et gérer
les infractions des établissements alimentaires.
"""
import json
import os
import secrets
import sqlite3
import unicodedata
from datetime import date

import bcrypt
import jsonschema
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, redirect, render_template, request
from flask import session, url_for
from werkzeug.exceptions import HTTPException

import import_data

app = Flask(__name__)
app.json.ensure_ascii = False  # affiche « ê » au lieu de « ê »
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))
DB_PATH = import_data.DB_PATH
MOT_DE_PASSE_MIN = 8


def sync_data():
    """Synchronise les données avec la base de données."""
    try:
        import_data.insert_data(import_data.download_csv())
        print("Synchronisation effectuée !")
    except Exception as e:  # le scheduler ne doit jamais s'arrêter
        print(f"Échec de la synchronisation : {e}")


def demarrer_scheduler():
    """Démarre la synchronisation quotidienne à minuit."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(sync_data, "cron", hour=0, minute=0)
    scheduler.start()


def get_db():
    """Retourne une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialiser_db():
    """Crée les tables si la base est vide."""
    conn = sqlite3.connect(DB_PATH)
    import_data.creer_tables(conn)
    conn.close()


@app.errorhandler(Exception)
def gerer_erreur(e):
    """Gère les erreurs non anticipées sans masquer les 404 et 405."""
    if isinstance(e, HTTPException):
        return jsonify({"erreur": e.description}), e.code
    app.logger.exception(e)
    return jsonify({"erreur": "Une erreur est survenue"}), 500


def sans_accent(texte):
    """Retire les accents d'un texte pour la recherche."""
    normalise = unicodedata.normalize("NFD", texte)
    return normalise.encode("ascii", "ignore").decode("utf-8")


def sans_accent_sql(texte):
    """Version de sans_accent utilisable dans une requête SQLite."""
    return sans_accent(texte) if texte else texte


def lire_json():
    """Retourne le corps JSON de la requête, ou None s'il est invalide."""
    return request.get_json(silent=True)


def erreur(message, code=400):
    """Construit une réponse d'erreur JSON."""
    return jsonify({"erreur": message}), code


@app.route("/", methods=["GET"])
def index():
    """Affiche la page d'accueil avec les formulaires de recherche."""
    return render_template("index.html")


COLONNES_RECHERCHE = {
    "etablissement": "etablissement",
    "proprietaire": "proprietaire",
    "rue": "adresse",
}


@app.route("/recherche", methods=["GET"])
def recherche():
    """Recherche les contraventions par établissement, propriétaire ou rue."""
    critere = request.args.get("critere", "")
    valeur = request.args.get("valeur", "").strip()
    colonne = COLONNES_RECHERCHE.get(critere)

    resultats = []
    if colonne and valeur:
        conn = get_db()
        # Les accents sont retirés des deux côtés : « marche » trouve
        # « MARCHÉ », et « marché » trouve « MARCHE ».
        conn.create_function("sans_accent", 1, sans_accent_sql,
                             deterministic=True)
        cursor = conn.execute(
            f"SELECT * FROM contrevenants "
            f"WHERE sans_accent({colonne}) LIKE ?",
            (f"%{sans_accent(valeur)}%",),
        )
        resultats = cursor.fetchall()
        conn.close()

    return render_template(
        "resultats.html", resultats=resultats, valeur=valeur
    )


def lire_date_iso(texte):
    """Convertit une date ISO 8601 (AAAA-MM-JJ) en date, sinon None."""
    try:
        return date.fromisoformat(texte)
    except (TypeError, ValueError):
        return None


@app.route("/contrevenants", methods=["GET"])
def contrevenants():
    """Retourne les contraventions entre deux dates en format JSON."""
    du_texte = request.args.get("du")
    au_texte = request.args.get("au")

    if not du_texte or not au_texte:
        return erreur("Les paramètres 'du' et 'au' sont obligatoires.")

    du = lire_date_iso(du_texte)
    au = lire_date_iso(au_texte)
    if du is None or au is None:
        return erreur("Les dates doivent être au format ISO 8601 "
                      "(AAAA-MM-JJ).")
    if du > au:
        return erreur("La date 'du' doit précéder la date 'au'.")

    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM contrevenants WHERE date >= ? AND date <= ? "
        "ORDER BY date",
        (du.strftime("%Y%m%d"), au.strftime("%Y%m%d")),
    )
    resultats = cursor.fetchall()
    conn.close()

    return jsonify([dict(r) for r in resultats])


@app.route("/etablissements", methods=["GET"])
def etablissements():
    """Retourne la liste de tous les établissements distincts."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT DISTINCT etablissement FROM contrevenants "
        "ORDER BY etablissement"
    )
    resultats = cursor.fetchall()
    conn.close()
    return jsonify([r["etablissement"] for r in resultats])


@app.route("/etablissement/<path:nom>", methods=["GET"])
def infractions_etablissement(nom):
    """Retourne toutes les infractions d'un établissement donné."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM contrevenants WHERE etablissement = ? "
        "ORDER BY date DESC",
        (nom,),
    )
    resultats = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in resultats])


@app.route("/doc", methods=["GET"])
def doc():
    """Affiche la documentation HTML de l'API REST."""
    return render_template("doc.html")


TEXTE_REQUIS = {"type": "string", "minLength": 1}

INSPECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "etablissement": TEXTE_REQUIS,
        "adresse": TEXTE_REQUIS,
        "ville": TEXTE_REQUIS,
        "date_visite": {"type": "string", "format": "date"},
        "nom_client": TEXTE_REQUIS,
        "prenom_client": TEXTE_REQUIS,
        "description": TEXTE_REQUIS,
    },
    "required": [
        "etablissement", "adresse", "ville",
        "date_visite", "nom_client", "prenom_client", "description"
    ],
    "additionalProperties": False
}

FORMAT_CHECKER = jsonschema.FormatChecker()


def valider(data, schema):
    """Valide data avec le schéma. Retourne un message d'erreur ou None."""
    if data is None:
        return "Le corps de la requête doit être du JSON valide."
    try:
        jsonschema.validate(data, schema, format_checker=FORMAT_CHECKER)
    except jsonschema.ValidationError as e:
        return e.message
    return None


def inserer_inspection(conn, data):
    """Insère une demande d'inspection dans la base de données."""
    conn.execute("""
        INSERT INTO inspections (
            etablissement, adresse, ville, date_visite,
            nom_client, prenom_client, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["etablissement"],
        data["adresse"],
        data["ville"],
        data["date_visite"],
        data["nom_client"],
        data["prenom_client"],
        data["description"]
    ))
    conn.commit()


@app.route("/inspections", methods=["POST"])
def creer_inspection():
    """Crée une nouvelle demande d'inspection après validation JSON Schema."""
    data = lire_json()
    message = valider(data, INSPECTION_SCHEMA)
    if message:
        return erreur(message)

    conn = get_db()
    inserer_inspection(conn, data)
    conn.close()

    return jsonify({"message": "Demande d'inspection créée !"}), 201


@app.route("/plainte", methods=["GET"])
def plainte():
    """Affiche le formulaire de plainte pour une demande d'inspection."""
    return render_template("plainte.html")


@app.route("/inspections/<int:id_inspection>", methods=["DELETE"])
def supprimer_inspection(id_inspection):
    """Supprime une demande d'inspection par son identifiant."""
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM inspections WHERE id = ?", (id_inspection,)
    )
    conn.commit()
    supprimees = cursor.rowcount
    conn.close()

    if supprimees == 0:
        return erreur("Inspection non trouvée", 404)
    return jsonify({"message": "Inspection supprimée !"}), 200


@app.route("/contrevenants/etablissements", methods=["GET"])
def liste_etablissements():
    """Retourne la liste des établissements triée par nombre d'infractions."""
    conn = get_db()
    cursor = conn.execute("""
        SELECT etablissement, COUNT(*) AS nombre_infractions
        FROM contrevenants
        GROUP BY etablissement
        ORDER BY nombre_infractions DESC, etablissement
    """)
    resultats = cursor.fetchall()
    conn.close()

    return jsonify([{
        "etablissement": r["etablissement"],
        "nombre_infractions": r["nombre_infractions"]
    } for r in resultats])


UTILISATEUR_SCHEMA = {
    "type": "object",
    "properties": {
        "nom_complet": TEXTE_REQUIS,
        "courriel": {
            "type": "string",
            "format": "email",
            "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            "maxLength": 254
        },
        "mot_de_passe": {
            "type": "string",
            "minLength": MOT_DE_PASSE_MIN,
            "maxLength": 72
        },
        "etablissements_surveilles": {
            "type": "array",
            "items": TEXTE_REQUIS
        }
    },
    "required": [
        "nom_complet", "courriel",
        "mot_de_passe", "etablissements_surveilles"
    ],
    "additionalProperties": False
}


def inserer_utilisateur(conn, data, mot_de_passe_hash, etablissements):
    """Insère un nouvel utilisateur dans la base de données."""
    conn.execute("""
        INSERT INTO utilisateurs (
            nom_complet, courriel,
            mot_de_passe, etablissements_surveilles
        ) VALUES (?, ?, ?, ?)
    """, (
        data["nom_complet"],
        data["courriel"].strip().lower(),
        mot_de_passe_hash,
        etablissements
    ))
    conn.commit()


@app.route("/utilisateurs", methods=["POST"])
def creer_utilisateur():
    """Crée un profil utilisateur après validation JSON Schema."""
    data = lire_json()
    message = valider(data, UTILISATEUR_SCHEMA)
    if message:
        return erreur(message)

    mot_de_passe_hash = bcrypt.hashpw(
        data["mot_de_passe"].encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    etablissements = json.dumps(data["etablissements_surveilles"])
    conn = get_db()

    try:
        inserer_utilisateur(conn, data, mot_de_passe_hash, etablissements)
    except sqlite3.IntegrityError:
        return erreur("Courriel déjà utilisé", 409)
    finally:
        conn.close()

    return jsonify({"message": "Utilisateur créé !"}), 201


@app.route("/inscription", methods=["GET"])
def inscription():
    """Affiche la page d'inscription."""
    return render_template("inscription.html")


@app.route("/connexion", methods=["GET"])
def connexion():
    """Affiche la page de connexion."""
    return render_template("connexion.html")


@app.route("/connexion", methods=["POST"])
def connexion_post():
    """Authentifie un utilisateur et crée une session."""
    data = lire_json() or {}
    courriel = data.get("courriel")
    mot_de_passe = data.get("mot_de_passe")
    if not isinstance(courriel, str) or not isinstance(mot_de_passe, str):
        return erreur("Courriel et mot de passe obligatoires.")

    conn = get_db()
    utilisateur = conn.execute(
        "SELECT * FROM utilisateurs WHERE courriel = ?",
        (courriel.strip().lower(),)
    ).fetchone()
    conn.close()

    # Même message dans les deux cas : on ne révèle pas si le compte existe.
    if utilisateur is None or not bcrypt.checkpw(
        mot_de_passe.encode("utf-8"),
        utilisateur["mot_de_passe"].encode("utf-8")
    ):
        return erreur("Courriel ou mot de passe incorrect", 401)

    session.clear()
    session["utilisateur_id"] = utilisateur["id"]
    session["utilisateur_courriel"] = utilisateur["courriel"]
    return jsonify({"message": "Connexion réussie !"}), 200


def utilisateur_connecte():
    """Retourne l'utilisateur de la session, ou None."""
    if "utilisateur_id" not in session:
        return None
    conn = get_db()
    utilisateur = conn.execute(
        "SELECT * FROM utilisateurs WHERE id = ?",
        (session["utilisateur_id"],)
    ).fetchone()
    conn.close()
    if utilisateur is None:
        session.clear()
    return utilisateur


@app.route("/profil", methods=["GET"])
def profil():
    """Affiche la page de profil de l'utilisateur connecté."""
    utilisateur = utilisateur_connecte()
    if utilisateur is None:
        return redirect(url_for("connexion"))
    etablissements = json.loads(utilisateur["etablissements_surveilles"])
    return render_template(
        "profil.html",
        utilisateur=utilisateur,
        etablissements=etablissements
    )


ETABLISSEMENTS_SCHEMA = {
    "type": "object",
    "properties": {
        "etablissements": {"type": "array", "items": TEXTE_REQUIS}
    },
    "required": ["etablissements"],
    "additionalProperties": False
}


@app.route("/profil/etablissements", methods=["POST"])
def modifier_etablissements():
    """Met à jour la liste des établissements surveillés de l'utilisateur."""
    if utilisateur_connecte() is None:
        return erreur("Non autorisé", 401)

    data = lire_json()
    message = valider(data, ETABLISSEMENTS_SCHEMA)
    if message:
        return erreur(message)

    conn = get_db()
    conn.execute(
        "UPDATE utilisateurs SET etablissements_surveilles = ? WHERE id = ?",
        (json.dumps(data["etablissements"]), session["utilisateur_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Établissements mis à jour !"}), 200


SIGNATURES_IMAGES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")


@app.route("/profil/photo", methods=["POST"])
def upload_photo():
    """Téléverse et sauvegarde la photo de profil de l'utilisateur."""
    if utilisateur_connecte() is None:
        return erreur("Non autorisé", 401)

    photo = request.files.get("photo")
    if photo is None or photo.filename == "":
        return erreur("Aucune photo fournie")

    photo_data = photo.read()
    extension_ok = photo.filename.lower().endswith((".jpg", ".jpeg", ".png"))
    contenu_ok = photo_data.startswith(SIGNATURES_IMAGES)
    if not extension_ok or not contenu_ok:
        return erreur("Format invalide. JPG ou PNG seulement")

    conn = get_db()
    conn.execute(
        "UPDATE utilisateurs SET photo = ? WHERE id = ?",
        (photo_data, session["utilisateur_id"])
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Photo uploadée !"}), 200


@app.route("/deconnexion", methods=["GET"])
def deconnexion():
    """Déconnecte l'utilisateur en vidant la session."""
    session.clear()
    return redirect(url_for("index"))


initialiser_db()

if __name__ == "__main__":
    demarrer_scheduler()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1",
            use_reloader=False)
