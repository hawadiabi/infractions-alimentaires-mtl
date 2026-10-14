CREATE TABLE IF NOT EXISTS contrevenants (
    id_poursuite INTEGER PRIMARY KEY,
    business_id  INTEGER,
    date         TEXT,
    description  TEXT,
    adresse      TEXT,
    date_jugement TEXT,
    etablissement TEXT,
    montant      INTEGER,
    proprietaire TEXT,
    ville        TEXT,
    statut       TEXT,
    date_statut  TEXT,
    categorie    TEXT
);

CREATE TABLE IF NOT EXISTS inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    etablissement TEXT NOT NULL,
    adresse TEXT NOT NULL,
    ville TEXT NOT NULL,
    date_visite TEXT NOT NULL,
    nom_client TEXT NOT NULL,
    prenom_client TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_complet TEXT NOT NULL,
    courriel TEXT NOT NULL UNIQUE,
    mot_de_passe TEXT NOT NULL,
    etablissements_surveilles TEXT NOT NULL,
    photo BLOB
);
