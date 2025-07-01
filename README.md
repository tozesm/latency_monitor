# simple_intranet_latency
A very simple way to monitor latency with ICMP, HTTP and DNS probes.

Built with Python, SQLite and StreamLit

### build

    docker build . -t intranet_latency

### Run locally
    docker run -d -v ./data:/data -v ./config:/config --name intranet_latency --network host intranet_latency

### Docker Compose
```
services:  
  intranet_latency:
    image: intranet_latency
    container_name: intranet_latency
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
    volumes:
      - ./data_intranet_latency/config:/config
      - ./data_intranet_latency/data:/data
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