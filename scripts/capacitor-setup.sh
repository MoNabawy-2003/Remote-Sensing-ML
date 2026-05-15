#!/bin/bash
set -euo pipefail

npm install --save-dev @capacitor/cli @capacitor/core @capacitor/android @capacitor/assets

npx cap init "Remote Sensing & ML" "me.nabawi.remotesensing" --web-dir public
npx cap add android

npx capacitor-assets generate --config capacitor-assets.json
npx cap sync android
