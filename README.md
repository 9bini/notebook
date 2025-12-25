# 🚀 서버 로그 수집 시스템

운영 및 테스트 환경에서 대규모 서버 로그를 실시간으로 수집, 처리, 저장, 분석할 수 있는 통합 로그 관리 시스템입니다.

## ✨ 주요 기능

### 🔄 실시간 로그 수집
- **다중 소스 지원**: 애플리케이션 로그, 시스템 로그, 액세스 로그
- **자동 파싱**: JSON, 일반 텍스트, 멀티라인 로그 지원
- **실시간 처리**: Filebeat + Logstash를 통한 실시간 수집 및 처리

### 📊 중앙화된 저장 및 검색
- **Elasticsearch**: 고성능 전문 검색 엔진
- **구조화된 인덱싱**: 환경별, 서비스별 인덱스 자동 생성
- **효율적 압축**: 스토리지 비용 최적화

### 🔍 강력한 시각화
- **Kibana**: 로그 검색 및 대시보드
- **Grafana**: 메트릭 기반 모니터링
- **실시간 대시보드**: WebSocket 기반 실시간 업데이트

### 🚨 지능형 알림 시스템
- **이상 감지**: 에러 급증, 성능 저하 자동 감지
- **다채널 알림**: Slack, Email, 웹훅 지원
- **알림 그룹화**: 스팸 방지 및 효율적 알림

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Log Sources   │ -> │   Collection    │ -> │   Processing    │
│                 │    │                 │    │                 │
│ • App Logs      │    │ • Filebeat      │    │ • Logstash      │
│ • System Logs   │    │ • Docker Logs   │    │ • Parsing       │
│ • Access Logs   │    │ • Syslog        │    │ • Filtering     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐            │
│   Visualization │ <- │     Storage     │ <──────────┘
│                 │    │                 │
│ • Kibana        │    │ • Elasticsearch │
│ • Grafana       │    │ • Redis Cache   │
│ • Custom UI     │    │ • Prometheus    │
└─────────────────┘    └─────────────────┘
```

## 🚀 빠른 시작

### 1. 시스템 요구사항
- Docker 20.10+
- Docker Compose 2.0+
- 최소 8GB RAM
- 20GB 이상 디스크 공간

### 2. 설치 및 실행
```bash
# 저장소 클론
git clone <repository-url>
cd log-collection-system

# 자동 설치 및 설정
./setup.sh
```

### 3. 수동 실행 (선택사항)
```bash
# 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

## 🔗 접속 주소

설치 완료 후 다음 주소로 접속 가능합니다:

- **Kibana**: http://localhost:5601 - 로그 검색 및 분석
- **Grafana**: http://localhost:3000 (admin/admin) - 메트릭 대시보드
- **Elasticsearch**: http://localhost:9200 - 검색 API
- **Prometheus**: http://localhost:9090 - 메트릭 수집
- **모니터링 대시보드**: http://localhost:8080 - 실시간 모니터링

## 📁 프로젝트 구조

```
log-collection-system/
├── docker-compose.yml          # 메인 서비스 정의
├── setup.sh                    # 자동 설치 스크립트
├── monitoring-dashboard.py     # 실시간 모니터링 대시보드
├── requirements.txt            # Python 의존성
├── filebeat/
│   └── filebeat.yml           # 로그 수집 설정
├── logstash/
│   ├── config/
│   │   └── pipeline.conf      # 로그 처리 파이프라인
│   └── patterns/              # 커스텀 grok 패턴
├── prometheus/
│   ├── prometheus.yml         # 메트릭 수집 설정
│   └── rules/
│       └── log-alerts.yml     # 알림 규칙
├── alertmanager/
│   └── alertmanager.yml       # 알림 라우팅 설정
└── logs/                      # 로그 파일 디렉토리
```

## 🔧 설정 가이드

### 로그 수집 대상 추가

1. **애플리케이션 로그 추가**
```yaml
# filebeat/filebeat.yml에 추가
- type: log
  enabled: true
  paths:
    - /path/to/your/app/*.log
  fields:
    logtype: application
    service: your-service-name
```

2. **Docker 컨테이너 로그 수집**
```yaml
# docker-compose.yml에 레이블 추가
services:
  your-service:
    labels:
      - "logging=enabled"
```

### 알림 설정

1. **Slack 알림 설정**
```yaml
# alertmanager/alertmanager.yml 수정
slack_configs:
- api_url: 'YOUR_SLACK_WEBHOOK_URL'
  channel: '#alerts'
```

2. **이메일 알림 설정**
```yaml
# alertmanager/alertmanager.yml 수정
global:
  smtp_smarthost: 'your-smtp-server:587'
  smtp_from: 'alerts@your-domain.com'
```

## 📊 사용법

### 1. Kibana에서 로그 분석
1. http://localhost:5601 접속
2. "Discover" 메뉴에서 `logs-*` 인덱스 패턴 선택
3. 시간 범위 설정 및 필터링
4. 시각화 및 대시보드 생성

### 2. Grafana에서 메트릭 모니터링
1. http://localhost:3000 접속 (admin/admin)
2. Prometheus 데이터소스 확인
3. 대시보드 생성 또는 템플릿 사용

### 3. 실시간 모니터링 대시보드
1. Python 의존성 설치: `pip install -r requirements.txt`
2. 대시보드 실행: `python monitoring-dashboard.py`
3. http://localhost:8080 접속

## 🔍 주요 쿼리 예시

### Elasticsearch 쿼리
```json
// 최근 1시간 에러 로그
GET logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"range": {"@timestamp": {"gte": "now-1h"}}},
        {"term": {"log_level": "ERROR"}}
      ]
    }
  }
}

// 서비스별 응답 시간 통계
GET logs-*/_search
{
  "aggs": {
    "services": {
      "terms": {"field": "service_name.keyword"},
      "aggs": {
        "avg_response_time": {
          "avg": {"field": "response_time"}
        }
      }
    }
  }
}
```

### Kibana KQL 쿼리
```kql
// 특정 서비스의 에러 로그
service_name: "payment-service" AND log_level: ERROR

// 응답 시간이 1초 이상인 요청
response_time: >1000

// 특정 사용자 관련 로그
user_id: "12345" OR message: *user_12345*
```

## ⚠️ 운영 가이드

### 성능 최적화
1. **Elasticsearch 설정**
   - 샤드 수 최적화 (인덱스 크기에 따라)
   - 리플리카 수 조정 (고가용성 vs 성능)
   - 메모리 할당 최적화

2. **로그 보관 정책**
   - Hot-Warm-Cold 아키텍처 구성
   - ILM (Index Lifecycle Management) 정책 설정
   - 압축 및 아카이빙 자동화

### 보안 설정
1. **네트워크 보안**
   - 방화벽 규칙 설정
   - VPN/프록시를 통한 접근 제한
   - SSL/TLS 암호화 활성화

2. **데이터 보안**
   - 민감 정보 마스킹
   - 사용자 인증 및 권한 관리
   - 감사 로그 활성화

### 모니터링 및 알림
1. **시스템 메트릭 모니터링**
   - CPU, 메모리, 디스크 사용량
   - 네트워크 I/O 및 디스크 I/O
   - 서비스별 응답 시간

2. **비즈니스 메트릭 모니터링**
   - 에러율 추이
   - 사용자 행동 패턴
   - 비즈니스 KPI 추적

## 🐛 문제 해결

### 일반적인 문제들

1. **Elasticsearch 클러스터가 시작되지 않음**
```bash
# 메모리 부족 확인
docker stats elasticsearch

# 로그 확인
docker logs elasticsearch

# 권한 문제 해결
sudo chown -R 1000:1000 elasticsearch_data/
```

2. **Logstash 파이프라인 오류**
```bash
# 설정 파일 구문 확인
docker exec logstash /usr/share/logstash/bin/logstash --config.test_and_exit

# 파이프라인 재로드
docker exec logstash curl -X POST "localhost:9600/_node/pipeline/main/_reload"
```

3. **Filebeat가 로그를 수집하지 않음**
```bash
# Filebeat 상태 확인
docker exec filebeat filebeat test config
docker exec filebeat filebeat test output

# 권한 문제 해결
sudo chmod -R 755 logs/
```

### 성능 튜닝

1. **높은 CPU 사용률**
   - Logstash 워커 수 조정
   - 불필요한 필터 제거
   - 배치 크기 최적화

2. **메모리 부족**
   - JVM 힙 크기 조정
   - 불필요한 필드 제거
   - 인덱스 최적화

3. **디스크 공간 부족**
   - 로그 로테이션 설정
   - 오래된 인덱스 삭제
   - 압축 설정 활성화

## 📚 참고 자료

- [Elasticsearch 공식 문서](https://www.elastic.co/guide/en/elasticsearch/reference/current/)
- [Logstash 설정 가이드](https://www.elastic.co/guide/en/logstash/current/)
- [Kibana 사용법](https://www.elastic.co/guide/en/kibana/current/)
- [Prometheus 모니터링](https://prometheus.io/docs/)
- [Grafana 대시보드](https://grafana.com/docs/)

## 🤝 기여하기

1. Fork 저장소
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문의사항이나 도움이 필요한 경우:
- GitHub Issues: 버그 리포트 및 기능 요청
- Email: support@your-domain.com
- Wiki: 상세한 사용법 및 FAQ