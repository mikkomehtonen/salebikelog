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


class TestGetUnmatchedPositions:
    def test_empty_list_no_trips(self, client):
        resp = client.get("/api/positions/unmatched")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_empty_list_all_positions_matched(self, client):
        from app.crud import create_position

        create_position("Helsinki Central Station", 60.17, 24.94, None)
        create_position("Esplanadi", 60.16, 24.93, None)

        resp = client.get("/api/positions/unmatched")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_unmatched_start_and_end(self, client, sample_image, monkeypatch):
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

        resp = client.get("/api/positions/unmatched")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        names = {item["name"] for item in data}
        assert names == {"Helsinki Central Station", "Esplanadi"}
        for item in data:
            assert item["source"] in ("start_pos", "end_pos")
            assert "trip_id" in item

    def test_returns_only_unmatched_when_partial_match(self, client, sample_image, monkeypatch):
        from app import main
        from app.crud import create_position

        create_position("Helsinki Central Station", 60.17, 24.94, None)

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

        resp = client.get("/api/positions/unmatched")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Esplanadi"
        assert data[0]["source"] == "end_pos"
