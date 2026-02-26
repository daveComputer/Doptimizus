let data = [
    { name: 'Caractéristique(s) principale(s)', value: 100/15 },
    { name: 'Dommages de Poussée', value: 100/15 },
    { name: 'Critique', value: 100/15 },
    { name: 'Résistances', value: 100/15 },
    { name: 'Vitalité', value: 100/15 },
    { name: 'PA', value: 100/15 },
    { name: 'PM', value: 100/15 },
    { name: 'PO', value: 100/15 },
    { name: 'Invocations', value: 100/15 },
    { name: 'Tacle', value: 100/15 },
    { name: 'Fuite', value: 100/15 },
    { name: 'Soins', value: 100/15 },
    { name: 'Retrait PA', value: 100/15 },
    { name: 'Retrait PM', value: 100/15 },
    { name: 'Initiative', value: 100/15 },
];

document.addEventListener("DOMContentLoaded", function() {
    const width = 600, height = 600;
    const margin = 100;
    const radius = Math.min(width, height) / 2 - margin;
    const angleStep = (Math.PI * 2) / data.length;
    data.forEach(d => d.locked = d.locked || false);

    const svg = d3.select("#chart").html("")
        .append("svg")
        .attr("width", width).attr("height", height)
        .append("g")
        .attr("transform", `translate(${width/2}, ${height/2})`);

    // Générateur de membrane
    const lineGen = d3.lineRadial()
        .angle((d, i) => i * angleStep)
        .radius(d => (d.value / 30) * radius)
        .curve(d3.curveCardinalClosed.tension(0));

    // Dessin initial de la membrane
    const blob = svg.append("path")
        .datum(data)
        .attr("class", "membrane")
        .attr("d", lineGen)
        .attr("fill", "rgba(0, 255, 200, 0.3)")
        .attr("stroke", "#00ffc8")
        .attr("stroke-width", 3);

    // Création des axes et labels (statiques)
    data.forEach((d, i) => {
        const angle = i * angleStep - Math.PI / 2;
        const x = Math.cos(angle) * radius;
        const y = Math.sin(angle) * radius;
        const labelRadius = radius + 60; // Plus loin du bord (était à 45)
        const foWidth = 120;  // Zone plus étroite
        const foHeight = 45; // Zone plus basse

        svg.append("line")
            .attr("x1", 0).attr("y1", 0)
            .attr("x2", x).attr("y2", y)
            .attr("stroke", "#333");

        // Création des conteneurs d'input (foreignObject)
        const labelContainers = svg.selectAll(".label-container")
            .data(data)
            .enter()
            .append("foreignObject")
            .attr("class", "label-container")
            // On centre le foreignObject : coordonnée - (largeur/2)
            .attr("x", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * labelRadius - foWidth / 2)
            .attr("y", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * labelRadius - foHeight / 2)
            .attr("width", foWidth)
            .attr("height", foHeight)
            .style("overflow", "visible");

        labelContainers.append("xhtml:div")
            .style("display", "flex")
            .style("flex-direction", "column")
            .style("align-items", "center")
            .style("justify-content", "center")
            .style("width", "100%")
            .html((d, i) => `
                <div style="
                    color: #8b949e; 
                    font-size: 8px; 
                    text-transform: uppercase; 
                    margin-bottom: 2px; 
                    text-align: center;
                    width: 100%;
                    pointer-events: none;
                ">${d.name}</div>
                <input type="number" 
                    id="input-val-${i}" 
                    value="${Math.round(d.value)}" 
                    style="
                            width: 28px; 
                            background: transparent; 
                            color: #00ffc8; 
                            border: 1px solid #333; 
                            border-radius: 2px; 
                            text-align: center; 
                            font-size: 10px; 
                            padding: 2px 0;
                            outline: none;
                            appearance: none; /* Sécurité supplémentaire */
                            -moz-appearance: textfield;
                    ">
            `);

        // Écouteur sur les inputs pour la saisie manuelle
        data.forEach((d, i) => {
            d3.select(`#input-val-${i}`).on("change", function() {
                let newValue = parseFloat(this.value);
                if (isNaN(newValue)) newValue = 0;
                
                // On applique la même logique de redistribution que pour le drag
                applyManualValue(i, newValue);
            });
        });
    });

    const lockButtons = svg.selectAll(".lock-btn")
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "lock-btn")
        .attr("r", 5) // Un peu plus gros pour cliquer facilement
        .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (radius + 20))
        .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (radius + 20))
        .attr("fill", d => d.locked ? "#ff4444" : "#555") // Rouge si bloqué, gris sinon
        .attr("stroke", "#fff")
        .style("cursor", "pointer")
        .on("click", function(event, d) {
            // Toggle de l'état
            d.locked = !d.locked;
            
            // Mise à jour visuelle du bouton
            d3.select(this).attr("fill", d.locked ? "#ff4444" : "#555");
            
            // Optionnel : ajouter une petite icône ou un effet visuel sur l'axe
            console.log(`${d.name} est maintenant ${d.locked ? 'verrouillé' : 'déverrouillé'}`);
        });

    // --- LOGIQUE INTERACTIVE (DRAG & DROP) ---

    const drag = d3.drag()
        .on("drag", function(event, d) {
            if (d.locked) return; // Un axe verrouillé ne peut pas être déplacé directement

            const i = data.indexOf(d);
            const angle = i * angleStep - Math.PI / 2;

            let projectedDistance = event.x * Math.cos(angle) + event.y * Math.sin(angle);
            let floor = getMinimumValue(d.name);
            let newValue = Math.min(30, Math.max(floor, (projectedDistance / radius) * 30));
            let delta = newValue - d.value;

            // --- NOUVELLE LOGIQUE DE FILTRAGE ---
            // On ne calcule la somme que sur les axes qui ne sont PAS l'axe actuel ET qui ne sont PAS verrouillés
            let otherEligibleAxes = data.filter((el, idx) => idx !== i && !el.locked);
            let otherValuesSum = otherEligibleAxes.reduce((sum, el) => sum + el.value, 0);

            // Si tous les autres axes sont verrouillés, on ne peut pas bouger celui-ci 
            // (car la somme totale doit rester fixe)
            if (otherEligibleAxes.length === 0) return;

            if (otherValuesSum > 0 || delta < 0) {
                let canRedistribute = true;
                
                // Vérification du plafond de 20% uniquement sur les axes éligibles
                if (delta < 0) {
                    otherEligibleAxes.forEach(el => {
                        let potentialValue = el.value - (delta * (el.value / otherValuesSum));
                        if (potentialValue > 30) canRedistribute = false;
                    });
                }

                if (canRedistribute) {
                    otherEligibleAxes.forEach(el => {
                        let reduction = delta * (el.value / otherValuesSum);
                        el.value = Math.max(0, Math.min(30, el.value - reduction));
                    });
                    d.value = newValue;
                }
            }

        updateGraph();
    });

    function getMinimumValue(name) {
        return (name === 'PA' || name === 'PM' || name === 'Vitalité') ? 1 : 0;
    }

    function updateGraph() {
        // Mise à jour de la membrane
        blob.attr("d", lineGen);

        // Mise à jour de toutes les poignées et de tous les textes
        svg.selectAll(".handle")
            .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (d.value / 30) * radius)
            .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (d.value / 30) * radius);

        data.forEach((d, i) => {
            d3.select(`#label-val-${i}`)
                .text(Math.round(d.value) + "%");
        });
        data.forEach((d, i) => {
        const input = document.getElementById(`input-val-${i}`);
        if (input) {
            input.value = Math.round(d.value);
            // Optionnel : on peut changer la couleur de bordure si l'axe est lock
            input.style.borderColor = d.locked ? "#ff4444" : "#333";
        }
    });
    }

    function applyManualValue(index, newValue) {
        const d = data[index];
        if (d.locked) return updateGraph(); 

        // 1. On définit le plancher pour l'axe actuel
        const floor = getMinimumValue(d.name);
        newValue = Math.max(floor, Math.min(30, newValue));
        
        let delta = newValue - d.value;

        // On récupère les autres axes qui ne sont pas verrouillés
        let otherEligibleAxes = data.filter((el, idx) => idx !== index && !el.locked);
        let otherValuesSum = otherEligibleAxes.reduce((sum, el) => sum + el.value, 0);

        if (otherEligibleAxes.length > 0 && (otherValuesSum > 0 || delta < 0)) {
            let canRedistribute = true;
            
            // 2. Vérification lors d'une AUGMENTATION de l'axe actuel
            // (Les autres vont donc baisser, on vérifie qu'ils ne passent pas sous leur plancher)
            if (delta > 0) {
                otherEligibleAxes.forEach(el => {
                    const elFloor = getMinimumValue(el.name);
                    let potentialValue = el.value - (delta * (el.value / otherValuesSum));
                    if (potentialValue < elFloor) canRedistribute = false;
                });
            }

            if (canRedistribute) {
                otherEligibleAxes.forEach(el => {
                    const elFloor = getMinimumValue(el.name);
                    let reduction = delta * (el.value / otherValuesSum);
                    // On bride la baisse au plancher spécifique de l'élément (1 ou 0)
                    el.value = Math.max(elFloor, Math.min(20, el.value - reduction));
                });
                d.value = newValue;
            }
        }
        updateGraph();
    }

    // Ajouter les poignées interactives
    const handles = svg.selectAll(".handle")
        .data(data)
        .enter()
        .append("circle")
        .attr("class", "handle")
        .attr("r", 4)
        .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (d.value / 30) * radius)
        .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (d.value / 30) * radius)
        .attr("fill", "#00ffc8")
        .style("cursor", "pointer")
        .call(drag);

    // Fonction pour calculer les scores et les préparer pour l'export
    function getDesirabilityData() {
        const vitalite = data.find(d => d.name === 'Vitalité').value;
        
        // Protection contre division par zéro
        const vFactor = vitalite > 0 ? vitalite : 1; 
        const targetSum = 100 / vFactor;

        // Calcul des scores de désirabilité
        const results = data.map(d => ({
            caracteristique: d.name,
            pourcentage: d.value.toFixed(2),
            score_desirabilite: (d.value * (targetSum / 100)).toFixed(2) 
            // Note: J'ai divisé par 100 pour que la SOMME totale soit égale à 100/V
        }));

        return {
            timestamp: new Date().toISOString(),
            global_sum_score: targetSum.toFixed(2),
            details: results
        };
    }

    const btn = document.getElementById("export-btn");
    if (btn) {
        btn.addEventListener("click", exportToJson);
    }

    function getGlobalConfig() {
        const selectedElements = Array.from(document.querySelectorAll('.element-check:checked'))
                                    .map(cb => cb.value);
        return {
            lvl: parseInt(document.getElementById('char-level').value) || 200,
            elements: selectedElements,
            moyenne_sort: parseFloat(document.getElementById('base-damage').value) || 30,
            radar_stats: getDesirabilityData() // On inclut les données du radar ici
        };
    }

    // On récupère l'événement 'e' pour bloquer le rafraîchissement
    async function exportToJson(e) {
        if (e) e.preventDefault(); 

        const btn = document.getElementById("export-btn");
        const config = getGlobalConfig(); // On récupère la config complète

        // --- NOUVELLE VALIDATION ---
        if (config.elements.length === 0) {
            showError("Veuillez sélectionner au moins un élément (Terre, Feu, Eau, Air) avant d'optimiser.");
            return; // On arrête tout ici, pas de requête serveur
        }

        try {
            btn.disabled = true;
            btn.innerText = "Calcul en cours...";
            
            // On cache un éventuel ancien message d'erreur
            hideError();

            // 1. Sauvegarde
            const saveResponse = await fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config),
            });

            if (!saveResponse.ok) throw new Error("Erreur lors de la sauvegarde");

            // 2. Récupération des résultats
            const resultsResponse = await fetch(`/get-results?lvl=${config.lvl}&t=${Date.now()}`);
            if (!resultsResponse.ok) throw new Error("Erreur lors du calcul des résultats");

            const data = await resultsResponse.json();
            displayResults(data, true);

        } catch (error) {
            console.error('Erreur:', error);
            showError("Une erreur est survenue : " + error.message);
        } finally {
            btn.disabled = false;
            btn.innerText = "Confirmer";
        }
    }

    function showError(message) {
        const container = document.getElementById("error-msg-container");
        const textSpan = document.getElementById("error-text");
        
        textSpan.innerText = message;
        container.style.display = "block";
        
        // Optionnel : faire vibrer le message pour attirer l'oeil
        container.style.animation = "shake 0.5s";
        setTimeout(() => container.style.animation = "", 500);
    }

    function hideError() {
        document.getElementById("error-msg-container").style.display = "none";
    }

    /**
     * Affiche les résultats (Items par type et Stuffs optimisés)
     * @param {Object} data - Les données JSON reçues du serveur
     */
    function displayResults(data, shouldScroll = false) {
        // Vérification de sécurité
        if (!data || !data.top_items) {
            console.error("Données invalides reçues du serveur");
            return;
        }

        // Afficher la section de résultats
        document.getElementById("results-section").style.display = "block";
        
        // --- PARTIE 1 : TOP ITEMS PAR TYPE ---
        const itemsContainer = document.getElementById("top-items-list");
        itemsContainer.innerHTML = ""; // On vide l'ancien contenu

        for (const [typeNom, items] of Object.entries(data.top_items)) {
            // Titre de la catégorie
            const typeHeader = document.createElement("div");
            typeHeader.className = "results-type-header";
            typeHeader.innerHTML = `<h4>${typeNom}</h4>`;
            itemsContainer.appendChild(typeHeader);

            // Liste des items de cette catégorie
            items.forEach(item => {
                const scoreValue = item.score || item.score_optimisation || 0;
                const itemName = item.nom || "Équipement inconnu";

                const card = document.createElement("div");
                card.className = "item-card";
                card.innerHTML = `
                    <div class="item-card-content">
                        <span class="item-name">${itemName}</span>
                        <span class="item-score">${Math.round(scoreValue)} pts</span>
                    </div>
                    <div class="item-type-subtitle">${typeNom}</div>
                `;
                itemsContainer.appendChild(card);
            });
        }

        // --- PARTIE 2 : TOP STUFFS (SOLUTIONS COMPLÈTES) ---
        const stuffsContainer = document.getElementById("top-stuffs-list");
        stuffsContainer.innerHTML = "";

        if (data.top_stuffs && data.top_stuffs.length > 0) {
            data.top_stuffs.forEach((solution, index) => {
                // Structure attendue : solution[0] = liste items, solution[1] = score total
                const itemsDetails = solution[0];
                const scoreTotal = solution[1];

                // On extrait les noms pour créer une liste lisible
                const listeNoms = itemsDetails.map(it => it.nom || "Item inconnu").join(', ');

                const stuffCard = document.createElement("div");
                stuffCard.className = "item-card stuff-card";
                stuffCard.innerHTML = `
                    <div class="item-card-content">
                        <span class="item-name">Composition Optimale #${index + 1}</span>
                        <span class="item-score">Total: ${Math.round(scoreTotal)} pts</span>
                    </div>
                    <div style="font-size: 0.85em; margin-top:8px; color:#c9d1d9; line-height: 1.4;">
                        <strong style="color: #58a6ff;">Équipements :</strong> ${listeNoms}
                    </div>
                `;
                stuffsContainer.appendChild(stuffCard);
            });
        } else {
            stuffsContainer.innerHTML = "<p style='color: #8b949e; text-align: center; width: 100%;'>Aucune solution complète trouvée pour ce niveau.</p>";
        }
        const resultsSection = document.getElementById("results-section");
        resultsSection.style.display = "block";
        if (shouldScroll) {
            setTimeout(() => {
                document.getElementById("results-section").scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }, 100);
        }
    }
});



