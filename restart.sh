#!/bin/bash
# NKP Cluster Visualizer Restart Script
# This script kills any running Flask instances and starts a fresh one

echo "🔄 Restarting NKP Cluster Visualizer..."

# Kill any existing Flask processes (NKP-specific only)
echo "🛑 Stopping existing NKP Flask processes..."
pkill -f "nkp-cluster-visualizer.*run.py" 2>/dev/null || true
pkill -f "nkp-cluster-visualizer.*cluster_api.py" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 2

# Verify processes are stopped
if pgrep -f "nkp-cluster-visualizer.*run.py" > /dev/null || pgrep -f "nkp-cluster-visualizer.*cluster_api.py" > /dev/null; then
    echo "⚠️  Force killing remaining NKP processes..."
    pkill -9 -f "nkp-cluster-visualizer.*run.py" 2>/dev/null || true
    pkill -9 -f "nkp-cluster-visualizer.*cluster_api.py" 2>/dev/null || true
    sleep 1
fi

# Change to the visualizer directory
cd /home/nutanix/dev/nkp-cluster-visualizer

# Activate virtual environment and start Flask
echo "🚀 Starting Flask application..."
source .venv/bin/activate

# Start Flask in the background with port 5001 for local development
export BIND_PORT=5001
export FLASK_ENV=development
nohup python run.py > flask.log 2>&1 &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Check if Flask is running
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask started successfully (PID: $FLASK_PID)"
    echo "📝 Logs: tail -f /home/nutanix/dev/nkp-cluster-visualizer/flask.log"
    echo "🌐 Visualizer: http://localhost:5001 (local dev)"
    echo "🔐 Default credentials: admin / admin"
    echo ""
    echo "To stop: pkill -f 'nkp-cluster-visualizer.*run.py'"
else
    echo "❌ Failed to start Flask. Check flask.log for errors:"
    tail -20 flask.log
    exit 1
fi