#!/usr/bin/env bash
# Checks the running app through the cluster's routing.
# Without TOKEN it checks health, config and the 401. With TOKEN (an Entra access token for the api) it also
# checks upload (F-2) and the chat stream (F-3).
set -euo pipefail

base_url="${BASE_URL:-http://localhost}"
token="${TOKEN:-}"

pass() { echo "PASS $*"; }
fail() { echo "FAIL $*"; exit 1; }

status_of() {
  curl -s -o /dev/null -w '%{http_code}' "$@"
}

[[ "$(status_of "$base_url/healthz")" == 200 ]] || fail "GET /healthz"
pass "GET /healthz: $(curl -s "$base_url/healthz")"

[[ "$(status_of "$base_url/config.json")" == 200 ]] || fail "GET /config.json"
pass "GET /config.json"

[[ "$(status_of "$base_url/files")" == 401 ]] || fail "GET /files without a token is not 401"
pass "GET /files without a token: 401"

if [[ -z "$token" ]]; then
  echo "SKIP upload and chat: set TOKEN to check them"
  exit 0
fi

auth=(-H "Authorization: Bearer $token")

upload_file="$(mktemp)"
trap 'rm -f "$upload_file"' EXIT
echo "smoke test $(date -u +%FT%TZ)" >"$upload_file"
object_key="$(curl -sf "${auth[@]}" -F "file=@$upload_file;filename=smoke.txt" "$base_url/upload" | jq -r .objectKey)"
pass "POST /upload: $object_key"

for _ in $(seq 1 30); do
  if curl -sf "${auth[@]}" "$base_url/files" | jq -e --arg key "$object_key" 'any(.[]; .object_key == $key)' >/dev/null; then
    pass "GET /files lists $object_key"
    break
  fi
  sleep 1
done
curl -sf "${auth[@]}" "$base_url/files" | jq -e --arg key "$object_key" 'any(.[]; .object_key == $key)' >/dev/null ||
  fail "the worker did not store $object_key"

first_token_ms=""
while IFS= read -r line; do
  if [[ -z "$first_token_ms" && "$line" == data:* ]]; then
    first_token_ms="$(date +%s%3N)"
  fi
done < <(curl -sNf "${auth[@]}" "$base_url/chat")
end_ms="$(date +%s%3N)"
[[ -n "$first_token_ms" ]] || fail "GET /chat sent no tokens"
gap_ms=$((end_ms - first_token_ms))
((gap_ms > 500)) || fail "GET /chat arrived in one block (first token ${gap_ms} ms before the end)"
pass "GET /chat streams: first token ${gap_ms} ms before the end"
