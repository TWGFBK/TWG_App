"""SMS webhook endpoints for SMS gateway integration"""

from flask import request, jsonify
from datetime import datetime
import json
import os
from .handler import process_sms_alarm

def log_sms_data(data, method, timestamp=None):
    """Log SMS data to file for debugging"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create log file with current date
        log_file = os.path.join(log_dir, f"sms_webhook_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        # Prepare log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "data": data,
            "raw_timestamp": timestamp
        }
        
        # Write to log file
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n" + "="*50 + "\n")
            
        print(f"SMS data logged to: {log_file}")
        
    except Exception as e:
        print(f"Error logging SMS data: {e}")

def register_sms_routes(app):
    """Register SMS webhook routes with Flask app"""
    
    @app.route('/sms-webhook', methods=['POST', 'GET'])
    def receive_sms():
        """Receive SMS alarms from SMS gateway"""
        
        try:
            if request.method == 'POST':
                # Handle both application/json and application/json; charset=utf-8
                if request.content_type and 'application/json' in request.content_type:
                    data = request.get_json()
                else:
                    data = request.get_json(force=True)
                
                print(f"SMS Webhook POST received: {data}")  # Debug logging
                print(f"Content-Type: {request.content_type}")  # Debug content type
                
                # Log to file
                log_sms_data(data, 'POST', data.get('timestamp') if data else None)
                
                content = data.get('content', '')
                sender = data.get('sender', '')
                recipient = data.get('recipient', '')
                mid = data.get('mid', '')
                timestamp = data.get('timestamp', int(datetime.now().timestamp()))
            else:  # GET
                args_dict = dict(request.args)
                print(f"SMS Webhook GET received: {args_dict}")  # Debug logging
                
                # Log to file
                log_sms_data(args_dict, 'GET', request.args.get('timestamp'))
                
                content = request.args.get('content', '')
                sender = request.args.get('sender', '')
                recipient = request.args.get('recipient', '')
                mid = request.args.get('mid', '')
                timestamp = int(request.args.get('timestamp', datetime.now().timestamp()))
            
            print(f"Parsed SMS: content='{content}', sender='{sender}', timestamp='{timestamp}'")
            
            if not content:
                print("ERROR: No content provided")
                return jsonify({'status': 'error', 'message': 'No content provided'}), 400
            
            # Process the SMS alarm
            result = process_sms_alarm(content, sender, timestamp)
            
            if result['status'] == 'success':
                return jsonify({
                    'status': 'success', 
                    'alarm_id': result['alarm_id'],
                    'department': result['department'],
                    'all_departments': result.get('all_departments', [result['department']]),
                    'kind': result['kind']
                })
            elif result['status'] == 'ignored':
                return jsonify({
                    'status': 'ignored',
                    'reason': result['reason']
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': result['message']
                }), 500
                
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/sms-test', methods=['POST'])
    def test_sms():
        """Test endpoint for SMS alarm processing"""
        
        try:
            data = request.get_json()
            content = data.get('content', '')
            
            if not content:
                return jsonify({'status': 'error', 'message': 'No content provided'}), 400
            
            # Process without creating database record
            from .parser import parse_sms_alarm
            alarm_data = parse_sms_alarm(content)
            
            return jsonify({
                'status': 'success',
                'parsed_data': alarm_data,
                'department_detected': alarm_data['department_code'] is not None
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    @app.route('/sms-debug', methods=['GET', 'POST'])
    def sms_debug():
        """Debug endpoint to see what's being received"""
        if request.method == 'POST':
            data = request.get_json()
            print(f"DEBUG POST: {data}")
            log_sms_data(data, 'DEBUG_POST')
            return jsonify({'received': data, 'method': 'POST'})
        else:
            args = dict(request.args)
            print(f"DEBUG GET: {args}")
            log_sms_data(args, 'DEBUG_GET')
            return jsonify({'received': args, 'method': 'GET'})
