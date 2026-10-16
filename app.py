from datetime import datetime
import os
import platform
import re
import sqlite3
from urllib.parse import parse_qs, urlencode, urlunparse, urlparse
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request

# --- FLASK APP INITIALIZATION (Required for Vercel) ---
app = Flask(__name__)


# --- DATABASE SETUP & AUTO-PURGE NOISE ---
def init_db():
  try:
    with sqlite3.connect("jobs_batch.db", check_same_thread=False) as conn:
      cursor = conn.cursor()
      cursor.execute("""
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
            """)

      # --- PURGE UI NOISE & IRRELEVANT ROLES ---
      cursor.execute(
          "DELETE FROM batch_jobs_v16 WHERE job_title LIKE '%Clear Filters%'"
          " OR job_title LIKE '%Caretaker%' OR job_title LIKE '%Matching"
          " candidate%' OR job_title LIKE '%No valid title%'"
      )
      cursor.execute(
          "DELETE FROM batch_jobs_v16 WHERE job_title LIKE '%Funding Advisor%'"
          " OR agency LIKE '%Flatrock%' OR agency LIKE '%Options Group%' OR"
          " agency LIKE '%ELH MGMT%'"
      )
      conn.commit()
      return True
  except Exception as e:
    print(f"Database Initialization Error: {str(e)}")
    return False


db_initialized = init_db()


def extract_resume_competencies(resume_text):
  common_skills = [
      "python",
      "sql",
      "langgraph",
      "llm",
      "financial modeling",
      "credit underwriting",
      "quantitative",
      "risk analysis",
      "dcf",
      "valuation",
      "excel",
      "bloomberg",
      "portfolio management",
      "accounting",
      "auditing",
      "budgeting",
      "data analysis",
      "project management",
      "compliance",
      "strategy",
      "research",
      "commercial lending",
      "microsoft office",
      "enrollment",
      "client services",
  ]
  return [skill for skill in common_skills if skill in resume_text.lower()]


# --- HTML FRONTEND TEMPLATE FOR VERCEL ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NYC Job Intelligence & AI Resume Generator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f4f7f6; color: #333; }
        .container { max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; }
        .job-card { background: #fafafa; border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 6px; }
        .job-title { font-size: 18px; font-weight: bold; color: #2980b9; text-decoration: none; }
        .meta { font-size: 14px; color: #555; margin-top: 5px; }
        .keywords { background: #e8f4f8; padding: 8px; border-radius: 4px; font-family: monospace; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 NYC Job Intelligence (Vercel Edition)</h1>
        <p>Welcome to your Flask-powered serverless deployment on Vercel!</p>
        
        <h2>📋 Saved Job Listings in Database</h2>
        {% if jobs %}
            <p>Displaying <b>{{ jobs|length }}</b> filtered job records:</p>
            {% for job in jobs %}
                <div class="job-card">
                    <a class="job-title" href="{{ job[2] }}" target="_blank">💼 {{ job[3] }}</a>
                    <div class="meta"><b>🏛️ Agency:</b> {{ job[4] }} | <b>💰 Salary:</b> {{ job[5] }}</div>
                    <div class="meta"><b>⏳ Posted Until:</b> {{ job[13] }} | <b>📅 Scraped On:</b> {{ job[14] }}</div>
                    <div class="keywords"><b>🔑 ATS Keywords:</b> {{ job[12] }}</div>
                    <p><b>📝 Description:</b> {{ job[8][:300] }}...</p>
                </div>
            {% endfor %}
        {% else %}
            <p>No job records found in SQLite database yet.</p>
        {% endif %}
    </div>
</body>
</html>
"""


@app.route("/")
def index():
  jobs = []
  try:
    with sqlite3.connect("jobs_batch.db") as conn:
      cursor = conn.cursor()
      cursor.execute(
          "SELECT * FROM batch_jobs_v16 ORDER BY id DESC LIMIT 20"
      )
      jobs = cursor.fetchall()
  except Exception as e:
    print(f"Error fetching jobs: {e}")

  return render_template_string(HTML_TEMPLATE, jobs=jobs)


if __name__ == "__main__":
  app.run(debug=True)
