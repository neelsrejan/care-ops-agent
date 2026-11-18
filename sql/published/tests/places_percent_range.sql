SELECT county_fips, measure_id
FROM published.places_county
WHERE county_fips !~ '^[0-9]{5}$'
   OR (crude_percent IS NOT NULL AND (crude_percent < 0 OR crude_percent > 100))
