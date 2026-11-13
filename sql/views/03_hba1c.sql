-- HEDIS-style (simplified) diabetes HbA1c control: patient-level rows; rates are computed in Python.
CREATE OR REPLACE VIEW mart.v_hba1c_control AS
WITH last_a1c AS (
  SELECT DISTINCT ON (o.patient_id) o.patient_id, o.value AS last_value, o.obs_ts
  FROM raw.observation o CROSS JOIN mart.v_as_of a
  WHERE o.code = '4548-4' AND o.obs_ts <= a.as_of_date + interval '1 day'
  ORDER BY o.patient_id, o.obs_ts DESC
)
SELECT p.patient_id, p.age, p.sex, l.last_value, l.obs_ts AS last_ts, (l.last_value < 8.0) AS met
FROM mart.v_patient p
JOIN (SELECT DISTINCT patient_id FROM raw.condition WHERE code = '44054006') d USING (patient_id)
LEFT JOIN last_a1c l USING (patient_id)
WHERE p.age BETWEEN 18 AND 75;
