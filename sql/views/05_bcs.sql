-- HEDIS-style (simplified) breast cancer screening: women 52-74, mammogram in the prior 27 months.
CREATE OR REPLACE VIEW mart.v_breast_cancer_screening AS
SELECT p.patient_id, p.age, p.sex,
       max(pr.proc_ts) AS last_ts,
       (count(pr.proc_ts) > 0) AS met
FROM mart.v_patient p
LEFT JOIN raw.procedure pr
  ON pr.patient_id = p.patient_id
 AND pr.proc_ts > p.as_of_date - interval '27 months' AND pr.proc_ts <= p.as_of_date + interval '1 day'
WHERE p.sex = 'female' AND p.age BETWEEN 52 AND 74
GROUP BY p.patient_id, p.age, p.sex;
