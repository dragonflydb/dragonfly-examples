#!/bin/bash

while true; do
    for ((id=1; id<=10; id++)); do
        url="http://localhost:8080/$id"   
        
        curl -X POST "$url" 
        curl "$url"                    
        
        sleep 2
    done
done