import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable
import os

# === Set your Gemini API key directly (Avoid .env for now) ===
os.environ["GOOGLE_API_KEY"] = "AIzaSyAxc4Ikam5dHn8VYbktZ3MtS824N0F6Ebk"

# === Set up the Gemini LLM via LangChain ===
try:
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)
except Exception as e:
    st.error("Error initializing Gemini LLM. Check API key and network.")
    st.stop()

# === Build the prompt template for translation ===
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful translator that translates English to French."),
    ("user", "Translate the following sentence to French:\n\n{sentence}")
])

# === Create the chain using LangChain's piping method ===
chain: Runnable = prompt | llm

# === Streamlit UI ===
st.set_page_config(page_title="English to French Translator", layout="centered")
st.title("🌍 English to French Translator")
st.markdown("Enter an English sentence, and get the French translation using Google Gemini.")

# User input
sentence = st.text_input("Enter English sentence:")
translate_btn = st.button("Translate")

# On click
if translate_btn:
    if not sentence.strip():
        st.warning("Please enter a valid English sentence.")
    else:
        try:
            response = chain.invoke({"sentence": sentence})
            translated = response.content if hasattr(response, "content") else str(response)
            st.success("✅ Translation successful!")
            st.markdown("**French Translation:**")
            st.code(translated, language="markdown")
        except Exception as e:
            st.error(f"🚨 Translation failed: {str(e)}")
