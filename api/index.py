import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import platform
import re
from docx import Document
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import time

# --- PAGE CONFIG ---
st.set_page_config(page_title="Resume-Gated Job Intelligence & Multi-Page AI Scraper", page_icon="🎯", layout="wide")

# --- DATABASE SETUP & AUTO-PURGE NOISE ---
def init_db():
    try:
        with sqlite3.connect("jobs_batch.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS batch_jobs_v16 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_url TEXT,
                    job_url TEXT UNIQUE,
                    job_title TEXT,
                    agency TEXT,
                    salary TEXT,
                    location TEXT,
                    category TEXT,
                    description TEXT,
                    min_qualifications TEXT,
                    preferred_qualifications TEXT,
                    preferred_skills TEXT,
                    ats_keywords TEXT,
                    posted_until TEXT,
                    timestamp TEXT
                )
            ''')
            
            # --- PURGE UI NOISE & IRRELEVANT ROLES ---
            cursor.execute("DELETE FROM batch_jobs_v16 WHERE job_title LIKE '%Clear Filters%' OR job_title LIKE '%Caretaker%' OR job_title LIKE '%Matching candidate%' OR job_title LIKE '%No valid title%'")
            cursor.execute("DELETE FROM batch_jobs_v16 WHERE job_title LIKE '%Funding Advisor%' OR agency LIKE '%Flatrock%' OR agency LIKE '%Options Group%' OR agency LIKE '%ELH MGMT%'")
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Database Initialization Error: {str(e)}")
        return False

db_initialized = init_db()

def save_jobs_batch(url, jobs_list):
    try:
        with sqlite3.connect("jobs_batch.db", check_same_thread=False) as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            saved_count = 0
            for job in jobs_list:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO batch_jobs_v16 (
                            search_url, job_url, job_title, agency, salary, location, 
                            category, description, min_qualifications, preferred_qualifications, 
                            preferred_skills, ats_keywords, posted_until, timestamp
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        url, job.get('job_url', 'https://cityjobs.nyc.gov/jobs'),
                        job.get('title', 'N/A'), job.get('agency', 'NYC Agency'), job.get('salary', 'Not Specified'), 
                        job.get('location', 'New York, NY'), job.get('category', 'Finance & Analysis'), 
                        job.get('description', 'N/A'), job.get('min_qualifications', 'N/A'), 
                        job.get('preferred_qualifications', 'N/A'), job.get('preferred_skills', 'N/A'), 
                        job.get('ats_keywords', 'N/A'), job.get('posted_until', 'Open / Unspecified'), timestamp
                    ))
                    if cursor.rowcount > 0:
                        saved_count += 1
                except sqlite3.IntegrityError:
                    pass 
            conn.commit()
            return saved_count
    except Exception as e:
        st.error(f"Database Save Error: {str(e)}")
        return 0

# --- RESUME PARSER & DYNAMIC FILTER ENGINE ---
def parse_uploaded_resume(uploaded_file):
    text = ""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == 'pdf':
            try:
                import pypdf
                reader = pypdf.PdfReader(uploaded_file)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            except ImportError:
                text = "Error: pypdf library is missing."
        elif file_extension in ['docx', 'doc']:
            doc = Document(uploaded_file)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
        else:
            text = uploaded_file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Error reading file: {str(e)}"
    return text.strip()

def extract_resume_competencies(resume_text):
    common_skills = [
        'python', 'sql', 'langgraph', 'llm', 'financial modeling', 'credit underwriting',
        'quantitative', 'risk analysis', 'dcf', 'valuation', 'excel', 'bloomberg', 
        'portfolio management', 'accounting', 'auditing', 'budgeting', 'data analysis',
        'project management', 'compliance', 'strategy', 'research', 'commercial lending',
        'microsoft office', 'enrollment', 'client services'
    ]
    return [skill for skill in common_skills if skill in resume_text.lower()]

def is_job_strictly_relevant(title, card_text):
    title_lower = title.lower()
    text_lower = card_text.lower()
    
    ui_noise = ['clear filters', 'apply', 'view job', 'details', 'save', 'filter by', 'sort by', 'matching candidate', 'no valid title', 'sign in']
    if any(noise in title_lower for noise in ui_noise) or len(title_lower) < 4:
        return False
        
    negative_keywords = [
        'caretaker', 'cook', 'cleaner', 'custodian', 'driver', 'carpenter', 
        'plumber', 'electrician', 'painter', 'mechanic', 'nurse', 'doctor', 
        'security guard', 'porter', 'gardener', 'mason', 'food service', 
        'internship -', 'student intern', 'lifeguard', 'sanitation', 'receptionist',
        'child care', 'childcare', 'daycare', 'teacher assistant', 'early childhood'
    ]
    if any(neg in title_lower or neg in text_lower for neg in negative_keywords):
        return False
        
    positive_anchors = [
        'analyst', 'finance', 'credit', 'lending', 'underwriter', 'risk', 
        'investment', 'banking', 'quantitative', 'software', 'data', 'python', 
        'strategy', 'research', 'accountant', 'auditor', 'budget', 'operations', 
        'administrator', 'planner', 'coordinator', 'project', 'associate', 'officer', 'specialist', 'enrollment'
    ]
    return any(anchor in title_lower or anchor in text_lower for anchor in positive_anchors)

def generate_ats_keywords(title, card_text, resume_competencies):
    title_lower = title.lower()
    text_lower = card_text.lower()
    
    if 'enrollment' in title_lower or 'enrollment' in text_lower:
        found = ['Enrollment Services', 'Client Support', 'Administrative Operations', 'Microsoft Office', 'Communication']
        return ", ".join(found)
        
    found = [comp.title() for comp in resume_competencies if comp in text_lower]
    pool = ['Underwriting', 'Credit Analysis', 'Financial Modeling', 'SQL', 'Python', 'Risk Management', 'Data Analysis', 'Microsoft Office']
    for term in pool:
        if term.lower() in text_lower and term not in found:
            found.append(term)
    return ", ".join(found[:6]) if found else "Finance, Analysis, Compliance"

def extract_posted_until(card_text):
    match = re.search(r'posted\s*until\s*[\r\n\s]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[A-Za-z]+\s+[0-9]{1,2},\s+[0-9]{4})', card_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    fallback_match = re.search(r'(?:closes?|deadline|expires?)\s*[:\-]?\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[A-Za-z]+\s+[0-9]{1,2},\s+[0-9]{4})', card_text, re.IGNORECASE)
    if fallback_match:
        return fallback_match.group(1).strip()
        
    return "Open / Unspecified"

def extract_highlighted_keywords(title, card_text, category_type="min"):
    text_lower = card_text.lower()
    title_lower = title.lower()
    
    min_pool = [
        'baccalaureate degree', 'associate degree', 'high school', 'professional experience', 
        '1 year of full-time experience', '2 years of full-time experience', '3 years of full-time experience', '4 years of full-time experience',
        'finance', 'accounting', 'administrative analysis', 'business administration',
        'quantitative skills', 'qualitative skills', 'meet tight deadlines', 
        'work evenings', 'work weekends', 'interpersonal skills',
        'written and verbal communication', 'creativity', 'organized'
    ]
    
    pref_pool = [
        'financial modeling', 'credit analysis', 'data systems', 'bloomberg terminal',
        'python', 'sql', 'risk analysis', 'valuation', 'portfolio management',
        'budgeting', 'auditing', 'compliance', 'project management', 'research'
    ]
    
    skill_pool = [
        'microsoft office', 'microsoft excel', 'microsoft word', 'data analysis tools', 
        'financial software', 'quantitative reporting', 'advanced excel', 'database management'
    ]
    
    active_pool = min_pool if category_type == "min" else (pref_pool if category_type == "pref" else skill_pool)
    
    matched_highlights = []
    for phrase in active_pool:
        if phrase in text_lower:
            matched_highlights.append(phrase.title())
            
    if category_type == "min":
        if matched_highlights:
            return " | ".join(matched_highlights[:5])
        if 'enrollment' in title_lower:
            return "Baccalaureate Degree | 1-2 Years Administrative Experience | Verbal & Written Communication"
        return "Baccalaureate Degree | Professional Experience | Meet Tight Deadlines | Communication"
        
    elif category_type == "pref":
        if matched_highlights:
            return " | ".join(matched_highlights[:5])
        if 'enrollment' in title_lower:
            return "Client Support Experience | Organization | Interpersonal Skills"
        return "Financial Modeling | Credit Analysis | Quantitative / Qualitative Skills"
        
    else:
        if matched_highlights:
            return " | ".join(matched_highlights[:5])
        return "Microsoft Office | Excel | Data Analysis Tools"

def kill_zombie_drivers():
    try:
        system_name = platform.system()
        if system_name == "Windows":
            os.system('taskkill /f /im chromedriver.exe /t >nul 2>&1')
            os.system('taskkill /f /im chrome.exe /t >nul 2>&1')
        else:
            os.system('pkill -f chromedriver >nul 2>&1')
            os.system('pkill -f chrome >nul 2>&1')
    except Exception:
        pass

def scrape_single_page(url, headless_mode=True):
    kill_zombie_drivers()
    options = Options()
    if headless_mode:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.page_load_strategy = 'eager'
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.get(url)
        WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
        html = driver.page_source
        if not html or len(html.strip()) < 100:
            return None, "Error: Scraped page content was empty."
        return html, None
    except Exception as e:
        return None, f"Scraper Error: {str(e)}"
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
        kill_zombie_drivers()

def build_paged_url(base_url, page_num):
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    query_params['page'] = [str(page_num)]
    new_query = urlencode(query_params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

# --- SIDEBAR UI ---
st.sidebar.title("🎯 Control Panel")
uploaded_resume_file = st.sidebar.file_uploader(
    "Attach your master resume (.pdf or .docx)", 
    type=["pdf", "docx"], 
    key="resume_uploader"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Scraper Settings")
run_headless = st.sidebar.checkbox("Run Headless Browser", value=True, help="Uncheck to watch actions live.")

user_resume_text = ""
resume_validated = False
resume_competencies = []

if uploaded_resume_file is not None:
    with st.spinner("Parsing resume & extracting competencies..."):
        raw_text = parse_uploaded_resume(uploaded_resume_file)
        text_lower = raw_text.lower()
        has_structure = any(kw in text_lower for kw in ['experience', 'education', 'skills', 'work history', 'employment', 'university', 'b.b.a'])
        
        if len(raw_text.strip()) < 50 or not has_structure:
            st.sidebar.error("❌ **Invalid File:** Not recognized as a standard resume.")
        else:
            resume_validated = True
            user_resume_text = raw_text
            resume_competencies = extract_resume_competencies(raw_text)
            st.sidebar.success(f"✅ **Resume Verified!** Found {len(resume_competencies)} core competency tags.")

# --- MAIN APP VIEW ---
st.title("🎯 Multi-Page Job Intelligence & AI Resume Generator")
st.markdown("Scrape multiple job board pages sequentially with full ATS keyword injection into customized resumes.")

if resume_validated:
    with st.expander("🔍 View Extracted Resume Competencies"):
        st.write("**Detected Competencies:**", ", ".join(resume_competencies) if resume_competencies else "General Professional")
    
    search_url = st.text_input("Job Search Results URL", "https://cityjobs.nyc.gov/jobs?options=75%2C3&page=1")
    max_pages = st.slider("Number of Pages to Scrape Sequentially", min_value=1, max_value=10, value=3)
    
    if st.button("Run Multi-Page Precision Scraping", type="primary"):
        total_new_saved = 0
        status_placeholder = st.empty()
        overall_progress = st.progress(0)
        
        for p in range(1, max_pages + 1):
            current_page_url = build_paged_url(search_url, p)
            status_placeholder.info(f"🔄 Processing Page {p} of {max_pages} (Isolated scraping & saving)...")
            
            html_content, error_msg = scrape_single_page(current_page_url, headless_mode=run_headless)
            if error_msg:
                st.warning(f"⚠ Skipping Page {p}: {error_msg}")
                continue
                
            soup = BeautifulSoup(html_content, "html.parser")
            job_links = soup.find_all('a', href=True)
            page_jobs = []
            seen_urls = set()
            
            for link in job_links:
                href = link['href']
                if '/job/' in href or 'jid-' in href or 'details' in href:
                    extracted_job_url = f"https://cityjobs.nyc.gov{href}" if href.startswith("/") else href
                    
                    if extracted_job_url in seen_urls:
                        continue
                    seen_urls.add(extracted_job_url)
                    
                    parent_card = link.find_parent(['div', 'tr', 'article', 'section', 'li'])
                    card_text = parent_card.get_text(separator="\n", strip=True) if parent_card else link.get_text(strip=True)
                    lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                    
                    title = link.get_text(strip=True)
                    if not title or len(title) < 4:
                        title = lines[0] if lines else "NYC Civil Service Role"
                    title_clean = title.split('|')[0].strip()
                    
                    if not is_job_strictly_relevant(title_clean, card_text):
                        continue
                        
                    agency = "NYC Agency"
                    salary = "Not Specified"
                    category = "Finance & Analysis"
                    
                    for line in lines:
                        line_lower = line.lower()
                        if any(term in line_lower for term in ['dept of', 'department', 'office of', 'bureau', 'nyc ', 'board', 'commission', 'police', 'fire', 'transit', 'housing']):
                            if len(line) < 60 and line != title_clean:
                                agency = line
                        if '$' in line or 'annual' in line_lower or 'salary' in line_lower or 'range' in line_lower:
                            if any(char.isdigit() for char in line):
                                salary = line
                        if any(cat in line_lower for cat in ['finance', 'analyst', 'engineering', 'technology', 'admin', 'legal', 'accounting']):
                            category = line
                            
                    if any(blocked in agency.lower() for blocked in ['flatrock', 'options group', 'elh']):
                        continue
                    
                    ats_kw = generate_ats_keywords(title_clean, card_text, resume_competencies)
                    description_text = card_text[:1000].replace('\n', ' ')
                    
                    min_q = extract_highlighted_keywords(title_clean, card_text, "min")
                    pref_q = extract_highlighted_keywords(title_clean, card_text, "pref")
                    pref_s = extract_highlighted_keywords(title_clean, card_text, "skill")
                    posted_until = extract_posted_until(card_text)
                    
                    job_record = {
                        "job_url": extracted_job_url,
                        "title": title_clean[:100],
                        "agency": agency[:80],
                        "salary": salary[:60],
                        "category": category[:50],
                        "description": description_text,
                        "min_qualifications": min_q,
                        "preferred_qualifications": pref_q,
                        "preferred_skills": pref_s,
                        "ats_keywords": ats_kw,
                        "posted_until": posted_until
                    }
                    page_jobs.append(job_record)
            
            if page_jobs:
                saved_count = save_jobs_batch(search_url, page_jobs)
                total_new_saved += saved_count
                st.success(f"✅ Page {p}: Scraped {len(page_jobs)} valid roles | Saved {saved_count} new listings.")
            else:
                st.info(f"ℹ Page {p}: No matching professional roles found.")
            
            overall_progress.progress(p / max_pages)
            time.sleep(0.5)
            
        status_placeholder.success(f"🎉 Multi-page scraping complete! Total new listings saved across all pages: {total_new_saved}")

    # --- RENDER SAVED JOBS & RESUME GENERATOR ---
    st.markdown("---")
    st.subheader("📋 Saved Job Listings & Comprehensive Resume Generator")
    
    try:
        with sqlite3.connect("jobs_batch.db") as conn:
            df_cards = pd.read_sql_query("SELECT * FROM batch_jobs_v16 ORDER BY id DESC", conn)
            
            if df_cards.empty:
                st.info("No records found in database yet. Run the scraper above to populate jobs.")
            else:
                st.write(f"Displaying **{len(df_cards)}** filtered job cards from database:")
                
                for index, row in df_cards.iterrows():
                    with st.container():
                        st.markdown(f"### 💼 [{row['job_title']}]({row['job_url']})")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**🏛️ Agency:** {row['agency']}")
                            st.markdown(f"**💰 Salary:** {row['salary']}")
                        with col2:
                            st.markdown(f"**📂 Category:** {row['category']}")
                            st.markdown(f"**⏳ Posted Until:** {row['posted_until']}")
                        with col3:
                            st.markdown(f"**📅 Scraped On:** {row['timestamp']}")
                            st.markdown(f"**🔗 [Direct Job Link]({row['job_url']})**")
                        
                        st.markdown(f"**🔑 ATS Keywords:** `{row['ats_keywords']}`")
                        st.markdown(f"**📝 Description Summary:** {row['description']}")
                        st.markdown(f"**📌 Minimum Qualifications (Highlighted):** `{row['min_qualifications']}`")
                        st.markdown(f"**⭐ Preferred Qualifications (Highlighted):** `{row['preferred_qualifications']}`")
                        st.markdown(f"**🛠 Preferred Skills (Highlighted):** `{row['preferred_skills']}`")
                        
                        # --- FULLY ATS-INJECTED RESUME GENERATOR EXPANDER ---
                        with st.expander(f"📄 Generate ATS-Optimized Customized Resume for: {row['job_title'][:40]}..."):
                            st.markdown(f"**Target Role:** {row['job_title']} at **{row['agency']}**")
                            
                            if st.button(f"Generate ATS Resume", key=f"btn_resume_{row['id']}"):
                                with st.spinner("Injecting discovered ATS keywords and compiling tailored resume..."):
                                    st.success("✅ ATS-Optimized Resume Generated Successfully!")
                                    
                                    # Render the comprehensive resume injecting the exact row['ats_keywords']
                                    st.markdown(f"""
                                    ---
                                    ### **ADAM LOKHANDWALLA**
                                    New York, NY | adam@email.com | LinkedIn / GitHub
                                    
                                    #### **PROFESSIONAL SUMMARY & TARGET ALIGNMENT**
                                    * **Target Position:** {row['job_title']} at **{row['agency']}**
                                    * **Discovered ATS Keywords Injected:** `{row['ats_keywords']}`
                                    * **Highlighted Minimum Criteria Met:** {row['min_qualifications']}
                                    * **Highlighted Preferred Background:** {row['preferred_qualifications']}
                                    * **Tools & Skills Highlight:** {row['preferred_skills']}
                                    
                                    #### **CORE COMPETENCIES & KEYWORD ALIGNMENT**
                                    `{row['ats_keywords']}` | **Microsoft Office** | **Financial Analysis** | **Quantitative & Qualitative Methods** | **Cross-Functional Communication**
                                    
                                    #### **PROFESSIONAL EXPERIENCE**
                                    **FlatRock Capital** | Commercial Lender / Credit Underwriting Support
                                    * Evaluated corporate financial performance, cash flows, and balance sheet liquidity integrating key competencies (`{row['ats_keywords']}`) to satisfy rigorous underwriting standards for **{row['agency']}**, meeting tight project deadlines.
                                    * Utilized **Bloomberg Terminal**, **Microsoft Office (Excel/Word)**, and advanced quantitative models to perform financial analysis, credit underwriting, and risk assessments.
                                    * Managed multi-asset investment portfolios across public equities, fixed income, and alternative assets, applying `{row['ats_keywords']}` with strong interpersonal and communication skills.
                                    * Prepared comprehensive credit memos, financial spreadsheets, and variance analyses supporting senior management decisions.
                                    
                                    **Options Group** | Financial Research & Market Analyst Intern
                                    * Conducted rigorous market research and data analysis utilizing Microsoft tools and proprietary databases aligned with `{row['ats_keywords']}` to support executive recruitment and benchmarking.
                                    * Built structured operational reports, meeting strict turnaround deadlines and preferred technical criteria.
                                    * Collaborated with senior analysts to streamline data extraction workflows and compile industry trend briefs.
                                    
                                    **ELH Management** | Financial Analyst
                                    * Assisted with corporate budget tracking, variance analysis, and operational financial reporting using Microsoft Excel.
                                    * Reconciled financial ledgers and prepared detailed cash flow forecasts to optimize organizational efficiency and compliance.
                                    
                                    #### **TECHNICAL PROJECTS & AUTOMATION**
                                    **Agentic AI Securities Research Platform** *(Python, LangGraph, Cursor AI)*
                                    * Developed multi-agent LLM workflows to automate securities research, financial data extraction, and quantitative analysis.
                                    * Designed SQL-backed data pipelines to streamline reporting, reduce manual data entry, and accelerate decision-making workflows.
                                    * Integrated modern software engineering practices to bridge financial data systems with automated agentic intelligence.
                                    
                                    #### **EDUCATION & CERTIFICATIONS**
                                    **Brooklyn College – Koppelman School of Business** | Brooklyn, NY
                                    * **Degree:** Bachelor of Science / B.B.A. in Business Administration (Finance Concentration)
                                    * **Academic Focus:** Corporate Finance, Quantitative Analysis, Financial Modeling, and Auditing.
                                    * **Additional Training:** freeCodeCamp coursework in programming, data structures, and algorithmic design patterns.
                                    ---
                                    """)
                        st.markdown("---")
    except Exception as e:
        st.error(f"Error loading job cards: {str(e)}")
else:
    st.warning("⚠️ Please upload your master resume in the sidebar to begin.")
