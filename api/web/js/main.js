// main.js
import { initialData } from './config.js';
import { initRadar } from './radar.js';
import { displayResults, showError, hideError } from './ui.js';
import { refreshBlacklistUI } from './blacklist.js';

document.addEventListener("DOMContentLoaded", function() {
    // 1. Initialisation du radar au chargement avec tes données de config
    initRadar("#chart", initialData);

    // 2. Initialisation de la blacklist
    refreshBlacklistUI();

    // 2. Gestion de l'écouteur sur le bouton d'export
    const btn = document.getElementById("export-btn");
    if (btn) {
        btn.addEventListener("click", exportToJson);
    }
});

/**
 * Calcule les scores et prépare les données pour l'export (Exactement ta logique)
 */
function getDesirabilityData() {
    const vitalite = initialData.find(d => d.name === 'Vitalité').value;
    
    // Protection contre division par zéro
    const vFactor = vitalite > 0 ? vitalite : 1; 
    const targetSum = 100 / vFactor;

    // Calcul des scores de désirabilité
    const results = initialData.map(d => ({
        caracteristique: d.name,
        pourcentage: d.value.toFixed(2),
        score_desirabilite: (d.value * (targetSum / 100)).toFixed(2) 
    }));

    return {
        timestamp: new Date().toISOString(),
        global_sum_score: targetSum.toFixed(2),
        details: results
    };
}

/**
 * Récupère la configuration globale (Exactement ton code)
 */
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

/**
 * Gère l'envoi au serveur et l'affichage des résultats (Exactement ton code)
 */
async function exportToJson(e) {
    if (e) e.preventDefault(); 

    const btn = document.getElementById("export-btn");
    const config = getGlobalConfig(); // On récupère la config complète

    // --- TA VALIDATION ---
    if (config.elements.length === 0) {
        showError("Veuillez sélectionner au moins un élément (Terre, Feu, Eau, Air) avant d'optimiser.");
        return; 
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
        
        // Affichage via le module UI
        displayResults(data, true);

    } catch (error) {
        console.error('Erreur:', error);
        showError("Une erreur est survenue : " + error.message);
    } finally {
        btn.disabled = false;
        btn.innerText = "Confirmer";
    }
}