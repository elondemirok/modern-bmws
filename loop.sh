#!/bin/bash

# Get max iterations from command line argument (default: infinite)
MAX_ITERATIONS=${1:-0}
ITERATION=0

while true; do
  # Check if we've reached max iterations (if specified)
  if [ "$MAX_ITERATIONS" -gt 0 ] && [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
    echo "Completed $ITERATION iterations"
    break
  fi

  ITERATION=$((ITERATION + 1))
  echo "=== Iteration $ITERATION$([ "$MAX_ITERATIONS" -gt 0 ] && echo " of $MAX_ITERATIONS" || echo "") ==="
  if [ -f prompt.md ]; then
    cat prompt.md | command claude \
      --print \
      --output-format stream-json \
      --dangerously-skip-permissions \
      --verbose \
    | jq -Rr --unbuffered '
        # Parse each line as JSON (ignore if invalid)
        fromjson? 
        # Only process messages with a message object
        | select(.message?)
        # Flatten role and chunk content
        | (.message.role // .type) as $role
        | .message.content[]? as $chunk
        # Filter by relevant chunk types
        | select(
            $chunk.type == "text" or 
            $chunk.type == "message" or 
            $chunk.type == "tool_result" or 
            $chunk.type == "thinking" or 
            $chunk.type == "analysis" or 
            $chunk.type == "reasoning"
          )
        # Pretty-print role + content
        | "[" + $role + "] " + ($chunk.type // "unknown") + ": " + ($chunk.content // $chunk.text // "")
      '
  else
    echo "Error: prompt.md not found"
    exit 1
  fi

  # Optional: small delay between runs
  sleep 1
done
