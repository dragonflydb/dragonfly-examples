# Magento + Dragonfly Benchmark Guide

This guide explains how to run load tests on your Magento + Dragonfly setup.

## Prerequisites

1. **Magento installed and running** (via `configure-dragonfly.sh`)
2. **Dragonfly running** on configured IP
3. **k6 installed** for load testing

### Install k6

```bash
# Ubuntu/Debian
sudo snap install k6

# macOS
brew install k6
```

## Quick Start

### 1. Install Sample Data

First, populate Magento with test products:

```bash
docker exec -it magento_app bash /var/www/html/setup-sample-data.sh
```

This installs:
- Categories (Women, Men, Gear, Training, Sale)
- 46 configurable products
- 2000+ simple products
- Sample customers and orders

**Time:** Several minutes

### 2. Run Load Test

```bash
MAGENTO_URL=http://testing.host k6 run k6-load-test.js
```

**Default test profile:**
- Ramp up: 0 → 20 → 50 → 100 users
- Duration: 5 minutes
- Mix of pages: homepage, categories, search

## Test Scenarios

### Standard Load Test (default)

```bash
MAGENTO_URL=http://testing.host k6 run k6-load-test.js
```

- 100 concurrent users max
- 5 minute duration
- Good for baseline performance

### Quick Test

```bash
MAGENTO_URL=http://testing.host k6 run --duration 1m --vus 50 k6-load-test.js
```

- 50 users for 1 minute
- Fast sanity check

### Stress Test

```bash
MAGENTO_URL=http://testing.host k6 run --duration 10m --vus 200 k6-load-test.js
```

- 200 users for 10 minutes
- Find breaking point

### Spike Test

```bash
MAGENTO_URL=http://testing.host k6 run --stage 1m:10,30s:200,1m:200,30s:10 k6-load-test.js
```

- Sudden spike from 10 to 200 users
- Tests cache under sudden load

## Monitoring During Tests

### Monitor Dragonfly (on Dragonfly server)

```bash
# Watch cache stats in real-time
watch -n 1 'redis-cli INFO stats | grep -E "(keyspace_hits|keyspace_misses|connected_clients)"'

# One-time check
redis-cli INFO stats
redis-cli INFO memory
redis-cli DBSIZE
```

### Monitor Magento

```bash
# Check cache status
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento cache:status

# View recent logs
docker exec -it magento_app tail -f /var/www/html/magento/var/log/system.log
```

## Understanding Results

### k6 Output Explained

```
http_req_duration..............: avg=94.58ms   p(95)=263.05ms
```

| Metric | Target | Meaning |
|--------|--------|---------|
| `avg` | < 200ms | Average response time |
| `p(95)` | < 500ms | 95% of requests faster than this |
| `p(99)` | < 1000ms | 99% of requests faster than this |
| `http_req_failed` | 0% | Failed requests |

### Performance Targets

| Page Type | Target Response Time |
|-----------|---------------------|
| Homepage (cached) | < 100ms |
| Category page (cached) | < 150ms |
| Product page | < 300ms |
| Search results | < 500ms |
| Checkout | < 1000ms |

### Good Results Example

```
✓ http_req_duration: avg=94ms, p(95)=263ms
✓ errors: 0%
✓ cache_response_time: avg=73ms

Dragonfly stats:
  keyspace_hits: 50000
  keyspace_misses: 500
  hit_ratio: 99%
```

## Troubleshooting

### High Response Times (>500ms)

1. **Check Full Page Cache:**
   ```bash
   docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento cache:status
   ```
   Ensure `full_page` is enabled.

2. **Warm up cache:**
   ```bash
   curl http://testing.host/
   curl http://testing.host/women.html
   ```

3. **Check Dragonfly connection:**
   ```bash
   redis-cli -h dragonfly.service PING
   ```

### Low Cache Hit Ratio (<80%)

1. **Flush and warm cache:**
   ```bash
   docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento cache:flush
   # Then run warmup requests
   ```

2. **Check cache configuration in `env.php`**

### 404 Errors on Static Files

```bash
# Redeploy static content
docker exec -it magento_app php -d memory_limit=4G /var/www/html/magento/bin/magento setup:static-content:deploy -f

# Fix permissions
docker exec -it magento_app chmod -R 777 /var/www/html/magento/pub/static
```

### Memory Errors

Increase PHP memory limit:
```bash
docker exec -it magento_app php -d memory_limit=4G /var/www/html/magento/bin/magento ...
```

## Advanced: Custom k6 Scripts

### Test Specific Pages

```javascript
// custom-test.js
import http from 'k6/http';
import { check } from 'k6';

export const options = {
    vus: 50,
    duration: '2m',
};

export default function () {
    // Test only product pages
    const response = http.get('http://testing.host/women/tops-women/jackets-women.html');
    check(response, { 'status is 200': (r) => r.status === 200 });
}
```

### Test with Login Session

```javascript
import http from 'k6/http';
import { check } from 'k6';

export function setup() {
    // Login and get session
    const loginRes = http.post('http://testing.host/customer/account/loginPost/', {
        'login[username]': 'test@example.com',
        'login[password]': 'Test123!',
    });
    return { cookies: loginRes.cookies };
}

export default function (data) {
    // Use session for authenticated requests
    const response = http.get('http://testing.host/customer/account/', {
        cookies: data.cookies,
    });
    check(response, { 'logged in': (r) => r.body.includes('My Account') });
}
```

## Resources

- [k6 Documentation](https://k6.io/docs/)
