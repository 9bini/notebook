# 🚀 서버 로그 수집 시스템 아키텍처

## 📋 시스템 개요

운영/테스트 환경에서 대규모 서버 로그를 효율적으로 수집, 처리, 저장, 분석할 수 있는 통합 로그 관리 시스템입니다.

### 🎯 핵심 목표
- **실시간 로그 수집**: 다양한 서버에서 발생하는 로그의 실시간 수집
- **중앙화 관리**: 분산된 서버 로그의 중앙 집중 관리
- **효율적 저장**: 대용량 로그 데이터의 비용 효율적 저장
- **빠른 검색**: 로그 데이터의 실시간 검색 및 분석
- **모니터링**: 이상 상황 감지 및 실시간 알림

## 🏗️ 아키텍처 설계

### 1. 수집 계층 (Collection Layer)
```
[Application Servers]
        ↓
[Log Agents] → [Message Queue] → [Processing Pipeline]
```

**주요 컴포넌트:**
- **Filebeat/Fluentd**: 로그 파일 수집 에이전트
- **Vector**: 고성능 로그 라우터 및 변환기
- **Kafka**: 대용량 메시지 큐 (버퍼링, 내결함성)

### 2. 처리 계층 (Processing Layer)
```
[Raw Logs] → [Parse/Filter] → [Enrich] → [Route]
```

**처리 기능:**
- 로그 파싱 및 구조화
- 필터링 및 노이즈 제거
- 메타데이터 추가 (timestamp, source, environment)
- 로그 레벨별 라우팅

### 3. 저장 계층 (Storage Layer)
```
Hot Data (Elasticsearch) ← Real-time Search
Warm Data (S3/GCS) ← Medium-term Storage  
Cold Data (Glacier) ← Long-term Archive
```

### 4. 분석 계층 (Analytics Layer)
```
[Kibana/Grafana] ← Visualization
[Alertmanager] ← Monitoring
[Custom APIs] ← Application Integration
```

## 🛠️ 기술 스택 선택

### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)
**장점:**
- 성숙한 생태계
- 강력한 전문 검색
- 풍부한 시각화

**단점:**
- 높은 리소스 사용량
- 복잡한 운영

### Option 2: EFK Stack (Elasticsearch, Fluentd, Kibana)
**장점:**
- 더 가벼운 수집 에이전트
- 유연한 플러그인 시스템
- Ruby 기반 확장성

### Option 3: Grafana Loki Stack
**장점:**
- 낮은 운영 비용
- 프로메테우스와 자연스러운 통합
- 레이블 기반 인덱싱

### Option 4: 클라우드 관리형 서비스
**AWS:** CloudWatch Logs, Kinesis Data Firehose
**GCP:** Cloud Logging, Pub/Sub
**Azure:** Azure Monitor, Event Hubs

## 🔧 구현 예시

### Docker Compose 기반 ELK 스택
```yaml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    ports:
      - "5044:5044"
      - "9600:9600"
    volumes:
      - ./logstash/config:/usr/share/logstash/pipeline
    environment:
      - "LS_JAVA_OPTS=-Xmx512m -Xms512m"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /var/log:/var/log:ro
    depends_on:
      - logstash

volumes:
  elasticsearch_data:
```

### Filebeat 설정
```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/app/*.log
  fields:
    logtype: application
    environment: production
  fields_under_root: true
  multiline.pattern: '^\d{4}-\d{2}-\d{2}'
  multiline.negate: true
  multiline.match: after

- type: docker
  containers.ids: "*"
  processors:
  - add_docker_metadata: ~

output.logstash:
  hosts: ["logstash:5044"]

processors:
- add_host_metadata:
    when.not.contains.tags: forwarded
```

### Logstash 파이프라인
```ruby
# logstash/config/pipeline.conf
input {
  beats {
    port => 5044
  }
}

filter {
  # JSON 로그 파싱
  if [fields][logtype] == "application" {
    json {
      source => "message"
    }
  }
  
  # 날짜 파싱
  date {
    match => [ "timestamp", "yyyy-MM-dd HH:mm:ss" ]
  }
  
  # 로그 레벨 정규화
  mutate {
    uppercase => [ "level" ]
  }
  
  # 불필요한 필드 제거
  mutate {
    remove_field => [ "agent", "ecs", "host" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{[fields][environment]}-%{+YYYY.MM.dd}"
    template_name => "logs"
    template_pattern => "logs-*"
    template => {
      "index_patterns" => ["logs-*"],
      "settings" => {
        "number_of_shards" => 1,
        "number_of_replicas" => 0
      }
    }
  }
  
  stdout {
    codec => rubydebug
  }
}
```