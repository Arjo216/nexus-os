use axum::{routing::post, Json, Router, extract::State, http::StatusCode, response::IntoResponse};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};
use std::collections::HashSet;
use rskafka::client::{ClientBuilder, partition::{UnknownTopicHandling, Compression}};
use rskafka::record::Record;
use chrono::Utc;

#[derive(Serialize, Deserialize, Debug, Clone)]
struct SensorEvent {
    sensor_id: String,
    sensor_type: String,
    value: f64,
    location: serde_json::Value,
    timestamp: i64,
}

// Updated to handle both BLOCK and UNBLOCK commands from AI/Dashboard
#[derive(Deserialize, Debug)]
struct ActionCommand {
    #[serde(alias = "block_id", alias = "unblock_id")]
    sensor_id: String,
    #[serde(default = "default_action")]
    action: String, // "BLOCK" or "UNBLOCK"
}

fn default_action() -> String { "BLOCK".to_string() }

struct AppState {
    producer: rskafka::client::partition::PartitionClient,
    blacklist: Arc<Mutex<HashSet<String>>>,
}

#[tokio::main]
async fn main() {
    let broker = "localhost:29092".to_string();
    println!("🦀 NEXUS SHIELD: Initializing Protective Gate at {}...", broker);

    let client = ClientBuilder::new(vec![broker.clone()]).build().await.unwrap();
    
    let producer = client
        .partition_client("nexus-raw-data".to_string(), 0, UnknownTopicHandling::Retry)
        .await
        .expect("❌ Failed to connect to topic.");

    let blacklist = Arc::new(Mutex::new(HashSet::new()));
    let blacklist_for_consumer = Arc::clone(&blacklist);

    // BACKGROUND FIREWALL COMMANDER
    tokio::spawn(async move {
        let consumer_client = ClientBuilder::new(vec![broker]).build().await.unwrap();
        let partition_client = consumer_client
            .partition_client("nexus-commands".to_string(), 0, UnknownTopicHandling::Retry)
            .await
            .expect("❌ Failed to connect to nexus-commands topic.");

        let mut offset = 0;
        println!("🛡️ SHIELD: Background Firewall Consumer Active.");

        // Replace the old loop logic with this structured check
loop {
    if let Ok((records, _)) = partition_client.fetch_records(offset, 1..1024*1024, 1000).await {
        for record in records {
            if let Some(val) = record.record.value {
                if let Ok(cmd) = serde_json::from_slice::<ActionCommand>(&val) {
                    let mut guard = blacklist_for_consumer.lock().unwrap();
                    
                    // --- UPDATE START ---
                    if cmd.action == "UNBLOCK" {
                        println!("🔓 SHIELD: AI Command - Unblocking {}", cmd.sensor_id);
                        guard.remove(&cmd.sensor_id);
                    } else if cmd.action == "BLOCK" {
                        println!("🚫 SHIELD: AI Command - Blacklisting {}", cmd.sensor_id);
                        guard.insert(cmd.sensor_id.clone());
                    }
                    // --- UPDATE END ---
                }
            }
            offset = record.offset + 1;
        }
    }
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
}
    });

    let state = Arc::new(AppState { producer, blacklist });

    let app = Router::new()
        .route("/ingest", post(handler))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("🚀 NEXUS Ingestor [FIREWALL ENABLED]: Port 3000");
    
    axum::serve(listener, app).await.unwrap();
}

async fn handler(
    State(state): State<Arc<AppState>>, 
    Json(payload): Json<SensorEvent>
) -> impl IntoResponse {
    // THE FIREWALL CHECK
    {
        let guard = state.blacklist.lock().unwrap();
        if guard.contains(&payload.sensor_id) {
            println!("🔥 FIREWALL INTERCEPT: Blocked Malicious Packet from {}", payload.sensor_id);
            return (StatusCode::FORBIDDEN, "Access Denied: Sensor Blocked by AI Commander").into_response();
        }
    }

    let data = serde_json::to_vec(&payload).unwrap();
    let record = Record {
        key: Some(payload.sensor_id.as_bytes().to_vec()),
        value: Some(data),
        headers: std::collections::BTreeMap::new(),
        timestamp: Utc::now(),
    };

    state.producer
        .produce(vec![record], Compression::default())
        .await
        .expect("❌ Failed to write to Redpanda");

    (StatusCode::OK, "OK").into_response()
}