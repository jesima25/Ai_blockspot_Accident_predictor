// dashboard.js — Chart.js analytics

const CHART_DEFAULTS = {
  color  : '#fff',
  grid   : '#2a2d3e',
  tooltip: { backgroundColor: '#1a1d2e', borderColor: '#2a2d3e', borderWidth: 1 }
};

async function loadDashboard() {
  try {
    const res  = await fetch('/api/stats');
    const data = await res.json();

    if (!data.success) return;

    // ── Stats cards
    document.getElementById('total-count').textContent =
      data.total_accidents.toLocaleString();
    document.getElementById('fatal-count').textContent =
      (data.severity['fatal'] || 0).toLocaleString();
    document.getElementById('major-count').textContent =
      (data.severity['major'] || 0).toLocaleString();
    document.getElementById('minor-count').textContent =
      (data.severity['minor'] || 0).toLocaleString();

    // ── City Chart
    const cities  = Object.keys(data.by_city);
    const cityVals= Object.values(data.by_city);
    new Chart(document.getElementById('cityChart'), {
      type: 'bar',
      data: {
        labels  : cities,
        datasets: [{
          label          : 'Accidents',
          data           : cityVals,
          backgroundColor: '#3498db',
          borderRadius   : 6
        }]
      },
      options: chartOptions('Number of Accidents')
    });

    // ── Severity Pie
    new Chart(document.getElementById('severityChart'), {
      type: 'doughnut',
      data: {
        labels  : ['Fatal', 'Major', 'Minor'],
        datasets: [{
          data           : [
            data.severity['fatal'] || 0,
            data.severity['major'] || 0,
            data.severity['minor'] || 0
          ],
          backgroundColor: ['#e74c3c', '#f39c12', '#2ecc71'],
          borderWidth    : 0
        }]
      },
      options: {
        plugins: {
          legend: { labels: { color: '#fff' } },
          tooltip: CHART_DEFAULTS.tooltip
        }
      }
    });

    // ── Weather Chart
    const weathers  = Object.keys(data.by_weather);
    const weatherVals = Object.values(data.by_weather);
    new Chart(document.getElementById('weatherChart'), {
      type: 'bar',
      data: {
        labels  : weathers,
        datasets: [{
          label          : 'Accidents',
          data           : weatherVals,
          backgroundColor: ['#3498db', '#9b59b6', '#1abc9c'],
          borderRadius   : 6
        }]
      },
      options: chartOptions('Number of Accidents')
    });

    // ── Road Type Chart
    const roads    = Object.keys(data.by_road);
    const roadVals = Object.values(data.by_road);
    new Chart(document.getElementById('roadChart'), {
      type: 'doughnut',
      data: {
        labels  : roads,
        datasets: [{
          data           : roadVals,
          backgroundColor: ['#e74c3c', '#f39c12', '#3498db'],
          borderWidth    : 0
        }]
      },
      options: {
        plugins: {
          legend: { labels: { color: '#fff' } },
          tooltip: CHART_DEFAULTS.tooltip
        }
      }
    });

    // ── Hour Chart
    const hours    = Object.keys(data.by_hour).map(Number).sort((a,b)=>a-b);
    const hourVals = hours.map(h => data.by_hour[String(h)] || 0);
    new Chart(document.getElementById('hourChart'), {
      type: 'line',
      data: {
        labels  : hours.map(h => h + ':00'),
        datasets: [{
          label          : 'Accidents per Hour',
          data           : hourVals,
          borderColor    : '#e74c3c',
          backgroundColor: 'rgba(231,76,60,0.1)',
          fill           : true,
          tension        : 0.4,
          pointRadius    : 4,
          pointBackgroundColor: '#e74c3c'
        }]
      },
      options: chartOptions('Number of Accidents')
    });

  } catch (err) {
    console.error('Dashboard error:', err);
  }
}

function chartOptions(yLabel) {
  return {
    responsive: true,
    plugins: {
      legend : { labels: { color: '#fff' } },
      tooltip: CHART_DEFAULTS.tooltip
    },
    scales: {
      x: {
        ticks: { color: '#aaa' },
        grid : { color: CHART_DEFAULTS.grid }
      },
      y: {
        ticks: { color: '#aaa' },
        grid : { color: CHART_DEFAULTS.grid },
        title: { display: true, text: yLabel, color: '#aaa' }
      }
    }
  };
}

window.onload = loadDashboard;