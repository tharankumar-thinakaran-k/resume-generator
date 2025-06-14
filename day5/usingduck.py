import os
import streamlit as st
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchRun

# === HARDCODED GEMINI API KEY ===
os.environ["GOOGLE_API_KEY"] = "apikey"

# === SETUP GEMINI MODEL ===
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3
)

# === SETUP SEARCH TOOL ===
search_tool = DuckDuckGoSearchRun()
tools = [
    Tool(
        name="DuckDuckGo Search",
        func=search_tool.run,
        description="Use this tool to search the internet for current events or real-time information"
    )
]

# === SETUP AGENT ===
agent_executor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True
)

# === STREAMLIT UI ===
st.set_page_config(page_title="🌐 Ask Real-Time Questions", layout="centered")
st.title("🌐 Real-Time Q&A with Gemini + DuckDuckGo")
st.markdown("Ask about **current events**, **news**, or **facts**. This assistant uses Gemini + live search 🧠🔎")

# Input field and button
question = st.text_input("📤 Enter your question:", key="input")
submit = st.button("🔍 Ask Gemini")

if submit and question:
    with st.spinner("🤖 Gemini is searching and thinking..."):
        try:
            response = agent_executor.run(question)
            st.success("✅ Here's the answer:")
            st.write(response)
        except Exception as e:
            st.error(f"❌ Error: {e}")
