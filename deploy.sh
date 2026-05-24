#!/usr/bin/env bash
# Build and push the 1618.dev image to Docker Hub.
# Usage:
#   ./deploy.sh              # tags as :latest and :<git-sha>
#   ./deploy.sh v1.2.3       # tags as :latest and :v1.2.3

set -euo pipefail

IMAGE="awmanoj/numlabs"
TAG="${1:-$(git rev-parse --short HEAD)}"

echo ">> Building $IMAGE:$TAG for linux/amd64"
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t "$IMAGE:$TAG" \
  -t "$IMAGE:latest" \
  --push \
  .

echo ">> Done. Pull on the server with: docker pull $IMAGE:latest"
