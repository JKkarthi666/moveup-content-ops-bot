import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from src.models import ChannelData, ReportResult
from src.prompts import SYSTEM_ANALYST_PROMPT, REPORT_GENERATION_PROMPT
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

class ReportEngine:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY in environment variables.")
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_report(self, channel_data: ChannelData) -> dict:
        logger.info(f"Generating LLM report for {channel_data.channel_handle}...")
        raw_data = channel_data.model_dump_json(indent=2)
        user_prompt = REPORT_GENERATION_PROMPT.format(channel_name=channel_data.channel_name, channel_data=raw_data)

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": SYSTEM_ANALYST_PROMPT}, {"role": "user", "content": user_prompt}],
            temperature=0.3
        )

        try:
            parsed = ReportResult.model_validate(json.loads(response.choices[0].message.content))
            return parsed.model_dump()
        except Exception as e:
            logger.error(f"LLM Parse Error during report generation: {e}")
            return {
                "overall_summary": "Data processed successfully, but AI synthesis encountered a formatting error.",
                "top_performers": "Please review the raw metrics table for highest proxy_score.",
                "underperforming": "Please review the raw metrics table for lowest proxy_score.",
                "content_themes": [{"theme_name": "Unknown", "performance_status": "N/A", "reasoning": "LLM Parsing Failed"}],
                "actionable_recommendations": [{"strategy": "Review raw metrics manually", "rationale": "The LLM output format failed validation."}]
            }