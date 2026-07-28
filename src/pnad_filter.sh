# 1. Filters by house head and urban areas
awk 'substr($0, 92, 2) == "01" && substr($0, 32, 1) == "1"' ../data/PNADC_2025_visita1.txt > ../data/pnad_urban_households.txt

# 2. Creates a sample file for testing
shuf -n 500 ../data/pnad_urban_households.txt > ../data/pnad_urban_households_prev.txt