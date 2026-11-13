SELECT patient_id FROM mart.v_hba1c_control GROUP BY 1 HAVING count(*) > 1
UNION ALL SELECT patient_id FROM mart.v_bp_control GROUP BY 1 HAVING count(*) > 1
UNION ALL SELECT patient_id FROM mart.v_breast_cancer_screening GROUP BY 1 HAVING count(*) > 1
