#!/bin/bash
set -euo pipefail

# === Required configuration ===
EC2_IP="98.87.169.216"
PEM_KEY_PATH="D:/Electronics and Comunication/4th Electronics and Communication/الترم التانى/Remote Sensing/Project/Sabry/remote.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/remote-sensing-app"
ARCHIVE_NAME="remote-sensing-app.tar.gz"
STAGING_DIR="staging_build"

# === Prepare staging directory ===
rm -rf "${STAGING_DIR}"
mkdir -p "${STAGING_DIR}"

tar \
  --warning=no-file-changed \
  --ignore-failed-read \
  --exclude="node_modules" \
  --exclude=".venv" \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="${ARCHIVE_NAME}" \
  -cf - . \
  | tar -xf - -C "${STAGING_DIR}"

# === Create archive from staging ===
rm -f "${ARCHIVE_NAME}"
tar -czf "${ARCHIVE_NAME}" -C "${STAGING_DIR}" .

# === Upload archive to EC2 ===
scp -i "${PEM_KEY_PATH}" "${ARCHIVE_NAME}" "${REMOTE_USER}@${EC2_IP}:/home/ubuntu/"

# === Remote extract, cleanup, and deploy ===
ssh -i "${PEM_KEY_PATH}" "${REMOTE_USER}@${EC2_IP}" <<EOF
set -euo pipefail

mkdir -p "${REMOTE_DIR}"
tar -xzf "${ARCHIVE_NAME}" -C "${REMOTE_DIR}"
rm -f "${ARCHIVE_NAME}"

cd "${REMOTE_DIR}"
sudo docker compose up -d --build
EOF

# === Local cleanup ===
rm -rf "${STAGING_DIR}"
rm -f "${ARCHIVE_NAME}"

echo "Deployment complete."
