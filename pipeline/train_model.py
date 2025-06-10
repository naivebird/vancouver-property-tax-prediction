from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import scipy
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error
import mlflow
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from mlflow.tracking import MlflowClient

from prefect import flow, task

TRACKING_URI = "http://ec2-54-244-11-127.us-west-2.compute.amazonaws.com:5000/"


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

    dv = DictVectorizer()

    df_train.dropna(inplace=True)
    train_dicts = df_train[features].to_dict(orient="records")
    X_train = dv.fit_transform(train_dicts)

    df_val.dropna(inplace=True)
    val_dicts = df_val[features].to_dict(orient="records")
    X_val = dv.transform(val_dicts)

    y_train = df_train["tax_levy"].values
    y_val = df_val["tax_levy"].values
    return X_train, X_val, y_train, y_val, dv


@task(log_prints=True)
def train_model(
    X_train: scipy.sparse._csr.csr_matrix,
    X_val: scipy.sparse._csr.csr_matrix,
    y_train: np.ndarray,
    y_val: np.ndarray,
    dv: sklearn.feature_extraction.DictVectorizer,
) -> None:
    """Train a model and register it to the model registry"""

    with mlflow.start_run() as run:

        lr = LinearRegression()
        lr.fit(X_train, y_train)

        y_pred = lr.predict(X_val)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        Path("models").mkdir(exist_ok=True)
        with open("models/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact("models/preprocessor.b", artifact_path="preprocessor")

        mlflow.sklearn.log_model(lr, artifact_path="model")

        run_id = run.info.run_id
        model_uri = f"runs:/{run_id}/model"

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
            prod_y_pred = prod_model.predict(X_val)
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
    X_train, X_val, y_train, y_val, dv = add_features(df_train, df_val)

    # Train
    train_model(X_train, X_val, y_train, y_val, dv)


if __name__ == "__main__":
    main_flow()