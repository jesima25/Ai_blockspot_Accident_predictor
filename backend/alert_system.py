# alert_system.py
# Purpose: Send emergency email alerts when fatal risk detected

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── CONFIG — change these ──────────────
SENDER_EMAIL    = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
RECEIVER_EMAIL  = "receiver_email@gmail.com"
# ──────────────────────────────────────

def send_emergency_alert(city, risk_level, risk_pct, alert_details, inputs):
    """Send emergency email when fatal risk detected"""
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subject = f"🚨 EMERGENCY ALERT — {risk_level} in {city} [{risk_pct}%]"

        body = f"""
        <html><body style="font-family:Arial;padding:20px">

        <div style="background:#e74c3c;color:white;padding:20px;border-radius:10px;margin-bottom:20px">
          <h1 style="margin:0">🚨 AI BLACKSPOT EMERGENCY ALERT</h1>
          <p style="margin:5px 0 0">Generated: {now}</p>
        </div>

        <div style="background:#fff3f3;border:2px solid #e74c3c;border-radius:10px;
                    padding:20px;text-align:center;margin-bottom:20px">
          <h1 style="color:#e74c3c;font-size:60px;margin:0">{risk_pct}%</h1>
          <h2 style="color:#e74c3c;margin:5px 0">{risk_level}</h2>
          <p>City: <strong>{city}</strong></p>
        </div>

        <h3>Road Conditions</h3>
        <table style="width:100%;border-collapse:collapse">
          <tr style="background:#1a1d2e;color:white">
            <th style="padding:10px;text-align:left">Factor</th>
            <th style="padding:10px;text-align:left">Value</th>
          </tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee">Weather</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{inputs.get('weather','—')}</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee">Road Type</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{inputs.get('road_type','—')}</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee">Hour</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{inputs.get('hour','—')}:00</td></tr>
          <tr><td style="padding:8px;border-bottom:1px solid #eee">Traffic</td>
              <td style="padding:8px;border-bottom:1px solid #eee">{inputs.get('traffic_density','—')}</td></tr>
          <tr><td style="padding:8px">Visibility</td>
              <td style="padding:8px">{inputs.get('visibility','—')}</td></tr>
        </table>

        <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;
                    padding:15px;margin-top:20px">
          <strong>⚠ Smart Alerts:</strong><br/>{alert_details}
        </div>

        <div style="background:#f8f9fa;border-radius:8px;padding:15px;margin-top:20px">
          <strong>🚗 Recommended Action:</strong><br/>
          Avoid this route immediately. Alert traffic police. Use alternate roads.
        </div>

        <p style="color:#aaa;font-size:12px;margin-top:30px;text-align:center">
          AI Blackspot Detection System | Auto-generated alert
        </p>

        </body></html>
        """

        msg                     = MIMEMultipart('alternative')
        msg['Subject']          = subject
        msg['From']             = SENDER_EMAIL
        msg['To']               = RECEIVER_EMAIL
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        return {"success": True, "message": f"Alert sent to {RECEIVER_EMAIL}"}

    except Exception as e:
        return {"success": False, "error": str(e)}