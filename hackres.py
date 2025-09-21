import streamlit as st
import re
import PyPDF2
from typing import Dict, List, Tuple

def standardize_text(text: str) -> str:
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return text.lower() if isinstance(text, str) else ''

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + '\n'
    return text

def parse_job_description(text: str) -> Dict:
    return {
        'role_title': "data scientist",
        'must_have_skills': ['python', 'machine learning', 'statistics'],
        'good_to_have_skills': ['deep learning', 'nlp'],
        'certifications': ['aws certified', 'google cloud certification'],
        'projects': ['fraud detection', 'chatbot'],
        'qualifications': ['bachelor', 'master']
    }

def find_matches(items: List[str], text: str) -> Tuple[List[str], List[str]]:
    found = [x for x in items if x in text]
    missing = [x for x in items if x not in text]
    return found, missing

def evaluate_resume(resume_text, jd_data, strictness='standard'):
    if strictness == 'lenient':
        w_must, w_good = 0.5, 0.5
        t_high, t_med = 65, 40
    elif strictness == 'strict':
        w_must, w_good = 0.9, 0.1
        t_high, t_med = 85, 70
    else:
        w_must, w_good = 0.7, 0.3
        t_high, t_med = 75, 50

    must_found, must_missing = find_matches(jd_data['must_have_skills'], resume_text)
    good_found, good_missing = find_matches(jd_data['good_to_have_skills'], resume_text)
    cert_found, cert_missing = find_matches(jd_data['certifications'], resume_text)
    proj_found, proj_missing = find_matches(jd_data['projects'], resume_text)
    qual_found, qual_missing = find_matches(jd_data['qualifications'], resume_text)

    must_total = len(jd_data['must_have_skills'])
    good_total = len(jd_data['good_to_have_skills'])

    must_score = len(must_found) / must_total if must_total else 0
    good_score = len(good_found) / good_total if good_total else 0

    score = (must_score * w_must + good_score * w_good) * 100

    if score >= t_high:
        verdict = 'High'
    elif score >= t_med:
        verdict = 'Medium'
    else:
        verdict = 'Low'

    feedback = []
    if must_missing:
        feedback.append(f"Missing must-have skills: {', '.join(must_missing)}.")
    if good_missing:
        feedback.append(f"Missing good-to-have skills: {', '.join(good_missing)}.")
    if cert_missing:
        feedback.append(f"Missing certifications: {', '.join(cert_missing)}.")
    if proj_missing:
        feedback.append(f"Missing projects: {', '.join(proj_missing)}.")
    if qual_missing:
        feedback.append(f"Missing qualifications: {', '.join(qual_missing)}.")
    if not feedback:
        feedback.append("All criteria met. Great job!")

    return {
        'score': score,
        'verdict': verdict,
        'missing_skills': must_missing + good_missing,
        'missing_certifications': cert_missing,
        'missing_projects': proj_missing,
        'missing_qualifications': qual_missing,
        'feedback': feedback,
        'strictness': strictness.capitalize()
    }

# Initialize session state for evaluations
if 'evaluations' not in st.session_state:
    st.session_state['evaluations'] = []

st.title('Resume Matcher')

st.header('Upload or Paste Job Description')
uploaded_jd = st.file_uploader('Upload Job Description (PDF)', type=['pdf'])
jd_text_input = st.text_area('Or paste the job description text here')

st.header('Paste Resume Text')
resume_text = st.text_area('Paste resume text here', height=200)

strictness = st.selectbox('Strictness', options=['standard', 'lenient', 'strict'], index=0)

if st.button('Evaluate'):
    jd_text = ''
    if uploaded_jd is not None:
        try:
            jd_text = extract_text_from_pdf(uploaded_jd)
        except Exception:
            st.error('Failed to extract text from PDF. Please try pasting the text instead.')
            jd_text = ''
    else:
        jd_text = jd_text_input

    if not jd_text.strip() or not resume_text.strip():
        st.error('Both job description and resume text are required!')
    else:
        resume_std = standardize_text(resume_text)
        jd_std = standardize_text(jd_text)
        jd_data = parse_job_description(jd_std)
        res = evaluate_resume(resume_std, jd_data, strictness)
        st.success(f"Match Score: {res['score']:.2f}% - Verdict: {res['verdict']} (Strictness: {res['strictness']})")
        for msg in res['feedback']:
            st.info(msg)

        # Save evaluation for dashboard
        st.session_state.evaluations.append({
            'role_title': jd_data['role_title'],
            'score': res['score'],
            'verdict': res['verdict'],
            'missing_skills': res['missing_skills'],
            'missing_certifications': res['missing_certifications'],
            'missing_projects': res['missing_projects']
        })

st.header('Evaluation Dashboard')
if st.session_state.evaluations:
    import pandas as pd
    df = pd.DataFrame(st.session_state.evaluations)
    df['missing_skills'] = df['missing_skills'].apply(lambda x: ', '.join(x) if x else 'None')
    df['missing_certifications'] = df['missing_certifications'].apply(lambda x: ', '.join(x) if x else 'None')
    df['missing_projects'] = df['missing_projects'].apply(lambda x: ', '.join(x) if x else 'None')
    st.dataframe(df.style.set_properties(**{'text-align': 'left'}))
else:
    st.info('No evaluations found')

