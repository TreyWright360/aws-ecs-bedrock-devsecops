import json
import logging
import os
import time
from typing import Literal, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bedrock-api")

app = FastAPI(
    title="AWS Bedrock Document Intelligence Microservice",
    description="Containerized GenAI API deployed on Amazon ECS Fargate with automated DevSecOps pipelines.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DEFAULT_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")

# Initialize boto3 Bedrock client lazily
bedrock_client = None


def get_bedrock_client():
    global bedrock_client
    if bedrock_client is None:
        try:
            import boto3
            bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        except Exception as e:
            logger.warning(f"Could not initialize live Bedrock client: {e}")
            bedrock_client = None
    return bedrock_client


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=15000, description="Input text to analyze")
    task: Literal["summarize", "sentiment", "action_items", "key_takeaways"] = Field(
        default="summarize", description="Analysis task to perform"
    )
    model_id: Optional[str] = Field(default=None, description="Amazon Bedrock model ID override")


class AnalyzeResponse(BaseModel):
    task: str
    result: str
    model: str
    source: Literal["aws-bedrock", "simulation-fallback"]
    execution_time_ms: float


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Liveness probe used by ALB Target Group and ECS container health checks."""
    return {
        "status": "healthy",
        "service": "aws-bedrock-microservice",
        "region": AWS_REGION,
        "default_model": DEFAULT_MODEL_ID,
        "timestamp": time.time(),
    }


@app.post("/api/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
def analyze_document(request: AnalyzeRequest):
    """
    Executes intelligent text analysis using Amazon Bedrock with least-privilege IAM credentials.
    Falls back gracefully if live model access is not yet provisioned.
    """
    start_time = time.time()
    model = request.model_id or DEFAULT_MODEL_ID

    prompt_map = {
        "summarize": f"Provide a concise, executive-level summary of the following content:\n\n{request.text}",
        "sentiment": f"Analyze the sentiment and emotional tone of the following text with key drivers:\n\n{request.text}",
        "action_items": f"Extract an actionable bulleted list of next steps and action items from this text:\n\n{request.text}",
        "key_takeaways": f"Identify the top 3-5 high-impact takeaways from this document:\n\n{request.text}",
    }
    user_prompt = prompt_map.get(request.task, prompt_map["summarize"])

    client = get_bedrock_client()

    if client:
        try:
            logger.info(f"Invoking Amazon Bedrock model: {model} for task: {request.task}")
            # Bedrock Converse API supports modern models (Claude 3/3.5, Titan, Llama, Mistral)
            response = client.converse(
                modelId=model,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": user_prompt}],
                    }
                ],
                inferenceConfig={"maxTokens": 1024, "temperature": 0.2},
            )
            output_text = response["output"]["message"]["content"][0]["text"]
            duration = round((time.time() - start_time) * 1000, 2)
            return AnalyzeResponse(
                task=request.task,
                result=output_text.strip(),
                model=model,
                source="aws-bedrock",
                execution_time_ms=duration,
            )
        except Exception as err:
            logger.error(f"Live Bedrock invocation failed: {err}")
            # Fall back to structured response if model access is pending or rate-limited

    # Graceful fallback for local dev / sandbox environments
    duration = round((time.time() - start_time) * 1000, 2)
    fallback_results = {
        "summarize": f"Executive Summary: Processed document containing {len(request.text)} characters. Primary themes identify cloud optimization, continuous security, and automated microservices.",
        "sentiment": "Sentiment Analysis: Neutral to Highly Positive (Confidence Score: 0.94). Tone reflects strategic planning and operational readiness.",
        "action_items": "• Finalize container vulnerability scanning with Trivy\n• Verify least-privilege IAM task roles\n• Deploy to AWS ECS Fargate cluster with automated ALB health probes",
        "key_takeaways": "1. Multi-tier isolation secures cloud workloads\n2. Serverless containers eliminate OS maintenance overhead\n3. Integrated GenAI elevates operational capability",
    }
    return AnalyzeResponse(
        task=request.task,
        result=fallback_results.get(request.task, fallback_results["summarize"]),
        model=model,
        source="simulation-fallback",
        execution_time_ms=duration,
    )
