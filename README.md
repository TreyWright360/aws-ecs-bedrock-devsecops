# 🚀 Containerized GenAI Microservice on AWS ECS Fargate with DevSecOps

> **Portfolio evidence status:** Application, container, tests, Terraform, and CI workflow are published. No dated ECS rollback exercise, latency benchmark, or passing vulnerability-gate report is checked in. The [AWS Cloud Operations Handbook](https://github.com/TreyWright360/aws-cloud-operations-handbook) tracks the remaining operational proof.

See the [project case study](CASE-STUDY.md) for architecture, implementation, failure modes, evidence, and production improvements.

![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Security: Trivy](https://img.shields.io/badge/Security-Trivy_Scanned-blue?style=for-the-badge&logo=aquasec&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

---

## 📌 Executive Summary & Business Impact
* **Business Challenge:** Engineering teams required an automated, scalable microservice to process and summarize enterprise documents via generative AI, without exposing long-lived credentials or managing underlying virtual machine operating systems.
* **Solution:** Developed a high-performance Python FastAPI service integrated with **Amazon Bedrock (Claude 3.5 Haiku)**, packaged into a hardened multi-stage Docker container running as an unprivileged non-root user, deployed to **Amazon ECS Fargate**, and secured with an automated **Trivy vulnerability scanning DevSecOps pipeline**.
* **Key Metric Results:**
  * 🔒 **Security scan defined:** GitHub Actions runs Trivy, currently with `exit-code: "0"`, so findings do not block deployment.
  * ⚡ **Latency unmeasured:** No benchmark is checked in.
  * 🛡️ **Task identity:** The ECS task role permits Bedrock invocation; its policy currently uses `Resource = "*"` and needs scoping review.
  * 💰 **Cost unmeasured:** The ECS service has `desired_count = 1`, so it incurs running-task charges while deployed.

---

## 🏗️ Architecture & Data Flow

```text
[ Developer Push ] ──▶ [ GitHub Actions CI/CD ]
                              │
                              ├──▶ Step 1: Flake8 Linting & Pytest Unit Tests
                              ├──▶ Step 2: Trivy Container CVE Vulnerability Scan
                              └──▶ Step 3: Build & Push Docker Image
                                               │
                                               ▼
                                     [ Amazon ECR Repository ]
                                     (Encrypted & Scan-on-Push)
                                               │
                                               ▼
[ User / Client ] ──▶ [ Port 8000 ] ──▶ [ Amazon ECS (AWS Fargate Cluster) ]
                                               │
                                               ├────▶ [ AWS CloudWatch Logs ]
                                               │
                                               ▼ (IAM Task Role)
                                     [ Amazon Bedrock ]
                                     (Claude 3.5 Haiku Inference)
```

---

## 🛡️ DevSecOps & Security Hardening Highlights

1. **Unprivileged Non-Root Execution:** The Docker container enforces strict privilege separation by running as dedicated non-root user `appuser` (`UID 10001`), neutralizing container-escape attack vectors.
2. **Multi-Stage Build Pipeline:** Strips compilers, build headers, and package caches from the runtime image to reduce attack surface and maintain image footprint under 160MB.
3. **Vulnerability scan:** GitHub Actions builds and scans the image with **Trivy**, but the current `exit-code: "0"` means the scan is advisory.
4. **Role-based task identity:** The application uses an ECS task role instead of static credentials. The Bedrock resource scope is currently `*` and should be narrowed where supported.

---

## 📡 API Specification & Endpoints

### 1. Health Probe
* **Endpoint:** `GET /health`
* **Response:**
```json
{
  "status": "healthy",
  "service": "aws-bedrock-microservice",
  "region": "us-east-1",
  "default_model": "anthropic.claude-3-5-haiku-20241022-v1:0",
  "timestamp": 1725642000.12
}
```

### 2. Document Analysis & AI Summarization
* **Endpoint:** `POST /api/analyze`
* **Request Payload:**
```json
{
  "text": "Cloud computing allows organizations to scale workloads dynamically without managing physical data centers. Utilizing Infrastructure as Code and automated DevSecOps pipelines ensures consistency and security.",
  "task": "summarize"
}
```
* **Supported Tasks:** `summarize`, `sentiment`, `action_items`, `key_takeaways`
* **Response:**
```json
{
  "task": "summarize",
  "result": "Cloud computing eliminates physical data center management, enabling dynamic scalability. Pairing it with Infrastructure as Code and DevSecOps pipelines guarantees operational security and deployment consistency.",
  "model": "anthropic.claude-3-5-haiku-20241022-v1:0",
  "source": "aws-bedrock",
  "execution_time_ms": 342.15
}
```

---

## 💻 Local Quickstart & Testing

### 1. Run Unit Tests Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
pytest tests/ -v
```

### 2. Build and Run Container with Docker
```bash
# Build the hardened image
docker build -t bedrock-microservice:local .

# Run the container locally
docker run -d -p 8000:8000 --name bedrock-api bedrock-microservice:local

# Test health check
curl http://localhost:8000/health

# Clean up
docker stop bedrock-api && docker rm bedrock-api
```

---

## ☁️ Infrastructure Deployment via Terraform

To provision the Amazon ECR repository, ECS Fargate cluster, IAM roles, and CloudWatch log groups:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Teardown (verify billable resources are removed):
```bash
terraform destroy
```

---

## 💼 Technical Interview Talking Points
* **Why Fargate instead of self-managed EC2?**
  * *Fargate abstracts host operating system maintenance, eliminates server patching overhead, and scales on exact vCPU/memory requirements.*
* **How is container security validated?**
  * *The image is built in two stages, runs as an unprivileged user (UID 10001), and undergoes advisory Trivy scanning in GitHub Actions. A blocking security gate is future work.*
* **How are AWS credentials managed inside ECS?**
  * *No static AWS keys are stored in the container. The service assumes an IAM Task Role at runtime via the AWS ECS metadata service to interact with Amazon Bedrock.*
