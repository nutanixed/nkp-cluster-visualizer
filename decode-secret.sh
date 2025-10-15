#!/bin/bash

if [ $# -eq 2 ]; then
    SECRET_NAME=$1
    NAMESPACE=$2
else
    read -p "Enter secret name: " SECRET_NAME
    read -p "Enter namespace: " NAMESPACE
fi

echo "Decoding secret: $SECRET_NAME in namespace: $NAMESPACE"
echo "================================================================"

kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o json | jq -r '.data | to_entries[] | "\(.key): \(.value)"' | while read -r line; do
    key=$(echo "$line" | cut -d: -f1)
    value=$(echo "$line" | cut -d: -f2- | xargs)
    decoded=$(echo "$value" | base64 -d 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "$key: $decoded"
    else
        echo "$key: [failed to decode]"
    fi
done
