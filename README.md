# Opus: Market Data Streaming Pipeline

Opus is a real-time market data streaming pipeline that ingests historical ticker data, serializes it using Confluent Avro with a Schema Registry, and processes it into meaningful financial metrics (like Tumbling Window OHLC and EMAs) using Apache Flink (PyFlink 2.2.0).

---

## 1. Prerequisites
- **Docker & Docker Compose**: For running Kafka, Zookeeper, Schema Registry, and Flink clusters.
- **uv**: Ultrafast Python package installer and resolver.
- **Java 17**: Required natively if executing PyFlink jobs locally rather than strictly inside the Flink TaskManagers.

---

## 2. Infrastructure Setup
The pipeline relies on a containerized ecosystem consisting of a Kafka broker, a Schema Registry, a Flink JobManager, and a Flink TaskManager.

To start the infrastructure, run:
```bash
docker compose up -d
```

---

## 3. Data Setup
Historical market data must be placed in a specific directory structure for the Opus publisher to discover it securely.

By default, place your gzipped CSV data files organized by year and date matching this pattern:
```text
data/
  └── 2018/
      └── 20181101/
          ├── AAPL.csv.gz
          └── MSFT.csv.gz
```
*Note: Ensure the CSV contains columns like `Date`, `Timestamp`, `Price`, and `Quantity`.*

---

## 4. Downloading Flink JAR Dependencies
PyFlink requires Java JARs to communicate with Kafka and deserialize Avro messages via Confluent Schema Registry. 

Create a `lib/` directory in the root of the project:
```bash
mkdir -p lib
```

Download the following files from [Maven Central](https://mvnrepository.com/) and place them in the `lib/` directory:
1. `flink-sql-connector-kafka-4.0.1-2.0.jar`
2. `flink-sql-avro-confluent-registry-2.2.0.jar`
3. `flink-avro-2.2.0.jar`
4. `flink-sql-avro-2.2.0.jar`

PyFlink mounts these locally formatted files into its classpath on startup.

---

## 5. Running the Pipeline

Before executing commands, synchronize your Python environment using `uv`:
```bash
uv sync
```

### Step 1: Publishing Historical Data
Start the publisher to ingest the `.csv.gz` files from the `data/` directory. It parses nanosecond-precision timestamps, serializes the rows to Avro, and strictly orders the events chronologically into the `market` Kafka topic.

```bash
uv run opus market publish AAPL --start 20181101 --end 20181130 --speed 1.0
```
*(You can adjust the speed multiplier to playback the historical data faster or slower than real-time).*

### Step 2: Processing the Stream with PyFlink
While the publisher is streaming data to the `market` topic, launch the PyFlink streaming process in another terminal. 

This job computes aggregated metrics continuously (e.g., 5-minute Tumbling OHLC boundaries, Exponential Moving Averages) and sinks them into derived Kafka topics.

```bash
uv run opus process stream --create-topics
```
*Note: Flink jobs hang indefinitely by design. You will see PyFlink startup noise, but the terminal will appear "stuck" while it perpetually evaluates new records.*

### Step 3: Verifying the Processed Sinks
To ensure your newly processed metrics are populating downstream properly, check one of the outgoing target topics (e.g., `OHLC_5M`) using a simple consumer script or via your Docker image's console consumer:

```bash
docker exec kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic OHLC_5M --from-beginning
```

### Step 4: Launching the Live Dashboard
Start the Streamlit dashboard with the built-in CLI command:

```bash
uv run opus ui
```

The dashboard reads from Kafka metric topics (default: `OHLC_5M`, `EMA_9`, `EMA_12`) and renders live Plotly charts per selected ticker.
By default it connects to `localhost:9092` for host-based runs; if you run the dashboard inside Docker, use `kafka:29092` instead.
