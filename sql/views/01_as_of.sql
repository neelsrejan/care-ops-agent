-- Measurement year end: Dec 31 of the latest year with observations in the extract.
CREATE OR REPLACE VIEW mart.v_as_of AS
SELECT make_date(CAST(max(extract(year FROM obs_ts)) AS int), 12, 31) AS as_of_date FROM raw.observation;
