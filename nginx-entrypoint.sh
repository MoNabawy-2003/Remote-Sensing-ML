#!/bin/sh
set -eu

DOMAIN="remote-sensing.nabawi.me"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
DUMMY_MARKER="${CERT_DIR}/.dummy"

if ! command -v openssl >/dev/null 2>&1; then
  apk add --no-cache openssl >/dev/null 2>&1
fi

if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
  mkdir -p "${CERT_DIR}"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "${CERT_DIR}/privkey.pem" \
    -out "${CERT_DIR}/fullchain.pem" \
    -subj "/CN=${DOMAIN}"
  touch "${DUMMY_MARKER}"
fi

nginx -g "daemon off;" &

while :; do
  sleep 5m
  nginx -s reload
done
