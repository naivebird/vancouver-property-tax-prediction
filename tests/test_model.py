import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.pipeline import Pipeline
from pipeline.train_model import (
    read_data,
    add_features,
    save_model,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES
)


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'tax_assessment_year': ['2020'] * 5,
        'current_land_value': [100000] * 5,
        'current_improvement_value': [50000] * 5,
        'previous_land_value': [90000] * 5,
        'previous_improvement_value': [45000] * 5,
        'year_built': [2000] * 5,
        'big_improvement_year': [2010] * 5,
        'legal_type': ['Strata'] * 5,
        'zoning_classification': ['RM-4'] * 5,
        'neighbourhood_code': ['WE'] * 5,
        'tax_levy': [5000] * 5
    })


def test_read_data(tmp_path, sample_data):
    # Save sample data to temporary parquet file
    data_path = tmp_path / "test_data.parquet"
    sample_data.to_parquet(data_path)

    # Test data reading
    result = read_data.fn(str(data_path), 2020)
    assert len(result) == 5
    assert result['tax_assessment_year'].values[0] == '2020'


def test_add_features(sample_data):
    X_train, X_test, y_train, y_test = add_features.fn(sample_data)

    # Check if features are correctly split
    assert isinstance(X_train, pd.DataFrame)
    assert isinstance(X_test, pd.DataFrame)
    assert isinstance(y_train, pd.Series)
    assert isinstance(y_test, pd.Series)

    # Verify all required features are present
    expected_features = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
    assert all(feature in X_train.columns for feature in expected_features)

    # Check if age and years_from_last_big_improvement are calculated correctly
    assert 'age' in X_train.columns
    assert 'years_from_last_big_improvement' in X_train.columns


def test_save_model(tmp_path):
    # Create dummy pipeline and predictions
    pipeline = Pipeline([('dummy', None)])
    predictions = np.array([1000, 2000])
    test_data = pd.DataFrame({
        'feature1': [1, 2],
        'feature2': [3, 4]
    })

    # Temporarily change working directory
    original_cwd = Path.cwd()
    try:
        # Create necessary directories
        Path(tmp_path / "data").mkdir(parents=True)
        Path(tmp_path / "models").mkdir(parents=True)
        
        # Change to temporary directory
        os.chdir(tmp_path)

        # Test model saving
        save_model(pipeline=pipeline,
                   predictions=predictions,
                   test_data=test_data,
                   reference_dir=Path(tmp_path / "data"),
                   model_dir=Path(tmp_path / "models"))

        # Verify files were created using tmp_path
        assert (tmp_path / "data" / "reference.parquet").exists()
        assert (tmp_path / "models" / "lin_reg.bin").exists()
    finally:
        # Restore working directory
        os.chdir(original_cwd)
