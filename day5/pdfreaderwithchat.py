import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import Runnable
from langchain.schema.output_parser import StrOutputParser

# === SET GEMINI API KEY HERE ===
os.environ["GOOGLE_API_KEY"] = "api key"

# === Streamlit UI Setup ===
st.set_page_config(page_title="📘 Chat with PDF", layout="centered")
st.title("📘 Chat with your PDF using Gemini + LangChain")
st.markdown("Upload a PDF and ask questions. It will remember your conversation.")

# === Session State Initialization ===
if "chat_chain" not in st.session_state:
    st.session_state.chat_chain = None
if "memory" not in st.session_state:
    st.session_state.memory = None

# === Upload and Process PDF ===
pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])

if pdf_file:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    with st.spinner("🔍 Processing PDF..."):
        loader = PyPDFLoader("temp.pdf")
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(pages)

        # Embedding + Vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(docs, embeddings)
        retriever = vectorstore.as_retriever()

        # Memory
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Gemini LLM setup
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

        # Prompt Template (manual history handling)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an intelligent assistant for answering questions from PDF content."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])

        # Create the full chain
        chain = (
            {"question": lambda x: x["question"],
             "chat_history": lambda x: memory.chat_memory.messages,
             "context": lambda x: retriever.get_relevant_documents(x["question"])}
            | prompt
            | llm
            | StrOutputParser()
        )

        # Save in session
        st.session_state.chat_chain = chain
        st.session_state.memory = memory

        st.success("✅ PDF processed. You can now chat with it!")

# === Chat UI ===
if st.session_state.chat_chain:
    user_input = st.text_input("Ask a question about the PDF:", key="input")

    if user_input:
        with st.spinner("🤖 Thinking..."):
            try:
                # Generate response and update memory manually
                response = st.session_state.chat_chain.invoke({"question": user_input})
                st.session_state.memory.chat_memory.add_user_message(user_input)
                st.session_state.memory.chat_memory.add_ai_message(response)

                st.markdown("### 🤖 Gemini's Answer")
                st.write(response)

            except Exception as e:
                st.error(f"❌ Error: {e}")

    # === Display past chat history ===
    st.markdown("### 💬 Chat History")
    if st.session_state.memory:
        history = st.session_state.memory.chat_memory.messages
        for msg in history:
            role = "🧑 You" if msg.type == "human" else "🤖 Gemini"
            st.markdown(f"**{role}:** {msg.content}")
