# AutoPerf Mode Documentation

## Overview

AutoPerf is WaddlePerf's intelligent, tiered network performance monitoring system that automatically escalates testing depth based on detected anomalies. It provides continuous monitoring with minimal resource usage during normal operations while automatically performing comprehensive diagnostics when issues are detected.

## Tier System

### Tier 1: Basic Monitoring (Light Tests)
**Frequency**: Every X minutes (configurable, default: 5 minutes)  
**Purpose**: Continuous baseline monitoring with minimal resource impact

#### Tests Included:
- **Basic Ping**: ICMP echo to verify connectivity
- **HTTP GET**: Simple HTTP request to check service availability
- **DNS Resolution**: Resolve target hostname
- **TCP Connect**: Basic TCP handshake verification

#### Thresholds (Default):
```yaml
tier1_thresholds:
  ping_latency: 100ms      # Trigger if avg latency > 100ms
  packet_loss: 5%           # Trigger if loss > 5%
  http_response: 2000ms     # Trigger if HTTP response > 2s
  dns_timeout: 1000ms       # Trigger if DNS > 1s
```

### Tier 2: Intermediate Diagnostics
**Triggered When**: Tier 1 thresholds are exceeded  
**Purpose**: Identify the nature and scope of network issues

#### Tests Included:
- **Extended Ping**: 50 packets with statistics
- **Traceroute/MTR**: Path analysis to destination
- **iperf3 Quick Test**: 10-second bandwidth test
- **Port Scan**: Check common service ports
- **SSL/TLS Check**: Certificate validation
- **HTTP Trace**: Detailed HTTP connection analysis

#### Thresholds (Default):
```yaml
tier2_thresholds:
  bandwidth: 10Mbps         # Trigger if throughput < 10Mbps
  jitter: 50ms             # Trigger if jitter > 50ms
  hop_count: 20            # Trigger if hops > 20
  ssl_expiry: 7days        # Alert if cert expires < 7 days
```

### Tier 3: Comprehensive Analysis
**Triggered When**: Tier 2 thresholds are exceeded  
**Purpose**: Full diagnostic suite for root cause analysis

#### Tests Included:
- **Extended iperf3**: 60-second bidirectional test
- **Full MTR**: 100-cycle MTR with detailed statistics
- **Packet Capture**: 30-second tcpdump (if enabled)
- **System Diagnostics**: CPU, memory, network interface stats
- **Application Tests**: Custom application-specific tests
- **Multi-endpoint Testing**: Test multiple servers simultaneously

## Configuration

### Enable AutoPerf Mode

#### Environment Variables
```bash
export AUTOPERF_ENABLED=true
export AUTOPERF_INTERVAL=300  # 5 minutes
export AUTOPERF_LOG_LEVEL=info
export AUTOPERF_TIER1_ENABLED=true
export AUTOPERF_TIER2_ENABLED=true
export AUTOPERF_TIER3_ENABLED=true
```

#### Configuration File (autoperf.yml)
```yaml
autoperf:
  enabled: true
  interval: 300  # seconds
  
  tier1:
    enabled: true
    tests:
      - ping
      - http_check
      - dns_resolve
      - tcp_connect
    thresholds:
      ping_latency: 100
      packet_loss: 5
      http_response: 2000
      dns_timeout: 1000
  
  tier2:
    enabled: true
    auto_trigger: true
    tests:
      - extended_ping
      - mtr
      - iperf3_quick
      - port_scan
      - ssl_check
      - http_trace
    thresholds:
      bandwidth: 10000000  # 10Mbps in bits
      jitter: 50
      hop_count: 20
  
  tier3:
    enabled: true
    auto_trigger: true
    require_confirmation: false  # Set true for manual approval
    tests:
      - iperf3_full
      - mtr_extended
      - packet_capture
      - system_diagnostics
      - application_tests
    notification:
      email: ops-team@example.com
      slack: "#network-alerts"
```

### Ansible Playbook Setup
```yaml
# client/jobs/run/autoperf.yml
---
- name: Configure AutoPerf Mode
  hosts: localhost
  vars_files:
    - "{{ playbook_dir }}/../../vars/base.yml"
  
  tasks:
    - name: Setup AutoPerf cron job
      cron:
        name: "WaddlePerf AutoPerf"
        minute: "*/{{ autoperf_interval_minutes | default(5) }}"
        job: "/opt/waddleperf/bin/autoperf.sh"
        state: present
    
    - name: Configure tier thresholds
      template:
        src: autoperf.j2
        dest: /etc/waddleperf/autoperf.conf
        mode: '0644'
```

## Usage Examples

### Starting AutoPerf

#### Docker
```bash
docker run -d \
  --name waddleperf-autoperf \
  -e AUTOPERF_ENABLED=true \
  -e AUTOPERF_INTERVAL=300 \
  -e TARGET_SERVER=server.example.com \
  -v /var/log/waddleperf:/app/logs \
  ghcr.io/penguincloud/waddleperf-client:latest \
  ansible-playbook jobs/run/autoperf.yml
```

#### Systemd Service
```ini
[Unit]
Description=WaddlePerf AutoPerf Service
After=network.target

[Service]
Type=simple
User=waddleperf
ExecStart=/usr/local/bin/waddleperf-autoperf
Restart=always
RestartSec=10
Environment="AUTOPERF_ENABLED=true"
Environment="TARGET_SERVER=server.example.com"

[Install]
WantedBy=multi-user.target
```

#### Go Client
```bash
# Start with AutoPerf enabled
waddleperf tray \
  --server server.example.com \
  --interval 300 \
  --autostart \
  --log-file /var/log/waddleperf.log
```

### Monitoring AutoPerf

#### View Current Status
```bash
# Check AutoPerf status
curl http://localhost:8080/api/autoperf/status

# Response
{
  "enabled": true,
  "current_tier": 1,
  "last_run": "2024-01-20T10:30:00Z",
  "next_run": "2024-01-20T10:35:00Z",
  "triggers": [],
  "test_count": 1234
}
```

#### View Recent Triggers
```bash
# Get tier escalation history
curl http://localhost:8080/api/autoperf/triggers

# Response
{
  "triggers": [
    {
      "timestamp": "2024-01-20T09:15:00Z",
      "from_tier": 1,
      "to_tier": 2,
      "reason": "ping_latency exceeded: 150ms > 100ms",
      "duration": "45s"
    }
  ]
}
```

### Custom Test Integration

#### Adding Custom Tier 1 Test
```python
# client/bins/custom_test.py
import json
import time

def run_custom_test(target):
    start = time.time()
    # Your test logic here
    result = {
        "test": "custom_check",
        "target": target,
        "success": True,
        "latency": (time.time() - start) * 1000,
        "tier": 1
    }
    return json.dumps(result)

if __name__ == "__main__":
    import sys
    print(run_custom_test(sys.argv[1]))
```

#### Register in AutoPerf
```yaml
# Add to autoperf.yml
tier1:
  tests:
    - name: custom_check
      script: /app/bins/custom_test.py
      timeout: 30
      threshold:
        latency: 500
```

## Results and Reporting

### Result Storage
Results are stored in multiple formats:
- **Local Files**: `/var/log/waddleperf/autoperf/`
- **Database**: SQLite or configured database
- **S3**: If configured, JSON results uploaded
- **Syslog**: If configured, sent to syslog endpoint

### Result Format
```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "mode": "autoperf",
  "tier": 1,
  "target": "server.example.com",
  "tests": [
    {
      "name": "ping",
      "success": true,
      "metrics": {
        "avg_latency": 45.2,
        "packet_loss": 0,
        "jitter": 2.1
      }
    }
  ],
  "triggered_escalation": false,
  "next_tier": null
}
```

### Alerting

#### Email Notifications
```yaml
notifications:
  email:
    enabled: true
    smtp_server: smtp.example.com
    from: autoperf@example.com
    to: 
      - ops-team@example.com
      - network-admin@example.com
    triggers:
      - tier2_triggered
      - tier3_triggered
      - test_failure
```

#### Webhook Integration
```yaml
notifications:
  webhook:
    enabled: true
    url: https://hooks.slack.com/services/XXX/YYY/ZZZ
    events:
      - tier_escalation
      - threshold_exceeded
    format: slack  # slack, teams, discord, custom
```

## Best Practices

### 1. Threshold Tuning
- Start with default thresholds
- Monitor for false positives
- Adjust based on baseline performance
- Document threshold changes

### 2. Resource Management
```yaml
resource_limits:
  tier1:
    cpu_limit: "10%"
    memory_limit: "50MB"
    test_timeout: 30s
  tier2:
    cpu_limit: "25%"
    memory_limit: "100MB"
    test_timeout: 60s
  tier3:
    cpu_limit: "50%"
    memory_limit: "200MB"
    test_timeout: 300s
```

### 3. Scheduling Considerations
- Avoid business-critical hours for Tier 3
- Stagger tests across multiple clients
- Consider time zones for global deployments
- Implement backoff for repeated failures

### 4. Data Retention
```yaml
retention:
  tier1_results: 7d    # Keep for 7 days
  tier2_results: 30d   # Keep for 30 days
  tier3_results: 90d   # Keep for 90 days
  aggregated_data: 1y  # Keep yearly summaries
```

## Troubleshooting

### AutoPerf Not Running
```bash
# Check if enabled
grep AUTOPERF_ENABLED /etc/waddleperf/config

# Check cron job
crontab -l | grep autoperf

# Check logs
tail -f /var/log/waddleperf/autoperf.log
```

### Excessive Tier Escalations
```bash
# Review thresholds
cat /etc/waddleperf/autoperf.conf

# Analyze recent results
sqlite3 /var/lib/waddleperf/results.db \
  "SELECT * FROM triggers WHERE timestamp > datetime('now', '-1 day')"

# Adjust thresholds
vi /etc/waddleperf/autoperf.conf
systemctl restart waddleperf-autoperf
```

### Performance Impact
```bash
# Monitor resource usage
top -p $(pgrep -f autoperf)

# Reduce test frequency
export AUTOPERF_INTERVAL=600  # 10 minutes

# Disable specific tiers
export AUTOPERF_TIER3_ENABLED=false
```

## Integration Examples

### Prometheus Metrics
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'waddleperf-autoperf'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics/autoperf'
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "WaddlePerf AutoPerf",
    "panels": [
      {
        "title": "Tier Escalations",
        "targets": [
          {
            "expr": "rate(waddleperf_tier_escalations_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack Integration
```yaml
# logstash.conf
input {
  file {
    path => "/var/log/waddleperf/autoperf/*.json"
    codec => "json"
    type => "waddleperf-autoperf"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "waddleperf-autoperf-%{+YYYY.MM.dd}"
  }
}
```