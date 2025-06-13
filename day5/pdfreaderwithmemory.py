import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# === Set Gemini API key directly ===
os.environ["GOOGLE_API_KEY"] = "AIzaSyAxc4Ikam5dHn8VYbktZ3MtS824N0F6Ebk"

# === Streamlit UI Setup ===
st.set_page_config(page_title="PDF Chat with Memory", layout="centered")
st.title("📚 Chat with your PDF (with Memory)")
st.markdown("Upload a PDF, ask questions, and continue the conversation contextually!")

# === PDF Upload ===
pdf_file = st.file_uploader("Upload your PDF file", type=["pdf"])

# === Initialize session state ===
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if pdf_file:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    # Load and split
    with st.spinner("Processing PDF..."):
        loader = PyPDFLoader("temp.pdf")
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(pages)

        # Vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(docs, embeddings)
        retriever = vectorstore.as_retriever()

        # Gemini LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

        # Memory for conversation
        memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )

        # RAG + Memory Chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory
        )

        st.session_state.qa_chain = qa_chain
        st.success("✅ PDF loaded. Ask your questions below!")

# === Ask Questions ===
if st.session_state.qa_chain:
    user_question = st.text_input("Ask a question about the PDF:")

    if user_question:
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.qa_chain.run(user_question)
                st.session_state.chat_history.append(("user", user_question))
                st.session_state.chat_history.append(("bot", response))

                # Display chat history
                for speaker, message in st.session_state.chat_history:
                    if speaker == "user":
                        st.markdown(f"🧑‍💬 **You:** {message}")
                    else:
                        st.markdown(f"🤖 **Gemini:** {message}")
            except Exception as e:
                st.error(f"🚨 Error: {e}")
