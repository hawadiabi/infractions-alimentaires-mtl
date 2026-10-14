# Infractions alimentaires Montréal

Application web Flask qui permet de consulter les infractions alimentaires des établissements de Montréal, à partir des [données ouvertes de la Ville](https://donnees.montreal.ca/dataset/inspection-aliments-contrevenants).

Projet individuel réalisé dans le cours INF5190 (Programmation Web avancée) à l'UQAM, à l'hiver 2026, puis corrigé et amélioré après la correction.

## Fonctionnalités

- Importation des données ouvertes de la Ville dans une base SQLite, et synchronisation automatique chaque nuit (APScheduler).
- Courriel automatique quand de nouvelles infractions sont détectées.
- Recherche par établissement, propriétaire ou rue, insensible aux accents.
- Recherche par période et par restaurant en Ajax, sans rechargement de la page.
- API REST documentée (HTML et RAML), avec validation des données par JSON Schema.
- Demandes d'inspection : création et suppression.
- Comptes utilisateurs : inscription, connexion, mots de passe hachés avec bcrypt, liste d'établissements surveillés et photo de profil.

## Technologies

Python, Flask, SQLite, APScheduler, JSON Schema, bcrypt, JavaScript (Fetch API), HTML, CSS.

## Installation

```bash
git clone https://github.com/hawadiabi/infractions-alimentaires-mtl.git
cd infractions-alimentaires-mtl
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS ou Linux
pip install -r requirements.txt
python import_data.py             # importe les données de la Ville
python app.py
```

Ouvrir ensuite http://127.0.0.1:5000.

Pour l'envoi des courriels, renseigner les adresses dans `config.yaml` et définir le mot de passe d'application dans la variable d'environnement `SMTP_MOT_DE_PASSE`. Il ne doit jamais être écrit dans un fichier du dépôt.

## Utilisation

Une fois l'application lancée, les pages sont accessibles à ces adresses :

| Page | Adresse |
|---|---|
| Accueil et recherche | http://127.0.0.1:5000/ |
| Créer un compte | http://127.0.0.1:5000/inscription |
| Se connecter | http://127.0.0.1:5000/connexion |
| Profil (après connexion) | http://127.0.0.1:5000/profil |
| Demander une inspection | http://127.0.0.1:5000/plainte |
| Documentation de l'API | http://127.0.0.1:5000/doc |

Pour créer un compte, il faut un courriel valide et un mot de passe d'au moins 8 caractères. Les établissements à surveiller sont facultatifs et séparés par des virgules (par exemple `TIM HORTONS, SUBWAY`). Sur la page de profil, on peut ensuite ajouter ou retirer des établissements et téléverser une photo (JPG ou PNG).

## API REST

| Méthode | Route | Description |
|---|---|---|
| GET | `/contrevenants?du=AAAA-MM-JJ&au=AAAA-MM-JJ` | Infractions entre deux dates |
| GET | `/contrevenants/etablissements` | Établissements triés par nombre d'infractions |
| POST | `/inspections` | Crée une demande d'inspection |
| DELETE | `/inspections/<id>` | Supprime une demande d'inspection |
| POST | `/utilisateurs` | Crée un compte utilisateur |

La documentation complète est disponible sur la page `/doc` de l'application.

## Corrections apportées après le cours

- L'importation échouait : le site de la Ville refusait les requêtes du script (erreur 403).
- Validation ajoutée pour les paramètres de date de l'API, le format du courriel et la longueur minimale du mot de passe.
- Recherche insensible aux accents dans les deux sens.
- JavaScript et CSS déplacés hors des pages HTML, et texte des données échappé avant l'affichage.
- Erreurs 404 qui étaient transformées en erreurs 500.
- Mot de passe SMTP retiré du fichier de configuration.
