// radar.js

let svg, lineGen, angleStep, radius, axesOrder, data;
const width = 600, height = 600, margin = 100;

export function initRadar(containerId, initialData) {
    data = initialData;
    radius = Math.min(width, height) / 2 - margin;
    angleStep = (Math.PI * 2) / data.length;
    data.forEach(d => d.locked = d.locked || false);
    axesOrder = data.map(d => d.name);

    svg = d3.select(containerId).html("")
        .append("svg")
        .attr("width", width).attr("height", height)
        .append("g")
        .attr("transform", `translate(${width/2}, ${height/2})`);

    // Générateur de membrane (basé sur ton code / 30)
    lineGen = d3.lineRadial()
        .angle((d, i) => i * angleStep)
        .radius(d => (d.value / 30) * radius)
        .curve(d3.curveCardinalClosed.tension(0));

    // 1. Membrane de l'utilisateur (Paramètres)
    svg.append("path")
        .datum(data)
        .attr("class", "membrane-input")
        .attr("d", lineGen)
        .attr("fill", "rgba(255, 255, 255, 0.1)")
        .attr("stroke", "#ccc")
        .attr("stroke-dasharray", "4")
        .attr("stroke-width", 2);

    // 2. Membrane de Sélection (Stuff/Item)
    svg.append("path")
        .attr("class", "membrane-selection")
        .attr("fill", "rgba(0, 255, 200, 0.4)")
        .attr("stroke", "#00ffc8")
        .attr("stroke-width", 3)
        .style("pointer-events", "none");

    // Création des axes et labels
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
        .attr("r", 5)
        .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (radius + 20))
        .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (radius + 20))
        .attr("fill", d => d.locked ? "#ff4444" : "#555")
        .attr("stroke", "#fff")
        .style("cursor", "pointer")
        .on("click", function(event, d) {
            d.locked = !d.locked;
            d3.select(this).attr("fill", d.locked ? "#ff4444" : "#555");
        });

    const drag = d3.drag()
        .on("drag", function(event, d) {
            if (d.locked) return;
            const i = data.indexOf(d);
            const angle = i * angleStep - Math.PI / 2;

            // 1. Calcul de la direction du mouvement (delta souhaité)
            let projectedDistance = event.x * Math.cos(angle) + event.y * Math.sin(angle);
            let myFloor = getMinimumValue(d.name);
            let targetValue = Math.min(30, Math.max(myFloor, (projectedDistance / radius) * 30));
            let requestedDelta = targetValue - d.value;

            if (Math.abs(requestedDelta) < 0.01) return;

            // 2. Identifier les autres axes qui PEUVENT encore bouger
            let others = data.filter((el, idx) => idx !== i && !el.locked);
            
            // On filtre ceux qui ont encore de la marge dans la direction opposée au delta
            let contributors = others.filter(el => {
                const elFloor = getMinimumValue(el.name);
                return requestedDelta > 0 ? el.value > elFloor : el.value < 30;
            });

            if (contributors.length === 0) return;

            // 3. Calculer la capacité totale de redistribution des contributeurs
            // (Combien de % peut-on leur prendre ou leur donner au total ?)
            let totalCapacity = 0;
            contributors.forEach(el => {
                const elFloor = getMinimumValue(el.name);
                totalCapacity += requestedDelta > 0 ? (el.value - elFloor) : (30 - el.value);
            });

            // 4. On ajuste le delta si les autres ne peuvent pas tout encaisser
            let actualDelta = Math.min(Math.abs(requestedDelta), totalCapacity) * (requestedDelta > 0 ? 1 : -1);

            // 5. Redistribution proportionnelle au "poids" de chaque contributeur
            // Pour une augmentation : on réduit proportionnellement à leur valeur actuelle
            // Pour une réduction : on augmente proportionnellement à l'espace vide restant
            let sumForWeight = contributors.reduce((sum, el) => {
                const elFloor = getMinimumValue(el.name);
                return sum + (actualDelta > 0 ? (el.value - elFloor) : (30 - el.value));
            }, 0);

            contributors.forEach(el => {
                const elFloor = getMinimumValue(el.name);
                const capacity = actualDelta > 0 ? (el.value - elFloor) : (30 - el.value);
                const weight = capacity / (sumForWeight || 1);
                el.value -= actualDelta * weight;
                
                // Sécurité anti-débordement par micro-arrondi
                el.value = Math.max(elFloor, Math.min(30, el.value));
            });

            // 6. Mise à jour de l'axe traîné
            d.value += actualDelta;
            d.value = Math.max(myFloor, Math.min(30, d.value));

            updateGraph();
        });

    svg.selectAll(".handle")
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
}

function getMinimumValue(name) {
    return (name === 'PA' || name === 'PM' || name === 'Vitalité') ? 1 : 0;
}

export function updateGraph() {
    d3.select(".membrane-input").attr("d", lineGen);
    svg.selectAll(".handle")
        .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (d.value / 30) * radius)
        .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (d.value / 30) * radius);

    data.forEach((d, i) => {
        const input = document.getElementById(`input-val-${i}`);
        if (input) {
            input.value = Math.round(d.value);
            input.style.borderColor = d.locked ? "#ff4444" : "#333";
        }
    });
}

function applyManualValue(index, newValue) {
    const d = data[index];
    if (d.locked) return updateGraph(); 
    const floor = getMinimumValue(d.name);
    newValue = Math.max(floor, Math.min(30, newValue));
    let delta = newValue - d.value;
    let otherEligibleAxes = data.filter((el, idx) => idx !== index && !el.locked);
    let otherValuesSum = otherEligibleAxes.reduce((sum, el) => sum + el.value, 0);

    if (otherEligibleAxes.length > 0 && (otherValuesSum > 0 || delta < 0)) {
        let canRedistribute = true;
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
                el.value = Math.max(elFloor, Math.min(20, el.value - reduction));
            });
            d.value = newValue;
        }
    }
    updateGraph();
}

export function updateSelectionMembrane(repartitionAxes, scoreTotal) {
    if (!repartitionAxes) return;
    const updatedData = axesOrder.map(axisName => {
        const points = repartitionAxes[axisName] || 0;
        const percentage = scoreTotal > 0 ? (points / scoreTotal) * 100 : 0;
        return { value: percentage };
    });

    const lineGenSelection = d3.lineRadial()
        .angle((d, i) => i * angleStep)
        .radius(d => (d.value / 100) * radius) // Gardé en / 100 pour le stuff
        .curve(d3.curveCardinalClosed.tension(0));

    d3.select(".membrane-selection")
        .datum(updatedData)
        .transition()
        .duration(600)
        .ease(d3.easeBackOut)
        .attr("d", lineGenSelection);
}