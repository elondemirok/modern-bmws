#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Clear screen and set up terminal
clear
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║           Claude Agent Loop - Real-time Visualizer              ║${NC}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to draw separator
draw_separator() {
    echo -e "${GRAY}────────────────────────────────────────────────────────────────────${NC}"
}

# Function to format timestamp
timestamp() {
    date '+%H:%M:%S'
}

# Function to format duration
format_duration() {
    local ms=$1
    if [ $ms -lt 1000 ]; then
        echo "${ms}ms"
    else
        local seconds=$(echo "scale=2; $ms / 1000" | bc)
        echo "${seconds}s"
    fi
}

# Function to format cost
format_cost() {
    local cost=$1
    printf "%.4f" $cost
}

# Process loop.sh output line by line
./loop.sh 2>&1 | while IFS= read -r line; do
    # Try to parse as JSON
    if echo "$line" | jq -e . >/dev/null 2>&1; then
        # Extract fields from JSON
        type=$(echo "$line" | jq -r '.type // "unknown"')
        subtype=$(echo "$line" | jq -r '.subtype // ""')
        is_error=$(echo "$line" | jq -r '.is_error // false')
        result=$(echo "$line" | jq -r '.result // ""')
        duration_ms=$(echo "$line" | jq -r '.duration_ms // 0')
        duration_api_ms=$(echo "$line" | jq -r '.duration_api_ms // 0')
        num_turns=$(echo "$line" | jq -r '.num_turns // 0')
        total_cost=$(echo "$line" | jq -r '.total_cost_usd // 0')
        session_id=$(echo "$line" | jq -r '.session_id // ""')

        # Input/output tokens
        input_tokens=$(echo "$line" | jq -r '.usage.input_tokens // 0')
        output_tokens=$(echo "$line" | jq -r '.usage.output_tokens // 0')
        cache_creation=$(echo "$line" | jq -r '.usage.cache_creation_input_tokens // 0')
        cache_read=$(echo "$line" | jq -r '.usage.cache_read_input_tokens // 0')

        # Clear screen for new response
        clear
        echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║           Claude Agent Loop - Real-time Visualizer              ║${NC}"
        echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        # Status header
        echo -e "${GRAY}[$(timestamp)]${NC}"
        if [ "$is_error" = "true" ]; then
            echo -e "${BOLD}${RED}● Status: ERROR${NC}"
        elif [ "$subtype" = "success" ]; then
            echo -e "${BOLD}${GREEN}● Status: SUCCESS${NC}"
        else
            echo -e "${BOLD}${YELLOW}● Status: ${type}${NC}"
        fi

        draw_separator

        # Performance metrics
        echo -e "${BOLD}${WHITE}⚡ Performance:${NC}"
        echo -e "  ${CYAN}Duration:${NC}     $(format_duration $duration_ms)"
        echo -e "  ${CYAN}API Time:${NC}     $(format_duration $duration_api_ms)"
        echo -e "  ${CYAN}Turns:${NC}        ${num_turns}"
        echo ""

        # Token usage
        echo -e "${BOLD}${WHITE}📊 Token Usage:${NC}"
        echo -e "  ${CYAN}Input:${NC}        ${input_tokens}"
        echo -e "  ${CYAN}Output:${NC}       ${output_tokens}"
        echo -e "  ${CYAN}Cache Read:${NC}   ${cache_read}"
        echo -e "  ${CYAN}Cache Create:${NC} ${cache_creation}"
        echo ""

        # Cost
        echo -e "${BOLD}${WHITE}💰 Cost:${NC} ${GREEN}\$$(format_cost $total_cost)${NC}"
        echo ""

        # Session ID (truncated)
        session_short=$(echo "$session_id" | cut -c1-8)
        echo -e "${GRAY}Session: ${session_short}...${NC}"

        draw_separator

        # Response content
        echo -e "${BOLD}${WHITE}📝 Response:${NC}"
        echo ""

        if [ -n "$result" ] && [ "$result" != "null" ]; then
            # Format markdown response with some basic highlighting
            echo "$result" | sed 's/^# /  /' | sed 's/^## /    /' | sed 's/^\* /  • /' | \
                while IFS= read -r response_line; do
                    # Highlight code blocks
                    if echo "$response_line" | grep -q '```'; then
                        echo -e "${YELLOW}$response_line${NC}"
                    # Highlight bold text
                    elif echo "$response_line" | grep -q '\*\*'; then
                        echo -e "${BOLD}$response_line${NC}"
                    else
                        echo -e "${WHITE}$response_line${NC}"
                    fi
                done
        else
            echo -e "${GRAY}(no response content)${NC}"
        fi

        echo ""
        draw_separator

        # Model usage breakdown
        echo -e "${BOLD}${WHITE}🤖 Model Usage:${NC}"
        echo "$line" | jq -r '.modelUsage | to_entries[] | "  \(.key): \(.value.inputTokens)in/\(.value.outputTokens)out ($\(.value.costUSD))"' 2>/dev/null || echo -e "${GRAY}  (no model data)${NC}"

        echo ""
        draw_separator
        echo -e "${GRAY}Waiting for next response...${NC}"

    else
        # Not JSON, display as-is (e.g., error messages from loop.sh)
        echo -e "${YELLOW}[$(timestamp)] ${line}${NC}"
    fi
done
