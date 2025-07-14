# monitor.py
import sqlite3
import yaml
import time
from multiping import MultiPing
import requests
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import dns.resolver


DB_PATH = 'data/monitoring.db'
CONFIG_PATH = 'config/config.yaml'

# Thread-safe SQLite connection using connection per thread
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Initialize database schema
def init_db():
    logging.info('Initializing database schema')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_checks (
            id INTEGER PRIMARY KEY,
            service_name TEXT,
            agent_type TEXT,
            target TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            success INTEGER,
            response_time REAL
        )
    ''')
    conn.commit()
    conn.close()

def load_config(file_path):
    logging.info(f'Loading configuration from {file_path}')
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)
    
def ping_check(ip):
    logging.debug(f'Performing ping check on {ip}')
    try:
        mp = MultiPing([ip])
        mp.send()
        responses, _ = mp.receive(1)
        success = ip in responses
        latency = responses[ip] * 1000 if success else None
        logging.debug(f'Ping check result for {ip}: success={success}, latency={latency}')
        return success, latency
    except Exception as e:
        logging.error(f'Ping check failed for {ip}: {e}')
        return False, None

def http_check(url):
    logging.debug(f'Performing HTTP check on {url}')
    try:
        response = requests.get(url, timeout=5)
        success = 200 <= response.status_code < 300
        latency = response.elapsed.total_seconds() * 1000
        logging.debug(f'HTTP check result for {url}: success={success}, latency={latency}')
        return success, latency
    except requests.exceptions.RequestException as e:
        logging.error(f'HTTP check failed for {url}: {e}')
        return False, None

def dns_check(dns_server, domain):
    logging.debug(f'Performing DNS check on {domain}')
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        start = time.time()
        answers = resolver.resolve(domain, 'A')
        latency = (time.time() - start) * 1000  # milliseconds
        ips = [rdata.to_text() for rdata in answers]
        success = len(ips) > 0
        logging.debug(f'DNS check result for {domain}: success={success}, latency={latency}, ips={ips}')
        return success, latency
    except Exception as e:
        logging.error(f'DNS check failed for {domain}: {e}')
        return False, None
    
def log_result(service, success, response_time):
    logging.debug(f'Logging result for service {service["name"]}: success={success}, response_time={response_time}')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO service_checks (service_name, agent_type, target, success, response_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (service['name'], service['agent'], service['target'], int(success), response_time))
    conn.commit()
    conn.close()

def run_checks():
    logging.debug('Running all service checks')
    config = load_config(CONFIG_PATH)

    for service in config['services']:
        if service['agent'] == 'ping':
            success, latency = ping_check(service['target'])
        elif service['agent'] == 'http':
            success, latency = http_check(service['target'])
        elif service['agent'] == 'dns':
            success, latency = dns_check(service['target'],service['domain'])
        else:
            logging.error(f'Unknown agent type {service["agent"]} for service {service["name"]}')
            continue
        log_result(service, success, latency)

if __name__ == "__main__":
    config = load_config(CONFIG_PATH)
    interval = config["settings"]["interval"]
    logLevel = config["settings"]["logLevel"]

    logging.basicConfig(level=logLevel.upper(), format='%(asctime)s - %(levelname)s - %(message)s')
    
    logging.info('Starting latency monitoring application')

    init_db()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_checks, 'interval', seconds=interval)  # Base interval
    scheduler.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown()
