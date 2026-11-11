-- Raw landing tables (PostgreSQL). Synthea FHIR R4 rows + CMS hospital seeds.
CREATE SCHEMA IF NOT EXISTS raw;
DROP TABLE IF EXISTS raw.patient, raw.condition, raw.observation, raw.procedure, raw.cms_hospital CASCADE;
CREATE TABLE raw.patient (patient_id text PRIMARY KEY, birth_date date, death_date date, sex text, city text, state text);
CREATE TABLE raw.condition (patient_id text, code text, onset date, abatement date);
CREATE TABLE raw.observation (patient_id text, obs_ts timestamptz, code text, value double precision);
CREATE TABLE raw.procedure (patient_id text, code text, proc_ts timestamptz);
CREATE TABLE raw.cms_hospital (facility_id text, facility_name text, city text, state text, county text,
  hospital_type text, ownership text, overall_rating text);
