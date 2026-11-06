from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_file, flash
)

from werkzeug.utils import secure_filename
from matching import analyze_resume, recommend_jobs

import io
import os

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "dev-key-change-before-deployment"
)

ALLOWED_EXTENSIONS = {"pdf", "txt"}


# --------------------------------------------------
# SAMPLE JOB DATABASE
# --------------------------------------------------

jobs = [
    {
        "id": 1,
        "title": "Python Developer",
        "company": "Tech Solutions",
        "location": "Chennai",
        "skills": "Python Flask SQL Git REST API",
        "description": (
            "Develop backend applications using Python and Flask. "
            "Work with SQL databases, REST APIs, Git, debugging, "
            "and software development."
        )
    },
    {
        "id": 2,
        "title": "Data Analyst",
        "company": "DataWorks",
        "location": "Bengaluru",
        "skills": "Python SQL Excel Power BI Statistics",
        "description": (
            "Analyze datasets using Python, SQL, Excel, and Power BI. "
            "Prepare reports, dashboards, and business insights."
        )
    },
    {
        "id": 3,
        "title": "Machine Learning Intern",
        "company": "AI Innovations",
        "location": "Chennai",
        "skills": "Python Machine Learning Statistics Scikit-learn",
        "description": (
            "Assist with machine learning projects using Python, "
            "statistics, data preprocessing, and scikit-learn."
        )
    },
    {
        "id": 4,
        "title": "Frontend Developer",
        "company": "WebCraft",
        "location": "Remote",
        "skills": "HTML CSS JavaScript React Git",
        "description": (
            "Build responsive websites using HTML, CSS, JavaScript, "
            "and React. Collaborate with designers and backend teams."
        )
    },
    {
        "id": 5,
        "title": "Cybersecurity Intern",
        "company": "SecureNet",
        "location": "Chennai",
        "skills": "Cybersecurity Networking Linux Python",
        "description": (
            "Assist with network security, Linux administration, "
            "security monitoring, vulnerability analysis, and Python."
        )
    }
]


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", jobs=jobs)


# --------------------------------------------------
# RESUME BUILDER
# --------------------------------------------------

@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():

    if request.method == "POST":

        resume = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "location": request.form.get("location", "").strip(),
            "summary": request.form.get("summary", "").strip(),
            "education": request.form.get("education", "").strip(),
            "skills": request.form.get("skills", "").strip(),
            "projects": request.form.get("projects", "").strip(),
            "experience": request.form.get("experience", "").strip()
        }

        if not resume["name"]:
            flash("Please enter your name.", "error")
            return render_template("resume_builder.html")

        session["resume"] = resume

        return render_template(
            "resume_result.html",
            resume=resume
        )

    return render_template("resume_builder.html")


# --------------------------------------------------
# DOWNLOAD RESUME AS PDF
# --------------------------------------------------

@app.route("/download-resume")
def download_resume():

    resume = session.get("resume")

    if not resume:
        flash("Please create your resume first.", "error")
        return redirect(url_for("resume_builder"))

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet

        buffer = io.BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()
        content = []

        def add_section(title, text):
            if text:
                content.append(Paragraph(title, styles["Heading2"]))
                content.append(
                    Paragraph(
                        text.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                            .replace("\n", "<br/>"),
                        styles["BodyText"]
                    )
                )
                content.append(Spacer(1, 12))

        content.append(
            Paragraph(
                resume.get("name", "Resume"),
                styles["Title"]
            )
        )

        contact = " | ".join(
            value for value in [
                resume.get("email", ""),
                resume.get("phone", ""),
                resume.get("location", "")
            ] if value
        )

        if contact:
            content.append(
                Paragraph(contact, styles["BodyText"])
            )

        content.append(Spacer(1, 15))

        add_section("Professional Summary", resume.get("summary", ""))
        add_section("Education", resume.get("education", ""))
        add_section("Skills", resume.get("skills", ""))
        add_section("Projects", resume.get("projects", ""))
        add_section("Experience", resume.get("experience", ""))

        document.build(content)

        buffer.seek(0)

        filename = secure_filename(
            resume.get("name", "resume")
        ) or "resume"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{filename}_resume.pdf"
        )

    except ImportError:
        flash(
            "PDF library is missing. Install reportlab first.",
            "error"
        )
        return redirect(url_for("resume_builder"))


# --------------------------------------------------
# RESUME ANALYZER AND JOB RECOMMENDATIONS
# --------------------------------------------------

@app.route("/analyzer", methods=["GET", "POST"])
def analyzer():

    analysis = None
    recommendations = []
    error = None

    if request.method == "POST":

        resume_text = request.form.get(
            "resume_text", ""
        ).strip()

        uploaded_file = request.files.get("resume_file")

        if uploaded_file and uploaded_file.filename:

            extension = uploaded_file.filename.rsplit(
                ".", 1
            )[-1].lower() if "." in uploaded_file.filename else ""

            if extension not in ALLOWED_EXTENSIONS:
                error = "Please upload a PDF or TXT resume."

            else:
                try:
                    file_bytes = uploaded_file.read()

                    if len(file_bytes) > 5 * 1024 * 1024:
                        error = "The file must be smaller than 5 MB."

                    elif extension == "txt":
                        resume_text = file_bytes.decode(
                            "utf-8", errors="replace"
                        ).strip()

                    elif extension == "pdf":
                        import fitz

                        with fitz.open(
                            stream=file_bytes,
                            filetype="pdf"
                        ) as document:

                            resume_text = "\n".join(
                                page.get_text()
                                for page in document
                            ).strip()

                        if not resume_text:
                            error = (
                                "No selectable text was found. "
                                "Please use a text-based PDF or "
                                "paste your resume text."
                            )

                except Exception:
                    error = (
                        "Unable to read the file. "
                        "Please try another PDF or TXT file."
                    )

        if not error and not resume_text:
            error = "Please upload a resume or paste your resume text."

        if not error:

            analysis = analyze_resume(resume_text)

            recommendations = recommend_jobs(
                resume_text,
                jobs
            )

    return render_template(
        "analyzer.html",
        analysis=analysis,
        recommendations=recommendations,
        error=error
    )


# --------------------------------------------------
# JOB SEARCH
# --------------------------------------------------

@app.route("/jobs")
def job_list():

    search_query = request.args.get(
        "q", ""
    ).strip().lower()

    filtered_jobs = [
        job for job in jobs
        if search_query in (
            job["title"] + " " +
            job["company"] + " " +
            job["location"] + " " +
            job["skills"] + " " +
            job["description"]
        ).lower()
    ]

    return render_template(
        "jobs.html",
        jobs=filtered_jobs,
        search_query=search_query
    )


# --------------------------------------------------
# ADD A JOB
# --------------------------------------------------

@app.route("/add-job", methods=["GET", "POST"])
def add_job():

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        location = request.form.get("location", "").strip()
        skills = request.form.get("skills", "").strip()
        description = request.form.get(
            "description", ""
        ).strip()

        if not all([title, company, description]):
            flash(
                "Job title, company, and description are required.",
                "error"
            )

            return render_template("add_job.html")

        new_job = {
            "id": max(
                (job["id"] for job in jobs),
                default=0
            ) + 1,
            "title": title,
            "company": company,
            "location": location,
            "skills": skills,
            "description": description
        }

        jobs.append(new_job)

        flash("Job listing added successfully.", "success")

        return redirect(url_for("job_list"))

    return render_template("add_job.html")


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)