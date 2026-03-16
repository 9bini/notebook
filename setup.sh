#!/bin/bash

# 로그 수집 시스템 설치 및 설정 스크립트

set -e

echo "🚀 로그 수집 시스템 설치를 시작합니다..."

# 필요한 도구들 설치 확인
check_requirements() {
    echo "📋 요구사항 확인 중..."
    
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker가 설치되어 있지 않습니다."
        echo "Docker 설치: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose가 설치되어 있지 않습니다."
        echo "Docker Compose 설치: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    echo "✅ 요구사항 확인 완료"
}

# 디렉토리 및 권한 설정
setup_directories() {
    echo "📁 디렉토리 설정 중..."
    
    # 로그 디렉토리 생성
    mkdir -p logs
    mkdir -p filebeat
    mkdir -p logstash/{config,patterns}
    mkdir -p prometheus
    mkdir -p grafana/provisioning/{dashboards,datasources}
    
    # 권한 설정
    chmod 755 logs
    chmod 644 filebeat/filebeat.yml
    chmod 644 logstash/config/pipeline.conf
    
    echo "✅ 디렉토리 설정 완료"
}

# Elasticsearch 인덱스 템플릿 설정
setup_elasticsearch() {
    echo "🔍 Elasticsearch 설정 대기 중..."
    
    # Elasticsearch가 준비될 때까지 대기
    until curl -s "http://localhost:9200/_cluster/health" > /dev/null; do
        echo "⏳ Elasticsearch 시작 대기 중..."
        sleep 10
    done
    
    echo "📊 인덱스 템플릿 설정 중..."
    
    # 로그 인덱스 템플릿 생성
    curl -X PUT "localhost:9200/_index_template/logs-template" \
        -H "Content-Type: application/json" \
        -d '{
            "index_patterns": ["logs-*"],
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "index.refresh_interval": "5s",
                    "index.codec": "best_compression"
                },
                "mappings": {
                    "properties": {
                        "@timestamp": { "type": "date" },
                        "log_level": { "type": "keyword" },
                        "service_name": { "type": "keyword" },
                        "environment": { "type": "keyword" },
                        "message": { "type": "text" },
                        "response_time": { "type": "float" }
                    }
                }
            }
        }'
    
    echo "✅ Elasticsearch 설정 완료"
}

# Kibana 대시보드 설정
setup_kibana() {
    echo "📊 Kibana 설정 대기 중..."
    
    # Kibana가 준비될 때까지 대기
    until curl -s "http://localhost:5601/api/status" > /dev/null; do
        echo "⏳ Kibana 시작 대기 중..."
        sleep 10
    done
    
    echo "🎨 기본 인덱스 패턴 생성 중..."
    
    # 인덱스 패턴 생성
    curl -X POST "localhost:5601/api/saved_objects/index-pattern" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d '{
            "attributes": {
                "title": "logs-*",
                "timeFieldName": "@timestamp"
            }
        }'
    
    echo "✅ Kibana 설정 완료"
}

# Grafana 데이터소스 설정
setup_grafana() {
    echo "📈 Grafana 설정 중..."
    
    # Grafana가 준비될 때까지 대기
    until curl -s "http://admin:admin@localhost:3000/api/health" > /dev/null; do
        echo "⏳ Grafana 시작 대기 중..."
        sleep 10
    done
    
    # Prometheus 데이터소스 추가
    curl -X POST "http://admin:admin@localhost:3000/api/datasources" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": true
        }'
    
    # Elasticsearch 데이터소스 추가
    curl -X POST "http://admin:admin@localhost:3000/api/datasources" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Elasticsearch",
            "type": "elasticsearch",
            "url": "http://elasticsearch:9200",
            "access": "proxy",
            "database": "logs-*",
            "jsonData": {
                "timeField": "@timestamp",
                "esVersion": "8.0.0"
            }
        }'
    
    echo "✅ Grafana 설정 완료"
}

# 테스트 로그 생성
generate_test_logs() {
    echo "🧪 테스트 로그 생성 중..."
    
    cat > logs/test-application.log << EOF
{"timestamp":"$(date -Iseconds)","level":"INFO","service":"web-service","message":"Application started successfully","version":"1.0.0"}
{"timestamp":"$(date -Iseconds)","level":"INFO","service":"web-service","message":"Processing user request","user_id":"12345","request_id":"$(uuidgen)"}
{"timestamp":"$(date -Iseconds)","level":"ERROR","service":"db-service","message":"Database connection failed","error":"Connection timeout after 30s"}
{"timestamp":"$(date -Iseconds)","level":"WARN","service":"auth-service","message":"Authentication attempt with invalid credentials","ip":"192.168.1.100"}
{"timestamp":"$(date -Iseconds)","level":"INFO","service":"web-service","message":"Request completed","response_time":150.5,"status_code":200}
EOF
    
    echo "✅ 테스트 로그 생성 완료"
}

# 상태 확인
check_status() {
    echo "🔍 시스템 상태 확인 중..."
    
    echo "📊 서비스 상태:"
    echo "- Elasticsearch: http://localhost:9200/_cluster/health"
    echo "- Kibana: http://localhost:5601"
    echo "- Grafana: http://localhost:3000 (admin/admin)"
    echo "- Prometheus: http://localhost:9090"
    
    echo ""
    echo "🔍 인덱스 상태:"
    curl -s "http://localhost:9200/_cat/indices/logs-*?v" || echo "인덱스가 아직 생성되지 않았습니다."
    
    echo ""
    echo "📈 로그 수집 상태:"
    echo "총 문서 수: $(curl -s 'http://localhost:9200/logs-*/_count' | jq -r '.count // 0')"
}

# 메인 실행
main() {
    echo "🌟 로그 수집 시스템 설치 시작"
    echo "================================"
    
    check_requirements
    setup_directories
    
    echo "🚀 Docker Compose 서비스 시작 중..."
    docker-compose up -d
    
    echo "⏳ 서비스 초기화 대기 중 (60초)..."
    sleep 60
    
    setup_elasticsearch
    setup_kibana
    setup_grafana
    generate_test_logs
    
    echo ""
    echo "🎉 설치 완료!"
    echo "=============="
    
    check_status
    
    echo ""
    echo "🔗 접속 주소:"
    echo "- Kibana: http://localhost:5601"
    echo "- Grafana: http://localhost:3000 (admin/admin)"
    echo "- Elasticsearch: http://localhost:9200"
    echo "- Prometheus: http://localhost:9090"
    echo ""
    echo "📝 로그 파일 위치: ./logs/"
    echo "🔧 설정 파일들: ./filebeat/, ./logstash/config/"
    echo ""
    echo "💡 사용법:"
    echo "1. Kibana에서 'logs-*' 인덱스 패턴으로 로그 확인"
    echo "2. Grafana에서 대시보드 생성"
    echo "3. ./logs/ 디렉토리에 로그 파일 추가"
}

# 스크립트 실행
main "$@"