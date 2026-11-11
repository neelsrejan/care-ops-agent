from care_ops_agent.data import download


def test_cms_url_comes_from_metastore(monkeypatch):
    class R:
        def json(self):
            return {"title": "Hospital General Information", "modified": "2026-07-22",
                    "distribution": [{"mediaType": "text/csv", "downloadURL": "https://example/x.csv"}]}
    monkeypatch.setattr(download.httpx, "get", lambda *a, **k: R())
    url, meta = download.cms_download_url()
    assert url == "https://example/x.csv" and meta["modified"] == "2026-07-22"
