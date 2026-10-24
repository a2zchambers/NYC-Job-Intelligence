# NYC Job Intelligence

A Python and Streamlit-based job search tool that helps users find and organize relevant NYC job postings based on their own resume.

The project started as a simple NYC Jobs scraper and has evolved into a more personalized job intelligence system. Users can upload a master resume, extract relevant competencies, scrape multiple pages of NYC job listings, filter out unrelated positions, identify important qualifications and ATS keywords, and generate customized resume content for individual jobs.

> **Status:** Work in progress
> **Current focus:** NYC Jobs / City of New York job postings

---

## What It Does

The application is designed to take some of the repetitive work out of searching through job postings.

### Current workflow

```text
User Resume
     ↓
Resume Parsing
     ↓
Competency Extraction
     ↓
NYC Jobs Search URL
     ↓
Multi-Page Selenium Scraping
     ↓
Job Relevance Filtering
     ↓
Qualification & Keyword Extraction
     ↓
SQLite Database
     ↓
Job Cards
     ↓
Customized Resume Content
```

The application currently supports:

* Uploading a master resume in PDF or DOCX format
* Basic resume validation
* Extracting competencies from the uploaded resume
* Scraping multiple NYC Jobs pages sequentially
* Running Selenium in headless or visible-browser mode
* Filtering out irrelevant roles and website UI noise
* Identifying relevant professional positions
* Extracting job titles, agencies, salary information, categories, and descriptions
* Identifying minimum qualifications
* Identifying preferred qualifications
* Identifying preferred skills
* Extracting ATS-related keywords
* Extracting job closing/posting dates
* Saving job listings to SQLite
* Preventing duplicate job URLs from being saved
* Displaying saved jobs through a Streamlit interface
* Generating customized resume content based on the selected job

---

## Why I Built It

I originally built this project to experiment with using Python, web scraping, databases, and AI/LLM tools to improve the job-search process.

The first version focused primarily on scraping and organizing NYC job postings.

As I worked with it, I realized that simply collecting jobs was not enough. The more useful problem was figuring out:

1. Which jobs are actually relevant to a candidate?
2. What qualifications does each job emphasize?
3. Which skills and keywords overlap with the candidate's background?
4. How can that information be used to customize an application?

That led to the current resume-gated version.

Instead of treating every job seeker the same way, the application starts with the user's own resume and uses that information when analyzing the available jobs.

---

## Project Architecture

```text
nyc-job-intelligence/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── app.py
│
├── scraper/
│   ├── __init__.py
│   └── job_scraper.py
│
├── analysis/
│   ├── __init__.py
│   ├── job_filter.py
│   └── job_analysis.py
│
├── resume/
│   ├── __init__.py
│   ├── resume_parser.py
│   └── resume_generator.py
│
├── database/
│   ├── __init__.py
│   └── database.py
│
├── ui/
│   ├── __init__.py
│   └── job_cards.py
│
└── data/
    ├── __init__.py
    └── keyword_lists.py
```

### `app.py`

The main Streamlit application.

Responsible for:

* User interface
* Resume upload
* Scraper settings
* Search URL
* Number of pages
* Application workflow
* Progress indicators
* Connecting the different components

The goal is for `app.py` to coordinate the application rather than contain all of the underlying logic.

### `scraper/`

Handles website scraping and browser automation.

Current responsibilities include:

* Selenium WebDriver setup
* Chrome configuration
* Headless browser support
* Page loading
* Multi-page URL generation
* HTML retrieval
* Job-link extraction

### `analysis/`

Handles job filtering and analysis.

This includes:

* Removing irrelevant roles
* Identifying relevant professional positions
* Extracting ATS keywords
* Identifying minimum qualifications
* Identifying preferred qualifications
* Identifying preferred skills
* Extracting job posting deadlines

### `resume/`

Handles the user's uploaded resume.

This includes:

* PDF parsing
* DOCX parsing
* Resume validation
* Competency extraction
* Customized resume generation

### `database/`

Handles persistent job storage using SQLite.

The database stores information such as:

* Job URL
* Job title
* Agency
* Salary
* Location
* Category
* Description
* Minimum qualifications
* Preferred qualifications
* Preferred skills
* ATS keywords
* Posting deadline
* Timestamp

### `ui/`

Contains reusable Streamlit components for displaying job information.

This keeps the main application file from becoming too large as the interface grows.

### `data/`

Contains reusable keyword lists and other static data used by the analysis system.

---

## Technologies Used

### Python

The main programming language used to build the application.

### Streamlit

Used to create the interactive web application and user interface.

### Selenium

Used for browser automation and retrieving dynamically loaded job-board pages.

### BeautifulSoup

Used to parse the HTML returned by Selenium.

### SQLite

Used for local storage of scraped job listings.

### Pandas

Used to load and display stored job data.

### pypdf

Used to extract text from uploaded PDF resumes.

### python-docx

Used to extract text from uploaded DOCX resumes.

### Ollama

Earlier versions of the project used Ollama for local LLM-powered job analysis and resume generation.

The Ollama setup used in the earlier version was:

```text
Ollama
Model: Llama 3.2:1b
```

The important distinction is that **Ollama is the local LLM runtime, while Llama 3.2:1b is the model running through Ollama**.

The current upgraded NYC Jobs code is primarily rule-based and does not currently make an Ollama call. Ollama remains part of the project's development history and may be incorporated into future versions where an LLM provides a useful advantage.

---

## Resume Personalization

One of the main changes from the earlier version is that the application now requires a resume before starting the job search.

The uploaded resume is parsed and checked for basic resume structure.

The application then looks for competencies such as:

* Python
* SQL
* Financial modeling
* Credit underwriting
* Risk analysis
* Excel
* Data analysis
* Accounting
* Auditing
* Budgeting
* Project management
* Commercial lending
* Research
* Microsoft Office

These competencies are compared with information found in job postings.

The purpose is not to assume that every job is relevant to every candidate.

Instead, the system attempts to create a connection between:

```text
Candidate Background
        ↓
Candidate Competencies
        ↓
Job Requirements
        ↓
Relevant Keywords
        ↓
Customized Application
```

---

## Job Filtering

The current version uses rule-based filtering to identify relevant jobs.

It uses two primary groups of keywords.

### Positive indicators

Examples include:

* Analyst
* Finance
* Credit
* Lending
* Underwriter
* Risk
* Investment
* Banking
* Quantitative
* Software
* Data
* Strategy
* Research
* Accounting
* Audit
* Budget
* Operations
* Project
* Associate
* Officer
* Specialist

### Negative indicators

Examples include:

* Caretaker
* Cook
* Cleaner
* Custodian
* Driver
* Carpenter
* Plumber
* Electrician
* Mechanic
* Nurse
* Doctor
* Security Guard
* Food Service
* Lifeguard
* Receptionist
* Child Care
* Daycare

This approach is intentionally simple and easy to modify.

---

## ATS Keyword Extraction

The application also looks for keywords that may be relevant when tailoring a resume to a particular position.

Examples include:

* Underwriting
* Credit Analysis
* Financial Modeling
* SQL
* Python
* Risk Management
* Data Analysis
* Microsoft Office
* Compliance
* Research
* Project Management

The system also looks for qualification-related phrases such as:

* Bachelor's degree
* Associate degree
* Professional experience
* Quantitative skills
* Communication
* Financial modeling
* Credit analysis
* Data systems
* Advanced Excel
* Database management

The goal is to identify what the job posting is emphasizing rather than simply copying the entire posting into a resume.

---

## Multi-Page Scraping

The application can scrape multiple pages from the NYC Jobs search results.

For example:

```text
Page 1
  ↓
Scrape
  ↓
Filter
  ↓
Save

Page 2
  ↓
Scrape
  ↓
Filter
  ↓
Save

Page 3
  ↓
Scrape
  ↓
Filter
  ↓
Save
```

Each page is processed independently.

This was designed to make the scraper more reliable than attempting to process a large number of pages in a single browser session.

The user can select between 1 and 10 pages.

---

## Database

Job listings are stored locally using SQLite.

The database currently uses a unique job URL to prevent duplicate listings from being inserted.

Example database structure:

```text
batch_jobs_v16

id
search_url
job_url
job_title
agency
salary
location
category
description
min_qualifications
preferred_qualifications
preferred_skills
ats_keywords
posted_until
timestamp
```

The database allows the application to retain previously scraped listings instead of relying entirely on the current browser session.

---

## Resume Generation

The application can generate customized resume content for an individual job.

The generated content uses information extracted from the job posting, including:

* Target job title
* Agency
* ATS keywords
* Minimum qualifications
* Preferred qualifications
* Preferred skills

The current version uses a structured resume template.

The resume-generation component is designed so that it can eventually be replaced or expanded with an LLM-based generation system.

---

## Important Note About AI

The project has evolved through several versions.

Earlier versions experimented more heavily with LLM-based job analysis using Ollama and the Llama 3.2:1b model.

The current upgraded NYC Jobs version focuses more heavily on deterministic, rule-based processing.

That means the current version does **not** use an LLM for every part of the workflow.

The current pipeline is primarily:

```text
Resume
  ↓
Keyword / Competency Matching
  ↓
Rule-Based Job Filtering
  ↓
Keyword & Qualification Extraction
  ↓
Resume Template
```

This was intentional.

Using deterministic rules makes certain parts of the system easier to test, understand, and modify.

Future versions may combine these rules with LLM-based analysis where an LLM provides a meaningful advantage.

---

## Lessons Learned

Building this project has shown me that job scraping is not a one-size-fits-all problem.

Different websites have:

* Different HTML structures
* Different pagination systems
* Different levels of standardization
* Different browser requirements
* Different limitations on automated requests

An approach that works well on one job board may not work on another.

I also learned that simply scraping more data does not necessarily make a job-search tool better.

The more useful questions are:

* What information actually matters?
* How should irrelevant jobs be removed?
* How can the candidate's background influence the search?
* Which information should be automated?
* Which information should be left for the user to review?

The project has therefore evolved through repeated testing rather than trying to build a perfect system from the beginning.

---

## Limitations

This is a work-in-progress project and should not be treated as a fully automated job application system.

Current limitations include:

* Resume competency extraction is based on a predefined keyword list.
* Job relevance is primarily determined through keyword rules.
* Keyword matching can miss context and synonyms.
* Some job-board HTML structures may change over time.
* Scraping reliability depends on the structure of the website.
* Job URLs are not guaranteed to remain active.
* Salary and agency extraction depend on how information appears on the page.
* The resume generator currently uses a structured template rather than fully generating a resume with an LLM.
* Extracted information should be reviewed by the user before being used in an application.

The goal is to assist with the job-search process, not blindly automate decisions.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/nyc-job-intelligence.git
cd nyc-job-intelligence
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### macOS / Linux

```bash
source venv/bin/activate
```

### Windows

```bash
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Start Streamlit:

```bash
streamlit run app.py
```

The application will open in your browser.

### Basic workflow

1. Upload a master resume.
2. Allow the application to validate and parse the resume.
3. Review the detected competencies.
4. Enter an NYC Jobs search-results URL.
5. Select the number of pages to scrape.
6. Choose whether to run the browser headlessly.
7. Start the scraper.
8. Review the filtered job listings.
9. Review extracted qualifications and ATS keywords.
10. Generate customized resume content for a selected position.

---

## Example Use Case

A user uploads a resume containing experience in:

```text
Commercial Lending
Credit Underwriting
Financial Analysis
Python
SQL
Data Analysis
```

The user then searches NYC Jobs.

The application can identify job postings containing related terms such as:

```text
Credit
Analyst
Finance
Risk
Underwriting
Data
Operations
```

The resulting job cards can then display:

```text
Job Title
Agency
Salary
Category
Posting Deadline

ATS Keywords

Minimum Qualifications

Preferred Qualifications

Preferred Skills

Direct Job Link
```

The user can then review the position and generate customized resume content.

---

## Future Improvements

Potential future improvements include:

* LLM-based resume competency extraction
* Semantic job-to-resume matching
* Better synonym handling
* Job relevance scoring
* Ranking jobs by candidate fit
* More accurate salary extraction
* Better agency identification
* More robust job URL validation
* Support for additional job boards
* LLM-assisted resume tailoring
* Downloadable DOCX resumes
* Cover-letter generation
* Job application tracking
* User profiles
* Better database management
* Automated testing
* More robust error handling
* Configurable keyword lists
* Support for additional resume formats

---

## Project Evolution

### Version 1 — NYC Job Scraper

The original version focused on:

```text
Scrape NYC Jobs
      ↓
Analyze Job Postings
      ↓
Filter Jobs
      ↓
Store Results
      ↓
Generate Resume
```

The earlier version also experimented with local LLM processing through Ollama and Llama 3.2:1b.

### Current Version — NYC Job Intelligence

The upgraded version adds:

```text
Upload Resume
      ↓
Extract Candidate Competencies
      ↓
Search NYC Jobs
      ↓
Scrape Multiple Pages
      ↓
Filter Relevant Jobs
      ↓
Extract Qualifications
      ↓
Match Candidate Competencies
      ↓
Identify ATS Keywords
      ↓
Store Results
      ↓
Customize Resume
```

The goal of the project has therefore shifted from simply **scraping jobs** to helping connect a candidate's background with available opportunities.

---

## Disclaimer

This project is for educational and personal research purposes.

Job listings, qualifications, salaries, deadlines, and other information should be verified against the original job posting before applying.

The application is intended to assist with job discovery and application preparation. It does not guarantee that a job is a good match or that an application will be successful.

---

## Author
### Adam Lokhandwalla

This project is part of an ongoing effort to develop practical skills in Python, AI/LLMs, automation, web scraping, data analysis, and application development.

Email: 200chambers@gmail.com

