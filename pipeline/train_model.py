from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any

import mlflow
import numpy as np
import pandas as pd
from joblib import dump
from mlflow.tracking import MlflowClient
from prefect import flow, task
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline, make_pipeline

# Configuration constants
TRACKING_URI = "http://ec2-34-220-213-61.us-west-2.compute.amazonaws.com:5000/"
MODEL_NAME = "vancouver-property-tax-regressor"
EXPERIMENT_NAME = "vancouver-property-tax-experiment"
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Feature configuration
NUMERICAL_FEATURES = [
    'current_land_value',
    'current_improvement_value',
    'previous_land_value',
    'previous_improvement_value',
    'age',
    'years_from_last_big_improvement'
]

CATEGORICAL_FEATURES = [
    'legal_type',
    'zoning_classification',
    'neighbourhood_code',
]

FeatureMatrix = pd.DataFrame
TargetVector = np.ndarray


@task(retries=3, retry_delay_seconds=2)
def read_data(filename: str, year: int) -> pd.DataFrame:
    """
    Read and filter property tax data for a specific year.
    
    Args:
        filename: Path to the parquet file
        year: Tax assessment year to filter
    Returns:
        Filtered DataFrame for the specified year
    """
    df = pd.read_parquet(filename)
    return df[df.tax_assessment_year == str(year)]


@task(log_prints=True)
def add_features(df: pd.DataFrame) -> Tuple[FeatureMatrix, FeatureMatrix, TargetVector, TargetVector]:
    """
    Prepare features and split data into training and testing sets.
    
    Args:
        df: Input DataFrame with raw features
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    df = df.copy()
    df.dropna(inplace=True)

    # Convert and calculate temporal features
    year_columns = ['year_built', 'big_improvement_year', 'tax_assessment_year']
    for col in year_columns:
        df[col] = df[col].astype(int)

    df["age"] = df['tax_assessment_year'] - df["year_built"]
    df["years_from_last_big_improvement"] = df['tax_assessment_year'] - df["big_improvement_year"]
    df.drop(columns=year_columns, inplace=True)

    features = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    return train_test_split(
        df[features],
        df["tax_levy"],
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )


def save_model(pipeline: Pipeline, predictions: np.ndarray, test_data: pd.DataFrame) -> None:
    """Save model artifacts and predictions."""
    test_data["prediction"] = predictions
    test_data.to_parquet("data/reference.parquet")

    model_dir = Path("models")
    model_dir.parent.mkdir(parents=True, exist_ok=True)
    with open(model_dir / "lin_reg.bin", "wb") as f_out:
        dump(pipeline, f_out)


def handle_model_staging(
        client: MlflowClient,
        registered_model: mlflow.entities.model_registry.ModelVersion,
        test_data: Dict[str, Any],
        y_test: np.ndarray,
        current_rmse: float
) -> None:
    """Handle model staging and promotion logic."""
    try:
        prod_model = mlflow.pyfunc.load_model(f"models:/{registered_model.name}/Production")
        prod_predictions = prod_model.predict(test_data)
        prod_rmse = root_mean_squared_error(y_test, prod_predictions)

        if current_rmse <= prod_rmse:
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


@task(log_prints=True)
def train_model(
        X_train: FeatureMatrix,
        X_test: FeatureMatrix,
        y_train: TargetVector,
        y_test: TargetVector
) -> None:
    """
    Train model, log metrics, and handle model registration.
    
    Args:
        X_train: Training features
        X_test: Test features
        y_train: Training target
        y_test: Test target
    """
    with mlflow.start_run() as run:
        # Train model
        pipeline = make_pipeline(DictVectorizer(), LinearRegression())
        train_dicts = X_train.to_dict(orient="records")
        test_dicts = X_test.to_dict(orient="records")
        pipeline.fit(train_dicts, y_train)

        # Generate and save predictions
        predictions = pipeline.predict(test_dicts)
        save_model(pipeline, predictions, X_test)

        # Log metrics
        rmse = root_mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)

        # Register model
        mlflow.sklearn.log_model(pipeline, artifact_path="model")
        model_uri = f"runs:/{run.info.run_id}/model"
        print(f"Registering model from URI: {model_uri}")

        registered_model = mlflow.register_model(
            model_uri=model_uri,
            name=MODEL_NAME
        )

        # Handle model staging
        client = MlflowClient()
        client.transition_model_version_stage(
            name=registered_model.name,
            version=registered_model.version,
            stage="Staging"
        )

        handle_model_staging(client, registered_model, test_dicts, y_test, rmse)


@flow()
def main_flow(train_path: str = "./data/property-tax-report.parquet") -> None:
    """
    Main training pipeline flow.
    
    Args:
        train_path: Path to the training data file
    """
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    df_train = read_data(train_path, 2020)
    X_train, X_test, y_train, y_test = add_features(df_train)
    train_model(X_train, X_test, y_train, y_test)


if __name__ == "__main__":
    main_flow()
