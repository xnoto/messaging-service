from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration from environment (docker-compose will set these)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'messaging_user')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'messaging_password')}@"
    f"{os.getenv('POSTGRES_HOST', 'db')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'messaging_service')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_a = db.Column(db.String, index=True)
    participant_b = db.Column(db.String, index=True)
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), index=True)
    from_addr = db.Column(db.String, index=True)
    to_addr = db.Column(db.String, index=True)
    type = db.Column(db.String, index=True)  # sms, mms, email
    provider_id = db.Column(db.String, index=True, nullable=True)
    body = db.Column(db.Text)
    attachments = db.Column(db.Text)  # comma-separated URLs
    timestamp = db.Column(db.DateTime, index=True)

def get_or_create_conversation(from_addr, to_addr):
    conv = Conversation.query.filter(
        or_(
            (Conversation.participant_a == from_addr) & (Conversation.participant_b == to_addr),
            (Conversation.participant_a == to_addr) & (Conversation.participant_b == from_addr)
        )
    ).first()
    if not conv:
        conv = Conversation(participant_a=from_addr, participant_b=to_addr)
        db.session.add(conv)
        db.session.commit()
    return conv

@app.route('/api/messages/sms', methods=['POST'])
def send_sms_mms():
    data = request.json
    from_addr = data.get('from')
    to_addr = data.get('to')
    msg_type = data.get('type', 'sms')  # 'sms' or 'mms'
    body = data.get('body')
    attachments = data.get('attachments')
    timestamp = data.get('timestamp')
    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    conv = get_or_create_conversation(from_addr, to_addr)
    msg = Message(
        conversation_id=conv.id,
        from_addr=from_addr,
        to_addr=to_addr,
        type=msg_type,
        body=body,
        attachments=','.join(attachments or []) if attachments else '',
        timestamp=ts
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "sent", "message_id": msg.id})

@app.route('/api/messages/email', methods=['POST'])
def send_email():
    data = request.json
    from_addr = data.get('from')
    to_addr = data.get('to')
    body = data.get('body')
    attachments = data.get('attachments')
    timestamp = data.get('timestamp')
    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    conv = get_or_create_conversation(from_addr, to_addr)
    msg = Message(
        conversation_id=conv.id,
        from_addr=from_addr,
        to_addr=to_addr,
        type='email',
        body=body,
        attachments=','.join(attachments or []) if attachments else '',
        timestamp=ts
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "sent", "message_id": msg.id})

@app.route('/api/webhooks/sms', methods=['POST'])
def inbound_sms_mms():
    data = request.json
    from_addr = data.get('from')
    to_addr = data.get('to')
    msg_type = data.get('type')
    provider_id = data.get('messaging_provider_id')
    body = data.get('body')
    attachments = data.get('attachments')
    timestamp = data.get('timestamp')
    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    conv = get_or_create_conversation(from_addr, to_addr)
    msg = Message(
        conversation_id=conv.id,
        from_addr=from_addr,
        to_addr=to_addr,
        type=msg_type,
        provider_id=provider_id,
        body=body,
        attachments=','.join(attachments or []) if attachments else '',
        timestamp=ts
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "received", "message_id": msg.id})

@app.route('/api/webhooks/email', methods=['POST'])
def inbound_email():
    data = request.json
    from_addr = data.get('from')
    to_addr = data.get('to')
    provider_id = data.get('xillio_id')
    body = data.get('body')
    attachments = data.get('attachments')
    timestamp = data.get('timestamp')
    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) if timestamp else datetime.utcnow()
    conv = get_or_create_conversation(from_addr, to_addr)
    msg = Message(
        conversation_id=conv.id,
        from_addr=from_addr,
        to_addr=to_addr,
        type='email',
        provider_id=provider_id,
        body=body,
        attachments=','.join(attachments or []) if attachments else '',
        timestamp=ts
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"status": "received", "message_id": msg.id})

@app.route('/api/conversations', methods=['GET'])
def list_conversations():
    convs = Conversation.query.all()
    result = []
    for conv in convs:
        result.append({
            "id": conv.id,
            "participants": [conv.participant_a, conv.participant_b],
            "message_count": len(conv.messages)
        })
    return jsonify(result)

@app.route('/api/conversations/<int:conv_id>/messages', methods=['GET'])
def list_messages(conv_id):
    msgs = Message.query.filter_by(conversation_id=conv_id).order_by(Message.timestamp).all()
    result = []
    for msg in msgs:
        result.append({
            "id": msg.id,
            "from": msg.from_addr,
            "to": msg.to_addr,
            "type": msg.type,
            "provider_id": msg.provider_id,
            "body": msg.body,
            "attachments": msg.attachments.split(',') if msg.attachments else [],
            "timestamp": msg.timestamp.isoformat()
        })
    return jsonify(result)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=8080)