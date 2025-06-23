from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.feature_extraction import DictVectorizer
import numpy as np


X_train = [
    {'current_land_value': 481000.0, 'current_improvement_value': 235000.0, 'previous_land_value': 453000.0, 'previous_improvement_value': 221000.0, 'year_built': '2008', 'big_improvement_year': '2008', 'tax_assessment_year': '2025', 'legal_type': 'STRATA', 'zoning_classification': 'Comprehensive Development', 'neighbourhood_code': '026', 'property_postal_code': 'V6E 4V2'},
    {'current_land_value': 1674000.0, 'current_improvement_value': 479000.0, 'previous_land_value': 1600000.0, 'previous_improvement_value': 458000.0, 'year_built': '2021', 'big_improvement_year': '2021', 'tax_assessment_year': '2025', 'legal_type': 'STRATA', 'zoning_classification': 'Comprehensive Development', 'neighbourhood_code': '009', 'property_postal_code': 'V5Z 0K1'},
    {'current_land_value': 542000.0, 'current_improvement_value': 190000.0, 'previous_land_value': 537000.0, 'previous_improvement_value': 188000.0, 'year_built': '1989', 'big_improvement_year': '1989', 'tax_assessment_year': '2025', 'legal_type': 'STRATA', 'zoning_classification': 'Residential', 'neighbourhood_code': '027', 'property_postal_code': 'V6E 1H5'}
 ]

y_train = np.array([6423.14, 1160.56, 1653.27])

pipeline = make_pipeline(
        DictVectorizer(),
        LinearRegression()
    )

pipeline.fit(X_train, y_train)

y_pred = pipeline.predict(X_train)
print(y_pred)