import socket
import urllib.request


def check_tcp_port(host, port, name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"[OK] {name} is reachable on {host}:{port}")
        else:
            print(f"[FAIL] {name} is NOT reachable on {host}:{port}")
        sock.close()
    except Exception as e:
        print(f"[ERROR] testing {name} on {host}:{port} - {e}")


def check_http_endpoint(url, name):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=2) as response:
            status = response.getcode()
            print(f"[OK] {name} is returning HTTP {status} at {url}")
    except Exception as e:
        print(f"[FAIL] {name} http request failed at {url} - {e}")


if __name__ == "__main__":
    print("--- Starting System Verification ---")

    # TCP Checks
    check_tcp_port("127.0.0.1", 9092, "Kafka Broker")
    check_tcp_port("127.0.0.1", 29092, "Kafka Internal")
    check_tcp_port("127.0.0.1", 6379, "Redis Server")
    check_tcp_port("127.0.0.1", 7077, "Spark Master RPC")

    # HTTP Checks
    check_http_endpoint("http://127.0.0.1:8081", "Schema Registry")
    check_http_endpoint("http://127.0.0.1:8082/#/overview", "Flink JobManager Web UI")
    check_http_endpoint("http://127.0.0.1:8080", "Spark Master Web UI")
    check_http_endpoint("http://127.0.0.1:8083", "Spark Worker Web UI")

    print("--- Verification Complete ---")
