import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from .config import settings

def ask_bedrock(question: str, context: dict) -> str:
    """Call Amazon Bedrock Converse API. Credentials are resolved by the AWS SDK chain."""
    session = boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region) if settings.aws_profile else boto3.Session(region_name=settings.aws_region)
    client = session.client("bedrock-runtime")
    prompt = f"""You are Sales Ninja, a concise sales analytics copilot.
Use only the supplied business snapshot. Do not invent numbers. If the snapshot lacks
the requested detail, say what is missing. Explain calculations briefly.
Business snapshot (JSON): {json.dumps(context, default=str)}
User question: {question}"""
    try:
        response = client.converse(
            modelId=settings.bedrock_model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 700, "temperature": 0.2, "topP": 0.9},
        )
        return response["output"]["message"]["content"][0]["text"]
    except (BotoCoreError, ClientError, KeyError) as exc:
        raise RuntimeError(f"Amazon Bedrock request failed: {exc}") from exc
