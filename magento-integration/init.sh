#!/bin/bash
# Install required system libraries
apt-get update && apt-get install -y libpng-dev libicu-dev libxml2-dev libxslt1-dev libzip-dev zip unzip git curl libjpeg-dev libfreetype6-dev

# Configure GD with JPEG and FreeType support
docker-php-ext-configure gd --with-jpeg --with-freetype

# Install PHP extensions required for Magento
docker-php-ext-install pdo_mysql gd bcmath intl zip soap xsl sockets ftp

# Install Redis extension (needed for Dragonfly connectivity)
if ! php -m | grep -q 'redis'; then
    pecl install redis && docker-php-ext-enable redis
fi

# Install Composer using official installer
curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

echo "System environment ready."

