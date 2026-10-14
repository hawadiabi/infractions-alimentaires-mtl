// Page de connexion.

function validerConnexion(courriel, motDePasse) {
   if (!courriel) return "Le courriel est obligatoire.";
   if (!motDePasse) return "Le mot de passe est obligatoire.";
   return null;
}

function connecter(event) {
   event.preventDefault();
   const courriel = document.getElementById("courriel").value.trim();
   const motDePasse = document.getElementById("mot_de_passe").value;
   const div = document.getElementById("message");

   const erreur = validerConnexion(courriel, motDePasse);
   if (erreur) {
      afficherMessage(div, erreur, false);
      return;
   }

   envoyerJson("/connexion", { courriel, mot_de_passe: motDePasse })
      .then(({ ok, data }) => {
         if (ok) {
            afficherMessage(div, data.message, true);
            setTimeout(() => { window.location.href = "/profil"; }, 1000);
         } else {
            afficherMessage(div, data.erreur, false);
         }
      })
      .catch(() => afficherMessage(div, "Impossible de joindre le serveur.", false));
}

document.addEventListener("DOMContentLoaded", () => {
   document.getElementById("form-connexion")
      .addEventListener("submit", connecter);
});
