import logging
import os

import mlflow
from fastapi import FastAPI
from mlflow.exceptions import RestException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_NAME = "vancouver-property-tax-regressor"
MODEL_STAGE = "Production"
mlflow_tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
app = FastAPI()

model = None


mlflow.set_tracking_uri(mlflow_tracking_uri)

def load_model_from_registry(model_name: str, model_stage: str):
    """
    Load a model from the MLflow model registry.

    Args:
        model_name: Name of the model in the registry
        model_stage: Stage of the model (e.g., 'Production', 'Staging')

    Returns:
        Loaded model or None if not found
    """
    try:
        return mlflow.pyfunc.load_model(f"models:/{model_name}/{model_stage}")
    except RestException as e:
        logger.warning(f"Error loading model {model_name} in stage {model_stage}: {e}")
        return None


class House(BaseModel):
    current_land_value: float
    current_improvement_value: float
    previous_land_value: float
    previous_improvement_value: float
    year_built: int
    big_improvement_year: int
    tax_assessment_year: int
    legal_type: str
    zoning_classification: str
    neighbourhood_code: str


def prepare_features(house: House):
    return {
        'current_land_value': house.current_land_value,
        'current_improvement_value': house.current_improvement_value,
        'previous_land_value': house.previous_land_value,
        'previous_improvement_value': house.previous_improvement_value,
        'age': house.tax_assessment_year - house.year_built,
        'years_from_last_big_improvement': house.tax_assessment_year - house.big_improvement_year,
        'legal_type': house.legal_type,
        'zoning_classification': house.zoning_classification,
        'neighbourhood_code': house.neighbourhood_code
    }


def make_prediction(features):
    preds = model.predict(features)
    return float(preds[0])



@app.post('/predict')
async def predict(house: House):
    global model
    if model is None:
        model = load_model_from_registry(MODEL_NAME, MODEL_STAGE)
    if model is None:
        return {"error": "Model not found in registry."}
    features = prepare_features(house)
    result = make_prediction(features)
    return {
        'tax_amount': result
    }
