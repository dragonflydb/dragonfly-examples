# Magento 2 + Dragonfly Docker Setup

Docker-based Magento 2.4.8 development environment with Dragonfly for caching and sessions.

## Requirements

- Docker & Docker Compose
- Magento Marketplace account ([get keys](https://marketplace.magento.com/customer/accessKeys/))
- Dragonfly running on your network
- ~4GB RAM available for containers

## Quick Start

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:
```bash
DRAGONFLY_IP=192.168.0.126          # Your Dragonfly server IP
ADOBE_PUBLIC_KEY=your_public_key    # Magento Marketplace public key
ADOBE_PRIVATE_KEY=your_private_key  # Magento Marketplace private key
```

### 2. Start containers

```bash
docker compose up -d
```

### 3. Wait for services (~1-2 minutes)

```bash
docker logs -f magento_opensearch
# Wait until you see "started", then Ctrl+C
```

### 4. Install Magento

```bash
docker exec -it magento_app bash /var/www/html/configure-dragonfly.sh
```

This will:
- Download Magento via Composer
- Install Magento with MySQL + OpenSearch
- Configure Dragonfly for cache & sessions
- Deploy static content
- Set proper permissions

### 5. Access Magento

After installation completes, you'll see:
```
=========================================
  DONE: Magento is now using Dragonfly
=========================================
Frontend: http://192.168.0.126/
Admin:    http://192.168.0.126/admin_xxxxx
Login:    admin / admin123
=========================================
```

## Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Nginx | magento_nginx | 80 | Web server |
| PHP 8.3-FPM | magento_app | 9000 | Application |
| MySQL 8.0 | magento_mysql | 3306 | Database |
| OpenSearch 2.12 | magento_opensearch | 9200 | Search engine |
| Dragonfly | external | 6379 | Cache & Sessions |

## Dragonfly Configuration

Magento uses Dragonfly (Redis protocol) for:

| Cache Type | Database |
|------------|----------|
| Default cache | db=0 |
| Page cache | db=1 |
| Sessions | db=2 |

## File Structure

```
.
├── .env.example              # Environment template (commit this)
├── .env                      # Your environment (DO NOT commit)
├── configure-dragonfly.sh    # Magento installation script
├── docker-compose.yml        # Docker services
├── init.sh                   # PHP extensions setup
├── nginx.conf                # Nginx configuration
├── setup-sample-data.sh      # Sample data installation
├── k6-load-test.js           # k6 load testing script
├── BENCHMARK.md              # Load testing documentation
├── magento/                  # Magento installation (auto-created)
└── README.md
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DRAGONFLY_IP` | IP address of your Dragonfly server |
| `ADOBE_PUBLIC_KEY` | Magento Marketplace public key |
| `ADOBE_PRIVATE_KEY` | Magento Marketplace private key |

## Commands

```bash
# Restart all containers
docker compose down && docker compose up -d

# Full reset (delete all data)
docker compose down -v
rm -rf magento/
docker compose up -d

# Enter PHP container
docker exec -it magento_app bash

# Magento CLI
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento

# Get admin URL
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento info:adminuri

# Clear cache
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento cache:flush

# Reindex
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento indexer:reindex

# Deploy static content
docker exec -it magento_app php -d memory_limit=2G /var/www/html/magento/bin/magento setup:static-content:deploy -f

# Fix permissions
docker exec -it magento_app bash -c "chown -R www-data:www-data /var/www/html/magento && chmod -R 777 /var/www/html/magento/var /var/www/html/magento/pub/static /var/www/html/magento/pub/media /var/www/html/magento/generated"
```

## Sample Data & Load Testing

### Install Sample Data

Populate Magento with test products for realistic testing:

```bash
docker exec -it magento_app bash /var/www/html/setup-sample-data.sh
```

### Run Load Test

Install [k6](https://grafana.com/docs/k6/latest/set-up/install-k6/), then:

```bash
MAGENTO_URL=http://192.168.0.126 k6 run k6-load-test.js
```

Default test: 100 concurrent users over 5 minutes.

See [BENCHMARK.md](BENCHMARK.md) for detailed testing scenarios and metrics.

## Troubleshooting

### 502 Bad Gateway
PHP-FPM not ready yet. Wait for init.sh to complete:
```bash
docker logs -f magento_app
```

### Permission errors
```bash
docker exec -it magento_app bash -c "chown -R www-data:www-data /var/www/html/magento && chmod -R 777 /var/www/html/magento/var /var/www/html/magento/pub/static /var/www/html/magento/pub/media /var/www/html/magento/generated"
```

### Memory exhausted
All Magento commands use `-d memory_limit=2G`. If issues persist, increase to `4G`.

### Composer auth error
Verify your Magento Marketplace keys in `.env`.

## PHP Extensions

Installed for Magento: pdo_mysql, gd (with jpeg/freetype), bcmath, intl, zip, soap, xsl, sockets, ftp, redis
