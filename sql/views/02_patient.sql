CREATE OR REPLACE VIEW mart.v_patient AS
SELECT p.patient_id, p.sex, p.city, p.state,
       date_part('year', age(a.as_of_date, p.birth_date))::int AS age, a.as_of_date
FROM raw.patient p CROSS JOIN mart.v_as_of a
WHERE p.death_date IS NULL OR p.death_date > a.as_of_date;
