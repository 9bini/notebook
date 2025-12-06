토이 프로젝트 진행 중 설정 파일을 하나의 `application.yml`에 모두 넣다 보니
가독성이 떨어지고 변경 시 위험성이 증가하는 문제를 경험했다.
이를 개선하기 위해 기능(MongoDB, Redis, Neo4j 등)별 설정 파일을 분리하는 방안을 고민했다.

Spring Boot에서는 `spring.config.import`를 이용하면 profile과 무관하게
필요한 기능 설정 파일들을 공통으로 불러올 수 있다.

```yaml
spring:
  config:
    import:
      - classpath:application-mongodb.yml
      - classpath:application-redis.yml
      - classpath:application-neo4j.yml
```
구조는 아래와 같이 환경 계층과 기능 계층으로 나눌 수 있다.

```
[환경 계층]
application.yml          # 공통
application-local.yml
application-dev.yml
application-prod.yml

[기능 계층]
application-mongodb.yml
application-redis.yml
application-neo4j.yml
```

## 장점

- 관심사 분리로 가독성과 변경 안정성 향상
  - 기능별 설정이 독립되어 있어, MongoDB·Redis·Neo4j 등 특정 기능을 수정할 때 해당 파일만 보면 된다.
  - 거대한 application.yml에서 스크롤하며 찾는 과정이 사라지고 실수 가능성도 감소한다.

- 환경 계층과 기능 계층의 역할이 명확해짐
  - 환경별 값(local/dev/prod)은 프로필 파일에서 관리하고 기능 공통 설정은 import 파일에서 관리해 책임이 분리된다.
  - 구조적 유지보수가 쉬워지고 팀 협업 효율도 높아진다

## 단점

- 분리 기준이 명확하지 않으면 오히려 복잡도가 증가
  - 기능별 분리가 지나치게 세분화되면 관리 포인트가 늘어 혼란이 커질 수 있다.
  - 큰 관심사 중심의 분리 기준이 필요하다.
