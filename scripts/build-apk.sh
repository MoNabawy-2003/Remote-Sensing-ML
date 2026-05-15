#!/bin/bash
set -euo pipefail

npx cap sync android
cd android
./gradlew assembleDebug
