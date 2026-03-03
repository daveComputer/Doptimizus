export async function saveConfig(config) {
    const response = await fetch('/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
    });
    return response.ok;
}

export async function excludeItem(itemName) {
    return fetch('/exclude-item', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_nom: itemName })
    });
}