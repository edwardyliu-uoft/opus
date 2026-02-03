# Campus Cafe Event Pipeline

A Kafka-based event streaming pipeline for processing customer interaction events from a campus cafe system. Built with Python, Apache Kafka, and Confluent Schema Registry to demonstrate modern event-driven architecture patterns.

## Overview

This project implements a complete streaming data pipeline where customer events (orders, loyalty scans, etc.) are produced to Kafka, validated against a JSON Schema in Schema Registry, and consumed for real-time processing.

### Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Producer   │────────>│   Kafka     │────────>│  Consumer   │
│  (Python)   │  events │   Topic     │  events │  (Python)   │
└─────────────┘         │   'demo'    │         └─────────────┘
                        │ 3 partitions│
                        └──────┬──────┘
                               │
                               ▼
                        ┌─────────────┐
                        │  Schema     │
                        │  Registry   │
                        └─────────────┘
```

### Components

- **Producer** (`producer.py`) - Generates 5 random customer events with schema validation
- **Consumer** (`consumer.py`) - Subscribes to events and displays them with metadata
- **Schema Registry** - Centralized schema management with version control
- **Kafka Broker** - Message broker with 3 partitions for parallel processing
- **Kafka UI** - Web interface for monitoring topics and messages

## Prerequisites

- **Docker Desktop** - For running Kafka infrastructure
- **Python 3.12+** - Required for the application code
- **Git** - For version control (optional)

## Setup Instructions

### 1. Clone or Navigate to Project

```bash
cd assignment_01
```

### 2. Create Python Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (Git Bash/WSL):**
```bash
source venv/Scripts/activate
```

**Windows (CMD):**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -e .
```

This installs the project in editable mode with all dependencies from `pyproject.toml`:
- `confluent-kafka` - Kafka client with Schema Registry support
- `certifi`, `requests`, `httpx` - Schema Registry dependencies

## Running the Pipeline

### Step 1: Start Docker Services

Start the Kafka infrastructure (Kafka Broker, Schema Registry, and Kafka UI):

```bash
docker-compose up -d
```

**Expected Output:**
```
[x] Network kafka-network       Created
[x] Container broker-schema     Started
[x] Container schema-registry   Started
[x] Container kafka-ui          Started
```

**Verify services are running:**
```bash
docker-compose ps
```

**Wait 30-45 seconds** for Kafka to fully initialize before proceeding.

### Step 2: Create Kafka Topic

Create the `demo` topic with 3 partitions and replication factor of 1:

```bash
python create_topic.py
```

**Expected Output:**
```
Topic 'demo' created successfully with 3 partitions and a replication factor of 1.
```

If the topic already exists, you'll see:
```
Topic 'demo' already exists!
```

### Step 3: Run the Consumer (Terminal 1)

Open a terminal and start the consumer to listen for incoming events:

```bash
source venv/Scripts/activate  # Windows Git Bash
python consumer.py
```

**Expected Output:**
```
Starting Cafe Event Consumer with Schema Registry...
Listening to topic 'demo' (group: cafe-event-consumer-group)...
Press Ctrl+C to stop

================================================================================
```

The consumer will now wait for messages. **Keep this terminal open.**

### Step 4: Run the Producer (Terminal 2)

Open a **second terminal**, activate the virtual environment, and run the producer:

```bash
source venv/Scripts/activate  # Windows Git Bash
python producer.py
```

**Example Expected Output:**
```
Starting Cafe Event Producer with Schema Registry...
Generating and sending 5 random customer events to topic 'demo'...

Event 1: Diana Martinez ordered 1x Espresso ($4.05 CAD) - Member: False
Delivered: demo [1] offset=6
Event 2: Diana Martinez ordered 2x Cappuccino ($7.96 CAD) - Member: True
Delivered: demo [1] offset=7
Event 3: Charlie Davis ordered 2x Cold Brew ($3.6 CAD) - Member: False
Delivered: demo [0] offset=5
Event 4: Diana Martinez ordered 3x Americano ($7.98 CAD) - Member: False
Delivered: demo [1] offset=8
Event 5: Bob Smith ordered 3x Latte ($6.77 CAD) - Member: False
Delivered: demo [2] offset=9

Flushing remaining messages...
All messages sent successfully!
```

### Step 5: Verify Messages in Consumer

Switch back to **Terminal 1** (consumer) and you should see all 5 messages received:

**Expected Output:**
```
Message #1
        ├─ Partition: 0 | Offset: 5
        ├─ Kafka Timestamp: 2026-02-02 21:16:55
        ├─ Event ID: d19fc126-039e-445e-a159-38d1ef21c70f
        ├─ Customer: Charlie Davis (Non-Member)
        ├─ Order: 2x Cold Brew
        ├─ Amount: $3.60
        └─ Event Time (UTC): 2026-02-03T02:16:55.763294+00:00
--------------------------------------------------------------------------------
Message #2
        ├─ Partition: 1 | Offset: 6
        ├─ Kafka Timestamp: 2026-02-02 21:16:55
        ├─ Event ID: 7a019f48-052a-4b07-b411-68e982736c65
        ├─ Customer: Diana Martinez (Non-Member)
        ├─ Order: 1x Espresso
        ├─ Amount: $4.05
        └─ Event Time (UTC): 2026-02-03T02:16:55.342335+00:00
--------------------------------------------------------------------------------
Message #3
        ├─ Partition: 1 | Offset: 7
        ├─ Kafka Timestamp: 2026-02-02 21:16:55
        ├─ Event ID: 6dc9c4e6-674b-4dfb-9294-3b6b6e2bf07e
        ├─ Customer: Diana Martinez (Member)
        ├─ Order: 2x Cappuccino
        ├─ Amount: $7.96
        └─ Event Time (UTC): 2026-02-03T02:16:55.562581+00:00
--------------------------------------------------------------------------------
Message #4
        ├─ Partition: 1 | Offset: 8
        ├─ Kafka Timestamp: 2026-02-02 21:16:55
        ├─ Event ID: 40c2c2e5-0f25-4793-a0a1-6d6e80ae593c
        ├─ Customer: Diana Martinez (Non-Member)
        ├─ Order: 3x Americano
        ├─ Amount: $7.98
        └─ Event Time (UTC): 2026-02-03T02:16:55.964196+00:00
--------------------------------------------------------------------------------
Message #5
        ├─ Partition: 2 | Offset: 9
        ├─ Kafka Timestamp: 2026-02-02 21:16:56
        ├─ Event ID: 707a6cca-08c9-4ec2-b570-4d62bd1568e1
        ├─ Customer: Bob Smith (Non-Member)
        ├─ Order: 3x Latte
        ├─ Amount: $6.77
        └─ Event Time (UTC): 2026-02-03T02:16:56.164873+00:00
--------------------------------------------------------------------------------
```

**Success!** You should see exactly 5 messages displayed with all event details.

Press `Ctrl+C` in the consumer terminal to stop it gracefully:
```
Shutting down consumer...
Closing consumer...
Consumer closed. Total messages consumed: 5
```

## Verification Checklist

Use this checklist to confirm the pipeline is working correctly:

- [ ] Docker containers are running (`docker-compose ps` shows 3 containers up)
- [ ] Topic `demo` exists with 3 partitions
- [ ] Producer sends exactly 5 events without errors
- [ ] Consumer receives and displays all 5 events
- [ ] Each message shows: partition, offset, timestamp, event details
- [ ] Messages are distributed across the 3 partitions
- [ ] Consumer displays loyalty status: `(Member)` or `(Non-Member)`
- [ ] Consumer commits offsets after processing each message

## Kafka UI (Optional)

View messages in the web interface at: **http://localhost:8080**

Steps:
1. Open browser to `http://localhost:8080`
2. Click **Topics** -> **demo**
3. Click **Messages** tab
4. See all 5 messages

## Project Structure

```
assignment_01\
├── consumer.py                  # Kafka consumer with Schema Registry
├── producer.py                  # Kafka producer with Schema Registry
├── create_topic.py              # Topic creation utility
├── customer_event.schema.json   # JSON Schema definition
├── docker-compose.yml           # Docker services configuration
├── pyproject.toml               # Python project dependencies
├── README.md                    # This file
└── venv/                        # Python virtual environment
```

## Configuration Details

### Producer Configuration (`producer.py`)

| Parameter           | Value                 | Purpose                                                      |
| ------------------- | --------------------- | ------------------------------------------------------------ |
| `bootstrap.servers` | `localhost:9092`      | Kafka broker connection                                      |
| `client.id`         | `cafe-event-producer` | Producer identifier for logging/monitoring                   |
| `acks`              | `1`                   | Leader acknowledgment (balance of performance vs durability) |
| `key.serializer`    | `StringSerializer`    | Serializes message keys as UTF-8 strings                     |
| `value.serializer`  | `JSONSerializer`      | Serializes message values using Schema Registry              |

### Consumer Configuration (`consumer.py`)

| Parameter            | Value                       | Purpose                                                        |
| -------------------- | --------------------------- | -------------------------------------------------------------- |
| `bootstrap.servers`  | `localhost:9092`            | Kafka broker connection                                        |
| `group.id`           | `cafe-event-consumer-group` | Consumer group for coordinated partition consumption           |
| `auto.offset.reset`  | `earliest`                  | Read from beginning when no offset exists                      |
| `enable.auto.commit` | `False`                     | Manual offset commit after processing (at-least-once delivery) |
| `key.deserializer`   | `StringDeserializer`        | Deserializes keys from UTF-8 strings                           |
| `value.deserializer` | `JSONDeserializer`          | Deserializes values using Schema Registry                      |

**Note:** The consumer uses manual offset commits (`enable.auto.commit=False`) with `consumer.commit(asynchronous=False)` after each message to ensure at-least-once delivery semantics.

### Event Schema (`customer_event.schema.json`)

JSON Schema definition for customer events:

| Field           | Type    | Constraints   | Description                           |
| --------------- | ------- | ------------- | ------------------------------------- |
| `event_id`      | string  | required      | Unique event identifier (UUID format) |
| `customer_name` | string  | required      | Full name of the customer             |
| `drink_name`    | string  | required      | Name of beverage ordered              |
| `quantity`      | integer | required, >=1 | Number of items in order              |
| `amount`        | number  | required, >=0 | Transaction amount in CAD             |
| `is_member`     | boolean | required      | Loyalty program membership status     |
| `ts_utc`        | string  | required      | ISO 8601 UTC timestamp                |

## Troubleshooting

### Issue: "ModuleNotFoundError" when running scripts

**Solution:** Activate the virtual environment and install dependencies:
```bash
source venv/Scripts/activate
pip install -e .
```

### Issue: Producer fails with "Connection refused"

**Solution:** 
1. Verify Docker containers are running: `docker-compose ps`
2. Wait 30-45 seconds after starting Docker for Kafka initialization
3. Check Kafka logs: `docker-compose logs kafka`

### Issue: Consumer doesn't receive messages

**Solutions:**
1. Verify producer ran successfully (check for "All messages sent successfully!")
2. Confirm topic exists: `docker exec broker-schema kafka-topics --list --bootstrap-server localhost:9092`
3. Check consumer group offset: Run consumer again; it should continue from last committed offset
4. Reset consumer group to read from beginning (if needed):
   ```bash
   docker exec broker-schema kafka-consumer-groups --bootstrap-server localhost:9092 --group cafe-event-consumer-group --reset-offsets --to-earliest --topic demo --execute
   ```

### Issue: Schema Registry errors (HTTP 422)

**Solution:**
- Verify Schema Registry is running: `docker-compose ps`
- Check Schema Registry logs: `docker-compose logs schema-registry`
- Ensure `customer_event.schema.json` is of a valid JSON Schema format

### Issue: Port already in use (9092, 8080, or 8081)

**Solution:**
1. Check what's using the port: 
   - Windows: `netstat -ano | findstr :9092`
   - Linux/Mac: `lsof -i :9092`
2. Stop conflicting service or change port in `docker-compose.yml`
3. Restart services: `docker-compose down && docker-compose up -d`

## Cleanup

### Stop Services (Keep Data)

```bash
docker-compose stop
```

### Stop and Remove Containers

```bash
docker-compose down
```

### Complete Cleanup (Remove All Data)

```bash
docker-compose down -v
```

This removes all containers, networks, and volumes including stored messages.

---

**Project:** Campus Cafe Event Pipeline  
**Author:** Edward Liu (edwardy.liu@mail.utoronto.ca)  
**Version:** 1.0.0  
**GitHub:** https://github.com/edwardyliu-uoft/opus  
**Last Updated:** February 2, 2026

