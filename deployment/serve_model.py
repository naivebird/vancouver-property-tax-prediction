import mlflow
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_NAME = "vancouver-property-tax-regressor"
MODEL_STAGE = "Production"
TRACKING_URI = "http://ec2-44-243-35-172.us-west-2.compute.amazonaws.com:5000/"

app = FastAPI()


mlflow.set_tracking_uri(TRACKING_URI)

model = mlflow.pyfunc.load_model(f"models:/{MODEL_NAME}/{MODEL_STAGE}")



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
    property_postal_code: str



def make_prediction(features):
    preds = model.predict(features)
    return float(preds[0])



@app.post('/predict')
async def predict(house: House):
    result = make_prediction(house.model_dump())
    return {
        'tax_amount': result
    }
