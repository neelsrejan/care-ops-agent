from care_ops_agent.fhir.parse import flatten_bundle

BUNDLE = {"resourceType": "Bundle", "entry": [
    {"resource": {"resourceType": "Patient", "id": "p1", "birthDate": "1960-01-01", "gender": "female", "address": [{"city": "X", "state": "MA"}]}},
    {"resource": {"resourceType": "Condition", "subject": {"reference": "urn:uuid:p1"}, "code": {"coding": [{"code": "59621000"}]}, "onsetDateTime": "2010-01-01T00:00:00Z"}},
    {"resource": {"resourceType": "Condition", "subject": {"reference": "urn:uuid:p1"}, "code": {"coding": [{"code": "99999"}]}}},
    {"resource": {"resourceType": "Observation", "subject": {"reference": "urn:uuid:p1"}, "code": {"coding": [{"code": "55284-4"}]},
                  "effectiveDateTime": "2019-05-01T00:00:00Z", "component": [
                      {"code": {"coding": [{"code": "8480-6"}]}, "valueQuantity": {"value": 150}},
                      {"code": {"coding": [{"code": "8462-4"}]}, "valueQuantity": {"value": 85}}]}},
    {"resource": {"resourceType": "Procedure", "subject": {"reference": "urn:uuid:p1"}, "code": {"coding": [{"code": "71651007"}]},
                  "performedPeriod": {"start": "2019-02-01T00:00:00Z"}}},
]}


def test_flatten_keeps_only_measure_codes():
    out = flatten_bundle(BUNDLE)
    assert len(out["patient"]) == 1 and out["patient"][0]["sex"] == "female"
    assert [c["code"] for c in out["condition"]] == ["59621000"]
    assert sorted(o["value"] for o in out["observation"]) == [85, 150]
    assert out["procedure"][0]["proc_ts"].startswith("2019-02-01")
