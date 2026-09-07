// Dashboard JavaScript — Chart.js + Fetch polling
const COLORS = {
    'ws-prod-01': '#58a6ff',
    'ws-db-02':    '#3fb950',
    'ws-web-03':   '#d29922',
};
const LABELS = {
    'ws-prod-01': 'WS-PROD-01',
    'ws-db-02':    'WS-DB-02',
    'ws-web-03':   'WS-WEB-03',
};

let chartCpu, chartMemory, chartDisk;

function initCharts() {
    const commonOpts = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: { legend: { position: 'top', labels: { boxWidth: 12, padding: 8 } } },
        scales: {
            x: { display: true, grid: { color: '#21262d' }, ticks: { maxTicksLimit: 8, color: '#8b949e' } },
            y: { min: 0, max: 100, grid: { color: '#21262d' }, ticks: { color: '#8b949e' } }
        }
    };

    function makeChart(id, label) {
        const ctx = document.getElementById(id).getContext('2d');
        return new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [] },
            options: { ...commonOpts }
        });
    }

    chartCpu    = makeChart('chart-cpu',    'CPU');
    chartMemory = makeChart('chart-memory', 'Memory');
    chartDisk   = makeChart('chart-disk',   'Disk');
}

async function fetchJSON(url) {
    const resp = await fetch(url);
    return resp.json();
}

async function loadOverview() {
    const data = await fetchJSON('/api/overview');
    document.getElementById('kpi-online').textContent = data.servers_online;
    document.getElementById('kpi-total').textContent = data.servers_online + ' / ' + data.servers_total;
    const cpuEl = document.getElementById('kpi-cpu');
    cpuEl.textContent = data.cpu_avg + '%';
    cpuEl.className = 'mb-0 ' + (data.cpu_avg > 80 ? 'text-danger' : data.cpu_avg > 60 ? 'text-warning' : 'text-success');
    const memEl = document.getElementById('kpi-memory');
    memEl.textContent = data.memory_avg + '%';
    memEl.className = 'mb-0 ' + (data.memory_avg > 85 ? 'text-danger' : data.memory_avg > 70 ? 'text-warning' : 'text-success');
    const diskEl = document.getElementById('kpi-disk');
    diskEl.textContent = data.disk_alerts;
    diskEl.className = 'mb-0 ' + (data.disk_alerts > 0 ? 'text-danger' : 'text-success');
    const svcEl = document.getElementById('kpi-services');
    svcEl.textContent = data.services_down;
    svcEl.className = 'mb-0 ' + (data.services_down > 0 ? 'text-danger' : 'text-success');
    document.getElementById('kpi-alerts').textContent = data.recent_alerts;
    document.getElementById('last-update').textContent = 'Last updated: ' + new Date(data.timestamp).toLocaleTimeString();
}

async function loadCharts() {
    const servers = ['ws-prod-01', 'ws-db-02', 'ws-web-03'];
    const metrics = [
        { key: 'cpu',    chart: chartCpu },
        { key: 'memory', chart: chartMemory },
        { key: 'disk',   chart: chartDisk },
    ];

    for (const m of metrics) {
        const datasets = [];
        let labels = [];
        for (const sid of servers) {
            const data = await fetchJSON(`/api/servers/${sid}/${m.key}`);
            if (data.history.length > 0 && labels.length === 0) {
                labels = data.history.map(h => h.timestamp.split('T')[1].substring(0, 8));
            }
            datasets.push({
                label: LABELS[sid],
                data: data.history.map(h => h.value),
                borderColor: COLORS[sid],
                backgroundColor: COLORS[sid] + '20',
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
                fill: true,
            });
        }
        m.chart.data.labels = labels;
        m.chart.data.datasets = datasets;
        m.chart.update('none');
    }
}

async function loadTables() {
    const servers = ['ws-prod-01', 'ws-db-02', 'ws-web-03'];

    // Services
    let svcHtml = '';
    for (const sid of servers) {
        const data = await fetchJSON(`/api/servers/${sid}/services`);
        for (const s of (data.services || [])) {
            const cls = s.status === 'Running' ? 'status-running' : s.status === 'Stopped' ? 'status-stopped' : 'status-paused';
            svcHtml += `<tr><td>${LABELS[sid]}</td><td>${s.display_name.substring(0, 25)}</td><td class="${cls}">${s.status}</td></tr>`;
        }
    }
    document.getElementById('tbl-services').innerHTML = svcHtml;

    // Processes
    let procHtml = '';
    for (const sid of servers) {
        const data = await fetchJSON(`/api/servers/${sid}/processes`);
        for (const p of (data.processes || []).slice(0, 3)) {
            procHtml += `<tr><td>${LABELS[sid]}</td><td>${p.name}</td><td>${p.cpu_percent}%</td><td>${Math.round(p.memory_mb)}</td></tr>`;
        }
    }
    document.getElementById('tbl-processes').innerHTML = procHtml;

    // Alerts
    const alerts = await fetchJSON('/api/alerts?limit=20');
    let alertHtml = '';
    for (const a of alerts) {
        const cls = a.severity === 'critical' ? 'alert-critical' : 'alert-warning';
        const ts = a.timestamp.split('T')[1].substring(0, 8);
        alertHtml += `<tr class="${cls}"><td>${ts}</td><td>${LABELS[a.server_id] || a.server_id}</td><td>${a.message.substring(0, 50)}</td></tr>`;
    }
    document.getElementById('tbl-alerts').innerHTML = alertHtml;
}

async function refreshAll() {
    const btn = document.getElementById('btn-refresh');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Loading...';
    try {
        await Promise.all([loadOverview(), loadCharts(), loadTables()]);
    } catch (e) {
        console.error('Refresh failed:', e);
    }
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    refreshAll();
    setInterval(refreshAll, 15000);
});

// Updated: 2026-09-07
