import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import io
import base64

# Configure Gemini API
genai.configure(api_key="AIzaSyA6xMnaLxir94mpBa9mVjAfdU0X579Uths")  # Replace with actual API key in quotes

def generate_resume(text, format_style, tone):
    prompt = f"Generate a professional resume in {format_style} format with a {tone} tone. Input: {text}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def convert_to_pdf(resume_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in resume_text.split('\n'):
        pdf.multi_cell(0, 10, line)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_bytes)

# Streamlit App UI
st.title("📄 AI Resume Generator with Gemini")

user_text = st.text_area("✍️ Enter your profile, experience, and skills:")

format_style = st.selectbox("📑 Choose Resume Format", ["Modern", "Traditional", "Creative"])
tone = st.radio("🎯 Select Tone", ["Formal", "Friendly", "Confident"])

if 'resume_text' not in st.session_state:
    st.session_state.resume_text = ''

if st.button("🚀 Generate Resume"):
    if user_text.strip() == "":
        st.warning("Please enter some text.")
    else:
        with st.spinner("Generating your resume..."):
            resume = generate_resume(user_text, format_style, tone)
            st.session_state.resume_text = resume
            st.success("Resume generated!")

if st.session_state.resume_text:
    st.subheader("📋 Generated Resume")
    st.text(st.session_state.resume_text)

    if st.button("🔁 Regenerate with New Format/Tone"):
        resume = generate_resume(user_text, format_style, tone)
        st.session_state.resume_text = resume
        st.experimental_rerun()

    # Convert and allow download
    pdf_buffer = convert_to_pdf(st.session_state.resume_text)
    b64_pdf = base64.b64encode(pdf_buffer.read()).decode('utf-8')
    href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="generated_resume.pdf">📥 Download Resume as PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
