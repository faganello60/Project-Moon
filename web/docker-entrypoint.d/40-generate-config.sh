#!/bin/sh
set -eu

API_BASE_URL_VALUE="${API_BASE_URL:-/api}"

cat > /usr/share/nginx/html/config.js <<EOF
window.APP_CONFIG = Object.assign(
    {
        API_BASE_URL: '${API_BASE_URL_VALUE}'
    },
    window.APP_CONFIG || {}
);
EOF
