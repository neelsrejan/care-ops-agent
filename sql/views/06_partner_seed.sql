-- Public CMS facilities used ONLY as name/location seeds for SYNTHETIC partner groups.
CREATE OR REPLACE VIEW mart.v_partner_seed AS
SELECT facility_id, facility_name, city, state, county, ownership,
       CASE WHEN overall_rating ~ '^[1-5]$' THEN overall_rating::int END AS overall_rating
FROM raw.cms_hospital WHERE hospital_type = 'Acute Care Hospitals';
