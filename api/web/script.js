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
    const axesOrder = data.map(d => d.name);

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

    // 1. Membrane de l'utilisateur (Paramètres)
    const inputBlob = svg.append("path")
        .datum(data)
        .attr("class", "membrane-input") // Classe spécifique
        .attr("d", lineGen)
        .attr("fill", "rgba(255, 255, 255, 0.1)") // Blanc translucide
        .attr("stroke", "#ccc")
        .attr("stroke-dasharray", "4") // Pointillés pour l'input
        .attr("stroke-width", 2);

    // 2. Membrane de Sélection (Stuff/Item)
    const selectionBlob = svg.append("path")
        .attr("class", "membrane-selection") // Classe spécifique
        .attr("fill", "rgba(0, 255, 200, 0.4)") // Vert/Bleu Dofus
        .attr("stroke", "#00ffc8")
        .attr("stroke-width", 3)
        .style("pointer-events", "none"); // Pour ne pas gêner les clics sur les axes

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

            // --- LOGIQUE DE FILTRAGE ET VÉRIFICATION ---
            let otherEligibleAxes = data.filter((el, idx) => idx !== i && !el.locked);
            let otherValuesSum = otherEligibleAxes.reduce((sum, el) => sum + el.value, 0);

            // 1. Si aucun autre axe n'est déverrouillé : blocage total
            if (otherEligibleAxes.length === 0) return;

            // 2. Si on veut AUGMENTER l'axe actuel (delta > 0) 
            // mais que les autres sont déjà tous à 0 : impossible de piocher dedans.
            if (delta > 0 && otherValuesSum <= 0) return;

            // 3. Vérification de la redistribution
            let canRedistribute = true;

            if (delta > 0) {
                // Cas où on augmente : on vérifie juste qu'on a de la réserve (déjà fait au point 2)
                // Mais on peut aussi vérifier si on ne descend pas sous le floor des autres si nécessaire
            } else if (delta < 0) {
                // Cas où on diminue l'axe : les autres vont augmenter. 
                // On vérifie qu'aucun ne dépasse le plafond de 30.
                otherEligibleAxes.forEach(el => {
                    // Formule de redistribution inverse
                    let potentialValue = el.value - (delta * (el.value / (otherValuesSum || 1))); 
                    // Note: le || 1 évite le NaN si on part de zéro partout
                    if (potentialValue > 30) canRedistribute = false;
                });
            }

            // --- APPLICATION DES VALEURS ---
            if (canRedistribute) {
                otherEligibleAxes.forEach(el => {
                    // On évite la division par zéro si otherValuesSum est à 0
                    let weight = otherValuesSum > 0 ? (el.value / otherValuesSum) : (1 / otherEligibleAxes.length);
                    let reduction = delta * weight;
                    el.value = Math.max(0, Math.min(30, el.value - reduction));
                });
                d.value = newValue;
            }

        updateGraph();
    });

    function getMinimumValue(name) {
        return (name === 'PA' || name === 'PM' || name === 'Vitalité') ? 1 : 0;
    }

    function updateGraph() {
        // Mise à jour de la membrane
        inputBlob.attr("d", lineGen);

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

        document.getElementById("left-panel").classList.add("panel-visible");
        document.getElementById("right-panel").classList.add("panel-visible");
        document.querySelector(".workspace-container").style.justifyContent = "space-between";

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
                // On ajoute le HTML de l'icône (ici un SVG simple pour éviter des polices externes)
                card.innerHTML = `
                    <button class="delete-btn" title="Exclure cet item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                    <div class="item-card-content">
                        <span class="item-name">${item.nom}</span>
                        <span class="item-score">${Math.round(item.score || 0)} pts</span>
                    </div>
                    <div class="item-type-subtitle">${typeNom}</div>
                `;
                itemsContainer.appendChild(card);
                card.addEventListener("click", () => {
                    // Style visuel pour la sélection
                    document.querySelectorAll('.item-card').forEach(c => c.style.borderColor = "#30363d");
                    card.style.borderColor = "#00ffc8";

                    // Appel de la mise à jour de la 2ème membrane
                    updateSelectionMembrane(item.repartition, item.score);
                });
                const bin = card.querySelector(".delete-btn");
                bin.addEventListener("click", async (e) => {
                    e.stopPropagation(); // Empêche de cliquer sur la carte
                    
                    if (confirm(`Exclure "${item.nom}" des prochaines recherches ?`)) {
                        // 1. Appel au backend pour blacklister
                        const response = await fetch('/exclude-item', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ item_nom: item.nom })
                        });

                        if (response.ok) {
                            // 2. Animation de disparition visuelle
                            card.style.opacity = "0";
                            card.style.transform = "translateX(20px)";
                            setTimeout(() => card.remove(), 300);
                        }
                    }
                });
            });
        }

        // --- PARTIE 2 : TOP STUFFS (SOLUTIONS COMPLÈTES) ---
        const stuffsContainer = document.getElementById("top-stuffs-list");
        stuffsContainer.innerHTML = "";

        if (data.top_stuffs && data.top_stuffs.length > 0) {
            data.top_stuffs.forEach((solution, index) => {
                // On vérifie si c'est l'ancien format [items, score] ou le nouveau format {stuff: items, ...}
                const itemsDetails = Array.isArray(solution) ? solution[0] : solution.stuff;
                const scoreTotal = Array.isArray(solution) ? solution[1] : solution.score;

                // Sécurité : si itemsDetails est toujours indéfini, on arrête pour cette itération
                if (!itemsDetails) {
                    console.warn(`Structure de solution inconnue à l'index ${index}`, solution);
                    return;
                }

                // Maintenant .map() ne plantera plus
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

                stuffCard.addEventListener("click", () => {
                    // Style visuel pour la sélection
                    document.querySelectorAll('.stuff-card').forEach(c => c.style.borderColor = "#30363d");
                    stuffCard.style.borderColor = "#00ffc8";

                    // Appel de la mise à jour de la 2ème membrane
                    updateSelectionMembrane(solution.repartition_axes, solution.score);
                });
            });
        } else {
            stuffsContainer.innerHTML = "<p style='color: #8b949e; text-align: center; width: 100%;'>Aucune solution complète trouvée pour ce niveau.</p>";
        }
        if (shouldScroll) {
            window.scrollTo({ top: document.querySelector(".workspace-container").offsetTop, behavior: 'smooth' });
        }
    }

    function updateSelectionMembrane(repartitionAxes, scoreTotal) {
        console.log("Mise à jour de la membrane de sélection avec :", repartitionAxes, "Score total :", scoreTotal);
        if (!repartitionAxes) return;

        // On transforme l'objet repartitionAxes en tableau ordonné selon axesOrder
        const updatedData = axesOrder.map(axisName => {
            // On récupère les points pour cet axe (ex: "Vitalité")
            const points = repartitionAxes[axisName] || 0;
            
            // Calcul du pourcentage : (Points de l'axe / Score Total du stuff) * 100
            const percentage = scoreTotal > 0 ? (points / scoreTotal) * 100 : 0;
            
            return { value: percentage };
        });

        // Générateur spécifique pour la sélection (échelle sur 100)
        const lineGenSelection = d3.lineRadial()
            .angle((d, i) => i * angleStep)
            .radius(d => (d.value / 100) * radius) // Ici on divise par 100
            .curve(d3.curveCardinalClosed.tension(0));

        // Animation de la membrane
        d3.select(".membrane-selection")
            .datum(updatedData)
            .transition()
            .duration(600)
            .ease(d3.easeBackOut)
            .attr("d", lineGenSelection);
    }
});



