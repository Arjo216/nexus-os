import socketio
import eventlet
import json
from confluent_kafka import Consumer

# Initialize Socket.io Server
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

# Kafka Setup to listen for AI Decisions
conf = {'bootstrap.servers': 'localhost:29092', 'group.id': 'nexus-bridge', 'auto.offset.reset': 'latest'}
consumer = Consumer(conf)
consumer.subscribe(['nexus-raw-data']) # In prod, listen to an 'ai-decisions' topic

def background_thread():
    print("🌐 WebSocket Bridge: Listening for AI decisions to push to 3D Twin...")
    while True:
        msg = consumer.poll(0.1)
        if msg is None: continue
        
        data = json.loads(msg.value().decode('utf-8'))
        
        # If it's a critical value, broadcast it to the Frontend
        if data['value'] > 0.8:
            print(f"📡 Broadcasting CRITICAL event for {data['sensor_id']}")
            sio.emit('anomaly_detected', data)
        
        eventlet.sleep(0)

if __name__ == '__main__':
    eventlet.spawn(background_thread)
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)