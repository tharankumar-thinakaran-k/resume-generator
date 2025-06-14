import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA



# === API key for Gemini (set inline, not in .env) ===
os.environ["GOOGLE_API_KEY"] = "apikey"

# === Page settings ===
st.set_page_config(page_title="📄 PDF Q&A with RAG", layout="centered")
st.title("📄 Ask Your PDF using RAG + Gemini")
st.markdown("Upload a PDF, then ask questions based on its content!")

# === Upload PDF ===
pdf_file = st.file_uploader("Upload your PDF file", type=["pdf"])

# === Session state to hold retriever/QA chain ===
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None

if pdf_file:
    # Save PDF to temp
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())

    # Load and split PDF
    with st.spinner("Processing PDF..."):
        loader = PyPDFLoader("temp.pdf")
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(pages)

        # Create vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_documents(docs, embeddings)
        retriever = vectorstore.as_retriever()

        # Gemini LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

        # RAG QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

        st.session_state.qa_chain = qa_chain
        st.success("✅ PDF processed successfully! You can now ask questions.")

# === Ask questions after upload ===
if st.session_state.qa_chain:
    query = st.text_input("Ask a question about the PDF:")

    if query:
        with st.spinner("Thinking..."):
            try:
                result = st.session_state.qa_chain.invoke({"query": query})
                st.markdown("### ✅ Answer:")
                st.write(result["result"])
            except Exception as e:
                st.error(f"Error while generating response: {e}")
