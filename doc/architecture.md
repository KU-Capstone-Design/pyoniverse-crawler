# Pyoniverse Crawler
## Flowchart
```mermaid
sequenceDiagram
    actor Event
    participant Runner
    participant Spiders
    participant Middlewares
    participant Pipelines
    actor Web
    actor Database
    actor Storage

    Event ->>+ Runner: Run spiders
    par Runner to Spiders
        Runner ->>+ Spiders: Execute an spider
    and
        Runner ->>+ Spiders: Execute other spiders parallel
    Spiders ->>+ Middlewares: HTTP Request
    Middlewares ->>+ Web: Re-generated HTTP Request
    Web -->>- Middlewares: HTTP Response
    Middlewares -->>- Spiders: Re-generated HTTP Response
    Spiders --> Spiders: Process responses
    Spiders -) Pipelines: Send data
    Pipelines ->>+ Database: Save Data
    Database ->>- Pipelines: OK
    Pipelines ->>+ Storage: Save images
    Storage ->>- Pipelines: OK
    Spiders -->>- Runner: OK
    Spiders -->>- Runner: OK
    end
```
- Scrapy Framework에서 제공하는 Architecture를 동일하게 적용함
- Middlewares를 통해 Random UA 등의 요청을 함으로써 Banned 시간을 늦춤
- Pipelines를 통해 이미지 저장, 데이터 검증, 데이터 저장 등을 수행
- Runners를 통해 배치 실행
