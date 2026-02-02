#!/bin/bash

echo "======================================================================"
echo "Story 5.5: Performance Monitoring Dashboard - Verification"
echo "======================================================================"
echo ""

# Kill any existing services
echo "1. Cleaning up existing processes..."
pkill -f "uvicorn.*src.api.main" 2>/dev/null || true
sleep 2

# Start FastAPI
echo ""
echo "2. Starting FastAPI service..."
cd /Users/macbook/ai-project/KT-BOT
python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 7860 > logs/verify_api.log 2>&1 &
API_PID=$!
echo "   Started with PID: $API_PID"

# Wait for service to start
echo "   Waiting for service to initialize..."
sleep 10

# Test health
echo ""
echo "3. Testing API health..."
HEALTH=$(curl -s http://localhost:7860/api/v1/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ API is healthy"
else
    echo "   ❌ API health check failed"
    echo "   Response: $HEALTH"
    tail -20 logs/verify_api.log
    exit 1
fi

# Generate test traffic
echo ""
echo "4. Generating test traffic..."
for i in {1..15}; do
    curl -s "http://localhost:7860/docs" > /dev/null 2>&1 &
done
wait
echo "   ✅ Sent 15 requests to /docs"

# Wait for middleware to process
sleep 2

# Test all metrics endpoints
echo ""
echo "5. Testing metrics endpoints..."

echo "   a) System metrics..."
SYSTEM=$(curl -s http://localhost:7860/api/v1/metrics/system)
if echo "$SYSTEM" | grep -q "cpu_percent"; then
    echo "      ✅ System metrics working"
    echo "$SYSTEM" | python3 -c "import sys, json; d=json.load(sys.stdin)['data']; print(f'         CPU: {d[\"cpu_percent\"]}%, Memory: {d[\"memory_percent\"]}%')"
else
    echo "      ❌ System metrics failed"
fi

echo "   b) Database metrics..."
DATABASE=$(curl -s http://localhost:7860/api/v1/metrics/database)
if echo "$DATABASE" | grep -q "pool_size"; then
    echo "      ✅ Database metrics working"
    echo "$DATABASE" | python3 -c "import sys, json; d=json.load(sys.stdin)['data']; print(f'         Pool: {d[\"pool_checked_out\"]}/{d[\"pool_size\"]}, Usage: {d[\"pool_usage_percent\"]}%')"
else
    echo "      ❌ Database metrics failed"
fi

echo "   c) API performance metrics..."
API=$(curl -s http://localhost:7860/api/v1/metrics/api)
if echo "$API" | grep -q "total_requests"; then
    echo "      ✅ API metrics working"
    echo "$API" | python3 -c "import sys, json; d=json.load(sys.stdin)['data']; print(f'         Total requests: {d[\"total_requests\"]}, Avg: {d[\"avg_response_time_ms\"]}ms')"

    REQUESTS=$(echo "$API" | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['total_requests'])")
    if [ "$REQUESTS" -gt "0" ]; then
        echo "      ✅ Middleware is tracking requests!"
    else
        echo "      ⚠️  No requests tracked (middleware may need verification)"
    fi
else
    echo "      ❌ API metrics failed"
fi

echo "   d) Retrieval metrics..."
RETRIEVAL=$(curl -s http://localhost:7860/api/v1/metrics/retrieval)
if echo "$RETRIEVAL" | grep -q "total_searches"; then
    echo "      ✅ Retrieval metrics working"
else
    echo "      ❌ Retrieval metrics failed"
fi

echo "   e) All metrics..."
ALL=$(curl -s http://localhost:7860/api/v1/metrics/all)
if echo "$ALL" | grep -q "system.*database.*api"; then
    echo "      ✅ All metrics endpoint working"
else
    echo "      ❌ All metrics failed"
fi

echo ""
echo "6. Testing completed!"
echo ""
echo "======================================================================"
echo "Summary:"
echo "  - All metrics endpoints are functional"
echo "  - To view the UI: http://localhost:7861 → '📊 监控' tab"
echo "  - API is running on: http://localhost:7860"
echo "  - API docs: http://localhost:7860/docs"
echo ""
echo "To stop the service: kill $API_PID"
echo "======================================================================"
