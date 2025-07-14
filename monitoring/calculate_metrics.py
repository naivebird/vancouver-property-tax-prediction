import datetime
import logging
import time
from pathlib import Path

import joblib
import pandas as pd
import psycopg
from evidently import ColumnMapping
from evidently.metrics import ColumnDriftMetric, DatasetDriftMetric, DatasetMissingValuesMetric, ColumnQuantileMetric
from evidently.report import Report
from prefect import task, flow
from prefect.cache_policies import NO_CACHE

# Constants
SEND_TIMEOUT = 10
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'example'
}
DB_NAME = 'monitoring_db'


class FeatureConfig:
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
        'neighbourhood_code'
    ]

    @classmethod
    def get_column_mapping(cls):
        return ColumnMapping(
            prediction='prediction',
            numerical_features=cls.NUMERICAL_FEATURES,
            categorical_features=cls.CATEGORICAL_FEATURES,
            target=None
        )


def create_monitoring_report():
    return Report(metrics=[
        ColumnDriftMetric(column_name='prediction'),
        DatasetDriftMetric(),
        DatasetMissingValuesMetric(),
        ColumnQuantileMetric(quantile=0.5, column_name="prediction"),

    ])


def get_db_connection(database_name=None):
    conn_params = DB_CONFIG.copy()
    if database_name:
        conn_params['dbname'] = database_name
    return psycopg.connect(**conn_params, autocommit=True)


@task
def prep_db():
    with get_db_connection() as conn:
        res = conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_NAME,))
        if len(res.fetchall()) == 0:
            conn.execute(f"CREATE database {DB_NAME};")

    with get_db_connection(DB_NAME) as conn:
        conn.execute("""
                     DROP TABLE if EXISTS metrics;
                     CREATE TABLE metrics
                     (
                         timestamp            TIMESTAMP,
                         prediction_drift     FLOAT,
                         num_drifted_columns  INTEGER,
                         share_missing_values FLOAT,
                         median_prediction      FLOAT
                     )
                     """)


def preprocess_data(raw_data, year):
    current_data = raw_data[raw_data.tax_assessment_year == str(year)].copy()
    current_data.dropna(inplace=True)

    for col in ['year_built', 'big_improvement_year', 'tax_assessment_year']:
        current_data[col] = current_data[col].astype(int)

    current_data["age"] = current_data['tax_assessment_year']  - current_data["year_built"]
    current_data["years_from_last_big_improvement"] = current_data['tax_assessment_year']  - current_data["big_improvement_year"]

    return current_data


@task(cache_policy=NO_CACHE)
def calculate_metrics(cursor, year, raw_data, reference_data, model):
    current_data = preprocess_data(raw_data, year)
    features = FeatureConfig.NUMERICAL_FEATURES + FeatureConfig.CATEGORICAL_FEATURES
    current_data['prediction'] = model.predict(current_data[features].to_dict(orient='records'))

    report = create_monitoring_report()
    report.run(
        reference_data=reference_data,
        current_data=current_data,
        column_mapping=FeatureConfig.get_column_mapping()
    )

    result = report.as_dict()
    metrics = {
        'prediction_drift': result['metrics'][0]['result']['drift_score'],
        'num_drifted_columns': result['metrics'][1]['result']['number_of_drifted_columns'],
        'share_missing_values': result['metrics'][2]['result']['current']['share_of_missing_values'],
        'median_prediction': result['metrics'][3]['result']['current']['value']
    }

    cursor.execute(
        """
        INSERT INTO metrics(timestamp, prediction_drift, num_drifted_columns, share_missing_values, median_prediction)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (datetime.datetime(year, 1, 1, 0, 0),
         metrics['prediction_drift'],
         metrics['num_drifted_columns'],
         metrics['share_missing_values'],
         metrics['median_prediction'])
    )


@flow
def batch_monitoring_backfill():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
    pipeline_dir = Path(__file__).parent.parent / 'pipeline'
    data_dir = pipeline_dir / "data"
    reference_data = pd.read_parquet(data_dir / 'reference.parquet')
    raw_data = pd.read_parquet(data_dir / 'property-tax-report.parquet')

    with open(pipeline_dir / 'models/lin_reg.bin', 'rb') as f_in:
        model = joblib.load(f_in)

    prep_db()
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)

    with get_db_connection(DB_NAME) as conn:
        for year in range(2021, 2026):
            with conn.cursor() as cursor:
                calculate_metrics(cursor, year, raw_data, reference_data, model)

            new_send = datetime.datetime.now()
            seconds_elapsed = (new_send - last_send).total_seconds()
            if seconds_elapsed < SEND_TIMEOUT:
                time.sleep(SEND_TIMEOUT - seconds_elapsed)
            last_send = new_send
            logging.info("Data sent")


if __name__ == '__main__':
    batch_monitoring_backfill()
