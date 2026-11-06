
import re
import math
from collections import Counter

# Common technical and professional skills
SKILLS = [
    "python", "java", "c++", "c", "javascript",
    "html", "css", "react", "flask", "django",
    "sql", "mysql", "mongodb", "machine learning",
    "deep learning", "artificial intelligence",
    "data analysis", "data science", "power bi",
    "excel", "communication", "leadership",
    "teamwork", "problem solving", "git",
    "github", "cloud computing", "aws",
    "cybersecurity", "networking", "linux",
    "natural language processing", "tensorflow",
    "pytorch", "scikit-learn", "rest api",
    "fastapi", "docker", "kubernetes",
    "project management", "testing",
    "software development", "statistics"
]

# Optional pretrained AI model
_model = None
_model_attempted = False


def get_ai_model():
    """Try to load the pretrained sentence embedding model."""
    global _model, _model_attempted

    if _model_attempted:
        return _model

    _model_attempted = True

    try:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
    except Exception as error:
        print("AI model unavailable; using built-in text matching.")
        print(error)

    return _model


def extract_skills(text):
    """Identify known skills in resume text."""
    text = str(text).lower()
    found_skills = []

    for skill in SKILLS:
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

        if re.search(pattern, text):
            found_skills.append(skill)

    return sorted(set(found_skills))


def keyword_similarity(text1, text2):
    """Calculate text similarity using built-in Python tools."""
    words1 = re.findall(r"\b[a-zA-Z0-9+#.]+\b", text1.lower())
    words2 = re.findall(r"\b[a-zA-Z0-9+#.]+\b", text2.lower())

    if not words1 or not words2:
        return 0.0

    stop_words = {
        "the", "and", "for", "with", "from", "this", "that",
        "are", "was", "were", "will", "you", "your", "our",
        "has", "have", "had", "but", "not", "into", "about",
        "job", "role", "work", "experience", "skills"
    }

    words1 = [w for w in words1 if w not in stop_words]
    words2 = [w for w in words2 if w not in stop_words]

    if not words1 or not words2:
        return 0.0

    count1 = Counter(words1)
    count2 = Counter(words2)

    vocabulary = set(count1) | set(count2)

    dot_product = sum(count1[w] * count2[w] for w in vocabulary)
    norm1 = math.sqrt(sum(v * v for v in count1.values()))
    norm2 = math.sqrt(sum(v * v for v in count2.values()))

    if not norm1 or not norm2:
        return 0.0

    return round((dot_product / (norm1 * norm2)) * 100, 2)


def calculate_similarity(resume_text, job_description):
    """Compare a resume with a job description."""
    resume_text = str(resume_text).strip()
    job_description = str(job_description).strip()

    if not resume_text or not job_description:
        return 0.0

    model = get_ai_model()

    if model is not None:
        try:
            embeddings = model.encode(
                [resume_text, job_description],
                normalize_embeddings=True
            )

            score = float(embeddings[0] @ embeddings[1])
            return round(max(0.0, min(100.0, score * 100)), 2)
        except Exception as error:
            print("AI comparison failed; using keyword matching.")
            print(error)

    return keyword_similarity(resume_text, job_description)


def analyze_resume(resume_text):
    """Analyze a resume and suggest improvements."""
    text = str(resume_text).strip()
    skills = extract_skills(text)
    suggestions = []

    if len(text.split()) < 100:
        suggestions.append(
            "Add more details about your education, projects, "
            "experience, and achievements."
        )

    if not skills:
        suggestions.append(
            "Include relevant skills that you genuinely possess."
        )

    if not re.search(r"\b(project|projects)\b", text, re.I):
        suggestions.append(
            "Add an academic or personal project and explain your contribution."
        )

    if not re.search(
        r"\b(education|degree|university|college|bachelor)\b",
        text,
        re.I
    ):
        suggestions.append(
            "Include your education and qualification details."
        )

    if not re.search(
        r"\b(achieved|developed|built|improved|created|designed)\b",
        text,
        re.I
    ):
        suggestions.append(
            "Use action verbs to describe your contributions and achievements."
        )

    if not suggestions:
        suggestions.append(
            "Check accuracy and tailor your resume to each job description."
        )

    return {
        "skills": skills,
        "word_count": len(text.split()),
        "suggestions": suggestions
    }


def recommend_jobs(resume_text, jobs):
    """Rank jobs by resume relevance and skill overlap."""
    recommendations = []
    resume_skills = set(extract_skills(resume_text))

    for job in jobs:
        description = (
            str(job.get("title", "")) + " " +
            str(job.get("description", "")) + " " +
            str(job.get("skills", ""))
        )

        job_skills = set(extract_skills(description))
        matched_skills = sorted(resume_skills & job_skills)
        missing_skills = sorted(job_skills - resume_skills)

        score = calculate_similarity(resume_text, description)

        recommendations.append({
            **job,
            "match_score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills
        })

    recommendations.sort(
        key=lambda job: job["match_score"],
        reverse=True
    )

    return recommendations
