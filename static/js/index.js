// Page d'accueil : recherche par dates (A5) et par restaurant (A6).

function erreurDans(div, texte) {
   div.innerHTML = `<p class="message-erreur">❌ ${echapper(texte)}</p>`;
}

function rechercherDates() {
   const du = document.getElementById("date-debut").value;
   const au = document.getElementById("date-fin").value;
   const div = document.getElementById("resultats-dates");

   if (!du || !au) {
      erreurDans(div, "Veuillez entrer les deux dates.");
      return;
   }
   if (du > au) {
      erreurDans(div, "La date de début doit être avant la date de fin.");
      return;
   }

   const params = new URLSearchParams({ du, au });
   fetch(`/contrevenants?${params}`)
      .then(lireReponse)
      .then(({ ok, data }) => {
         if (!ok) {
            erreurDans(div, data.erreur);
            return;
         }
         afficherResultats(data);
      })
      .catch(() => erreurDans(div, "Impossible de joindre le serveur."));
}

function afficherResultats(data) {
   const div = document.getElementById("resultats-dates");

   if (data.length === 0) {
      div.innerHTML = "<p>Aucun résultat trouvé.</p>";
      return;
   }

   const compteur = {};
   data.forEach(r => {
      compteur[r.etablissement] = (compteur[r.etablissement] || 0) + 1;
   });

   let html = `<p>${data.length} contravention(s) trouvée(s)</p>
      <table>
         <thead>
            <tr>
               <th>Établissement</th>
               <th>Nombre de contraventions</th>
            </tr>
         </thead>
         <tbody>`;

   const lignes = Object.entries(compteur).sort((a, b) => b[1] - a[1]);
   for (const [nom, nombre] of lignes) {
      html += `<tr><td>${echapper(nom)}</td><td>${nombre}</td></tr>`;
   }

   html += "</tbody></table>";
   div.innerHTML = html;
}

function chargerRestaurants() {
   const select = document.getElementById("liste-restaurants");
   fetch("/etablissements")
      .then(response => response.json())
      .then(data => {
         select.innerHTML = "";
         const vide = document.createElement("option");
         vide.value = "";
         vide.textContent = "-- Choisir un restaurant --";
         select.appendChild(vide);
         data.forEach(nom => {
            const option = document.createElement("option");
            option.value = nom;
            option.textContent = nom;
            select.appendChild(option);
         });
      })
      .catch(() => {
         select.innerHTML = "<option value=''>Erreur de chargement</option>";
      });
}

function rechercherRestaurant() {
   const nom = document.getElementById("liste-restaurants").value;
   const div = document.getElementById("resultats-restaurant");

   if (!nom) {
      erreurDans(div, "Veuillez choisir un restaurant.");
      return;
   }

   fetch(`/etablissement/${encodeURIComponent(nom)}`)
      .then(response => response.json())
      .then(afficherInfractions)
      .catch(() => erreurDans(div, "Impossible de joindre le serveur."));
}

function afficherInfractions(data) {
   const div = document.getElementById("resultats-restaurant");

   if (data.length === 0) {
      div.innerHTML = "<p>Aucune infraction trouvée.</p>";
      return;
   }

   let html = `<p>${data.length} infraction(s) trouvée(s)</p>`;
   data.forEach(r => {
      html += `<div class="carte">
         <p><strong>Date :</strong> ${echapper(formaterDate(r.date))}</p>
         <p><strong>Description :</strong> ${echapper(r.description)}</p>
         <p><strong>Adresse :</strong> ${echapper(r.adresse)}</p>
         <p><strong>Montant :</strong> ${echapper(r.montant)} $</p>
         <p><strong>Statut :</strong> ${echapper(r.statut)}</p>
         <p><strong>Catégorie :</strong> ${echapper(r.categorie)}</p>
      </div>`;
   });
   div.innerHTML = html;
}

document.addEventListener("DOMContentLoaded", () => {
   document.getElementById("btn-dates")
      .addEventListener("click", rechercherDates);
   document.getElementById("btn-restaurant")
      .addEventListener("click", rechercherRestaurant);
   chargerRestaurants();
});
