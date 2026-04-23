class TestHealthCheck:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_status_true(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert data["status"] is True


class TestUploadTrip:
    def test_upload_success(self, client, sample_image):
        resp = client.post(
            "/api/trips/upload",
            files={"file": ("trip.png", sample_image, "image/png")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["bike_id"] == "TRE00410"
        assert data["length_min"] == 35
        assert "id" in data
        assert "image_url" in data
        assert "created_at" in data

    def test_upload_rejects_non_image(self, client):
        resp = client.post(
            "/api/trips/upload",
            files={"file": ("data.txt", b"not an image", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_analysis_failure(self, client, sample_image, monkeypatch):
        from app import main

        def raise_error(*args, **kwargs):
            raise RuntimeError("Ollama unreachable")

        monkeypatch.setattr(main, "analyze_image", raise_error)

        resp = client.post(
            "/api/trips/upload",
            files={"file": ("trip.png", sample_image, "image/png")},
        )
        assert resp.status_code == 500


class TestListTrips:
    def test_empty_list(self, client):
        resp = client.get("/api/trips")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_data(self, client, sample_image, monkeypatch):
        from app import main

        def mock_analyze(*args, **kwargs):
            return {
                "length_min": 35,
                "start_time": "08:15",
                "end_time": "08:50",
                "start_pos": "Helsinki Central Station",
                "end_pos": "Esplanadi",
                "bike_id": "TRE00410",
                "serial": "SN123456",
            }

        monkeypatch.setattr(main, "analyze_image", mock_analyze)

        client.post(
            "/api/trips/upload",
            files={"file": ("trip.png", sample_image, "image/png")},
        )

        resp = client.get("/api/trips")
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestGetTrip:
    def test_get_existing(self, client, sample_image, monkeypatch):
        from app import main

        def mock_analyze(*args, **kwargs):
            return {
                "length_min": 35,
                "start_time": "08:15",
                "end_time": "08:50",
                "start_pos": "Helsinki Central Station",
                "end_pos": "Esplanadi",
                "bike_id": "TRE00410",
                "serial": "SN123456",
            }

        monkeypatch.setattr(main, "analyze_image", mock_analyze)

        upload_resp = client.post(
            "/api/trips/upload",
            files={"file": ("trip.png", sample_image, "image/png")},
        )
        trip_id = upload_resp.json()["id"]

        resp = client.get(f"/api/trips/{trip_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == trip_id

    def test_get_missing(self, client):
        resp = client.get("/api/trips/99999")
        assert resp.status_code == 404


class TestDeleteTrip:
    def test_delete_existing(self, client, sample_image, monkeypatch):
        from app import main

        def mock_analyze(*args, **kwargs):
            return {
                "length_min": 35,
                "start_time": "08:15",
                "end_time": "08:50",
                "start_pos": "Helsinki Central Station",
                "end_pos": "Esplanadi",
                "bike_id": "TRE00410",
                "serial": "SN123456",
            }

        monkeypatch.setattr(main, "analyze_image", mock_analyze)

        upload_resp = client.post(
            "/api/trips/upload",
            files={"file": ("trip.png", sample_image, "image/png")},
        )
        trip_id = upload_resp.json()["id"]

        resp = client.delete(f"/api/trips/{trip_id}")
        assert resp.status_code == 204

    def test_delete_missing(self, client):
        resp = client.delete("/api/trips/99999")
        assert resp.status_code == 404
