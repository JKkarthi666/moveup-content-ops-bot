import os
import shutil
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
def validate_env():
    if not os.getenv("YOUTUBE_API_KEY"):
        st.error("🚨 Missing YouTube API Key!")
        st.stop()
    if not os.getenv("GROQ_API_KEY"):
        st.error("🚨 Missing Groq API Key!")
        st.stop()

st.set_page_config(page_title="MoveUp ContentOps AI", page_icon="⚡", layout="wide")
validate_env()

from src.agent import ContentOpsAgent
from src.youtube import YouTubeExtractor
from src.analytics import AnalyticsEngine
from src.cache import CacheLayer

# Load SaaS Configuration
with open("config/channels.json", "r") as f:
    config_data = json.load(f)
MOVEUP_CHANNELS = config_data.get("moveup", [])
COMPETITORS = config_data.get("competitors", [])
ALL_CHANNELS = MOVEUP_CHANNELS + COMPETITORS

@st.cache_resource
def get_systems():
    return {"agent": ContentOpsAgent(), "youtube": YouTubeExtractor(), "analytics": AnalyticsEngine(), "cache": CacheLayer()}

systems = get_systems()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome to the MoveUp Intelligence Hub. How can I help you analyze our channels today?"}]

def fetch_channel_overview(handle):
    cached_data = systems["cache"].load_channel_cache(handle)
    if cached_data: return cached_data
    raw_data = systems["youtube"].fetch_last_10_videos(handle)
    scored_data = systems["analytics"].calculate_scores(raw_data)
    systems["cache"].save_channel_cache(handle, scored_data)
    return scored_data

@st.cache_data(ttl=3600)
def get_llm_report(handle): return systems["agent"].generate_full_report(handle)

with st.sidebar:
    st.title("⚡ MoveUp ContentOps")
    st.divider()
    st.markdown("**🛡️ MoveUp Properties:**")
    for ch in MOVEUP_CHANNELS: st.code(ch)
    st.markdown("**⚔️ Tracked Competitors:**")
    for ch in COMPETITORS: st.code(ch)
    
    # ELITE FIX: Cleared the deprecation warning
    if st.button("🔄 Force API Sync", width="stretch"):
        if os.path.isdir("data/cache"): shutil.rmtree("data/cache")
        os.makedirs("data/cache", exist_ok=True)
        st.cache_data.clear()
        st.success("Persistent cache wiped. Pulling live data.")

st.markdown("### 📊 Executive Overview")
total_videos = 0
for ch in ALL_CHANNELS:
    try:
        data = fetch_channel_overview(ch)
        if data and data.videos: total_videos += len(data.videos)
    except Exception:
        pass

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(label="Total Videos Analyzed", value=str(total_videos), delta="Live API Data")
kpi2.metric(label="Active Properties", value=f"{len(MOVEUP_CHANNELS)} MoveUp", delta=f"{len(COMPETITORS)} Competitors", delta_color="off")
kpi3.metric(label="System Status", value="Autonomous", delta="Groq API", delta_color="normal")
kpi4.metric(label="Last Sync", value=datetime.now().strftime("%H:%M UTC"), delta="Persistent Cache")

st.divider()
tab_dashboard, tab_reports, tab_benchmark, tab_agent = st.tabs(["📊 Channel Metrics", "📑 AI Reports", "⚔️ Benchmark", "🤖 Agent"])

with tab_dashboard:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📺 {MOVEUP_CHANNELS[0]}")
        try:
            netflu_data = fetch_channel_overview(MOVEUP_CHANNELS[0])
            t_col1, t_col2 = st.columns(2)
            t_col1.metric("Avg Engagement Rate", f"{netflu_data.average_engagement_rate}%")
            if netflu_data.trend: t_col2.metric("Trend", netflu_data.trend.direction.title(), f"{netflu_data.trend.engagement_change_pct}%")
            
            for video in netflu_data.videos:
                tier, score = video.metrics.performance_tier, video.metrics.proxy_score
                color = "🟢" if tier == "Strong" else "🟡" if tier == "Average" else "🔴"
                st.markdown(f"{color} **[{score}/100]** | [{video.title[:45]}...]({video.url})")
        except: st.error("Error loading data.")

    with col2:
        st.subheader(f"📺 {MOVEUP_CHANNELS[1]}")
        try:
            playoffs_data = fetch_channel_overview(MOVEUP_CHANNELS[1])
            t_col1, t_col2 = st.columns(2)
            t_col1.metric("Avg Engagement Rate", f"{playoffs_data.average_engagement_rate}%")
            if playoffs_data.trend: t_col2.metric("Trend", playoffs_data.trend.direction.title(), f"{playoffs_data.trend.engagement_change_pct}%")
            
            for video in playoffs_data.videos:
                tier, score = video.metrics.performance_tier, video.metrics.proxy_score
                color = "🟢" if tier == "Strong" else "🟡" if tier == "Average" else "🔴"
                st.markdown(f"{color} **[{score}/100]** | [{video.title[:45]}...]({video.url})")
        except: st.error("Error loading data.")

with tab_reports:
    report_target = st.selectbox("Select Channel to Generate Report:", MOVEUP_CHANNELS)
    if st.button(f"Generate Report for {report_target}", type="primary"):
        with st.spinner("🧠 AI is analyzing the data..."):
            try:
                report_dict = json.loads(get_llm_report(report_target))
                st.info(report_dict.get("overall_summary", ""))
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    st.subheader("🏆 Top Performers")
                    st.success(report_dict.get("top_performers", ""))
                with r_col2:
                    st.subheader("📉 Underperforming")
                    st.error(report_dict.get("underperforming", ""))

                st.subheader("🧠 Content Pattern Analyzer")
                themes = report_dict.get("content_themes", [])
                if themes:
                    th_cols = st.columns(len(themes))
                    for i, theme in enumerate(themes):
                        with th_cols[i % len(th_cols)]:
                            icon = "🔥" if theme.get("performance_status", "").lower() == "winning" else "⚠️"
                            st.markdown(f"**{icon} {theme.get('theme_name', 'Theme')}**\n\n<small>{theme.get('reasoning', '')}</small>", unsafe_allow_html=True)

                st.subheader("🎯 Recommendations")
                for i, rec in enumerate(report_dict.get("actionable_recommendations", [])):
                    st.warning(f"**{i+1}. {rec.get('strategy', 'Strategy')}**\n\n*Rationale:* {rec.get('rationale', '')}")
            except Exception as e:
                st.error(f"Failed to parse report: {e}")

with tab_benchmark:
    try:
        benchmark_data = []
        best_eng, best_trend, content_leader, trend_leader = 0, 0, "", ""
        
        for handle in ALL_CHANNELS:
            data = fetch_channel_overview(handle)
            if not data or not data.videos: continue
            
            eng, trend_val = data.average_engagement_rate, data.trend.engagement_change_pct if data.trend else 0
            if eng > best_eng: best_eng, content_leader = eng, handle
            if trend_val > best_trend: best_trend, trend_leader = trend_val, handle
            
            avg_proxy = round(sum(v.metrics.proxy_score for v in data.videos) / len(data.videos), 2)
            top_score = data.top_videos[0].metrics.proxy_score if (data.top_videos and len(data.top_videos) > 0) else 0
            worst_score = data.bottom_videos[0].metrics.proxy_score if (data.bottom_videos and len(data.bottom_videos) > 0) else 0

            benchmark_data.append({"Channel": handle, "Type": "MoveUp" if handle in MOVEUP_CHANNELS else "Competitor", "Avg Engagement (%)": eng, "Avg Proxy Score": avg_proxy, "Top Video Score": top_score, "Worst Video Score": worst_score, "Trend": data.trend.direction.title() if data.trend else "N/A"})
        
        if MOVEUP_CHANNELS:
            moveup_eng = sum(item["Avg Engagement (%)"] for item in benchmark_data if item["Type"] == "MoveUp") / len(MOVEUP_CHANNELS)
            gap = round(best_eng - moveup_eng, 2)
            st.success(f"🏆 **Content Leader:** {content_leader} ({best_eng}% Eng) | 🚀 **Momentum Leader:** {trend_leader} (+{best_trend}%) | 📉 **MoveUp Engagement Gap:** {gap}%")
        
        # ELITE FIX: Cleared the deprecation warning
        st.dataframe(pd.DataFrame(benchmark_data), width="stretch")
    except Exception as e:
        import traceback
        st.error(f"Error loading benchmark: {str(e)}")

with tab_agent:
    st.markdown("**Suggested Prompts:**")
    p1, p2, p3, p4 = st.columns(4)
    if p1.button("Compare channels"): st.session_state.agent_input = f"Compare engagement gaps of {MOVEUP_CHANNELS[0]} and {MOVEUP_CHANNELS[1]}."
    if p2.button("Best video"): st.session_state.agent_input = "What was the single best performing video across our channels?"
    if p3.button("Worst video"): st.session_state.agent_input = f"Identify the worst performing video for {MOVEUP_CHANNELS[0]}. Why did it drop?"
    if p4.button("Weekly recommendations"): st.session_state.agent_input = f"Give me actionable recommendations for {MOVEUP_CHANNELS[1]} based on this week's data."
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    prompt = st.chat_input("Ask the agent anything...")
    if "agent_input" in st.session_state:
        prompt = st.session_state.agent_input
        del st.session_state.agent_input 

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = systems["agent"].chat(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})