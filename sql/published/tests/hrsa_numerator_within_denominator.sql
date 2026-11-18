SELECT bhcmis_id, measure_id
FROM published.hrsa_measure
WHERE numerator < 0 OR denominator <= 0 OR numerator > denominator
