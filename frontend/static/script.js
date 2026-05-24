// script.js
// Purpose: Handle prediction, weather, PDF, sound, voice, explainability

// Store last prediction result
let lastResult = null;

// ─────────────────────────────────────
// 1. PLAY GENTLE ALERT SOUND
// ─────────────────────────────────────
function playSound(type) {
    var audio = new AudioContext();

    if (type === 'fatal') {
        // Soft 3-note melody - gentle but noticeable
        var notes = [523, 659, 784]; // C, E, G - pleasant chord
        notes.forEach(function(freq, i) {
            var osc  = audio.createOscillator();
            var gain = audio.createGain();
            osc.connect(gain);
            gain.connect(audio.destination);
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0, audio.currentTime + i * 0.25);
            gain.gain.linearRampToValueAtTime(0.8, audio.currentTime + i * 0.25 + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + i * 0.25 + 0.4);
            osc.start(audio.currentTime + i * 0.25);
            osc.stop(audio.currentTime + i * 0.25 + 0.4);
        });

    } else if (type === 'major') {
        // 2 soft notes - gentle warning
        var notes2 = [523, 659];
        notes2.forEach(function(freq, i) {
            var osc  = audio.createOscillator();
            var gain = audio.createGain();
            osc.connect(gain);
            gain.connect(audio.destination);
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0, audio.currentTime + i * 0.25);
            gain.gain.linearRampToValueAtTime(0.7, audio.currentTime + i * 0.25 + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + i * 0.25 + 0.35);
            osc.start(audio.currentTime + i * 0.25);
            osc.stop(audio.currentTime + i * 0.25 + 0.35);
        });

    } else {
        // Single soft ding for safe
        var osc  = audio.createOscillator();
        var gain = audio.createGain();
        osc.connect(gain);
        gain.connect(audio.destination);
        osc.type = 'sine';
        osc.frequency.value = 523;
        gain.gain.setValueAtTime(0, audio.currentTime);
        gain.gain.linearRampToValueAtTime(0.6, audio.currentTime + 0.05);
        gain.gain.exponentialRampToValueAtTime(0.01, audio.currentTime + 0.5);
        osc.start(audio.currentTime);
        osc.stop(audio.currentTime + 0.5);
    }
}

// ─────────────────────────────────────
// 2. SPEAK ALERT (Voice)
// ─────────────────────────────────────
function speakAlert(type, city, percent) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();

    var message = '';
    if (type === 'fatal') {
        message = 'Warning. Fatal accident risk detected in ' + city +
                  '. Risk is ' + percent + ' percent. Please avoid this route.';
    } else if (type === 'major') {
        message = 'Caution. High accident risk in ' + city +
                  '. Risk is ' + percent + ' percent. Please drive carefully.';
    } else {
        message = 'Road is safe in ' + city +
                  '. Risk is ' + percent + ' percent. Have a safe journey.';
    }

    var speech    = new SpeechSynthesisUtterance(message);
    speech.lang   = 'en-IN';
    speech.rate   = 0.85;
    speech.volume = 0.8;
    speech.pitch  = 1.0;
    window.speechSynthesis.speak(speech);
}

// ─────────────────────────────────────
// 3. GENTLE FLASH SCREEN
// ─────────────────────────────────────
function flashScreen(color) {
    var overlay            = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top      = '0';
    overlay.style.left     = '0';
    overlay.style.width    = '100%';
    overlay.style.height   = '100%';
    overlay.style.background  = color;
    overlay.style.opacity     = '0.15';
    overlay.style.zIndex      = '9999';
    overlay.style.pointerEvents = 'none';
    overlay.style.transition  = 'opacity 0.5s';
    document.body.appendChild(overlay);
    setTimeout(function() { overlay.style.opacity = '0'; }, 300);
    setTimeout(function() { overlay.remove(); }, 800);
}

// ─────────────────────────────────────
// 4. AI EXPLAINABILITY
// ─────────────────────────────────────
function explainRisk(data) {
    var reasons = [];
    var weather = data.inputs.weather;
    var hour    = data.inputs.hour;
    var traffic = data.inputs.traffic_density;
    var vis     = data.inputs.visibility;
    var road    = data.inputs.road_type;
    var percent = data.risk_percentage;

    if (weather === 'rain')
        reasons.push('🌧 Rain reduced road visibility and grip');
    if (weather === 'fog')
        reasons.push('🌫 Fog critically reduced visibility');
    if (weather === 'clear' && percent < 40)
        reasons.push('☀ Clear weather kept risk low');
    if (hour >= 22 || hour <= 5)
        reasons.push('🌙 Night time — risk increased by 1.4x');
    if (hour >= 8 && hour <= 10)
        reasons.push('🕗 Morning peak hour — high congestion');
    if (hour >= 17 && hour <= 20)
        reasons.push('🕔 Evening rush hour — more accidents');
    if (traffic === 'high')
        reasons.push('🚗 High traffic increased collision risk');
    if (traffic === 'low' && percent < 40)
        reasons.push('🛣 Low traffic kept risk down');
    if (vis === 'low')
        reasons.push('👁 Low visibility reduced reaction time');
    if (road === 'highway')
        reasons.push('🛣 Highway speed increases accident severity');
    if (road === 'rural')
        reasons.push('🌾 Rural road — poor lighting detected');
    if (reasons.length === 0)
        reasons.push('✅ No major risk factors detected');

    var box = document.getElementById('explain-box');
    if (!box) return;

    var title = percent >= 70 ? 'high' : percent >= 45 ? 'medium' : 'low';
    var html  = '<h4 style="color:#fff;margin-bottom:0.8rem">🧠 Why is risk ' + title + '?</h4>';
    html += '<ul style="list-style:none;padding:0;margin:0">';
    for (var i = 0; i < reasons.length; i++) {
        html += '<li style="padding:8px 0;border-bottom:1px solid #2a2d3e;color:#ccc;font-size:0.9rem">' + reasons[i] + '</li>';
    }
    html += '</ul>';
    box.innerHTML     = html;
    box.style.display = 'block';
}

// ─────────────────────────────────────
// 5. FETCH LIVE WEATHER
// ─────────────────────────────────────
async function fetchWeather() {
    var city = document.getElementById('weather-city').value;
    if (!city) { alert('Please enter a city name!'); return; }

    var result          = document.getElementById('weather-result');
    result.style.display = 'block';
    result.textContent  = 'Fetching weather...';
    result.style.color  = '#aaa';

    try {
        var response = await fetch('/api/weather?city=' + city);
        var data     = await response.json();

        if (data.success) {
            document.getElementById('city').value       = data.data.city;
            document.getElementById('weather').value    = data.data.weather;
            document.getElementById('visibility').value = data.data.visibility;
            result.style.color = '#2ecc71';
            result.innerHTML   = '✅ ' + data.data.city + ': ' +
                                 data.data.description + ' | ' +
                                 data.data.temp + '°C | ' +
                                 'Weather: ' + data.data.weather;
        } else {
            result.style.color = '#e74c3c';
            result.textContent = '❌ City not found. Try: Chennai, Delhi, Mumbai';
        }
    } catch (error) {
        result.style.color = '#e74c3c';
        result.textContent = '❌ Failed to fetch weather.';
    }
}

// ─────────────────────────────────────
// 6. PREDICT RISK
// ─────────────────────────────────────
async function predictRisk() {
    var btn       = document.querySelector('.btn-predict');
    btn.innerHTML = '<span class="spinner"></span> Analyzing...';
    btn.disabled  = true;

    var inputs = {
        city            : document.getElementById('city').value,
        hour            : parseInt(document.getElementById('hour').value),
        weather         : document.getElementById('weather').value,
        road_type       : document.getElementById('road_type').value,
        traffic_density : document.getElementById('traffic_density').value,
        visibility      : document.getElementById('visibility').value,
        is_weekend      : document.getElementById('is_weekend').checked ? 1 : 0,
        is_peak_hour    : document.getElementById('is_peak_hour').checked ? 1 : 0,
        risk_score      : parseFloat(document.getElementById('risk_score').value)
    };

    try {
        var response = await fetch('/api/predict', {
            method  : 'POST',
            headers : { 'Content-Type': 'application/json' },
            body    : JSON.stringify(inputs)
        });
        var data = await response.json();

        if (data.success) {
            lastResult = data;
            showResult(data);
            playSound(data.prediction);
            speakAlert(data.prediction, data.city, data.risk_percentage);
            if (data.prediction === 'fatal') {
                flashScreen('#e74c3c');
            } else if (data.prediction === 'major') {
                flashScreen('#f39c12');
            }
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Server error: ' + error.message);
    }

    btn.innerHTML = '<i class="fa fa-brain"></i> Analyze Risk';
    btn.disabled  = false;
}

// ─────────────────────────────────────
// 7. SHOW RESULT
// ─────────────────────────────────────
function showResult(data) {
    var card = document.getElementById('result-card');
    card.classList.add('show');

    var circle       = document.getElementById('result-circle');
    circle.className = 'result-risk-circle ' + data.risk_color;

    document.getElementById('result-pct').textContent   = data.risk_percentage + '%';
    document.getElementById('result-label').textContent = data.prediction.toUpperCase();

    var level       = document.getElementById('result-level');
    level.textContent = data.risk_emoji + ' ' + data.risk_level;
    level.style.color = data.risk_color === 'red'   ? '#e74c3c' :
                        data.risk_color === 'orange' ? '#f39c12' : '#2ecc71';

    document.getElementById('result-message').textContent = data.risk_message;

    if (data.confidence) {
        var fatal = data.confidence['fatal'] || 0;
        var major = data.confidence['major'] || 0;
        var minor = data.confidence['minor'] || 0;
        document.getElementById('conf-fatal').style.width     = fatal + '%';
        document.getElementById('conf-fatal-pct').textContent = fatal + '%';
        document.getElementById('conf-major').style.width     = major + '%';
        document.getElementById('conf-major-pct').textContent = major + '%';
        document.getElementById('conf-minor').style.width     = minor + '%';
        document.getElementById('conf-minor-pct').textContent = minor + '%';
    }

    var alertBox = document.getElementById('alert-box');
    if (data.alert && data.alert_details) {
        alertBox.style.display = 'block';
        alertBox.innerHTML = '⚠ <strong>Smart Alert:</strong> ' + data.alert_details;
    } else {
        alertBox.style.display = 'none';
    }

    explainRisk(data);

    var pdfBtn = document.getElementById('pdf-btn');
    if (pdfBtn) pdfBtn.style.display = 'block';

    card.scrollIntoView({ behavior: 'smooth' });
}

// ─────────────────────────────────────
// 8. DOWNLOAD PDF
// ─────────────────────────────────────
async function downloadPDF() {
    if (!lastResult) { alert('Please run prediction first!'); return; }

    var btn       = document.getElementById('pdf-btn');
    btn.innerHTML = '<span class="spinner"></span> Generating...';
    btn.disabled  = true;

    try {
        var response = await fetch('/api/pdf-report', {
            method  : 'POST',
            headers : { 'Content-Type': 'application/json' },
            body    : JSON.stringify(lastResult)
        });
        var blob = await response.blob();
        var url  = URL.createObjectURL(blob);
        var link = document.createElement('a');
        link.href     = url;
        link.download = 'blackspot_report_' + lastResult.city + '.html';
        link.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('PDF error: ' + error.message);
    }

    btn.innerHTML = '<i class="fa fa-file-pdf"></i> Download PDF Report';
    btn.disabled  = false;
}

// ─────────────────────────────────────
// 9. GENERATE ALERT (Alert page)
// ─────────────────────────────────────
async function generateAlert() {
    var btn = document.querySelector('.btn-predict');
    if (btn) { btn.innerHTML = '<span class="spinner"></span> Generating...'; btn.disabled = true; }

    var inputs = {
        city            : document.getElementById('alert-city').value,
        hour            : parseInt(document.getElementById('alert-hour').value),
        weather         : document.getElementById('alert-weather').value,
        road_type       : 'urban',
        traffic_density : document.getElementById('alert-traffic').value,
        visibility      : 'medium',
        is_weekend      : 0,
        is_peak_hour    : 0,
        risk_score      : 0.7
    };

    try {
        var response = await fetch('/api/predict', {
            method  : 'POST',
            headers : { 'Content-Type': 'application/json' },
            body    : JSON.stringify(inputs)
        });
        var data = await response.json();

        if (data.success) {
            playSound(data.prediction);
            speakAlert(data.prediction, data.city, data.risk_percentage);
            if (data.prediction === 'fatal') flashScreen('#e74c3c');

            var liveAlert         = document.getElementById('live-alert');
            liveAlert.style.display = 'block';
            var color  = data.risk_color === 'red' ? '#e74c3c' :
                         data.risk_color === 'orange' ? '#f39c12' : '#2ecc71';
            var border = data.risk_color === 'red' ? 'danger' :
                         data.risk_color === 'orange' ? 'warning' : 'safe';

            liveAlert.innerHTML =
                '<div class="alert-item ' + border + '">' +
                '<div class="alert-icon">' + data.risk_emoji + '</div>' +
                '<div class="alert-content">' +
                '<h3>' + data.risk_level + ' — ' + data.city + '</h3>' +
                '<p>' + data.risk_message + ' Risk: <strong style="color:' + color + '">' +
                data.risk_percentage + '%</strong></p>' +
                (data.alert_details ? '<p style="color:#aaa">⚠ ' + data.alert_details + '</p>' : '') +
                '</div><div class="alert-time">Just now</div></div>';
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }

    if (btn) { btn.innerHTML = '<i class="fa fa-bell"></i> Generate Alert'; btn.disabled = false; }
}