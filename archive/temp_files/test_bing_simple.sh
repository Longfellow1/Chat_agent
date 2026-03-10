#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
export MODE=stdio
export DEFAULT_SEARCH_ENGINE=bing

echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search","arguments":{"query":"Tesla Model 3","limit":2,"engines":["bing"]}}}' | npx open-websearch@latest 2>&1 | tail -20
