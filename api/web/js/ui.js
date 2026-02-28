// ui.js
import { updateSelectionMembrane } from './radar.js';
import { refreshBlacklistUI } from './blacklist.js';
/**
 * Affiche les résultats (Items par type et Stuffs optimisés)
 * @param {Object} data - Les données JSON reçues du serveur
 * @param {boolean} shouldScroll - Si vrai, scrolle vers la zone de résultats
 */
export function displayResults(data, shouldScroll = false) {
    // Vérification de sécurité
    if (!data || !data.top_items) {
        console.error("Données invalides reçues du serveur");
        return;
    }

    const blacklistSection = document.getElementById("blacklist-section");
    if (blacklistSection) {
        blacklistSection.classList.add("section-visible");
    }

    // Gestion de la visibilité des panneaux selon ta logique
    document.getElementById("left-panel").classList.add("panel-visible");
    document.getElementById("right-panel").classList.add("panel-visible");
    document.querySelector(".workspace-container").style.justifyContent = "space-between";

    const clearAllHighlights = () => {
        document.querySelectorAll('.item-card').forEach(c => {
            c.classList.remove('selected'); // On retire la classe partout
        });
    };

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
            
            // On ajoute le HTML de l'icône (SVG simple) + Contenu
            card.innerHTML = `
                <button class="delete-btn" title="Exclure cet item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
                <div class="item-card-content">
                    <span class="item-name">${itemName}</span>
                </div>
                <div class="item-score">${Math.round(scoreValue)} pts</div>
            `;
            
            itemsContainer.appendChild(card);

            // Listener : Sélection d'un item (Mise à jour membrane)
            card.addEventListener("click", () => {
                clearAllHighlights();
                card.classList.add('selected'); // On active le néon
                updateSelectionMembrane(item.repartition, item.score);
            });

            // Listener : Suppression (Blacklist)
            const bin = card.querySelector(".delete-btn");
            bin.addEventListener("click", async (e) => {
                e.stopPropagation(); // Empêche de cliquer sur la carte
                
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
                    markVisualsAsBanned(item.nom);
                    refreshBlacklistUI();
                }
            });
        });
    }

    // --- PARTIE 2 : TOP STUFFS (SOLUTIONS COMPLÈTES) ---
    const stuffsContainer = document.getElementById("top-stuffs-list");
    stuffsContainer.innerHTML = "";

    if (data.top_stuffs && data.top_stuffs.length > 0) {
        data.top_stuffs.forEach((solution, index) => {
            const itemsDetails = Array.isArray(solution) ? solution[0] : solution.stuff;
            const scoreTotal = Array.isArray(solution) ? solution[1] : solution.score;

            if (!itemsDetails) return;

            const stuffCard = document.createElement("div");
            stuffCard.className = "item-card stuff-card";
            
            // En-tête de la carte
            stuffCard.innerHTML = `
                <div class="item-card-content">
                    <span class="item-name">Composition Optimale #${index + 1}</span>
                    <span class="item-score-stuff">Total: ${Math.round(scoreTotal)} pts</span>
                </div>
                <div class="stuff-equipment-list"></div>
            `;

            const listContainer = stuffCard.querySelector(".stuff-equipment-list");

            // On crée un badge pour CHAQUE item du stuff
            itemsDetails.forEach(item => {
                                // Dans ta boucle itemsDetails.forEach(item => { ... }) pour les stuffs :

                const badge = document.createElement("div");
                badge.className = "equipment-badge";
                badge.innerHTML = `
                    <span>${item.nom}</span>
                    <button class="delete-mini-btn" title="Bannir cet item">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                `;

                // Événement sur le bouton (uniquement l'icône)
                badge.querySelector(".delete-mini-btn").addEventListener("click", async (e) => {
                    e.stopPropagation(); // Évite de sélectionner le stuff pour le radar

                    // 1. Appel au backend pour mettre à jour la blacklist
                    const response = await fetch('/exclude-item', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ item_nom: item.nom })
                    });

                    if (response.ok) {
                        // 2. On marque le container du STUFF en rouge
                        // stuffCard est défini plus haut dans ta fonction
                        stuffCard.classList.add('is-banned');
                        badge.classList.add('is-banned-item');
                        markVisualsAsBanned(item.nom);
                        refreshBlacklistUI();
                        
                        console.log(`${item.nom} a été banni. Le stuff #${index + 1} est marqué comme invalide.`);
                    }
                });

                listContainer.appendChild(badge);
            });

            stuffsContainer.appendChild(stuffCard);

            // Sélection du stuff pour le radar
            stuffCard.addEventListener("click", () => {
                document.querySelectorAll('.item-card').forEach(c => c.classList.remove('selected'));
                stuffCard.classList.add('selected');
                updateSelectionMembrane(solution.repartition_axes, solution.score);
            });
        });
    }

    // Scroll vers la zone de travail
    if (shouldScroll) {
        window.scrollTo({ top: document.querySelector(".workspace-container").offsetTop, behavior: 'smooth' });
    }
}

/**
 * Affiche un message d'erreur
 */
export function showError(message) {
    const container = document.getElementById("error-msg-container");
    const textSpan = document.getElementById("error-text");
    
    if (textSpan) textSpan.innerText = message;
    if (container) {
        container.style.display = "block";
        container.style.animation = "shake 0.5s";
        setTimeout(() => container.style.animation = "", 500);
    }
}

/**
 * Cache le message d'erreur
 */
export function hideError() {
    const container = document.getElementById("error-msg-container");
    if (container) container.style.display = "none";
}

export function rehabilitateVisuals(itemName) {
    // 1. On cherche tous les badges qui portent ce nom d'item
    const badges = document.querySelectorAll('.equipment-badge');
    
    badges.forEach(badge => {
        if (badge.querySelector('span').innerText === itemName) {
            // On remet le badge en normal
            badge.classList.remove('is-banned-item');
            badge.style.borderColor = ""; // Reset du style inline
            badge.style.color = "";
        }
    });

    // 2. On vérifie chaque stuff-card : doit-elle rester rouge ?
    const stuffCards = document.querySelectorAll('.stuff-card.is-banned');
    
    stuffCards.forEach(card => {
        // On compte s'il reste des badges bannis à l'intérieur de cette carte
        const remainingBanned = card.querySelectorAll('.is-banned-item').length;
        
        if (remainingBanned === 0) {
            // Plus aucun item banni dans ce stuff ? On enlève le contour rouge !
            card.classList.remove('is-banned');
        }
    });
}

export function markVisualsAsBanned(itemName) {
    // 1. GESTION DU PANNEAU GAUCHE (Items individuels)
    // On cherche la carte dans la liste de gauche et on la fait disparaître
    const itemCards = document.querySelectorAll('.item-card:not(.stuff-card)');
    itemCards.forEach(card => {
        const nameSpan = card.querySelector('.item-name');
        if (nameSpan && nameSpan.innerText === itemName) {
            card.style.opacity = "0";
            card.style.transform = "translateX(20px)";
            setTimeout(() => card.remove(), 300);
        }
    });

    // 2. GESTION DU PANNEAU DROIT (Badges dans les stuffs)
    const badges = document.querySelectorAll('.equipment-badge');
    badges.forEach(badge => {
        const span = badge.querySelector('span');
        if (span && span.innerText === itemName) {
            // On marque le badge en rouge
            badge.classList.add('is-banned-item');
            badge.style.borderColor = "#ff4444";
            badge.style.color = "#ff4444";
            
            // On remonte au parent (la stuff-card) pour la mettre en rouge aussi
            const parentStuffCard = badge.closest('.stuff-card');
            if (parentStuffCard) {
                parentStuffCard.classList.add('is-banned');
            }
        }
    });
}