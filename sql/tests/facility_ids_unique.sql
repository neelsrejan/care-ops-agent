SELECT facility_id FROM raw.cms_hospital GROUP BY 1 HAVING count(*) > 1 OR facility_id IS NULL
