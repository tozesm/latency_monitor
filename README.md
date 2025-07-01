# Latency Monitor
A very simple way to monitor latency with ICMP, HTTP and DNS probes.

Built with Python, SQLite and StreamLit

### build

    docker build . -t latency_monitor

### Run locally
    docker run -d --network host -v ./data:/data -v ./config:/config --name latency_monitor latency_monitor

### Docker Compose
```
services:  
  latency_monitor:
    image: latency_monitor
    container_name: latency_monitor
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
    volumes:
      - ./data_latency_monitor/config:/config
      - ./data_latency_monitor/data:/data
    network_mode: "host"
    restart: unless-stopped
```

### Sample config file

```
settings:
  interval: 30

services:
  - name: "Google DNS ping"
    agent: ping
    target: "8.8.8.8"

  - name: "Google DNS"
    agent: dns
    target: "8.8.8.8"
    domain: "www.google.com"
  
  - name: "Google"
    agent: http
    target: "https://www.google.com"
```