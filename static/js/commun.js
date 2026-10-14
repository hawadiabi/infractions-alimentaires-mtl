// Fonctions partagées par toutes les pages.

// Échappe le texte avant de l'insérer avec innerHTML.
function echapper(texte) {
   const div = document.createElement("div");
   div.textContent = texte == null ? "" : String(texte);
   return div.innerHTML;
}

// Affiche un message de succès ou d'erreur dans l'élément donné.
function afficherMessage(element, texte, succes) {
   element.classList.remove("message-succes", "message-erreur");
   element.classList.add(succes ? "message-succes" : "message-erreur");
   element.textContent = (succes ? "✅ " : "❌ ") + texte;
}

// Convertit une date AAAAMMJJ en AAAA-MM-JJ.
function formaterDate(d) {
   if (!d || d.length !== 8) return d || "";
   return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}`;
}

// Envoie du JSON et retourne { ok, data } même en cas d'erreur HTTP.
function envoyerJson(url, donnees) {
   return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(donnees)
   }).then(lireReponse);
}

function lireReponse(response) {
   return response.json()
      .catch(() => ({ erreur: "Réponse invalide du serveur." }))
      .then(data => ({ ok: response.ok, data }));
}
