import requests

house = {
    'current_land_value': 455000,
    'current_improvement_value': 178000,
    'previous_land_value': 450000,
    'previous_improvement_value': 176000,
    'year_built': 1997,
    'big_improvement_year': 1997, 
    'tax_assessment_year': 2025,
    'legal_type': 'STRATA',
    'zoning_classification': 'Commercial',
    'neighbourhood_code': '023',
    'property_postal_code': 'V5R 6E5'
}

url = 'http://ec2-34-212-168-220.us-west-2.compute.amazonaws.com:8000/predict'
headers = {'Content-Type': 'application/json'}

response = requests.post(url, json=house, headers=headers)
print(response.json())