// Page de demande d'inspection.

const CHAMPS_PLAINTE = {
   etablissement: "L'établissement est obligatoire.",
   adresse: "L'adresse est obligatoire.",
   ville: "La ville est obligatoire.",
   date_visite: "La date de visite est obligatoire.",
   prenom_client: "Le prénom est obligatoire.",
   nom_client: "Le nom est obligatoire.",
   description: "La description est obligatoire."
};

function validerPlainte(data) {
   for (const [champ, message] of Object.entries(CHAMPS_PLAINTE)) {
      if (!data[champ]) return message;
   }
   return null;
}

function remonter() {
   window.scrollTo({ top: 0, behavior: "smooth" });
}

function envoyerPlainte(event) {
   event.preventDefault();
   const data = {};
   for (const champ of Object.keys(CHAMPS_PLAINTE)) {
      data[champ] = document.getElementById(champ).value.trim();
   }
   const div = document.getElementById("message");

   const erreur = validerPlainte(data);
   if (erreur) {
      afficherMessage(div, erreur, false);
      remonter();
      return;
   }

   envoyerJson("/inspections", data)
      .then(({ ok, data: resultat }) => {
         if (ok) {
            afficherMessage(div, resultat.message, true);
            document.getElementById("form-plainte").reset();
         } else {
            afficherMessage(div, "Erreur : " + resultat.erreur, false);
         }
         remonter();
      })
      .catch(() => afficherMessage(div, "Impossible de joindre le serveur.", false));
}

document.addEventListener("DOMContentLoaded", () => {
   document.getElementById("form-plainte")
      .addEventListener("submit", envoyerPlainte);
});
