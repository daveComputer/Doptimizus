export function initTooltips() {
    // 1. Créer l'élément unique de tooltip s'il n'existe pas
    let tooltipEl = document.getElementById('global-tooltip');
    if (!tooltipEl) {
        tooltipEl = document.createElement('div');
        tooltipEl.id = 'global-tooltip';
        tooltipEl.className = 'custom-tooltip';
        document.body.appendChild(tooltipEl);
    }

    const icons = document.querySelectorAll('.info-icon');

    icons.forEach(icon => {
        icon.addEventListener('mouseenter', (e) => {
            const text = icon.getAttribute('data-tooltip');
            tooltipEl.innerHTML = text;
            tooltipEl.classList.add('visible');

            const iconRect = icon.getBoundingClientRect();
            const tooltipRect = tooltipEl.getBoundingClientRect();

            // --- CALCUL DE LA POSITION "SÉCURISÉE" ---
            
            // On tente de centrer par défaut
            let left = iconRect.left + (iconRect.width / 2) - (tooltipRect.width / 2);
            let top = iconRect.top - tooltipRect.height - 15;

            // Sécurité Bord GAUCHE (min 10px du bord)
            if (left < 10) left = 10;

            // Sécurité Bord DROIT (min 10px du bord)
            if (left + tooltipRect.width > window.innerWidth - 10) {
                left = window.innerWidth - tooltipRect.width - 10;
            }

            // Sécurité Bord HAUT (si pas de place en haut, on affiche en bas)
            if (top < 10) {
                top = iconRect.bottom + 15;
            }

            tooltipEl.style.left = `${left}px`;
            tooltipEl.style.top = `${top}px`;
        });

        icon.addEventListener('mouseleave', () => {
            tooltipEl.classList.remove('visible');
        });
    });
}