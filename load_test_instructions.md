# SSE Load Testing Guide

## Quick Start

### Basic Load Test (50 connections, 10 codes, 60 seconds)
```bash
python load_test_sse.py
```

### Custom Load Test
```bash
python load_test_sse.py <connections> <codes> <duration>
```

**Examples:**
```bash
# Test with 100 connections
python load_test_sse.py 100

# Test with 200 connections, 20 codes, 120 seconds
python load_test_sse.py 200 20 120

# Stress test: 500 connections
python load_test_sse.py 500 50 180
```

## What It Tests

1. **Connection Scalability**
   - Creates multiple concurrent WebSocket connections
   - Measures connection success rate
   - Tracks connection stability

2. **Code Broadcasting**
   - Sends codes via HTTP API
   - Verifies all connected clients receive codes
   - Measures code delivery rate

3. **Error Handling**
   - Tracks connection errors
   - Monitors WebSocket errors
   - Reports failed operations

## Test Phases

### Phase 1: Connection
- Connects all clients concurrently (max 20 at a time)
- Reports connection success rate

### Phase 2: Code Broadcasting
- Sends codes over the test duration
- Monitors code reception in real-time
- Tracks codes received per connection

### Phase 3: Statistics
- Disconnects all clients
- Collects detailed statistics
- Reports results

## Expected Results

**Good Performance:**
- >95% connection success rate
- All sent codes received by all connections
- <1% error rate
- Stable connections throughout test

**Warning Signs:**
- 80-95% connection success rate
- Some codes not received by all connections
- Occasional connection drops

**Issues:**
- <80% connection success rate
- Many codes not received
- Frequent connection errors
- Connection timeouts

## Monitoring

The script provides real-time updates:
- Connection progress
- Codes sent/received
- Error counts
- Final statistics

## Tips

1. **Start Small**: Begin with 50 connections, then scale up
2. **Monitor Server**: Watch Render logs during test
3. **Check Database**: Ensure database can handle load
4. **Network**: Test from different locations if possible
5. **Duration**: Longer tests reveal stability issues

## Troubleshooting

**Low Connection Rate:**
- Check server resources (CPU/Memory)
- Verify database connection pool
- Check network connectivity

**Codes Not Received:**
- Verify broadcasting logic
- Check WebSocket connection stability
- Monitor server logs for errors

**High Error Rate:**
- Check database connection limits
- Verify server can handle concurrent connections
- Review error messages for patterns

## Performance Targets

For 200-400 users on 2GB RAM:
- **50 connections**: Should be 100% success
- **100 connections**: Should be >95% success
- **200 connections**: Should be >90% success
- **500+ connections**: May see degradation (stress test)

