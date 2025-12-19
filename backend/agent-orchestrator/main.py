import os, json, time, redis, groq
from groq import Groq
from dotenv import load_dotenv
from confluent_kafka import Consumer, Producer

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Kafka for Data and Action Commands
conf = {'bootstrap.servers': 'localhost:29092', 'group.id': 'nexus-agents'}
consumer = Consumer(conf)
consumer.subscribe(['nexus-raw-data'])
producer = Producer({'bootstrap.servers': 'localhost:29092'})

def expert_council_decision(sensor_data):
    sensor_id = sensor_data['sensor_id']
    
    # 1. THE HISTORIAN: Get last 5 readings from Redis
    history = r.lrange(f"history:{sensor_id}", 0, 4)
    
    # 2. THE TECHNICIAN: Physical impossibility check (Value > 5.0 is a sensor error/hack)
    is_impossible = sensor_data['value'] > 5.0

    # 3. THE COMMANDER: Final Multi-Agent Reasoning
    prompt = f"""
    SYSTEM: NEXUS Commander. 
    CONTEXT: Historian shows {history}. Technician reports physical impossibility: {is_impossible}.
    DATA: {json.dumps(sensor_data)}

    DECISION RULES:
    1. If Physical Anomaly is YES -> ACTION: BLOCK.
    2. If 3/5 previous entries were > 0.8 -> ACTION: BLOCK.
    3. If only one spike -> ACTION: ALERT.

    RETURN JSON: {{"action": "BLOCK" | "ALLOW", "reasoning": "string"}}
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant", # Faster response for real-time governance
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

while True:
    msg = consumer.poll(1.0)
    if msg is None: continue
    data = json.loads(msg.value().decode('utf-8'))
    
    # Record to Redis
    r.lpush(f"history:{data['sensor_id']}", data['value'])
    r.ltrim(f"history:{data['sensor_id']}", 0, 9)

    if data['value'] > 0.6:
        try:
            decision = expert_council_decision(data)
            
            # SAFE CHECK: Ensure 'action' exists in the AI response
            action = decision.get('action', 'ALLOW') # Default to ALLOW if missing
            reason = decision.get('reasoning', 'No reason provided')

            # Change 'iif' to 'if'
            if decision.get('action') == "BLOCK":
                # Ensure this exact line exists and uses the correct topic name
                producer.produce('nexus-commands', json.dumps({"block_id": data['sensor_id']}))
                producer.flush() # CRITICAL: This forces the message to send immediately
                print(f"🛑 SHIELD ACTIVATED: Blocked {data['sensor_id']}")
            else:
                print(f"✅ AI VERIFIED: {data['sensor_id']} is safe. Reasoning: {reason}")
                
        except Exception as e:
            print(f"⚠️ AI Parsing Error: {e}. Defaulting to safety (ALLOW).")
            continue