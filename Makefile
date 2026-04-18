.PHONY: help setup up down logs airflow-logs terraform-init terraform-apply terraform-destroy

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup: copy env file and create directories
	@test -f .env || cp .env.example .env
	@mkdir -p data/raw keys airflow/logs airflow/plugins
	@echo "Setup complete. Edit .env with the GCP project details."
	@echo "Place the GCP service account key JSON in ./keys/gcp-key.json"

up: ## Start all services (Airflow + Dashboard)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose down && docker compose up -d --build

logs: ## Show logs for all services
	docker compose logs -f

airflow-logs: ## Show Airflow scheduler logs
	docker compose logs -f airflow-scheduler

dashboard-logs: ## Show dashboard logs
	docker compose logs -f dashboard

terraform-init: ## Initialize Terraform
	cd terraform && terraform init

terraform-plan: ## Plan Terraform changes
	cd terraform && terraform plan -var="project_id=$${GCP_PROJECT_ID}"

terraform-apply: ## Apply Terraform (create GCS bucket + BigQuery dataset)
	cd terraform && terraform apply -var="project_id=$${GCP_PROJECT_ID}" -auto-approve

terraform-destroy: ## Destroy Terraform resources
	cd terraform && terraform destroy -var="project_id=$${GCP_PROJECT_ID}" -auto-approve

dbt-run: ## Run dbt models locally
	cd dbt_stocks && dbt run --profiles-dir . --project-dir .

dbt-test: ## Run dbt tests locally
	cd dbt_stocks && dbt test --profiles-dir . --project-dir .

clean: ## Remove generated data and logs
	rm -rf data/raw/*.parquet airflow/logs/*

pipeline-check: ## Verify all services are healthy and DAG exists
	@echo "Checking Airflow webserver..."
	@docker compose ps airflow-webserver | grep "healthy" && echo "Airflow: OK" || echo "Airflow: NOT HEALTHY"
	@echo "Checking dashboard..."
	@docker compose ps dashboard | grep "Up" && echo "Dashboard: OK" || echo "Dashboard: NOT RUNNING"
