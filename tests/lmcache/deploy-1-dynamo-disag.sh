#!/bin/bash

# ASSUMPTION: dynamo and its dependencies are properly installed
# i.e. nats and etcd are running

# Overview:
# This script deploys dynamo disaggregated serving without LMCache on port 8080
# Used as baseline for correctness testing
set -e
trap 'echo Cleaning up...; kill 0' EXIT

# Arguments:
MODEL_URL=$1

if [ -z "$MODEL_URL" ]; then
    echo "Usage: $0 <MODEL_URL>"
    echo "Example: $0 Qwen/Qwen3-0.6B"
    exit 1
fi

echo "🚀 Starting dynamo disaggregated serving setup without LMCache:"
echo "   Model: $MODEL_URL"
echo "   Port: 8080"
echo "   Mode: Disaggregated (prefill + decode workers)"

# Get script directory and navigate there
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

# Navigate to dynamo examples directory
DYNAMO_DIR="$SCRIPT_DIR/../../examples/vllm"
cd $DYNAMO_DIR

# Kill any existing dynamo processes
echo "🧹 Cleaning up any existing dynamo processes..."
pkill -f "dynamo-run" || true
sleep 2

# Disable LMCache
export ENABLE_LMCACHE=0
echo "🔧 Starting dynamo disaggregated serving without LMCache..."

dynamo run in=http out=dyn &

CUDA_VISIBLE_DEVICES=0 python3 components/main.py --model $MODEL_URL --enforce-eager &

CUDA_VISIBLE_DEVICES=1 python3 components/main.py \
    --model $MODEL_URL \
    --enforce-eager \
    --is-prefill-worker &


