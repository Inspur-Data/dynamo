#!/bin/bash
# ASSUMPTION: dynamo and its dependencies are properly installed
# i.e. nats and etcd are running

# Overview:
# This script deploys dynamo with LMCache enabled on port 8080
# Used for LMCache correctness testing
set -e
trap 'echo Cleaning up...; kill 0' EXIT
# Arguments:
MODEL_URL=$1

if [ -z "$MODEL_URL" ]; then
    echo "Usage: $0 <MODEL_URL>"
    echo "Example: $0 Qwen/Qwen3-0.6B"
    exit 1
fi

echo "🚀 Starting dynamo setup with LMCache:"
echo "   Model: $MODEL_URL"
echo "   Port: 8080"
echo "   !! Remmber to kill the old dynamo processes other wise the port will be busy !! "

# Get script directory and navigate there
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR  

# Navigate back to dynamo directory
DYNAMO_DIR="$SCRIPT_DIR/../../components/backends/vllm"
cd $DYNAMO_DIR


# Kill any existing dynamo processes
echo "🧹 Cleaning up any existing dynamo processes..."
pkill -f "dynamo-run" || true
sleep 2

# Enable LMCache
export ENABLE_LMCACHE=1

# Set LMCache configuration environment variables

echo "🔧 Starting dynamo worker with LMCache enabled..."

dynamo run in=http out=dyn &
python3 components/main.py --model $MODEL_URL --enforce-eager
