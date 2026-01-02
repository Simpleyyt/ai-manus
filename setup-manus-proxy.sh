#!/bin/bash
# Setup script for *.manus.you reverse proxy with njs
# Run this on the VM: bash setup-manus-proxy.sh

set -e

echo "🚀 Setting up *.manus.you reverse proxy with dynamic port lookup..."
echo ""

# 1. Pull latest code
echo "📥 Pulling latest code..."
cd /home/samihalawa/ai-manus
git pull origin main

# 2. Check for nginx-module-njs
echo ""
echo "🔍 Checking for nginx njs module..."
if nginx -V 2>&1 | grep -q "http_js_module"; then
    echo "✅ nginx njs module is installed"
else
    echo "⚠️  nginx njs module NOT found"
    echo "Installing libnginx-mod-http-js..."
    sudo apt-get update
    sudo apt-get install -y libnginx-mod-http-js
fi

# 3. Check for existing SSL certificate for *.manus.you
echo ""
echo "🔒 Checking SSL certificates..."
if sudo certbot certificates | grep -q "manus.you"; then
    echo "✅ Certificate for manus.you found"
    CERT_EXISTS=true
else
    echo "⚠️  No certificate found for manus.you"
    CERT_EXISTS=false
fi

# 4. Obtain SSL certificate if needed
if [ "$CERT_EXISTS" = false ]; then
    echo ""
    echo "🔐 Obtaining SSL certificate for *.manus.you..."
    echo "⚠️  This requires DNS challenge verification!"
    echo ""
    echo "Run this command:"
    echo "  sudo certbot certonly --manual --preferred-challenges dns -d '*.manus.you' -d manus.you"
    echo ""
    echo "When prompted, add the TXT record to Cloudflare DNS:"
    echo "  1. Go to Cloudflare dashboard -> manus.you -> DNS"
    echo "  2. Add record:"
    echo "     Type: TXT"
    echo "     Name: _acme-challenge"
    echo "     Content: <value from certbot>"
    echo "     TTL: Auto"
    echo "  3. Wait for DNS propagation (~1-2 min)"
    echo "  4. Press Enter in certbot"
    echo ""
    read -p "Press Enter after obtaining the certificate..."
fi

# 5. Copy njs lookup module
echo ""
echo "📝 Installing njs lookup module..."
sudo cp manus_lookup.js /etc/nginx/manus_lookup.js
sudo chmod 644 /etc/nginx/manus_lookup.js

# 6. Install Nginx config
echo ""
echo "📝 Installing Nginx configuration..."
sudo cp nginx-manus-proxy.conf /etc/nginx/sites-available/manus-proxy

# Create symlink if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/manus-proxy ]; then
    sudo ln -s /etc/nginx/sites-available/manus-proxy /etc/nginx/sites-enabled/manus-proxy
    echo "✅ Created symlink in sites-enabled"
else
    echo "✅ Symlink already exists"
fi

# 7. Test Nginx configuration
echo ""
echo "🧪 Testing Nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

# 8. Reload Nginx
echo ""
echo "♻️  Reloading Nginx..."
sudo systemctl reload nginx

# 9. Rebuild and restart Docker containers
echo ""
echo "🐳 Rebuilding Docker containers..."
docker-compose build backend sandbox

echo ""
echo "♻️  Restarting containers..."
docker-compose up -d

# 10. Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# 11. Test the setup
echo ""
echo "🧪 Testing the deployment..."
echo ""

# Check if backend is running
if docker-compose ps | grep -q "backend.*Up"; then
    echo "✅ Backend container is running"
else
    echo "❌ Backend container is not running"
fi

# Check Nginx is listening
if sudo netstat -tuln | grep -q ":443.*LISTEN"; then
    echo "✅ Nginx is listening on port 443"
else
    echo "❌ Nginx is not listening on port 443"
fi

# Check DNS resolution
echo ""
echo "🌐 Testing DNS resolution..."
if nslookup test123.manus.you | grep -q "34.59.167.52"; then
    echo "✅ DNS wildcard is resolving correctly to VM IP"
else
    echo "⚠️  DNS may not be fully propagated yet (this can take a few minutes)"
fi

# Check njs module
echo ""
echo "🧪 Testing njs module..."
if sudo nginx -V 2>&1 | grep -q "http_js_module"; then
    echo "✅ njs module is loaded and active"
else
    echo "❌ njs module not found in nginx"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Architecture:"
echo "  • ExposeTool generates: https://{12-char-random}.manus.you"
echo "  • Writes mapping to: /tmp/manus_port_mappings.json"
echo "  • Nginx uses njs to lookup port dynamically"
echo "  • Clean URLs like real Manus (no port in URL)"
echo ""
echo "📋 Next steps:"
echo "1. Test ExposeTool via Manus UI:"
echo "   - Deploy a Gradio app"
echo "   - Verify URL format: https://abc123xyz789.manus.you (12 chars)"
echo "   - Test URL accessibility"
echo ""
echo "2. Monitor logs:"
echo "   docker-compose logs -f backend | grep ExposeTool"
echo "   sudo tail -f /var/log/nginx/manus-access.log"
echo "   sudo tail -f /var/log/nginx/manus-error.log"
echo ""
echo "🎉 All deployments will now use clean manus.you URLs!"
