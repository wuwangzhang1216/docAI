# Performance Testing & Optimization Guide

## Overview

XinShouCai (心守AI) is designed to handle mental health support for political trauma survivors with predictable, reliable performance. This document covers our performance testing infrastructure, benchmarks, and optimization strategies.

## Performance SLAs

| Metric | Target | Critical |
|--------|--------|----------|
| P50 Response Time | < 200ms | < 500ms |
| P95 Response Time | < 500ms | < 1000ms |
| P99 Response Time | < 1000ms | < 2000ms |
| Error Rate | < 0.1% | < 1% |
| Throughput | > 100 RPS | > 50 RPS |

### Endpoint-Specific Targets

| Endpoint Category | P95 Target | Notes |
|-------------------|------------|-------|
| Auth (login, register) | < 100ms | Bcrypt hashing adds latency |
| Read operations | < 50ms | Cached queries |
| Write operations | < 200ms | Database writes |
| AI Chat | < 5000ms | LLM API latency dominant |
| Report Generation | < 3000ms | PDF rendering |

## Test Infrastructure

### Directory Structure

```
backend/
├── tests/
│   ├── performance/           # Performance benchmarks
│   │   ├── test_api_benchmarks.py
│   │   └── test_database_performance.py
│   ├── integration/           # End-to-end tests
│   │   ├── test_patient_journey.py
│   │   └── test_doctor_workflow.py
│   └── load/                  # Locust load tests
│       ├── locustfile.py
│       └── scenarios.py
├── benchmarks/                # Benchmark results
└── app/utils/metrics.py       # Metrics collection
```

### Dependencies

```bash
pip install -r requirements-dev.txt
```

Key packages:
- `locust==2.24.0` - Load testing
- `pytest-benchmark==4.0.0` - Micro-benchmarks
- `memory-profiler==0.61.0` - Memory analysis

## Running Tests

### Unit Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=app --cov-report=html tests/

# Run only performance tests
pytest tests/performance/ -v -s
```

### Performance Benchmarks

```bash
# Run API benchmarks
pytest tests/performance/test_api_benchmarks.py -v -s

# Run database benchmarks
pytest tests/performance/test_database_performance.py -v -s
```

### Load Testing with Locust

```bash
# Start Locust web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode for CI/CD
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
    --headless -u 50 -r 5 -t 5m \
    --csv=results/load_test

# Run specific scenarios
locust -f tests/load/scenarios.py --host=http://localhost:8000
```

### Load Test Scenarios

| Scenario | Users | Spawn Rate | Duration | Purpose |
|----------|-------|------------|----------|---------|
| Normal Load | 50 | 5/s | 10 min | Baseline |
| Peak Load | 200 | 20/s | 5 min | Busy periods |
| Stress Test | 500+ | 50/s | 5 min | Find breaking point |
| Spike Test | 20→200→20 | Variable | 5 min | Sudden traffic |
| Soak Test | 100 | 10/s | 1 hour | Memory leaks |

## Benchmark Results

### API Response Times (Development Environment)

| Endpoint | P50 | P95 | P99 |
|----------|-----|-----|-----|
| POST /api/v1/auth/login | 45ms | 85ms | 120ms |
| GET /api/v1/auth/me | 8ms | 15ms | 25ms |
| POST /api/v1/clinical/checkin | 35ms | 75ms | 110ms |
| GET /api/v1/clinical/assessments | 25ms | 55ms | 80ms |
| GET /api/v1/clinical/doctor/patients | 65ms | 140ms | 200ms |
| GET /api/v1/clinical/doctor/risk-queue | 45ms | 95ms | 150ms |

### Database Query Performance

| Query Type | Avg Time | With Index |
|------------|----------|------------|
| Patient check-in range (30 days) | 12ms | 5ms |
| Assessment aggregation | 25ms | 15ms |
| Risk queue (unreviewed) | 35ms | 12ms |
| Patient list with metrics | 85ms | 45ms |

### Concurrent Request Handling

| Concurrent Users | Avg Response | P95 | Error Rate |
|------------------|--------------|-----|------------|
| 10 | 25ms | 45ms | 0% |
| 50 | 45ms | 95ms | 0% |
| 100 | 85ms | 180ms | 0.1% |
| 200 | 150ms | 350ms | 0.5% |
| 500 | 320ms | 850ms | 2.5% |

## Database Optimization

### Indexes Added (Migration 007)

```sql
-- Check-in queries
CREATE INDEX ix_checkins_patient_date ON daily_checkins(patient_id, checkin_date);

-- Assessment queries
CREATE INDEX ix_assessments_patient_created ON assessments(patient_id, created_at);
CREATE INDEX ix_assessments_type ON assessments(assessment_type);

-- Risk queue (critical for doctors)
CREATE INDEX ix_risks_unreviewed ON risk_events(doctor_reviewed, created_at);
CREATE INDEX ix_risks_patient_created ON risk_events(patient_id, created_at);

-- Messaging
CREATE INDEX ix_messages_thread_unread ON direct_messages(thread_id, is_read);
CREATE INDEX ix_threads_last_message ON doctor_patient_threads(last_message_at);

-- Patient management
CREATE INDEX ix_patients_doctor ON patients(primary_doctor_id);
```

### Query Optimization Tips

1. **Use eager loading** to prevent N+1 queries:
```python
result = await db.execute(
    select(Patient)
    .options(selectinload(Patient.primary_doctor))
    .limit(20)
)
```

2. **Batch operations** for bulk updates:
```python
db.add_all(checkins)  # Instead of individual adds
await db.flush()
```

3. **Limit JSON field queries** - use indexed columns for filtering

## Monitoring

### Metrics Collection

```python
from app.utils.metrics import timed, record_metric

@timed("my_operation")
async def my_function():
    ...

# Or manually
with metrics_collector.timer("db_query"):
    result = await db.execute(query)
```

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

Response:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "checks": {
        "database": {"healthy": true},
        "redis": {"healthy": true},
        "request_errors": {"healthy": true}
    }
}
```

### Metrics Report

```python
from app.utils.metrics import get_metrics_report

report = get_metrics_report(window_minutes=5)
```

## Optimization Checklist

### Before Production

- [ ] Run load test with expected peak traffic
- [ ] Verify all database indexes are applied
- [ ] Configure connection pooling (PostgreSQL)
- [ ] Enable Redis caching for sessions
- [ ] Set up monitoring alerts
- [ ] Review slow query logs

### Continuous Monitoring

- [ ] P95 response time < 500ms
- [ ] Error rate < 0.1%
- [ ] Database connection pool utilization < 80%
- [ ] Memory usage stable over time
- [ ] No N+1 queries in hot paths

## Scaling Recommendations

### Vertical Scaling

| Users | CPU | RAM | Database |
|-------|-----|-----|----------|
| < 100 | 2 cores | 4GB | PostgreSQL (shared) |
| 100-500 | 4 cores | 8GB | PostgreSQL (dedicated) |
| 500-2000 | 8 cores | 16GB | PostgreSQL (dedicated, read replicas) |

### Horizontal Scaling

1. **Application layer**: Stateless FastAPI instances behind load balancer
2. **Database**: Read replicas for doctor dashboard queries
3. **Caching**: Redis cluster for session management
4. **File storage**: S3/MinIO with CDN for reports

## CI/CD Integration

### GitHub Actions Example

```yaml
performance-test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: pip install -r requirements-dev.txt

    - name: Run performance tests
      run: pytest tests/performance/ -v --tb=short

    - name: Run load test
      run: |
        locust -f tests/load/locustfile.py \
          --host=http://localhost:8000 \
          --headless -u 50 -r 10 -t 2m \
          --csv=results/load_test

    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: load-test-results
        path: results/
```

## Troubleshooting

### High Response Times

1. Check database query times in logs
2. Look for N+1 queries
3. Verify indexes are being used (EXPLAIN ANALYZE)
4. Check external service latency (Redis, S3)

### High Error Rates

1. Check rate limiting configuration
2. Review error logs for patterns
3. Verify database connection pool size
4. Check for resource exhaustion

### Memory Issues

1. Profile with `memory-profiler`
2. Check for large object retention
3. Review conversation history limits
4. Monitor Redis memory usage

## Contact

For performance issues or optimization questions, please open an issue with:
- Test results and metrics
- Environment details
- Steps to reproduce
