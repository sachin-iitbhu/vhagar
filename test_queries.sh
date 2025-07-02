#!/bin/bash

# Array of queries
declare -a queries=(
  "What were the total compensations for SDE II at Google in Bangalore and SDE III at Amazon in Gurgaon in 2024?"
  "Compare the base salary and bonus for SDE I at Google in Noida and SDE III at Uber in India for the year 2023."
  "List all compensation details for SDE II roles at any company in India posted after January 2024."
  "Which company offered the highest stocks for SDE roles in Bangalore in 2024?"
  "What is the difference in total compensation between SDE II at Google in Bangalore and SDE II at Salesforce in India, as per the latest available data?"
  "Give me the compensation breakdown for all SDE III roles posted in March 2024."
  "How did the compensation for SDE I at Google in Noida change between 2023 and 2024?"
  "Show me the bonus amounts for SDE II at Google in Bangalore and SDE III at Amazon in Gurgaon, posted after February 2024."
  "What are the compensation details for all Google SDE roles in Noida posted in 2024?"
  "List the URLs for all compensation posts for SDE II roles at any company in India from 2024."
)

output_file="qa_results.txt"
> "$output_file"

for query in "${queries[@]}"
do
  echo "Question: $query" >> "$output_file"
  response=$(curl -s -X POST http://localhost:8080/query -H 'Content-Type: application/json' -d "{\"query\": \"$query\"}")
  echo "Answer: $response" >> "$output_file"
  echo "" >> "$output_file"
done

echo "All queries executed. Results saved in $output_file."
