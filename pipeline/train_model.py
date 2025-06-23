from pathlib import Path
from typing import List
import pandas as pd
import numpy as np
import scipy
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error, r2_score
import mlflow
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from mlflow.tracking import MlflowClient
from sklearn.pipeline import make_pipeline


from prefect import flow, task

TRACKING_URI = "http://ec2-44-243-35-172.us-west-2.compute.amazonaws.com:5000/"


@task(retries=3, retry_delay_seconds=2)
def read_data(filename: str) -> pd.DataFrame:
    """Read data into DataFrame"""
    return pd.read_parquet(filename)



@task(log_prints=True)
def add_features(
    df_train: pd.DataFrame, df_val: pd.DataFrame
) -> tuple(
    [
        scipy.sparse._csr.csr_matrix,
        scipy.sparse._csr.csr_matrix,
        np.ndarray,
        np.ndarray,
        sklearn.feature_extraction.DictVectorizer,
    ]
):  # type: ignore
    """Add features to the model"""

    features = ['current_land_value', 
        'current_improvement_value',
        'previous_land_value',
        'previous_improvement_value',
        'year_built',
        'big_improvement_year', 
        'tax_assessment_year',
        'legal_type', 
        'zoning_classification',
        'neighbourhood_code',
        'property_postal_code'
        ]

    df_train.dropna(inplace=True)
    df_val.dropna(inplace=True)


    for col in ['year_built', 'big_improvement_year', 'tax_assessment_year']:
        df_train[col] = df_train[col].astype(int)
        df_val[col] = df_val[col].astype(int)

    train_dicts = df_train[features].to_dict(orient="records")

    val_dicts = df_val[features].to_dict(orient="records")

    y_train = df_train["tax_levy"].values
    y_val = df_val["tax_levy"].values
    return train_dicts, val_dicts, y_train, y_val


@task(log_prints=True)
def train_model(
    train_dicts: List[dict],
    val_dicts: List[dict],
    y_train: np.ndarray,
    y_val: np.ndarray
) -> None:
    """Train a model and register it to the model registry"""

    with mlflow.start_run() as run:

        pipeline = make_pipeline(
        DictVectorizer(),
        LinearRegression()
    )
        pipeline.fit(train_dicts, y_train)

        y_pred = pipeline.predict(val_dicts)

        rmse = root_mean_squared_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)

        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)

        mlflow.sklearn.log_model(pipeline, artifact_path="model")

        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/model"
        print("register model")

        registered_model = mlflow.register_model(
            model_uri=model_uri,
            name="vancouver-property-tax-regressor"
        )
        
        client = MlflowClient()
        client.transition_model_version_stage(
            name=registered_model.name,
            version=registered_model.version,
            stage="Staging"
        )

        try:
            prod_model = mlflow.pyfunc.load_model(f"models:/{registered_model.name}/Production")
            prod_y_pred = prod_model.predict(val_dicts)
            prod_rmse = root_mean_squared_error(y_val, prod_y_pred)

            if rmse > prod_rmse:
                client.transition_model_version_stage(
                    name=registered_model.name,
                    version=registered_model.version,
                    stage="Production",
                    archive_existing_versions=True
                )

        except mlflow.MlflowException:
            client.transition_model_version_stage(
                name=registered_model.name,
                version=registered_model.version,
                stage="Production",
                archive_existing_versions=True
            )

    return None


@flow(log_prints=True)
def main_flow(
    train_path: str = "./data/property-tax-report-2024.parquet",
    val_path: str = "./data/property-tax-report-2025.parquet",
) -> None:
    """The main training pipeline"""

    # MLflow settings
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("vancouver-property-tax-experiment")


    # Load
    df_train = read_data(train_path)
    df_val = read_data(val_path)

    # Transform
    train_dicts, val_dicts, y_train, y_val = add_features(df_train, df_val)

    # Train
    train_model(train_dicts, val_dicts, y_train, y_val)


if __name__ == "__main__":
    main_flow()