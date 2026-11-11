-- HEDIS-style (simplified) controlling high blood pressure: latest paired reading < 140/90.
CREATE OR REPLACE VIEW mart.v_bp_control AS
WITH paired AS (
  SELECT s.patient_id, s.obs_ts, s.value AS sbp, d.value AS dbp
  FROM raw.observation s JOIN raw.observation d
    ON d.patient_id = s.patient_id AND d.obs_ts = s.obs_ts AND d.code = '8462-4'
  WHERE s.code = '8480-6'
), last_bp AS (
  SELECT DISTINCT ON (patient_id) patient_id, sbp, dbp, obs_ts
  FROM paired CROSS JOIN mart.v_as_of a WHERE obs_ts <= a.as_of_date + interval '1 day'
  ORDER BY patient_id, obs_ts DESC
)
SELECT p.patient_id, p.age, p.sex, b.sbp AS last_sbp, b.dbp AS last_dbp, b.obs_ts AS last_ts,
       (b.sbp < 140 AND b.dbp < 90) AS met
FROM mart.v_patient p
JOIN (SELECT DISTINCT patient_id FROM raw.condition WHERE code = '59621000') h USING (patient_id)
LEFT JOIN last_bp b USING (patient_id)
WHERE p.age BETWEEN 18 AND 85;
