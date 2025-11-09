#!/bin/bash
cd /Users/autumn/Documents/Projects/ProjectReminder
mkdir -p nlp_results

API_TOKEN="008223a499e66c474928a628c8d523a5a286a8decf0782ed6a90768ed6a1a564"

echo "=== NLP PARSING TEST (25 transcriptions) ===" > nlp_results/summary.txt
echo "" >> nlp_results/summary.txt
echo "Timestamp: $(date)" >> nlp_results/summary.txt
echo "" >> nlp_results/summary.txt

success_count=0
fail_count=0

for i in {1..25}; do
  if [ -f "transcriptions/test_${i}.txt" ]; then
    text=$(cat "transcriptions/test_${i}.txt")
    echo "[$i] Parsing: $text"
    
    # Call NLP parsing endpoint with local mode
    response=$(curl -s -X POST http://localhost:8000/api/voice/parse \
      -H "Authorization: Bearer $API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"text\":\"$text\",\"mode\":\"local\"}" 2>&1)
    
    # Save response
    echo "$response" > "nlp_results/result_${i}.json"
    
    # Check for success (look for due_date or error)
    if echo "$response" | grep -q '"due_date"'; then
      ((success_count++))
      # Extract key fields for summary
      due_date=$(echo "$response" | grep -o '"due_date":"[^"]*"' | cut -d'"' -f4)
      due_time=$(echo "$response" | grep -o '"due_time":"[^"]*"' | cut -d'"' -f4)
      priority=$(echo "$response" | grep -o '"priority":"[^"]*"' | cut -d'"' -f4)
      confidence=$(echo "$response" | grep -o '"confidence":[0-9.]*' | cut -d':' -f2)
      location=$(echo "$response" | grep -o '"location":"[^"]*"' | cut -d'"' -f4)
      
      echo "[$i] Text: $text" >> nlp_results/summary.txt
      echo "    Date: $due_date | Time: $due_time | Priority: $priority | Confidence: $confidence | Location: $location" >> nlp_results/summary.txt
      echo "" >> nlp_results/summary.txt
    else
      ((fail_count++))
      error=$(echo "$response" | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)
      echo "[$i] FAILED - $error" >> nlp_results/summary.txt
      echo "" >> nlp_results/summary.txt
    fi
  fi
done

echo "=== PARSING COMPLETE ===" >> nlp_results/summary.txt
echo "Success: $success_count/25" >> nlp_results/summary.txt
echo "Failed: $fail_count/25" >> nlp_results/summary.txt
echo "Results saved to nlp_results/" >> nlp_results/summary.txt
