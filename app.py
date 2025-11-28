from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
import uuid
from datetime import datetime

from astro_calculator import AstroCalculator
from report_generator import ReportGenerator
from email_sender import EmailSender

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允许跨域

# 初始化服务
calculator = AstroCalculator()
generator = ReportGenerator(api_key=os.getenv('OPENAI_API_KEY'))
email_sender = EmailSender(
    api_key=os.getenv('SENDGRID_API_KEY'),
    from_email=os.getenv('FROM_EMAIL', 'noreply@soulmate.app')
)

# 简单的文件存储
READINGS_DIR = 'readings'
os.makedirs(READINGS_DIR, exist_ok=True)


def save_reading(reading_data):
    """保存订单到JSON文件"""
    reading_id = str(uuid.uuid4())
    filepath = os.path.join(READINGS_DIR, f'{reading_id}.json')
    
    reading_data['reading_id'] = reading_id
    reading_data['created_at'] = datetime.now().isoformat()
    reading_data['paid'] = False
    reading_data['sent'] = False
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reading_data, f, ensure_ascii=False, indent=2)
    
    return reading_id


def get_reading(reading_id):
    """读取订单"""
    filepath = os.path.join(READINGS_DIR, f'{reading_id}.json')
    if not os.path.exists(filepath):
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_reading(reading_id, updates):
    """更新订单"""
    reading = get_reading(reading_id)
    if not reading:
        return False
    
    reading.update(updates)
    filepath = os.path.join(READINGS_DIR, f'{reading_id}.json')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(reading, f, ensure_ascii=False, indent=2)
    
    return True


def get_all_readings():
    """获取所有订单"""
    readings = []
    for filename in os.listdir(READINGS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(READINGS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                readings.append(json.load(f))
    
    # 按创建时间倒序
    readings.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return readings


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': 'Soulmate API is running',
        'version': '1.0.0'
    })


@app.route('/api/create-reading', methods=['POST'])
def create_reading():
    """
    创建完整的星盘报告（一次性生成所有内容）
    """
    try:
        data = request.json
        
        # 验证必需字段
        required = ['year', 'month', 'day', 'hour', 'minute', 'city', 'email']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        print(f"[CREATE] New reading request for {data['email']}")
        
        # 1. 计算星盘
        print("[STEP 1] Calculating birth chart...")
        chart_data = calculator.calculate_birth_chart({
            'name': data.get('name', 'User'),
            'year': int(data['year']),
            'month': int(data['month']),
            'day': int(data['day']),
            'hour': int(data['hour']),
            'minute': int(data['minute']),
            'city': data['city'],
            'nation': data.get('nation', 'US')
        })
        
        # 2. 生成完整报告（包括图片）
        print("[STEP 2] Generating full report with AI...")
        gender = data.get('gender', 'female')
        full_data = generator.generate_full_report_with_image(chart_data, gender)
        
        # 3. 创建预览版本
        print("[STEP 3] Creating preview version...")
        preview_data = generator.create_preview_from_full(full_data)
        
        # 4. 保存完整数据
        reading_id = save_reading({
            'email': data['email'],
            'name': data.get('name', 'User'),
            'birth_data': data,
            'chart': chart_data,
            'full_report': full_data,
            'preview': preview_data,
            'gender': gender
        })
        
        print(f"[SUCCESS] Reading created: {reading_id}")
        
        # 5. 返回预览给前端
        return jsonify({
            'success': True,
            'reading_id': reading_id,
            'chart': {
                'sun': chart_data['sun']['sign'],
                'moon': chart_data['moon']['sign'],
                'venus': chart_data['venus']['sign'],
                'rising': chart_data['rising']['sign']
            },
            'preview': preview_data
        })
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-report/<reading_id>', methods=['POST'])
def send_report(reading_id):
    """
    发送完整报告到用户邮箱（管理员手动触发）
    """
    try:
        reading = get_reading(reading_id)
        
        if not reading:
            return jsonify({'error': 'Reading not found'}), 404
        
        if reading.get('sent'):
            return jsonify({'error': 'Already sent'}), 400
        
        print(f"[SEND] Sending report to {reading['email']}")
        
        # 发送邮件
        success = email_sender.send_full_report(
            to_email=reading['email'],
            name=reading['name'],
            report_data=reading['full_report'],
            chart_data=reading['chart']
        )
        
        if success:
            # 标记为已发送
            update_reading(reading_id, {
                'sent': True,
                'sent_at': datetime.now().isoformat()
            })
            print(f"[SUCCESS] Report sent to {reading['email']}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/admin', methods=['GET'])
def admin_panel():
    """
    简单的管理后台 - 显示所有订单
    """
    readings = get_all_readings()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Soulmate Admin</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1200px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }
            h1 { color: #333; }
            table { 
                width: 100%; 
                background: white;
                border-collapse: collapse; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            th, td { 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #ddd;
            }
            th { 
                background: #6366f1; 
                color: white;
                font-weight: bold;
            }
            button { 
                padding: 8px 16px; 
                background: #10b981; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer;
                font-size: 14px;
            }
            button:hover { background: #059669; }
            button:disabled { 
                background: #ccc; 
                cursor: not-allowed;
            }
            .status { 
                padding: 4px 8px; 
                border-radius: 4px; 
                font-size: 12px;
                font-weight: bold;
            }
            .status.sent { background: #d1fae5; color: #065f46; }
            .status.pending { background: #fef3c7; color: #92400e; }
            .email { color: #6366f1; }
        </style>
    </head>
    <body>
        <h1>📧 Soulmate Admin - Pending Reports</h1>
        <p>Total readings: <strong>""" + str(len(readings)) + """</strong></p>
        <table>
            <thead>
                <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Created</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for reading in readings:
        sent = reading.get('sent', False)
        status_class = 'sent' if sent else 'pending'
        status_text = '✅ Sent' if sent else '⏳ Pending'
        button_disabled = 'disabled' if sent else ''
        
        html += f"""
                <tr>
                    <td class="email">{reading['email']}</td>
                    <td>{reading['name']}</td>
                    <td>{reading['created_at'][:19]}</td>
                    <td><span class="status {status_class}">{status_text}</span></td>
                    <td>
                        <button onclick="sendReport('{reading['reading_id']}')" {button_disabled}>
                            Send Report
                        </button>
                    </td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <script>
            async function sendReport(readingId) {
                if (!confirm('Send full report to this user?')) return;
                
                try {
                    const response = await fetch(`/api/send-report/${readingId}`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        alert('✅ Report sent successfully!');
                        location.reload();
                    } else {
                        const error = await response.json();
                        alert('❌ Error: ' + error.error);
                    }
                } catch (err) {
                    alert('❌ Network error: ' + err.message);
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
