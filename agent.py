import os
import json
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from src.youtube import YouTubeExtractor
from src.analytics import AnalyticsEngine
from src.report_engine import ReportEngine
from src.cache import CacheLayer
from src.prompts import AGENT_ROUTER_PROMPT
from src.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

# Load config for strict tool validation
with open("config/channels.json", "r") as f:
    config = json.load(f)
VALID_HANDLES = config.get("moveup", []) + config.get("competitors", [])

MAX_TOOL_CALLS = 10 

class ContentOpsAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY. Add it to your .env file.")
        
        self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        self.youtube = YouTubeExtractor()
        self.analytics = AnalyticsEngine()
        self.reporting = ReportEngine()
        self.cache = CacheLayer()

    def _get_channel_data(self, handle: str):
        """Helper method to fetch channel data with cache support."""
        cached_data = self.cache.load_channel_cache(handle)
        if cached_data:
            logger.info(f"Agent using cached data for {handle}")
            return cached_data
            
        logger.info(f"Agent fetching live API data for {handle}")
        raw_data = self.youtube.fetch_last_10_videos(handle)
        scored_data = self.analytics.calculate_scores(raw_data)
        self.cache.save_channel_cache(handle, scored_data)
        return scored_data

    def fetch_and_analyze(self, handle: str) -> str:
        data = self._get_channel_data(handle)
        # Using model_dump(mode="json") to safely serialize datetime objects
        summary = {
            "channel_handle": data.channel_handle,
            "average_engagement_rate": data.average_engagement_rate,
            "trend": data.trend.model_dump(mode="json") if data.trend else None,
            "top_videos": [v.model_dump(mode="json") for v in data.top_videos],
            "bottom_videos": [v.model_dump(mode="json") for v in data.bottom_videos]
        }
        # default=str is the safety net for JSON serialization
        return json.dumps(summary, indent=2, default=str)

    def generate_full_report(self, handle: str) -> str:
        data = self._get_channel_data(handle)
        report_data = self.reporting.generate_report(data)
        return json.dumps(report_data, indent=2, default=str)

    def compare_channels(self, handle_1: str, handle_2: str) -> str:
        d1 = self._get_channel_data(handle_1)
        d2 = self._get_channel_data(handle_2)
        
        e1, e2 = d1.average_engagement_rate, d2.average_engagement_rate
        winner = handle_1 if e1 > e2 else handle_2
        
        trend_adv = f"{handle_1} has better momentum." if (d1.trend and d2.trend and d1.trend.engagement_change_pct > d2.trend.engagement_change_pct) else f"{handle_2} has better momentum."
        eng_adv = f"{winner} maintains a higher average viewer engagement."

        comparison = {
            "channel_1_summary": {"handle": d1.channel_handle, "avg_engagement": e1, "trend": d1.trend.direction if d1.trend else "N/A"},
            "channel_2_summary": {"handle": d2.channel_handle, "avg_engagement": e2, "trend": d2.trend.direction if d2.trend else "N/A"},
            "winner": winner,
            "winner_reason": "Higher average engagement and stronger top-performing content.",
            "engagement_advantage": eng_adv,
            "trend_advantage": trend_adv,
            "engagement_gap": round(abs(e1 - e2), 2)
        }
        return json.dumps(comparison, indent=2, default=str)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def _execute_llm_call(self, messages, tools=None):
        kwargs = {"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.3}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return self.client.chat.completions.create(**kwargs)

    def chat(self, user_input: str) -> str:
        tools = [
            {"type": "function", "function": {"name": "fetch_and_analyze", "description": "Get metrics for ONE channel.", "parameters": {"type": "object", "properties": {"handle": {"type": "string", "enum": VALID_HANDLES}}, "required": ["handle"]}}},
            {"type": "function", "function": {"name": "generate_full_report", "description": "Generate a weekly report for ONE channel.", "parameters": {"type": "object", "properties": {"handle": {"type": "string", "enum": VALID_HANDLES}}, "required": ["handle"]}}},
            {"type": "function", "function": {"name": "compare_channels", "description": "Compare performance gaps between TWO channels.", "parameters": {"type": "object", "properties": {"handle_1": {"type": "string", "enum": VALID_HANDLES}, "handle_2": {"type": "string", "enum": VALID_HANDLES}}, "required": ["handle_1", "handle_2"]}}}
        ]

        messages = [{"role": "system", "content": AGENT_ROUTER_PROMPT}, {"role": "user", "content": user_input}]

        try:
            response = self._execute_llm_call(messages, tools)
            response_message = response.choices[0].message

            if response_message.tool_calls:
                if len(response_message.tool_calls) > MAX_TOOL_CALLS:
                    logger.warning(f"Agent requested {len(response_message.tool_calls)} tools. Restricting to safe execution window.")
                    safe_tool_calls = response_message.tool_calls[:MAX_TOOL_CALLS]
                else:
                    safe_tool_calls = response_message.tool_calls
                
                messages.append(response_message) 
                
                for tool_call in safe_tool_calls:
                    f_name = tool_call.function.name
                    f_args = json.loads(tool_call.function.arguments)

                    if f_name == "fetch_and_analyze": res = self.fetch_and_analyze(f_args.get("handle"))
                    elif f_name == "generate_full_report": res = self.generate_full_report(f_args.get("handle"))
                    elif f_name == "compare_channels": res = self.compare_channels(f_args.get("handle_1"), f_args.get("handle_2"))
                    else: res = "Error: Unknown function."

                    messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": f_name, "content": res})

                messages.append({"role": "system", "content": "CRITICAL: Synthesize the tool results into a natural language response. Explain the data cleanly. DO NOT output raw <function> tags, XML, or raw JSON arrays."})
                final_response = self._execute_llm_call(messages)
                return final_response.choices[0].message.content
            return response_message.content
            
        except Exception:
            logger.error(f"Agent chat exception:\n{traceback.format_exc()}")
            return "⚠️ I encountered an error. Please check the logs."