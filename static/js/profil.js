// Page de profil : établissements surveillés et photo.

let etablissements = [];

function rafraichir() {
   const liste = document.getElementById("liste-etablissements");
   liste.innerHTML = "";
   etablissements.forEach(nom => {
      const item = document.createElement("div");
      item.className = "etablissement-item";

      const texte = document.createElement("span");
      texte.textContent = nom;

      const bouton = document.createElement("button");
      bouton.type = "button";
      bouton.className = "supprimer";
      bouton.textContent = "Supprimer";
      // Le nom est gardé tel quel : les apostrophes ne cassent plus rien.
      bouton.addEventListener("click", () => supprimer(nom));

      item.append(texte, bouton);
      liste.appendChild(item);
   });
}

function ajouter() {
   const champ = document.getElementById("nouvel-etablissement");
   const val = champ.value.trim();
   const div = document.getElementById("message");
   if (!val) {
      afficherMessage(div, "Veuillez entrer un nom d'établissement.", false);
      return;
   }
   if (etablissements.includes(val)) {
      afficherMessage(div, "Cet établissement est déjà dans la liste.", false);
      return;
   }
   sauvegarder([...etablissements, val], () => { champ.value = ""; });
}

function supprimer(nom) {
   sauvegarder(etablissements.filter(e => e !== nom));
}

// La liste locale n'est modifiée que si le serveur a accepté le changement.
function sauvegarder(nouvelleListe, siSucces) {
   const div = document.getElementById("message");
   envoyerJson("/profil/etablissements", { etablissements: nouvelleListe })
      .then(({ ok, data }) => {
         if (ok) {
            etablissements = nouvelleListe;
            rafraichir();
            afficherMessage(div, data.message, true);
            if (siSucces) siSucces();
         } else {
            afficherMessage(div, data.erreur, false);
         }
         window.scrollTo({ top: 0, behavior: "smooth" });
      })
      .catch(() => afficherMessage(div, "Impossible de joindre le serveur.", false));
}

function validerPhoto(fichier) {
   const nom = fichier.name.toLowerCase();
   return [".jpg", ".jpeg", ".png"].some(ext => nom.endsWith(ext));
}

function uploadPhoto() {
   const fichier = document.getElementById("photo").files[0];
   const div = document.getElementById("message");

   if (!fichier) {
      afficherMessage(div, "Veuillez sélectionner une photo.", false);
      return;
   }
   if (!validerPhoto(fichier)) {
      afficherMessage(div, "Format invalide. JPG ou PNG seulement.", false);
      return;
   }

   const formData = new FormData();
   formData.append("photo", fichier);

   fetch("/profil/photo", { method: "POST", body: formData })
      .then(lireReponse)
      .then(({ ok, data }) => {
         afficherMessage(div, ok ? data.message : data.erreur, ok);
         window.scrollTo({ top: 0, behavior: "smooth" });
      })
      .catch(() => afficherMessage(div, "Impossible de joindre le serveur.", false));
}

document.addEventListener("DOMContentLoaded", () => {
   const liste = document.getElementById("liste-etablissements");
   etablissements = JSON.parse(liste.dataset.etablissements || "[]");
   rafraichir();
   document.getElementById("btn-ajouter").addEventListener("click", ajouter);
   document.getElementById("btn-photo").addEventListener("click", uploadPhoto);
});
