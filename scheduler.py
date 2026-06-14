import os
import json
import time
import schedule
import traceback
from datetime import datetime
from src.agent import ContentOpsAgent
from src.logger import get_logger

logger = get_logger(__name__)

with open("config/channels.json", "r") as f:
    config_data = json.load(f)
CHANNELS = config_data.get("moveup", []) + config_data.get("competitors", [])

def run_weekly_pipeline():
    logger.info("⚡ Initiating weekly ContentOps pipeline...")
    agent = ContentOpsAgent()
    
    for handle in CHANNELS:
        try:
            logger.info(f"▶ Generating analytical report for {handle}...")
            report_json = agent.generate_full_report(handle)
            clean_handle = handle.replace('@', '')
            timestamp = datetime.now().strftime('%Y%m%d')
            
            os.makedirs("data/reports", exist_ok=True)
            filename = f"data/reports/{clean_handle}_weekly_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_json)
            logger.info(f"✅ Successfully saved report to {filename}")
        except Exception as e:
            logger.error(f"❌ Pipeline failed for {handle}.\n{traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("🤖 Starting MoveUp ContentOps Scheduler...")
    logger.info("⏳ Pipeline configured to run every Monday at 06:00 UTC.")
    schedule.every().monday.at("06:00").do(run_weekly_pipeline)
    
    while True:
        schedule.run_pending()
        time.sleep(60)