/**
 * Affiche les poids sous forme de texte simple : "1 PA = 400 Vitalité"
 * @param {Object} weights - Dictionnaire des poids calculés
 */
export function displayWeights(weights) {
    const container = document.getElementById('weights-list');
    if (!container) return;

    container.innerHTML = "";

    if (!weights || Object.keys(weights).length === 0) {
        container.innerHTML = "<p class='weight-line'>Calcul en attente...</p>";
        return;
    }

    // Tri décroissant
    const sortedWeights = Object.entries(weights).sort((a, b) => b[1] - a[1]);

    sortedWeights.forEach(([name, value]) => {
        const line = document.createElement('div');
        line.className = 'weight-line';
        line.innerHTML = `1 <strong>${name}</strong> = ${value} Vitalité`;
        container.appendChild(line);
    });
    document.getElementById("weights-container").classList.add("panel-visible");
}