-- Public reported inputs. Rates are not stored here. Python computes them.
CREATE SCHEMA IF NOT EXISTS published;
DROP TABLE IF EXISTS
  published.hrsa_measure,
  published.places_county,
  published.cms_contract_measure,
  published.source
CASCADE;

CREATE TABLE published.source (
  source_id text PRIMARY KEY,
  title text NOT NULL,
  publisher text NOT NULL,
  vintage text NOT NULL,
  retrieved_on date NOT NULL,
  source_url text NOT NULL,
  license text NOT NULL,
  grain text NOT NULL,
  row_count integer NOT NULL,
  file_sha256 text NOT NULL,
  notes text NOT NULL
);

CREATE TABLE published.hrsa_measure (
  reporting_year integer NOT NULL,
  bhcmis_id text NOT NULL,
  health_center_name text NOT NULL,
  city text NOT NULL,
  state text NOT NULL,
  measure_id text NOT NULL,
  numerator double precision NOT NULL,
  denominator double precision NOT NULL,
  published_percent double precision,
  percent_status text NOT NULL,
  percent_note text NOT NULL,
  PRIMARY KEY (reporting_year, bhcmis_id, measure_id),
  CHECK (
    (percent_status = 'published' AND published_percent IS NOT NULL)
    OR (percent_status = 'unavailable' AND published_percent IS NULL)
  ),
  CHECK (denominator > 0),
  CHECK (numerator >= 0),
  CHECK (numerator <= denominator),
  CHECK (measure_id IN ('breast_cancer_screening', 'bp_control', 'diabetes_poor_control'))
);

CREATE TABLE published.places_county (
  release text NOT NULL,
  county_fips text NOT NULL,
  state_abbr text NOT NULL,
  state_name text NOT NULL,
  county_name text NOT NULL,
  total_population integer,
  pop_18plus integer,
  measure_id text NOT NULL,
  crude_percent double precision,
  published_ci_low double precision,
  published_ci_high double precision,
  PRIMARY KEY (release, county_fips, measure_id),
  CHECK (county_fips ~ '^[0-9]{5}$'),
  CHECK (crude_percent IS NULL OR (crude_percent >= 0 AND crude_percent <= 100)),
  CHECK (measure_id IN ('diabetes_prevalence', 'bp_medication', 'mammography'))
);

CREATE TABLE published.cms_contract_measure (
  ratings_year integer NOT NULL,
  contract_id text NOT NULL,
  organization_type text NOT NULL,
  contract_name text NOT NULL,
  parent_organization text NOT NULL,
  measure_code text NOT NULL,
  measure_id text NOT NULL,
  measure_name text NOT NULL,
  measurement_period text NOT NULL,
  published_percent double precision,
  status text,
  PRIMARY KEY (ratings_year, contract_id, measure_code),
  CHECK (published_percent IS NULL OR (published_percent >= 0 AND published_percent <= 100)),
  CHECK (published_percent IS NOT NULL OR status IS NOT NULL),
  CHECK (measure_code IN ('C01', 'C12', 'C14'))
);
