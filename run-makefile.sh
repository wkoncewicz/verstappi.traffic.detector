#!/bin/bash

# Run: ./run-makefile.sh <frontend|backend>

if [ $# -ne 1 ]; then
    echo "Error: Specifying frontend or backend is required."
    echo "Usage: $0 <frontend|backend>"
    exit 1
fi

if [ "$1" != "frontend" ] && [ "$1" != "backend" ]; then
    echo "Error: Invalid argument. Please specify 'frontend' or 'backend'."
    exit 1
fi

read -s -p "Enter your password: " PASSWORD
echo \n

make build -e DEPLOYMENT=dev -e COMPONENT=$1 -e DOCKER_TOKEN=$PASSWORD
