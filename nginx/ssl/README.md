# SSL Certificates Directory

This directory should contain your SSL/TLS certificates for HTTPS configuration.

## Required Files

- `fullchain.pem` - Full certificate chain (certificate + intermediate certificates)
- `privkey.pem` - Private key
- `chain.pem` - Intermediate certificates (optional, for OCSP stapling)

## Getting Certificates

### Option 1: Let's Encrypt (Recommended for Production)

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate (HTTP-01 challenge)
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d ktbot.example.com \
  -d www.ktbot.example.com \
  --email admin@example.com \
  --agree-tos

# Copy certificates to this directory
sudo cp /etc/letsencrypt/live/ktbot.example.com/fullchain.pem ./
sudo cp /etc/letsencrypt/live/ktbot.example.com/privkey.pem ./
sudo cp /etc/letsencrypt/live/ktbot.example.com/chain.pem ./

# Set proper permissions
chmod 644 fullchain.pem chain.pem
chmod 600 privkey.pem
```

### Option 2: Self-Signed Certificate (Development/Testing Only)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=ktbot.example.com"

# Copy chain from fullchain
cp fullchain.pem chain.pem
```

### Option 3: Commercial Certificate

If you purchased a certificate from a commercial CA:

1. Place the certificate file as `fullchain.pem`
2. Place the private key as `privkey.pem`
3. Place intermediate certificates as `chain.pem`

## Auto-Renewal (Let's Encrypt)

Add to crontab for automatic renewal:

```bash
# Renew certificates twice daily
0 0,12 * * * certbot renew --quiet --deploy-hook "docker-compose -f docker-compose.prod.yml restart nginx"
```

## Security Notes

- **Never commit private keys to version control**
- Keep proper file permissions (600 for privkey.pem, 644 for others)
- Use strong encryption (RSA 2048-bit minimum, prefer 4096-bit or ECDSA)
- Enable OCSP stapling for better performance
- Monitor certificate expiration

## Testing Configuration

After placing certificates:

```bash
# Test nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## SSL Labs Test

Test your SSL configuration:
https://www.ssllabs.com/ssltest/analyze.html?d=ktbot.example.com
