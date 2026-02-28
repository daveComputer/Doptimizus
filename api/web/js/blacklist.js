import { rehabilitateVisuals } from './ui.js';

/**
 * Charge la blacklist depuis le serveur et l'affiche
 */
export async function refreshBlacklistUI() {
    const container = document.getElementById("blacklist-container");
    if (!container) return;

    try {
        const response = await fetch('/get-blacklist');
        const items = await response.json();

        container.innerHTML = "";

        if (items.length === 0) {
            container.innerHTML = "<p style='color: #484f58;'>Aucun item dans la blacklist.</p>";
            return;
        }

        items.forEach(nom => {
            const tag = document.createElement("div");
            tag.className = "blacklist-tag";
            tag.innerHTML = `
                <span>${nom}</span>
                <button class="rehabilitate-btn" title="Réhabiliter cet item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6"></path><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                </button>
            `;

            tag.querySelector(".rehabilitate-btn").addEventListener("click", async () => {
                await rehabilitateItem(nom);
            });

            container.appendChild(tag);
        });
    } catch (error) {
        console.error("Erreur blacklist:", error);
    }
}

/**
 * Envoie la requête de réhabilitation au serveur
 */


async function rehabilitateItem(nom) {
    const response = await fetch('/rehabilitate-item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_nom: nom })
    });

    if (response.ok) {
        // 1. Rafraîchir la liste des tags en bas
        refreshBlacklistUI();
        
        // 2. SYNCHRONISATION : Nettoyer les stuffs en haut
        rehabilitateVisuals(nom);
    }
}