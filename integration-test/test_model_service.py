from unittest.mock import patch

class DummyModel:
    def predict(self, x):
        return [12345.67]

@patch("deployment.serve_model.load_model_from_registry", return_value=DummyModel())
def test_predict_endpoint(mock_load_model):
    from deployment.serve_model import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    payload = {
        "current_land_value": 100000,
        "current_improvement_value": 50000,
        "previous_land_value": 90000,
        "previous_improvement_value": 45000,
        "year_built": 2000,
        "big_improvement_year": 2010,
        "tax_assessment_year": 2020,
        "legal_type": "Strata",
        "zoning_classification": "RM-4",
        "neighbourhood_code": "WE"
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["tax_amount"] == 12345.67