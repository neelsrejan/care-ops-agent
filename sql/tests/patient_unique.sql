SELECT patient_id FROM raw.patient GROUP BY 1 HAVING count(*) > 1
