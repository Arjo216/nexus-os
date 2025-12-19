import redis
from flask import Flask, request, jsonify

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/unblock', methods=['POST'])
def unblock_sensor():
    sensor_id = request.json.get('sensor_id')
    # Clearing historical critical hits in Redis
    r.delete(f"history:{sensor_id}")
    return jsonify({"status": "SUCCESS", "message": f"Sensor {sensor_id} history cleared and unblocked."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)