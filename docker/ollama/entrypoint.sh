#!/bin/sh
ollama serve &
sleep 5
ollama pull deepseek-r1:latest
ollama pull llama3.3:70b
wait