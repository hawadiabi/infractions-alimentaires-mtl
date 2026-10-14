// Page d'inscription. Les mêmes règles sont vérifiées par le serveur.

const MOT_DE_PASSE_MIN = 8;
const FORMAT_COURRIEL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function validerInscription(nom, courriel, motDePasse) {
   if (!nom) return "Le nom complet est obligatoire.";
   if (!courriel) return "Le courriel est obligatoire.";
   if (!FORMAT_COURRIEL.test(courriel)) return "Le courriel n'est pas valide.";
   if (!motDePasse) return "Le mot de passe est obligatoire.";
   if (motDePasse.length < MOT_DE_PASSE_MIN) {
      return `Le mot de passe doit avoir au moins ${MOT_DE_PASSE_MIN} caractères.`;
   }
   return null;
}

function inscrire(event) {
   event.preventDefault();
   const nom = document.getElementById("nom_complet").value.trim();
   const courriel = document.getElementById("courriel").value.trim();
   const motDePasse = document.getElementById("mot_de_passe").value;
   const etablissements = document.getElementById("etablissements").value
      .split(",").map(e => e.trim()).filter(e => e);
   const div = document.getElementById("message");

   const erreur = validerInscription(nom, courriel, motDePasse);
   if (erreur) {
      afficherMessage(div, erreur, false);
      return;
   }

   envoyerJson("/utilisateurs", {
      nom_complet: nom,
      courriel: courriel,
      mot_de_passe: motDePasse,
      etablissements_surveilles: etablissements
   })
      .then(({ ok, data }) => {
         if (ok) {
            afficherMessage(div, data.message, true);
            setTimeout(() => { window.location.href = "/connexion"; }, 1000);
         } else {
            afficherMessage(div, data.erreur, false);
         }
      })
      .catch(() => afficherMessage(div, "Impossible de joindre le serveur.", false));
}

document.addEventListener("DOMContentLoaded", () => {
   document.getElementById("form-inscription")
      .addEventListener("submit", inscrire);
});
