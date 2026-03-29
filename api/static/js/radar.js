// radar.js

let svg, lineGen, angleStep, radius, axesOrder, data;
const width = 600, height = 600, margin = 150;
let currentMode="individual"

const GROUPS = [
    { name: "Attaque", angle: 0, color: "#FF4500", axes: ["Caractéristique(s) principale(s)","Dommages Poussée", "Critique"] },
    { name: "Défense", angle: 90,color: "#1E90FF", axes: ["Résistances","Vitalité"] },
    { name: "Adaptabilité", angle: 180, color: "#32CD32",axes: ["PA","PO", "PM", "Invocations"] },
    { name: "Situationnel", angle: 270,color: "#FFD700", axes: ["Tacle","Soins", "Fuite", "Retrait PA", "Retrait PM","Initiative"] }];

export function initRadar(containerId, initialData) {
    data = initialData;
    radius = Math.min(width, height) / 2 - margin;
    angleStep = (Math.PI * 2) / data.length;
    data.forEach(d => d.locked = d.locked || false);
    axesOrder = data.map(d => d.name);
    d3.select(containerId).selectAll("*").remove(); 
    d3.selectAll(".radar-tooltip").remove();

    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "radar-tooltip");

    svg = d3.select(containerId).html("")
        .append("svg")
        // viewBox = "min-x min-y largeur hauteur"
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")  // Le SVG prend toute la largeur de son parent
        .style("height", "auto") // La hauteur s'adapte proportionnellement
        .append("g")
        .attr("transform", `translate(${width/2}, ${height/2})`);

    const clickZones = svg.append("g").attr("class", "click-zones-layer");

    // --- 1. ANNEAU INDIVIDUEL (Interne : r à r+100) ---
    const individualRing = d3.arc()
        .innerRadius(radius+40)
        .outerRadius(radius + 100)
        .startAngle(0)
        .endAngle(Math.PI * 2);

    clickZones.append("path")
        .attr("d", individualRing)
        .attr("class", "global-zone-individual")
        .style("fill", "transparent")
        .style("cursor", "pointer")
        .on("click", () => toggleMode("individual"))
        .on("mouseover", function() {
            tooltip.style("opacity", 1)
                .html(`<span class="tooltip-title">Mode individuel</span>`);
            })
        .on("mousemove", (event) => {
            tooltip.style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px");
        })
        .on("mouseout", () => tooltip.style("opacity", 0))
        .style("pointer-events", "all");

    // --- 2. ANNEAU GROUPE (Externe : r+100 à r+200) ---
    const groupRing = d3.arc()
        .innerRadius(radius + 100)
        .outerRadius(radius + 160)
        .startAngle(0)
        .endAngle(Math.PI * 2);

    clickZones.append("path")
        .attr("d", groupRing)
        .attr("class", "global-zone-group")
        .style("fill", "transparent")
        .style("cursor", "pointer")
        .on("click", () => toggleMode("group"))
        .on("mouseover", function() {
            tooltip.style("opacity", 1)
                .html(`<span class="tooltip-title" >Mode groupé</span>`);
            })
        .on("mousemove", (event) => {
            tooltip.style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px");
        })
        .on("mouseout", () => tooltip.style("opacity", 0))
        .style("pointer-events", "all");


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
        const labelContainers = svg.selectAll(".axis-label-container")
            .data(data)
            .enter()
            .append("foreignObject")
            .attr("class", "axis-label-container")
            // On centre le foreignObject : coordonnée - (largeur/2)
            .attr("x", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * labelRadius - foWidth / 2)
            .attr("y", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * labelRadius - foHeight / 2)
            .attr("width", foWidth)
            .attr("height", foHeight)
            .style("overflow", "visible")
            .style("pointer-events", "all"); // Important pour les interactions

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

                <div style="display: flex; align-items: center; justify-content: center; gap: 2px;">
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
                            appearance: none;
                            -moz-appearance: textfield;
                        ">
                    <span style="color: #8b949e; font-size: 10px; font-weight: bold;">%</span>
                </div>

                <div id="selection-val-${i}" 
                    style="color: #00ffc8; font-size: 9px; font-weight: bold; margin-top: 2px; opacity: 0; transition: opacity 0.3s ease;">
                    0%
                </div>
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

    const anglePerAxis = (24 * Math.PI) / 180; // 24 degrés en radians
    let currentAxisIndex = 0;
    // Configuration des distances
    const groupLabelRadius = radius + 120; 
    const braceRadius = radius + 100; // L'accolade est entre l'axe et le titre

    const groupContainer = svg.append("g").attr("class", "groups-layer");
    const foWidth = 60;  // Zone plus étroite
    const foHeight = 20; // Zone plus basse

    GROUPS.forEach(group => {
        // 1. Position du texte (Conversion degrés -> radians)
        // On retire 90° car en SVG/D3 le 0 est souvent à droite, on le veut en haut
        const angleRad = (group.angle - 90) * (Math.PI / 180);
        const x = groupLabelRadius * Math.cos(angleRad);
        const y = groupLabelRadius * Math.sin(angleRad);
        const startIndex = currentAxisIndex;
        const endIndex = currentAxisIndex + group.axes.length - 1;
        const startAngle = startIndex * anglePerAxis - 0.15;
        const endAngle = endIndex * anglePerAxis + 0.15;

        svg.append("line")
            .attr("class", "group-axis-line")   
            .attr("x1", 0).attr("y1", 0)
            .attr("x2", x/groupLabelRadius*(radius+90)).attr("y2", y/groupLabelRadius*(radius+90))
            .attr("stroke", "#333")
            .style("opacity", 0);

        // 2. Affichage du titre du groupe
        const textElement =groupContainer.append("text")
            .attr("x", x)
            .attr("y", y)
            .attr("class", "group-label-text")
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "middle")
            .text(group.name.toUpperCase())
            .style("fill", group.color)
            .style("font-weight", "bold")
            .style("letter-spacing", "2px")
            .style("font-size", "14px")
            .style("text-shadow", `0 0 10px ${group.color}66`);

        if (group.angle === 90 || group.angle === 270) {
            // On tourne le texte de 90° (ou -90°) autour de son propre point (x, y)
            const rotation = (group.angle === 90) ? 90 : -90;
            textElement.attr("transform", `rotate(${rotation}, ${x}, ${y})`);
        }

        // 3. Dessin de l'accolade (Arc stylisé)
        // On calcule l'angle de début et de fin basé sur les axes contenus
        // Pour simplifier, on fait un arc de 60 degrés centré sur l'angle du groupe
        currentAxisIndex += group.axes.length;

        // 2. Dessin de l'accolade (Arc de cercle)
        const arcGenerator = d3.arc()
            .innerRadius(braceRadius)
            .outerRadius(braceRadius + 4)
            .startAngle(startAngle)
            .endAngle(endAngle)
            .cornerRadius(2);

        groupContainer.append("path")
            .attr("d", arcGenerator)
            .attr("fill", `${group.color}20`) // Un fond transparent (Hexa + Opacité 20%)
            .attr("stroke", group.color) // La couleur du groupe
            .attr("stroke-width", 1.5)
            .attr("class", "group-brace")
            .style("filter", `drop-shadow(0 0 5px ${group.color})`);
    });

    

    // --- CALCUL DES DONNÉES DE GROUPE ---
    const groupData = GROUPS.map(g => {
        // Correction : On cherche l'objet dans le tableau 'data' par son nom
        const totalValue = g.axes.reduce((sum, axisName) => {
            const axisObj = data.find(d => d.name === axisName);
            console.log(axisObj)
            return sum + (axisObj ? axisObj.value : 0);
        }, 0);

        return {
            name: g.name,
            angleDeg: g.angle, // 0, 90, 180, 270
            angleRad: (g.angle - 90) * (Math.PI / 180), // Système D3
            value: totalValue,
            color: g.color
        };
    });



    const labelDistance = groupLabelRadius + 10; // Distance radiale
    const angularOffset = Math.PI / 10; // Ton décalage pour ne pas être sur le texte

    // --- CRÉATION DES CONTAINERS GLOBAUX ---
    const globalLabels = svg.selectAll(".global-label-container")
        .data(groupData)
        .enter()
        .append("foreignObject")
        .attr("class", "global-label-container")
        .attr("width", foWidth)
        .attr("height", foHeight)
        .style("overflow", "visible")
        .style("opacity", 0) // Caché par défaut (géré par toggleMode)
        .style("pointer-events", "all")
        .each(function(d) {
            // 1. Calcul du CENTRE exact où l'input doit être
            const cx = Math.cos(d.angleRad + angularOffset) * labelDistance;
            const cy = Math.sin(d.angleRad + angularOffset) * labelDistance;

            // 2. Positionnement du foreignObject (on centre le rectangle sur cx, cy)
            d3.select(this)
                .attr("x", cx - foWidth / 2)
                .attr("y", cy - foHeight / 2);

            // 3. Application de la rotation autour de ce MEME centre cx, cy
            if (d.angleDeg === 90 || d.angleDeg === 270) {
                const rotation = (d.angleDeg === 90) ? 90 : -90;
                d3.select(this)
                    .attr("transform", `rotate(${rotation}, ${cx}, ${cy})`);
            }
        });

    globalLabels.append("xhtml:div")
        .style("display", "flex")
        .style("flex-direction", "column")
        .style("align-items", "center")
        .style("width", "100%")
        .html((d, i) => `
            <div style="display: flex; align-items: center; gap: 2px;">
                <input type="number" 
                    id="global-input-val-${i}" 
                    value="${Math.round(d.value)}" 
                    style="
                        width: 32px; 
                        background: rgba(255, 0, 60, 0.1); 
                        color: #FF003C; 
                        border: 1px solid #FF003C; 
                        border-radius: 2px; 
                        text-align: center; 
                        font-size: 11px;
                        font-weight: bold;
                        outline: none;
                    ">
                <span style="color: #FF003C; font-size: 10px; font-weight: bold;">%</span>
            </div>
        `)

        

    // --- ÉCOUTEUR SUR LES INPUTS GLOBAUX ---
    GROUPS.forEach((group, i) => {
        d3.select(`#global-input-val-${i}`).on("change", function() {
            let newValue = parseFloat(this.value);
            if (isNaN(newValue)) newValue = 0;

            // On appelle la fonction de redistribution macro
            applyMacroValue(i, newValue);
        });
    });

    // Fermeture de la boucle pour le tracé
    groupData.push(groupData[0]);

    // --- GÉNÉRATEUR DE LIGNE (SCALING CORRIGÉ) ---
    const groupLine = d3.lineRadial()
        // Ici, on divise par 120 (somme max théorique de 4 axes à 30%) 
        // et on multiplie par 'radius' pour être à la bonne échelle SVG
        .radius(d => (d.value / 100) * radius) 
        .angle(d => d.angleDeg * (Math.PI / 180)) 
        .curve(d3.curveCardinalClosed.tension(0.3));

    const groupMembraneLayer = svg.append("g").attr("class", "group-membrane-layer");

    groupMembraneLayer.append("path")
    .datum(groupData)
    .attr("class", "group-membrane background-mode")
    .attr("d", groupLine)
    // Style Rouge Néon
    .attr("fill", "rgba(255, 0, 60, 0.15)") // Fond rouge translucide
    .attr("stroke", "#FF003C")              // Rouge vif
    .attr("stroke-width", 2.5)
    
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
        })
        .append("title")
        .text(d => d.locked ? "Débloquer cet axe" : "Bloquer cet axe");

    const groupLockButtons = svg.selectAll(".group-lock-btn")
        .data(GROUPS)
        .enter()
        .append("circle")
        .attr("class", "group-lock-btn")
        .attr("r", 5) // Légèrement plus grand que les individuels
        .attr("cx", d => {
            // Angle du titre + 10 degrés (on retire 90 pour la synchro D3)
            const angle = (d.angle + 25 - 90) * (Math.PI / 180);
            return Math.cos(angle) * (radius + 130);
        })
        .attr("cy", d => {
            const angle = (d.angle + 25 - 90) * (Math.PI / 180);
            return Math.sin(angle) * (radius + 130);
        })
        .attr("fill", "#555")
        .attr("stroke", d => d.color) // Bordure de la couleur du groupe
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("click", function(event, g) {
            // 1. Déterminer le nouvel état (si l'un des axes est déverrouillé, on verrouille tout)
            const axesDuGroupe = data.filter(a => g.axes.includes(a.name));
            const estDejaVerrouille = axesDuGroupe.every(a => a.locked);
            const nouvelEtat = !estDejaVerrouille;

            // 2. Appliquer l'état à tous les axes du groupe
            axesDuGroupe.forEach(a => a.locked = nouvelEtat);

            // 3. Mise à jour visuelle du bouton de groupe
            d3.select(this).attr("fill", nouvelEtat ? "#ff4444" : "#555");

            // 4. Synchronisation : Mise à jour des petits cadenas individuels
            svg.selectAll(".lock-btn")
                .attr("fill", d => d.locked ? "#ff4444" : "#555");
                
        })
        .style("opacity", 0);

    groupLockButtons.append("title")
        .text(d => `Verrouiller/Déverrouiller le groupe ${d.name}`);


    const dragIndividual = d3.drag()
        .on("drag", function(event, d) {
            if (d.locked) return;
            const i = data.indexOf(d);
            const angle = i * angleStep - Math.PI / 2;
            const proj = event.x * Math.cos(angle) + event.y * Math.sin(angle);
            const target = Math.min(30, Math.max(getMinimumValue(d.name), (proj / radius) * 30));
            
            moveAxis(i, target - d.value);
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
        .call(dragIndividual);
}

function getMinimumValue(name) {
    return (name === 'PA' || name === 'PM' || name === 'Vitalité') ? 1 : 0;
}

export function updateGraph() {

    // 1. Mise à jour de la membrane principale (les 15 axes individuels)
    d3.select(".membrane-input").attr("d", lineGen);
    d3.select(".membrane-input").interrupt();
    d3.select(".group-membrane").interrupt();

    // 2. Mise à jour des poignées (handles)
    svg.selectAll(".handle")
        .attr("cx", (d, i) => Math.cos(i * angleStep - Math.PI / 2) * (d.value / 30) * radius)
        .attr("cy", (d, i) => Math.sin(i * angleStep - Math.PI / 2) * (d.value / 30) * radius);

    // --- NOUVEAU : Mise à jour de la membrane de GROUPE ---
    
    // Dans updateGraph()
    const groupPoints = GROUPS.map((g,i) => {
        const somme = g.axes.reduce((sum, axisName) => {
            const axisObj = data.find(d => d.name === axisName); // Correction ici aussi
            return sum + (axisObj ? axisObj.value : 0);
        }, 0);
        const globalInput = document.getElementById(`global-input-val-${i}`);
        if (globalInput) {
            globalInput.value = Math.round(somme);
        }
        return { angle: (g.angle * Math.PI / 180), value: somme };
    });
    groupPoints.push(groupPoints[0]);


    // Générateur spécifique pour la membrane de groupe
    // Note : on divise par un facteur (ex: 5) pour que la somme ne sorte pas du cadre
    const groupLineGen = d3.lineRadial()
        .radius(d => (d.value / 100) * radius) // Ajuste le '120' selon l'échelle souhaitée
        .angle(d => d.angle)
        .curve(d3.curveCardinalClosed.tension(0.3));

    d3.select(".group-membrane").attr("d", groupLineGen(groupPoints));

    // --- FIN NOUVEAU ---

    // 3. Mise à jour des inputs numériques et des bordures de verrouillage
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
    const updatedData = axesOrder.map((axisName, i) => {
        const points = repartitionAxes[axisName] || 0;
        const percentage = scoreTotal > 0 ? (points / scoreTotal) * 100 : 0;
        const textElement = document.getElementById(`selection-val-${i}`);
        if (textElement) {
            textElement.innerText = Math.round(percentage) + "%";
            textElement.style.opacity = "1"; // On affiche le texte
        }
        return { value: Math.max(0, Math.min(30, percentage)) };
    });

    const lineGenSelection = d3.lineRadial()
        .angle((d, i) => i * angleStep)
        .radius(d => (d.value / 30) * radius)
        .curve(d3.curveCardinalClosed.tension(0));

    d3.select(".membrane-selection")
        .datum(updatedData)
        .transition()
        .duration(600)
        .ease(d3.easeBackOut)
        .attr("d", lineGenSelection);
}

function toggleMode(mode) {
    if (currentMode === mode) return;
    currentMode = mode;

    if (mode === "group") {
        // Activation visuelle Membrane Rouge
        d3.select(".group-membrane")
            .interrupt()
            .classed("background-mode", false)
            .classed("active-mode", true);
        
        d3.select(".membrane-input").style("opacity", 0.2);
        switchToGroupHandles(); 
    } else {
        // Activation visuelle Membrane Verte
        d3.select(".group-membrane")
            .interrupt()
            .classed("background-mode", true)
            .classed("active-mode", false);
            
        d3.select(".membrane-input").style("opacity", 1);
        switchToIndividualHandles(); 
    }

    svg.selectAll(".group-lock-btn")
        .transition().duration(300)
        .style("opacity", mode === "group" ? 1 : 0)
        .style("pointer-events", mode === "group" ? "all" : "none");

    svg.selectAll(".lock-btn")
        .transition().duration(300)
        .style("opacity", mode === "group" ? 0 : 1)
        .style("pointer-events", mode === "group" ? "none" : "all");

    svg.selectAll(".axis-label-container")
        .transition().duration(300)
        .style("opacity", mode === "group" ? 0 : 1)
        .style("pointer-events", mode === "group" ? "none" : "all");

    svg.selectAll("line")
        .transition().duration(300)
        .style("opacity", mode === "group" ? 0 : 1)

    svg.selectAll(".group-axis-line")
        .transition()
        .duration(300)
        .style("opacity", mode === "group" ? 1 : 0);

    svg.selectAll(".global-label-container")
        .transition()
        .duration(300)
        .style("opacity", mode === "group" ? 1 : 0)
        .style("pointer-events", mode === "group" ? "all" : "none");
}

function switchToGroupHandles() {
    // 1. On recalcule les sommes pour les 4 handles rouges
    const groupHandlesData = GROUPS.map(g => {
        const somme = g.axes.reduce((s, name) => s + (data.find(d => d.name === name).value), 0);
        return { group: g, value: somme };
    });

    const handles = svg.selectAll(".handle").data(groupHandlesData);
    handles.exit().remove();

    const groupDrag = d3.drag()
        .on("drag", function(event, d) {
            const angleRad = (d.group.angle - 90) * Math.PI / 180;
            let proj = event.x * Math.cos(angleRad) + event.y * Math.sin(angleRad);
            let targetGroupValue = Math.min(100, Math.max(0, (proj / radius) * 100));
            let totalRequestedDelta = targetGroupValue - d.value;

            if (Math.abs(totalRequestedDelta) < 0.05) return;

            // --- SÉCURITÉ : "TOUT OU RIEN" ---
            const groupAxes = data.filter(a => d.group.axes.includes(a.name));
            const groupSum = groupAxes.reduce((s, a) => s + a.value, 0) || 1;

            let isPossible = true;
            groupAxes.forEach(a => {
                if (a.locked) isPossible = false;
                const weight = a.value / groupSum;
                const individualDelta = totalRequestedDelta * weight;
                const nextVal = a.value + individualDelta;
                
                // Si un membre dépasse ses bornes (0-30), on bloque tout le groupe
                if (nextVal < getMinimumValue(a.name) || nextVal > 30) isPossible = false;
            });

        if (!isPossible) return; // Bloquage total si un élément coince

        // --- EXÉCUTION : On appelle les drags individuels ---
        groupAxes.forEach(a => {
            const weight = a.value / groupSum;
            const individualDelta = totalRequestedDelta * weight;
            
            // On appelle notre fonction atomique
            moveAxis(data.indexOf(a), individualDelta);
        });

        updateGraph();
        updateGroupHandlesPositions();
    });

    // 2. Mise à jour visuelle des handles
    handles.enter().append("circle").attr("class", "handle")
        .merge(handles)
        .transition().duration(500)
        .attr("r", 4)
        .attr("fill", "#FF003C")
        .style("filter", "drop-shadow(0 0 5px #FF003C)")
        .attr("cx", d => Math.cos((d.group.angle - 90) * Math.PI / 180) * (d.value / 100) * radius)
        .attr("cy", d => Math.sin((d.group.angle - 90) * Math.PI / 180) * (d.value / 100) * radius);

    svg.selectAll(".handle").call(groupDrag);
}

// Dans le gestionnaire de drag pour le mode groupe :
function dragGroup(event, d) {
    const angle = (d.group.angle - 90) * Math.PI / 180;
    let projected = event.x * Math.cos(angle) + event.y * Math.sin(angle);
    let newTotal = Math.min(100, Math.max(0, (projected / radius) * 100));
    
    let oldTotal = d.value;
    let ratio = newTotal / (oldTotal || 1);

    // On applique le ratio à chaque axe du groupe
    d.group.axes.forEach(axisName => {
        let axis = data.find(a => a.name === axisName);
        axis.value = Math.min(30, axis.value * ratio);
    });

    updateGraph();
}

function updateGroupHandlesPositions() {
    svg.selectAll(".handle").each(function(d) {
        // On recalcule la somme actuelle pour chaque groupe
        const currentSum = d.group.axes.reduce((s, name) => s + (data.find(a => a.name === name).value), 0);
        d.value = currentSum; // On synchronise l'objet data du handle
        
        d3.select(this)
            .attr("cx", Math.cos((d.group.angle - 90) * Math.PI / 180) * (currentSum / 100) * radius)
            .attr("cy", Math.sin((d.group.angle - 90) * Math.PI / 180) * (currentSum / 100) * radius);
    });
}

export function switchToIndividualHandles() {
    // 1. On lie à nouveau les handles aux 15 axes individuels (le tableau 'data')
    const handles = svg.selectAll(".handle")
        .data(data, d => d.name); // Utiliser le nom comme clé pour une transition propre

    // 2. Suppression des handles de groupe en trop (si nécessaire)
    handles.exit().remove();

    // 3. Création/Mise à jour des 15 handles
    const newHandles = handles.enter()
        .append("circle")
        .attr("class", "handle")
        .style("cursor", "pointer");

    newHandles.merge(handles)
        .interrupt() // On stoppe les animations en cours
        .transition()
        .duration(500)
        .ease(d3.easeCubicOut)
        .attr("r", 4)
        .attr("fill", "#00ffc8") // Retour au cyan d'origine
        .style("filter", "none") // On enlève le glow rouge
        .attr("cx", (d, i) => {
            const angle = i * angleStep - Math.PI / 2;
            return Math.cos(angle) * (d.value / 30) * radius;
        })
        .attr("cy", (d, i) => {
            const angle = i * angleStep - Math.PI / 2;
            return Math.sin(angle) * (d.value / 30) * radius;
        });

    const dragIndividual = d3.drag()
        .on("drag", function(event, d) {
            if (d.locked) return;
            const i = data.indexOf(d);
            const angle = i * angleStep - Math.PI / 2;
            const proj = event.x * Math.cos(angle) + event.y * Math.sin(angle);
            const target = Math.min(30, Math.max(getMinimumValue(d.name), (proj / radius) * 30));
            
            moveAxis(i, target - d.value);
            updateGraph();
        });
    
    // 4. On réattache le comportement de drag individuel
    // (Assure-toi que la variable 'drag' de ton initRadar est accessible ou redéfinie ici)
    svg.selectAll(".handle").call(dragIndividual);

    // 5. On rafraîchit le graphe pour s'assurer que tout est synchro
    updateGraph();
}

// Fonction "Atomique" : Déplace un axe et redistribue sur les autres
function moveAxis(axisIndex, requestedDelta) {
    const d = data[axisIndex];
    const myFloor = getMinimumValue(d.name);
    
    // 1. Identifier les contributeurs (les autres axes non verrouillés)
    let others = data.filter((el, idx) => idx !== axisIndex && !el.locked);
    let contributors = others.filter(el => {
        const elFloor = getMinimumValue(el.name);
        return requestedDelta > 0 ? el.value > elFloor : el.value < 30;
    });

    if (contributors.length === 0) return 0; // Rien ne peut bouger

    // 2. Calculer la capacité réelle de redistribution
    let totalCapacity = 0;
    contributors.forEach(el => {
        const elFloor = getMinimumValue(el.name);
        totalCapacity += requestedDelta > 0 ? (el.value - elFloor) : (30 - el.value);
    });

    // On s'adapte à la capacité maximale si le delta est trop grand
    let finalDelta = Math.abs(requestedDelta) > totalCapacity 
                     ? (requestedDelta > 0 ? totalCapacity : -totalCapacity) 
                     : requestedDelta;

    // 3. Appliquer la redistribution proportionnelle
    let sumForWeight = contributors.reduce((sum, el) => sum + el.value, 0);
    contributors.forEach(el => {
        const weight = el.value / (sumForWeight || 1);
        el.value -= finalDelta * weight;
        el.value = Math.max(getMinimumValue(el.name), Math.min(30, el.value));
    });

    // 4. Mettre à jour l'axe principal
    d.value += finalDelta;
    d.value = Math.max(myFloor, Math.min(30, d.value));

    return finalDelta; // On renvoie ce qui a réellement été bougé
}

function applyMacroValue(groupIndex, newValue) {
    const group = GROUPS[groupIndex];
    
    // 1. Calcul de la somme actuelle du groupe
    const groupAxes = data.filter(a => group.axes.includes(a.name));
    const currentTotal = groupAxes.reduce((s, a) => s + a.value, 0) || 1;
    
    // 2. Calcul du Delta global souhaité
    let totalRequestedDelta = newValue - currentTotal;
    if (Math.abs(totalRequestedDelta) < 0.1) return;

    // 3. SÉCURITÉ : Vérifier si le mouvement est possible pour TOUS
    let isPossible = true;
    groupAxes.forEach(a => {
        if (a.locked) isPossible = false;
        const weight = a.value / currentTotal;
        const individualDelta = totalRequestedDelta * weight;
        const nextVal = a.value + individualDelta;

        // On check les bornes 0-30 de chaque membre
        if (nextVal < getMinimumValue(a.name) || nextVal > 30) {
            isPossible = false;
        }
    });

    // 4. EXÉCUTION : Si tout est OK, on applique
    if (isPossible) {
        groupAxes.forEach(a => {
            const weight = a.value / currentTotal;
            const individualDelta = totalRequestedDelta * weight;
            
            // On délègue à moveAxis pour gérer la redistribution sur les AUTRES groupes
            moveAxis(data.indexOf(a), individualDelta);
        });
    } else {
        console.warn("Mouvement macro bloqué : une limite individuelle a été atteinte.");
    }

    // 5. Toujours rafraîchir pour réinitialiser l'input si le mouvement a été bloqué
    updateGraph();
    updateGroupHandlesPositions();
}