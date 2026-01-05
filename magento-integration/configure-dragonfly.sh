#!/bin/bash
set -e

# Use environment variables (set in docker-compose.yml from .env)
DRAGONFLY_HOST="dragonfly.service"
MAGENTO_DIR="/var/www/html/magento"
MAGENTO_IP="${DRAGONFLY_IP:-192.168.0.126}"

echo "=== Magento + Dragonfly Setup ==="
echo "Dragonfly IP: ${MAGENTO_IP}"

echo "Step 1: Checking for Magento source code..."
if [ ! -f "${MAGENTO_DIR}/bin/magento" ]; then
    echo "Magento not found. Starting download via Composer..."

    # Generate auth.json from environment variables
    mkdir -p ~/.composer
    cat > ~/.composer/auth.json << EOF
{
    "http-basic": {
        "repo.magento.com": {
            "username": "${ADOBE_PUBLIC_KEY}",
            "password": "${ADOBE_PRIVATE_KEY}"
        }
    }
}
EOF

    # Create Magento in a subdirectory
    /usr/local/bin/composer create-project --repository-url=https://repo.magento.com magento/project-community-edition ${MAGENTO_DIR} --no-interaction

    # Copy auth.json to project dir for future use (persists in mounted volume)
    cp ~/.composer/auth.json ${MAGENTO_DIR}/auth.json
fi

if [ -f "${MAGENTO_DIR}/bin/magento" ]; then
    cd ${MAGENTO_DIR}

    # Check if Magento is already installed
    if [ ! -f "app/etc/env.php" ]; then
        echo "Step 2: Installing Magento..."

        php -d memory_limit=2G bin/magento setup:install \
          --base-url=http://${MAGENTO_IP}/ \
          --db-host=mysql \
          --db-name=magento \
          --db-user=magento \
          --db-password=magento \
          --admin-firstname=Admin \
          --admin-lastname=User \
          --admin-email=admin@example.com \
          --admin-user=admin \
          --admin-password=admin123 \
          --language=en_US \
          --currency=USD \
          --timezone=America/New_York \
          --use-rewrites=1 \
          --search-engine=opensearch \
          --opensearch-host=opensearch \
          --opensearch-port=9200 \
          --cache-backend=redis --cache-backend-redis-server=${DRAGONFLY_HOST} --cache-backend-redis-db=0 \
          --page-cache=redis --page-cache-redis-server=${DRAGONFLY_HOST} --page-cache-redis-db=1 \
          --session-save=redis --session-save-redis-host=${DRAGONFLY_HOST} --session-save-redis-db=2

        echo "Step 3: Disabling Two-Factor Auth for development..."
        php -d memory_limit=2G bin/magento module:disable Magento_AdminAdobeImsTwoFactorAuth Magento_TwoFactorAuth
        php -d memory_limit=2G bin/magento setup:upgrade

        echo "Step 4: Setting permissions..."
        chown -R www-data:www-data /var/www/html/magento
        chmod -R 775 /var/www/html/magento
        chmod -R 777 /var/www/html/magento/var /var/www/html/magento/pub/static /var/www/html/magento/pub/media /var/www/html/magento/generated

        echo "Step 5: Compiling DI..."
        php -d memory_limit=2G bin/magento setup:di:compile

        echo "Step 6: Deploying static content..."
        php -d memory_limit=2G bin/magento setup:static-content:deploy -f

        echo "Step 7: Reindexing..."
        php -d memory_limit=2G bin/magento indexer:reindex

        echo "Step 8: Final permissions..."
        chown -R www-data:www-data /var/www/html/magento
        chmod -R 777 /var/www/html/magento/var /var/www/html/magento/pub/static /var/www/html/magento/pub/media /var/www/html/magento/generated

    else
        echo "Step 2: Magento already installed. Configuring Dragonfly..."

        php -d memory_limit=2G bin/magento setup:config:set \
          --cache-backend=redis --cache-backend-redis-server=${DRAGONFLY_HOST} --cache-backend-redis-db=0 \
          --page-cache=redis --page-cache-redis-server=${DRAGONFLY_HOST} --page-cache-redis-db=1 \
          --session-save=redis --session-save-redis-host=${DRAGONFLY_HOST} --session-save-redis-db=2 \
          --no-interaction
    fi

    echo "Step 9: Flushing Magento cache..."
    php -d memory_limit=2G bin/magento cache:flush

    # Get admin URI
    ADMIN_URI=$(php -d memory_limit=2G bin/magento info:adminuri | grep -oP '/admin_\w+' || echo "/admin")

    echo ""
    echo "========================================="
    echo "  DONE: Magento is now using Dragonfly"
    echo "========================================="
    echo "Frontend: http://${MAGENTO_IP}/"
    echo "Admin:    http://${MAGENTO_IP}${ADMIN_URI}"
    echo "Login:    admin / admin123"
    echo "========================================="
else
    echo "Error: bin/magento was not created. Check Composer logs."
    exit 1
fi
