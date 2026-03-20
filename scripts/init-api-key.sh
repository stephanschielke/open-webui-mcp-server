#!/usr/bin/env bash
set -euo pipefail

# init-api-key.sh
# Creates an API key in Open WebUI for automated testing/development.
#
# Usage:
#   ./scripts/init-api-key.sh
#
# Environment variables:
#   WEBUI_URL        - Open WebUI URL (default: http://localhost:3000)
#   WEBUI_ADMIN_EMAIL    - Admin email (default: __VG_EMAIL_c614b20057b1__)
#   WEBUI_ADMIN_PASSWORD - Admin password (default: password)
#   API_KEY_OUTPUT_FILE  - Where to save the API key (default: .openwebui-api-key)

WEBUI_URL="${WEBUI_URL:-http://localhost:3000}"
WEBUI_ADMIN_EMAIL="${WEBUI_ADMIN_EMAIL:-__VG_EMAIL_c614b20057b1__}"
WEBUI_ADMIN_PASSWORD="${WEBUI_ADMIN_PASSWORD:-password}"
API_KEY_OUTPUT_FILE="${API_KEY_OUTPUT_FILE:-.openwebui-api-key}"
MAX_RETRIES=30
RETRY_DELAY=2

log_info() { printf "\033[0;34mℹ\033[0m %s\n" "$@"; }
log_success() { printf "\033[0;32m✓\033[0m %s\n" "$@"; }
log_error() { printf "\033[0;31m✗\033[0m %s\n" "$@" >&2; }
log_warn() { printf "\033[0;33m⚠\033[0m %s\n" "$@"; }

# Wait for Open WebUI to be ready
wait_for_openwebui() {
  log_info "Waiting for Open WebUI at ${WEBUI_URL}..."
  local retries=0
  while [ $retries -lt $MAX_RETRIES ]; do
    if curl -s -o /dev/null -w "%{http_code}" "${WEBUI_URL}/health" 2>/dev/null | grep -q "200\|404"; then
      log_success "Open WebUI is ready"
      return 0
    fi
    retries=$((retries + 1))
    log_info "Attempt $retries/$MAX_RETRIES - waiting ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
  done
  log_error "Open WebUI did not become ready in time"
  return 1
}

# Sign in and get session cookie
signin() {
  log_info "Signing in as ${WEBUI_ADMIN_EMAIL}..."
  local response
  response=$(curl -s -c /tmp/owui-cookies.txt -X POST "${WEBUI_URL}/api/v1/auths/signin" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"${WEBUI_ADMIN_EMAIL}\", \"password\": \"${WEBUI_ADMIN_PASSWORD}\"}")

  if echo "$response" | grep -q "token\|id"; then
    log_success "Signed in successfully"
    return 0
  else
    log_error "Failed to sign in: $response"
    return 1
  fi
}

# Create API key
create_api_key() {
  log_info "Creating API key..."
  local response
  response=$(curl -s -b /tmp/owui-cookies.txt -X POST "${WEBUI_URL}/api/v1/auths/api_key")

  local api_key
  api_key=$(echo "$response" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4)

  if [ -n "$api_key" ]; then
    log_success "API key created: ${api_key:0:10}..."
    echo "$api_key" >"$API_KEY_OUTPUT_FILE"
    log_success "API key saved to ${API_KEY_OUTPUT_FILE}"
    return 0
  else
    log_error "Failed to create API key: $response"
    return 1
  fi
}

# Check if API key already exists
check_existing_key() {
  if [ -f "$API_KEY_OUTPUT_FILE" ]; then
    local existing_key
    existing_key=$(cat "$API_KEY_OUTPUT_FILE")
    if [ -n "$existing_key" ]; then
      log_warn "API key file already exists at ${API_KEY_OUTPUT_FILE}"
      log_info "Existing key: ${existing_key:0:10}..."
      read -p "Create new key? (y/N): " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Keeping existing key"
        return 1
      fi
    fi
  fi
  return 0
}

# Main
main() {
  log_info "Open WebUI API Key Initialization"
  log_info "================================="
  echo

  check_existing_key || exit 0
  wait_for_openwebui || exit 1
  signin || exit 1
  create_api_key || exit 1

  echo
  log_success "Done! API key saved to ${API_KEY_OUTPUT_FILE}"
  log_info "To use: export WEBUI_API_KEY=\$(cat ${API_KEY_OUTPUT_FILE})"
}

main "$@"
