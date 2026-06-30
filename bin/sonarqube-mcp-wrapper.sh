#!/bin/bash
export SONAR_HOST_URL="http://localhost:9000"
export SONAR_TOKEN="squ_83fb83e4a4f235171ac3b831a5c068895afac288"
exec /home/cesar/.config/opencode/node_modules/.bin/sonarqube-mcp "$@"
