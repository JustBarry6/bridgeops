function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

async function fetchTransfers() {
  const res = await fetch('/transfers');
  if (!res.ok) return;
  renderTransfers(await res.json());
}

async function fetchStats() {
  const res = await fetch('/dashboard/api/stats');
  if (!res.ok) return;
  renderStats(await res.json());
}

function statusLabel(status) {
  return { queued: 'En file', running: 'En cours', completed: 'Terminé', failed: 'Échoué' }[status] || status;
}

function renderTransfers(transfers) {
  const tbody = document.querySelector('#transfers-table tbody');
  tbody.innerHTML = '';
  transfers.forEach((t) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td class="mono">${t.id.slice(0, 8)}</td>
      <td>${escapeHtml(t.source)} &rarr; ${escapeHtml(t.destination)}</td>
      <td><span class="status-badge status-${t.status}"><span class="status-dot"></span>${statusLabel(t.status)}</span></td>
      <td class="mono">${t.retry_count}</td>
      <td class="mono">${new Date(t.created_at).toLocaleTimeString()}</td>
      <td><a href="/dashboard/transfers/${t.id}">Détails</a></td>
    `;
    tbody.appendChild(row);
  });
}

function renderStats(stats) {
  document.querySelector('#stat-today').textContent = stats.transfers_today;
  document.querySelector('#stat-running').textContent = stats.running;
  document.querySelector('#stat-completed').textContent = stats.completed;
  document.querySelector('#stat-failed').textContent = stats.failed;
  document.querySelector('#stat-duration').textContent =
    stats.avg_duration_seconds !== null ? `${stats.avg_duration_seconds}s` : '—';
}

document.querySelector('#new-transfer-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.target;
  const payload = {
    source: form.source.value,
    destination: form.destination.value,
    connection_id: form.connection_id.value || null,
  };
  const res = await fetch('/transfers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (res.ok) {
    form.reset();
    fetchTransfers();
    fetchStats();
  } else {
    alert('Erreur lors de la création du transfert.');
  }
});

fetchTransfers();
fetchStats();
setInterval(() => { fetchTransfers(); fetchStats(); }, 2500);