for i in $(seq 1 3162); do
  curl -fs "https://xkcd.com/$i/info.0.json" | jq -c . 2>/dev/null || true
done >xkcd.ndjson
