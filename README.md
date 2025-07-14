# vancouver-property-tax-prediction

## Problem Statement
Municipalities require accurate and efficient prediction of property tax amounts for residential properties based on various features such as land value, improvement value, property age, legal type, zoning, and neighborhood. Manual assessment is time-consuming and prone to inconsistencies. This project aims to develop and deploy a machine learning model as a web service that predicts property tax amounts using structured property data, enabling automated, scalable, and reliable tax estimation for city officials and property owners in Vancouver.

## Dataset
This project uses the Property tax report dataset from City of Vancouver's [Open Data Portal](https://opendata.vancouver.ca/explore/dataset/property-tax-report/information/?sort=-tax_assessment_year). The dataset contains information on properties from BC Assessment (BCA) and City sources from 2020.

## Technologies
- Cloud: AWS (EC2, S3, RDS, ECR)
- Experiment tracking tool: MLFlow
- Workflow orchestration: Prefect
- Model Serving: FastAPI
- Monitoring: Evidently, Grafana
- Infrastructure as code (IaC): Terraform

## Architecture
### Overview
Yearly property data is downloaded from the Open Data Portal and stored locally. A local pipeline, orchestrated with Prefect, can be triggered to train a new regression model on the latest data. The trained model is logged to MLflow, registered in the model registry (backed by S3) under the Staging stage, and evaluated using tracked performance metrics. If the new model outperforms the current one, it is promoted to Production.

A FastAPI-based prediction service, hosted on a dedicated EC2 instance, loads the Production model and serves predictions through the `/predict` endpoint. The MLflow tracking server runs on a separate EC2 instance.

For model monitoring, Evidently, Grafana, and supporting services can be started locally using Docker Compose. A Prefect backfill pipeline is also available to compute historical monitoring metrics. A prebuilt dashboard.json is provided in `monitoring/dashboards` for direct import into Grafana.

All cloud infrastructure components, including EC2 instances, RDS, S3 buckets, and networking, are provisioned and managed using Terraform for reproducibility and infrastructure-as-code best practices.

The project is well tested using unit tests and integration tests.

### Diagram

<img width="841" height="521" alt="MLOps Diagram drawio" src="https://github.com/user-attachments/assets/d7893868-9cd9-414c-94b1-07143e11e29d" />

## Steps to Reproduce
### Prerequisites
To get this project working, you need to have an AWS account and configure its credentials in your local environment. In addition, the latest version of Terraform is required.

### Step 1: Clone this repo
```bash
git clone https://github.com/naivebird/vancouver-property-tax-prediction.git
cd vancouver-property-tax-prediction
```
### Step 2: Set up a local environment
Install pipenv
```bash
pip install --user pipenv
```
Install required libraries
```bash
pipenv install --dev
```

### Step 3: Build and push a Docker image for the model service to ECR
This step helps prepare the Docker image for the API server provisioned by Terraform in the next step.
```bash
cd deployment
./build_and_push.sh
```
### Step 4: Create cloud resources
In this step, you'll use Terraform to provision the following AWS resources: 
- An MLFlow server on EC2
- An API web service on EC2
- S3 for storing MLFlow artifacts
- A PostgreSQL database on RDS for MLFlow backend

Before running the Terraform commands, you should use the `terraform/terraform.tfvars.example` file as a reference to create a new file named `terraform/terraform.tfvars` and fill in your cloud variables where needed.

Init terraform:
```bash
cd terraform
terraform init
```
Check if resources are correct:
```bash
terraform plan
```
Create resources:
```bash
terraform apply
```

After Terraform finishes provisioning all the resources, it'll output the MLFlow server URI and also the API server URL.

<img width="585" height="199" alt="Screenshot 2025-07-14 at 1 48 12 PM" src="https://github.com/user-attachments/assets/6fec2321-7706-4c2e-bb83-02a6130119f5" />


### Step 5: Run the model training pipeline

Update the `TRACKING_URI` variable in the `train_model.py` file with the one in the Terraform output.

Start a local prefect server
```bash
prefect server start
```
Start a local prefect worker
```bash
export PREFECT_API_URL="http://127.0.0.1:4200/api"
prefect worker start --pool 'default'
```
Download training data
```bash
python pipeline/download_data.py
```
Run the pipeline
```bash
python pipeline/train_model.py
```
Access Prefect's UI at `http://127.0.0.1:4200/runs` to see the visualization of the pipeline:

<img width="2216" height="629" alt="image" src="https://github.com/user-attachments/assets/77c3b9af-aa92-41da-902c-ba52a5eafdce" />

Go to MLFlow URI in the Terraform output to view the model experiment as well as the registered model:

Model experiment:

<img width="2553" height="1264" alt="image" src="https://github.com/user-attachments/assets/183c98c7-7746-4f75-9855-11fd71057e38" />

Model metrics:

<img width="2554" height="809" alt="image" src="https://github.com/user-attachments/assets/68bab388-d601-424b-a776-4719772c9265" />

Registered model:

<img width="2544" height="586" alt="image" src="https://github.com/user-attachments/assets/ac08f368-c265-4610-a709-d236ea2f931f" />

Model artifacts can be found on the `vancouver-property-tax-models` bucket on S3:

<img width="2532" height="744" alt="image" src="https://github.com/user-attachments/assets/b98c5715-96e5-487c-8f62-838aafaf5b38" />

### Step 6: Test model service

Update the `url` variable in the `deployment/api_dev.py` file with the ec2_service_url in the Terraform output.

Run the file to test the service:
```bash
python deployment/api_dev.py
```
### Step 7: Monitor the model

Start PostgreSQL and Grafana:

```
cd monitoring
docker compose up --build -d
```

Run batch monitoring backfill pipeline to calculate historical metrics using Evidently:

```
python calculate_metrics.py
```
The pipeline is visualized on Prefect's UI at `http://127.0.0.1:4200/runs` :

<img width="2217" height="631" alt="image" src="https://github.com/user-attachments/assets/d34844a1-3cf9-493e-b04b-352b051b476b" />

After the metrics are stored in the PostgreSQL database, you can visit Grafana's UI to create a Dashboard. Alternatively, you can import the `monitoring/dashboards/dashboard.json` file to Grafana.

<img width="2242" height="647" alt="Screenshot 2025-07-14 at 2 28 04 PM" src="https://github.com/user-attachments/assets/bbf5f388-e887-43d0-bd25-3561ea5db433" />

### Step 8: Terminate all the cloud resources

```bash
terraform destroy
```

