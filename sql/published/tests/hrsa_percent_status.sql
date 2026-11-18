SELECT bhcmis_id, measure_id, percent_status
FROM published.hrsa_measure
WHERE (percent_status = 'unavailable' AND published_percent IS NOT NULL)
   OR (percent_status = 'published' AND published_percent IS NULL)
   OR percent_status NOT IN ('published', 'unavailable')
   OR percent_note = ''
