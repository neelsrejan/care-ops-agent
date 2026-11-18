SELECT contract_id, measure_code
FROM published.cms_contract_measure
WHERE (published_percent IS NULL AND (status IS NULL OR status = ''))
   OR (published_percent IS NOT NULL AND (published_percent < 0 OR published_percent > 100))
