SELECT o.patient_id FROM raw.observation o LEFT JOIN raw.patient p USING (patient_id) WHERE p.patient_id IS NULL
