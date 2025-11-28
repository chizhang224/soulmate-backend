from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import os

class EmailSender:
    """邮件发送服务"""
    
    def __init__(self, api_key=None, from_email=None):
        self.api_key = api_key or os.getenv('SENDGRID_API_KEY')
        self.from_email = from_email or os.getenv('FROM_EMAIL', 'noreply@soulmate.app')
        self.sg = SendGridAPIClient(self.api_key)
    
    def send_full_report(self, to_email, name, report_data, chart_data):
        """发送完整报告"""
        
        subject = f"✨ {name}, Your Soulmate Reading is Ready!"
        
        html_content = self._build_email_html(name, report_data, chart_data)
        
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )
        
        try:
            response = self.sg.send(message)
            print(f"Email sent to {to_email}, status: {response.status_code}")
            return response.status_code == 202
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
    
    def _build_email_html(self, name, report_data, chart_data):
        """构建邮件HTML"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Georgia', serif;
            line-height: 1.8;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #667eea;
            text-align: center;
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section-title {{
            color: #667eea;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        img {{
            max-width: 100%;
            border-radius: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✨ Your Soulmate Reading ✨</h1>
        <p style="text-align:center">Personalized for {name}</p>
        
        <div style="text-align:center; margin:20px 0">
            <img src="{report_data['hd_image_url']}" alt="Soulmate Portrait">
        </div>
        
        <div class="section">
            <div class="section-title">💫 Your Love Style</div>
            <p>{report_data['personality_analysis']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">💖 How You Approach Love</div>
            <p>{report_data['love_approach']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">👤 Physical Appearance</div>
            <p>{report_data['soulmate_appearance']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">✨ Personality Traits</div>
            <p>{report_data['soulmate_personality']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">💼 Career & Lifestyle</div>
            <p>{report_data['soulmate_career']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">📍 Where You'll Meet</div>
            <p>{report_data['meeting_places']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">📅 Best Timing in 2025</div>
            <p>{report_data['best_timing']}</p>
        </div>
        
        <div class="section">
            <div class="section-title">💡 Compatibility Tips</div>
            <p>{report_data['compatibility_tips']}</p>
        </div>
        
        <p style="text-align:center; color:#888; margin-top:40px">
            © 2025 Soulmate Astrology
        </p>
    </div>
</body>
</html>
        """
```

---

## 📁 最终文件结构
```
soulmate-backend/
├── app.py
├── requirements.txt
├── runtime.txt
├── .env.example
├── astro_calculator.py
├── report_generator.py
├── email_sender.py
└── readings/  (空文件夹)