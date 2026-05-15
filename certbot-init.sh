#!/bin/sh
set -eu

DOMAIN="remote-sensing.nabawi.me"
EMAIL="${CERTBOT_EMAIL:-you@example.com}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
DUMMY_MARKER="${CERT_DIR}/.dummy"

if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  certbot certonly --webroot \
    --webroot-path /var/www/certbot \
    --domain "${DOMAIN}" \
    --email "${EMAIL}" \
    --agree-tos \
    --non-interactive
fi

if [ -f "${DUMMY_MARKER}" ]; then
  rm -f "${DUMMY_MARKER}"
fi

while :; do
  certbot renew --webroot -w /var/www/certbot --quiet
  sleep 12h
 done
