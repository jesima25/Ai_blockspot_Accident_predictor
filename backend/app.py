# app.py - Full version with all features

from flask import Flask, request, jsonify, render_template, make_response
import joblib
import pandas as pd
from weather_api  import get_weather
from prone_areas  import get_prone_areas
from alert_system import send_emergency_alert

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

print("[*] Loading model...")
model           = joblib.load("model.pkl")
feature_columns = joblib.load("feature_columns.pkl")
encoders        = joblib.load("encoders.pkl")
print("[*] Model loaded!")

# ─────────────────────────────────────────
# SMART RISK CALCULATOR
# ─────────────────────────────────────────
def calculate_smart_risk(data, risk_score_raw):
    weather         = data.get('weather', 'clear')
    hour            = int(data.get('hour', 12))
    traffic_density = data.get('traffic_density', 'medium')
    visibility      = data.get('visibility', 'medium')
    is_peak_hour    = int(data.get('is_peak_hour', 0))
    road_type       = data.get('road_type', 'urban')

    score = int(risk_score_raw * 100)
    if weather == 'rain':  score += 15
    elif weather == 'fog': score += 20
    if hour >= 22 or hour <= 5: score = int(score * 1.4)
    if traffic_density == 'high': score += 10
    elif traffic_density == 'low': score -= 10
    if visibility == 'low':  score += 15
    elif visibility == 'high': score -= 5
    if is_peak_hour: score += 8
    if road_type == 'highway' and weather in ['rain','fog']: score += 10

    score = max(5, min(99, score))
    if score >= 70:   severity = 'fatal'
    elif score >= 45: severity = 'major'
    else:             severity = 'minor'
    return score, severity

def get_risk_info(severity, risk_pct):
    if severity == 'fatal':
        return {"level":"FATAL RISK","color":"red","emoji":"🔴",
                "message":"Extreme danger! Avoid this route immediately.","alert":True}
    elif severity == 'major':
        return {"level":"HIGH RISK","color":"orange","emoji":"🟠",
                "message":"High accident probability. Drive with caution.","alert":True}
    else:
        return {"level":"LOW RISK","color":"green","emoji":"🟢",
                "message":"Relatively safe. Follow normal precautions.","alert":False}

# ─────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────
@app.route('/')
def index(): return render_template('index.html')

@app.route('/predict')
def predict_page(): return render_template('predict.html')

@app.route('/map')
def map_page(): return render_template('map.html')

@app.route('/dashboard')
def dashboard_page(): return render_template('dashboard.html')

@app.route('/alert')
def alert_page(): return render_template('alert.html')

@app.route('/prone')
def prone_page(): return render_template('prone.html')

@app.route('/traffic')
def traffic_page(): return render_template('traffic.html')

# ─────────────────────────────────────────
# API — WEATHER
# ─────────────────────────────────────────
@app.route('/api/weather', methods=['GET'])
def weather():
    city = request.args.get('city', 'Chennai')
    data = get_weather(city)
    if data: return jsonify({"success": True, "data": data})
    return jsonify({"success": False, "error": "City not found"}), 404

# ─────────────────────────────────────────
# API — PREDICT
# ─────────────────────────────────────────
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data            = request.get_json()
        weather         = data.get('weather', 'clear')
        road_type       = data.get('road_type', 'urban')
        hour            = int(data.get('hour', 12))
        is_weekend      = int(data.get('is_weekend', 0))
        traffic_density = data.get('traffic_density', 'medium')
        visibility      = data.get('visibility', 'medium')
        is_peak_hour    = int(data.get('is_peak_hour', 0))
        risk_score_raw  = float(data.get('risk_score', 0.5))
        city            = data.get('city', 'Unknown')

        def encode(col, val):
            if col in encoders:
                le = encoders[col]
                if val in le.classes_:
                    return int(le.transform([val])[0])
            return 0

        input_dict = {
            'weather'        : encode('weather', weather),
            'road_type'      : encode('road_type', road_type),
            'hour'           : hour,
            'is_weekend'     : is_weekend,
            'traffic_density': encode('traffic_density', traffic_density),
            'visibility'     : encode('visibility', visibility),
            'is_peak_hour'   : is_peak_hour,
            'risk_score'     : risk_score_raw
        }

        input_df        = pd.DataFrame([input_dict])[feature_columns]
        ml_pred_proba   = model.predict_proba(input_df)[0]
        smart_pct, smart_severity = calculate_smart_risk(data, risk_score_raw)
        risk_info = get_risk_info(smart_severity, smart_pct)

        confidence = {}
        if 'accident_severity' in encoders:
            for label, prob in zip(encoders['accident_severity'].classes_, ml_pred_proba):
                confidence[label] = round(float(prob)*100, 1)

        alerts = []
        if hour >= 22 or hour <= 5: alerts.append("Night-time — risk boosted 1.4x")
        if weather == 'rain':       alerts.append("Rainy conditions increase danger")
        if weather == 'fog':        alerts.append("Foggy — reduce speed immediately")
        if traffic_density=='high': alerts.append("High traffic — stay alert")
        if visibility == 'low':     alerts.append("Low visibility — hazard ahead")
        if is_peak_hour:            alerts.append("Peak hour — higher accident risk")
        if road_type=='highway' and weather in ['rain','fog']:
            alerts.append("Highway + bad weather — extremely dangerous")

        alert_msg = ". ".join(alerts)
        result = {
            "success"        : True,
            "city"           : city,
            "prediction"     : smart_severity,
            "risk_level"     : risk_info['level'],
            "risk_color"     : risk_info['color'],
            "risk_emoji"     : risk_info['emoji'],
            "risk_percentage": smart_pct,
            "risk_message"   : risk_info['message'],
            "alert"          : risk_info['alert'],
            "alert_details"  : alert_msg,
            "confidence"     : confidence,
            "inputs"         : {
                "weather"        : weather,
                "road_type"      : road_type,
                "hour"           : hour,
                "traffic_density": traffic_density,
                "visibility"     : visibility
            }
        }

        # Auto send emergency email if fatal
        if smart_severity == 'fatal':
            send_emergency_alert(city, risk_info['level'],
                                 smart_pct, alert_msg, result['inputs'])

        return jsonify(result)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────
# API — BLACKSPOTS
# ─────────────────────────────────────────
@app.route('/api/blackspots', methods=['GET'])
def get_blackspots():
    try:
        df        = pd.read_csv("accident_data.csv")
        high_risk = df[df['accident_severity'].isin(['fatal','major'])].copy()
        spots     = high_risk[['latitude','longitude','city',
                               'accident_severity','weather',
                               'road_type','risk_score']].dropna().head(300)
        result = []
        for _, row in spots.iterrows():
            result.append({
                "lat"       : round(float(row['latitude']), 6),
                "lng"       : round(float(row['longitude']), 6),
                "city"      : str(row['city']),
                "severity"  : str(row['accident_severity']),
                "weather"   : str(row['weather']),
                "road"      : str(row['road_type']),
                "risk_score": round(float(row['risk_score']), 2)
            })
        return jsonify({"success":True,"total":len(result),"blackspots":result})
    except Exception as e:
        return jsonify({"success":False,"error":str(e)}), 500

# ─────────────────────────────────────────
# API — STATS
# ─────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        df = pd.read_csv("accident_data.csv")
        return jsonify({
            "success"        : True,
            "total_accidents": len(df),
            "severity"       : df['accident_severity'].value_counts().to_dict(),
            "by_city"        : df['city'].value_counts().head(8).to_dict(),
            "by_weather"     : df['weather'].value_counts().to_dict(),
            "by_hour"        : {str(k):v for k,v in df['hour'].value_counts().sort_index().to_dict().items()},
            "by_road"        : df['road_type'].value_counts().to_dict()
        })
    except Exception as e:
        return jsonify({"success":False,"error":str(e)}), 500

# ─────────────────────────────────────────
# API — PRONE AREAS
# ─────────────────────────────────────────
@app.route('/api/prone-areas', methods=['GET'])
def prone_areas():
    try:
        areas = get_prone_areas()
        return jsonify({"success": True, "total": len(areas), "areas": areas})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────
# API — LIVE TRAFFIC DENSITY
# ─────────────────────────────────────────
@app.route('/api/traffic', methods=['GET'])
def get_traffic():
    try:
        city = request.args.get('city', 'Chennai')
        df   = pd.read_csv("accident_data.csv")

        city_data = df[df['city'].str.lower() == city.lower()]

        if city_data.empty:
            # Use all data if city not found
            city_data = df

        # Hour-wise traffic density simulation
        hour_density = city_data.groupby('hour')['traffic_density'].apply(
            lambda x: x.value_counts().index[0] if len(x) > 0 else 'medium'
        ).to_dict()

        # Count accidents per hour
        hour_accidents = city_data.groupby('hour').size().to_dict()

        # Current hour simulation
        import datetime
        current_hour = datetime.datetime.now().hour

        current_density = hour_density.get(current_hour, 'medium')
        current_accidents = hour_accidents.get(current_hour, 0)

        # Traffic score 0-100
        density_score = {'low': 25, 'medium': 55, 'high': 85}
        traffic_score = density_score.get(current_density, 55)

        # Rush hour check
        is_rush = current_hour in [8,9,10,17,18,19,20]

        return jsonify({
            "success"          : True,
            "city"             : city,
            "current_hour"     : current_hour,
            "current_density"  : current_density,
            "traffic_score"    : traffic_score,
            "accidents_this_hour": current_accidents,
            "is_rush_hour"     : is_rush,
            "hour_data"        : {str(k): v for k,v in hour_density.items()},
            "hour_accidents"   : {str(k): v for k,v in hour_accidents.items()}
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────
# API — EMERGENCY ALERT
# ─────────────────────────────────────────
@app.route('/api/emergency-alert', methods=['POST'])
def emergency_alert():
    try:
        data       = request.get_json()
        city       = data.get('city', 'Unknown')
        risk_level = data.get('risk_level', '')
        risk_pct   = data.get('risk_percentage', 0)
        alerts     = data.get('alert_details', '')
        inputs     = data.get('inputs', {})

        result = send_emergency_alert(city, risk_level, risk_pct, alerts, inputs)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────
# API — PDF REPORT
# ─────────────────────────────────────────
@app.route('/api/pdf-report', methods=['POST'])
def pdf_report():
    try:
        data       = request.get_json()
        city       = data.get('city', 'Unknown')
        risk_level = data.get('risk_level', 'LOW RISK')
        risk_pct   = data.get('risk_percentage', 0)
        risk_msg   = data.get('risk_message', '')
        alerts     = data.get('alert_details', '')
        inputs     = data.get('inputs', {})
        confidence = data.get('confidence', {})

        from datetime import datetime
        now        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color_map  = {'FATAL RISK':'#e74c3c','HIGH RISK':'#f39c12','LOW RISK':'#2ecc71'}
        risk_color = color_map.get(risk_level, '#2ecc71')

        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"/>
        <style>
          body{{font-family:Arial,sans-serif;padding:40px;color:#222}}
          .header{{background:#1a1d2e;color:white;padding:30px;border-radius:10px;margin-bottom:30px}}
          .header h1{{margin:0;font-size:24px}}
          .header p{{margin:5px 0 0;color:#aaa;font-size:14px}}
          .risk-box{{background:{risk_color}22;border:2px solid {risk_color};
                     border-radius:10px;padding:20px;text-align:center;margin-bottom:30px}}
          .risk-pct{{font-size:60px;font-weight:900;color:{risk_color};margin:0}}
          .risk-lbl{{font-size:22px;font-weight:700;color:{risk_color}}}
          .risk-msg{{color:#555;margin-top:8px}}
          table{{width:100%;border-collapse:collapse;margin-bottom:25px}}
          th{{background:#1a1d2e;color:white;padding:10px;text-align:left}}
          td{{padding:10px;border-bottom:1px solid #eee}}
          tr:nth-child(even){{background:#f9f9f9}}
          .alert-box{{background:#fff3cd;border:1px solid #ffc107;
                      border-radius:8px;padding:15px;margin-bottom:25px}}
          .footer{{text-align:center;color:#aaa;font-size:12px;
                   margin-top:40px;border-top:1px solid #eee;padding-top:20px}}
        </style></head><body>
        <div class="header">
          <h1>🚗 AI Blackspot Detection — Risk Report</h1>
          <p>Generated: {now} | City: {city}</p>
        </div>
        <div class="risk-box">
          <p class="risk-pct">{risk_pct}%</p>
          <p class="risk-lbl">{risk_level}</p>
          <p class="risk-msg">{risk_msg}</p>
        </div>
        <h2>Road Conditions</h2>
        <table>
          <tr><th>Factor</th><th>Value</th></tr>
          <tr><td>City</td><td>{city}</td></tr>
          <tr><td>Weather</td><td>{inputs.get('weather','—').title()}</td></tr>
          <tr><td>Road Type</td><td>{inputs.get('road_type','—').title()}</td></tr>
          <tr><td>Hour</td><td>{inputs.get('hour','—')}:00</td></tr>
          <tr><td>Traffic Density</td><td>{inputs.get('traffic_density','—').title()}</td></tr>
          <tr><td>Visibility</td><td>{inputs.get('visibility','—').title()}</td></tr>
        </table>
        <h2>AI Confidence Breakdown</h2>
        <table>
          <tr><th>Severity</th><th>Confidence</th></tr>
          <tr><td>🔴 Fatal</td><td>{confidence.get('fatal',0)}%</td></tr>
          <tr><td>🟠 Major</td><td>{confidence.get('major',0)}%</td></tr>
          <tr><td>🟢 Minor</td><td>{confidence.get('minor',0)}%</td></tr>
        </table>
        {'<h2>Smart Alerts</h2><div class="alert-box">⚠ ' + alerts + '</div>' if alerts else ''}
        <h2>Safety Recommendation</h2>
        <table>
          <tr><th>Risk Level</th><th>Action</th></tr>
          <tr><td>🔴 Fatal (70-99%)</td><td>Avoid route immediately. Use alternate roads.</td></tr>
          <tr><td>🟠 High (45-69%)</td><td>Drive carefully. Reduce speed. Stay alert.</td></tr>
          <tr><td>🟢 Low (0-44%)</td><td>Safe to travel. Follow normal precautions.</td></tr>
        </table>
        <div class="footer">
          AI Blackspot Detection System | B.Sc Computer Science Project<br/>
          Powered by Random Forest ML | Dataset: 20,000 Indian Accident Records
        </div>
        </body></html>"""

        response = make_response(html)
        response.headers['Content-Type']        = 'text/html'
        response.headers['Content-Disposition'] = f'attachment; filename=blackspot_report_{city}.html'
        return response

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("   AI BLACKSPOT SERVER STARTING...")
    print("="*50)
    print("\n   Open browser: http://localhost:5000\n")
    app.run(debug=True, port=5000)