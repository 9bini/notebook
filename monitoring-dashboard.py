#!/usr/bin/env python3
"""
실시간 로그 모니터링 대시보드
실시간으로 로그 상태를 모니터링하고 알림을 발송하는 시스템
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import aiohttp
import redis
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 설정
ELASTICSEARCH_URL = "http://localhost:9200"
REDIS_URL = "redis://localhost:6379"
LOG_INDEX_PATTERN = "logs-*"

app = FastAPI(title="Log Monitoring Dashboard")
templates = Jinja2Templates(directory="templates")

class LogAlert(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str
    environment: str
    alert_type: str

class MonitoringService:
    def __init__(self):
        self.es = AsyncElasticsearch([ELASTICSEARCH_URL])
        self.redis_client = redis.Redis.from_url(REDIS_URL)
        self.active_connections: List[WebSocket] = []

    async def get_log_statistics(self) -> Dict:
        """로그 통계 정보 조회"""
        try:
            # 최근 1시간 로그 통계
            query = {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": "now-1h"
                        }
                    }
                },
                "aggs": {
                    "log_levels": {
                        "terms": {
                            "field": "log_level.keyword",
                            "size": 10
                        }
                    },
                    "services": {
                        "terms": {
                            "field": "service_name.keyword", 
                            "size": 20
                        }
                    },
                    "environments": {
                        "terms": {
                            "field": "environment.keyword",
                            "size": 10
                        }
                    },
                    "error_timeline": {
                        "date_histogram": {
                            "field": "@timestamp",
                            "fixed_interval": "5m"
                        },
                        "aggs": {
                            "error_count": {
                                "filter": {
                                    "terms": {
                                        "log_level.keyword": ["ERROR", "FATAL"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            response = await self.es.search(
                index=LOG_INDEX_PATTERN,
                body=query,
                size=0
            )
            
            return {
                "total_logs": response["hits"]["total"]["value"],
                "log_levels": response["aggregations"]["log_levels"]["buckets"],
                "services": response["aggregations"]["services"]["buckets"],
                "environments": response["aggregations"]["environments"]["buckets"],
                "error_timeline": response["aggregations"]["error_timeline"]["buckets"]
            }
        except Exception as e:
            logging.error(f"통계 조회 에러: {e}")
            return {}

    async def get_recent_errors(self, limit: int = 50) -> List[Dict]:
        """최근 에러 로그 조회"""
        try:
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now-15m"
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "log_level.keyword": ["ERROR", "FATAL"]
                                }
                            }
                        ]
                    }
                },
                "sort": [
                    {
                        "@timestamp": {
                            "order": "desc"
                        }
                    }
                ]
            }
            
            response = await self.es.search(
                index=LOG_INDEX_PATTERN,
                body=query,
                size=limit
            )
            
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            logging.error(f"에러 로그 조회 실패: {e}")
            return []

    async def detect_anomalies(self) -> List[LogAlert]:
        """로그 패턴 이상 감지"""
        alerts = []
        
        try:
            # 에러 로그 급증 감지
            error_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now-5m"
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "log_level.keyword": ["ERROR", "FATAL"]
                                }
                            }
                        ]
                    }
                },
                "aggs": {
                    "services": {
                        "terms": {
                            "field": "service_name.keyword",
                            "size": 50
                        }
                    }
                }
            }
            
            response = await self.es.search(
                index=LOG_INDEX_PATTERN,
                body=error_query,
                size=0
            )
            
            total_errors = response["hits"]["total"]["value"]
            if total_errors > 20:  # 5분간 20개 이상 에러
                alerts.append(LogAlert(
                    timestamp=datetime.now(),
                    level="critical",
                    service="system",
                    message=f"에러 로그 급증 감지: {total_errors}건",
                    environment="production",
                    alert_type="error_spike"
                ))
            
            # 서비스별 에러 체크
            for bucket in response["aggregations"]["services"]["buckets"]:
                service_name = bucket["key"]
                error_count = bucket["doc_count"]
                
                if error_count > 10:  # 서비스별 10개 이상 에러
                    alerts.append(LogAlert(
                        timestamp=datetime.now(),
                        level="warning",
                        service=service_name,
                        message=f"서비스 에러 증가: {error_count}건",
                        environment="production", 
                        alert_type="service_error"
                    ))
            
            # 응답 시간 이상 감지
            slow_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": "now-5m"
                                    }
                                }
                            },
                            {
                                "range": {
                                    "response_time": {
                                        "gte": 1000
                                    }
                                }
                            }
                        ]
                    }
                }
            }
            
            slow_response = await self.es.search(
                index=LOG_INDEX_PATTERN,
                body=slow_query,
                size=0
            )
            
            slow_count = slow_response["hits"]["total"]["value"]
            if slow_count > 5:
                alerts.append(LogAlert(
                    timestamp=datetime.now(),
                    level="warning",
                    service="performance",
                    message=f"응답 시간 지연: {slow_count}건",
                    environment="production",
                    alert_type="performance"
                ))
                
        except Exception as e:
            logging.error(f"이상 감지 실패: {e}")
        
        return alerts

    async def send_alert(self, alert: LogAlert):
        """알림 발송"""
        # Redis에 알림 저장
        alert_data = alert.dict()
        alert_data['timestamp'] = alert.timestamp.isoformat()
        
        self.redis_client.lpush("alerts", json.dumps(alert_data))
        self.redis_client.ltrim("alerts", 0, 999)  # 최근 1000건만 유지
        
        # WebSocket으로 실시간 알림
        if self.active_connections:
            message = {
                "type": "alert",
                "data": alert_data
            }
            await self.broadcast_message(json.dumps(message))
        
        # 심각한 알림은 외부 시스템으로 전송
        if alert.level == "critical":
            await self.send_external_alert(alert)

    async def send_external_alert(self, alert: LogAlert):
        """외부 알림 시스템으로 전송 (Slack, Email 등)"""
        try:
            # Slack 웹훅 예시
            webhook_url = "YOUR_SLACK_WEBHOOK_URL"
            
            payload = {
                "text": f"🚨 Critical Alert: {alert.message}",
                "attachments": [
                    {
                        "color": "danger",
                        "fields": [
                            {"title": "Service", "value": alert.service, "short": True},
                            {"title": "Environment", "value": alert.environment, "short": True},
                            {"title": "Time", "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"), "short": True},
                            {"title": "Type", "value": alert.alert_type, "short": True}
                        ]
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        logging.error(f"Slack 알림 전송 실패: {response.status}")
                        
        except Exception as e:
            logging.error(f"외부 알림 전송 에러: {e}")

    async def broadcast_message(self, message: str):
        """모든 연결된 WebSocket에 메시지 브로드캐스트"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.active_connections.remove(connection)

monitoring = MonitoringService()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    monitoring.active_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        monitoring.active_connections.remove(websocket)

@app.get("/api/stats")
async def get_statistics():
    """로그 통계 API"""
    return await monitoring.get_log_statistics()

@app.get("/api/errors")
async def get_recent_errors():
    """최근 에러 로그 API"""
    return await monitoring.get_recent_errors()

@app.get("/api/alerts")
async def get_alerts():
    """최근 알림 목록 API"""
    alerts = monitoring.redis_client.lrange("alerts", 0, 99)
    return [json.loads(alert) for alert in alerts]

@app.post("/api/test-alert")
async def create_test_alert():
    """테스트 알림 생성"""
    test_alert = LogAlert(
        timestamp=datetime.now(),
        level="warning",
        service="test-service",
        message="테스트 알림입니다",
        environment="development",
        alert_type="test"
    )
    await monitoring.send_alert(test_alert)
    return {"message": "테스트 알림 생성됨"}

async def monitoring_loop():
    """백그라운드 모니터링 루프"""
    while True:
        try:
            alerts = await monitoring.detect_anomalies()
            for alert in alerts:
                await monitoring.send_alert(alert)
            
            # 통계 정보를 WebSocket으로 전송
            stats = await monitoring.get_log_statistics()
            if stats and monitoring.active_connections:
                message = {
                    "type": "stats",
                    "data": stats
                }
                await monitoring.broadcast_message(json.dumps(message))
                
        except Exception as e:
            logging.error(f"모니터링 루프 에러: {e}")
        
        await asyncio.sleep(30)  # 30초마다 실행

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작시 백그라운드 태스크 시작"""
    asyncio.create_task(monitoring_loop())

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8080)