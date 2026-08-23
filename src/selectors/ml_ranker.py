import re
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from src.utils.logger import logger

CATEGORY_TAXONOMY = {
    "engineering": {
        "color": "blue",
        "label": "Software Engineering",
        "frame": "./assets/frame-blue.png",
        "thumb_title_l1": "Software Engineer",
        "thumb_title_l2": "Opportunities",
        "thumb_subtitle": "Curated software engineering roles with direct application links.",
        "keywords": [
            "software engineer", "frontend", "backend", "full stack", "fullstack", "developer",
            "react", "node", "python developer", "java", "golang", "go developer", "c++",
            "ios", "android", "typescript", "javascript", "django", "fastapi", "spring",
            "applications software engineer", "custom software engineer", "sde", "software dev"
        ],
        "default_skills": ["React", "Node.js", "Python"]
    },
    "data": {
        "color": "pink",
        "label": "Data & Analytics",
        "frame": "./assets/frame-pink.png",
        "thumb_title_l1": "Data & Analytics",
        "thumb_title_l2": "Opportunities",
        "thumb_subtitle": "Curated data analytics, AI & data science roles with direct application links.",
        "keywords": [
            "data analyst", "data scientist", "machine learning", "ml engineer", "ai engineer",
            "data engineering", "bigquery", "snowflake", "power bi", "tableau", "deep learning",
            "analytics", "analyst", "sql", "spark", "databricks", "etl", "nlp", "llm",
            "business analyst", "it analyst", "operations analyst", "bi developer"
        ],
        "default_skills": ["SQL", "Python", "Power BI"]
    },
    "devops": {
        "color": "green",
        "label": "DevOps & Cloud",
        "frame": "./assets/frame-green.png",
        "thumb_title_l1": "DevOps & Cloud",
        "thumb_title_l2": "Opportunities",
        "thumb_subtitle": "Curated infrastructure, cloud & reliability roles with direct application links.",
        "keywords": [
            "devops", "cloud", "aws", "azure", "gcp", "kubernetes", "k8s", "docker",
            "terraform", "sre", "site reliability", "infrastructure", "infra", "security",
            "qa", "automation testing", "test engineer", "ci/cd"
        ],
        "default_skills": ["AWS", "Docker", "Kubernetes"]
    },
    "product": {
        "color": "yellow",
        "label": "Product & Design",
        "frame": "./assets/frame-yellow.png",
        "thumb_title_l1": "Product & Design",
        "thumb_title_l2": "Opportunities",
        "thumb_subtitle": "Curated product management & design roles with direct application links.",
        "keywords": [
            "product manager", "product owner", "ui/ux", "product designer", "ux designer",
            "ui designer", "figma", "user research", "engineering manager", "technical program manager"
        ],
        "default_skills": ["Product", "UI/UX", "Strategy"]
    }
}

class MLJobSelector:
    """
    Intelligent ML & NLP scoring engine that selects and ranks the top richest
    jobs strictly within a single coherent category (e.g. Engineering only or Data only).
    """

    def __init__(self):
        self.categories = CATEGORY_TAXONOMY

    def detect_job_category(self, title: str, metadata_text: str = "") -> str:
        """Detects whether a job belongs to 'engineering', 'data', 'devops', or 'product'."""
        t_low = title.lower()
        meta_low = metadata_text.lower()
        full_text = f"{t_low} {meta_low}"

        # 1. Check Data / Analytics / AI first
        if any(w in t_low for w in ["analyst", "analytics", "data", "machine learning", "ml ", "ai ", "scientist", "power bi", "tableau", "bi developer"]):
            return "data"

        # 2. Check DevOps / Cloud / Infrastructure / QA
        if any(w in t_low for w in ["devops", "cloud", "sre", "kubernetes", "k8s", "infrastructure", "infra", "qa ", "testing", "security"]):
            return "devops"

        # 3. Check Product / Design / Management
        if any(w in t_low for w in ["product manager", "product owner", "ui/ux", "designer", "engineering manager", "program manager"]):
            return "product"

        # 4. Check Engineering / Developer
        if any(w in t_low for w in ["software", "developer", "engineer", "frontend", "backend", "full stack", "fullstack", "sde", "programmer", "architect"]):
            return "engineering"

        # Metadata fallback
        if any(w in full_text for w in self.categories["data"]["keywords"]):
            return "data"
        if any(w in full_text for w in self.categories["devops"]["keywords"]):
            return "devops"

        return "engineering"

    def extract_top_skills(self, title: str, category_key: str, existing_skills: Optional[str] = None) -> List[str]:
        """Extracts 2-3 clean skill tags for the job card badges."""
        extracted = []
        if existing_skills and pd.notnull(existing_skills) and str(existing_skills).strip() not in ["", "nan", "None"]:
            raw_parts = [s.strip() for s in re.split(r"[,|\n•/]", str(existing_skills)) if s.strip()]
            for p in raw_parts:
                if len(p) <= 20 and p.lower() not in [e.lower() for e in extracted]:
                    extracted.append(p)
                if len(extracted) >= 3:
                    break

        cat_meta = self.categories.get(category_key, self.categories["engineering"])
        if len(extracted) < 3:
            t_lower = title.lower()
            for sk in cat_meta["keywords"]:
                if sk in t_lower and 2 < len(sk) <= 15:
                    clean_sk = sk.upper() if len(sk) <= 4 else sk.title()
                    if clean_sk not in extracted:
                        extracted.append(clean_sk)
                if len(extracted) >= 3:
                    break

        for def_sk in cat_meta["default_skills"]:
            if def_sk not in extracted:
                extracted.append(def_sk)
            if len(extracted) >= 3:
                break

        return extracted[:3]

    def format_card_title(self, raw_title: str) -> Tuple[str, str]:
        """Splits long job titles into clean two-line format for 1080x1080 card layout."""
        clean = re.sub(r"\b(jr|req|id|job)\b[:\-#]?\s*\d+", "", raw_title, flags=re.IGNORECASE)
        clean = re.sub(r"\(.*?\)", "", clean)
        # Normalize AI/ML, UI/UX, CI/CD
        clean = re.sub(r"(\b[A-Za-z]{2,4})/([A-Za-z]{2,4}\b)", r"\1 / \2", clean)
        # Clean noisy suffixes like | or --
        clean = re.sub(r"[|â€\–].*$", "", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        words = clean.split()
        if len(words) <= 2:
            return " ".join(words), ""
        
        mid = (len(words) + 1) // 2
        return " ".join(words[:mid]), " ".join(words[mid:])

    def calculate_richness_score(self, row: pd.Series) -> float:
        """Calculates an intelligent multi-factor data richness score (0 - 100)."""
        score = 0.0

        # 1. Metadata completeness (45 pts)
        if pd.notnull(row.get("company_logo")) and str(row.get("company_logo")).strip() not in ["", "nan", "None"]:
            score += 12.0
        if pd.notnull(row.get("job_url_direct")) and str(row.get("job_url_direct")).strip() not in ["", "nan", "None"]:
            score += 10.0
        if pd.notnull(row.get("min_amount")) or pd.notnull(row.get("max_amount")):
            score += 10.0
        if pd.notnull(row.get("skills")) and str(row.get("skills")).strip() not in ["", "nan", "None"]:
            score += 8.0
        if pd.notnull(row.get("company_rating")) and pd.notnull(row.get("company_reviews_count")):
            score += 5.0

        # 2. Company Profile (20 pts)
        if pd.notnull(row.get("company_description")) and len(str(row.get("company_description"))) > 20:
            score += 8.0
        if pd.notnull(row.get("company_num_employees")):
            score += 6.0
        if pd.notnull(row.get("company_url")) and str(row.get("company_url")).startswith("http"):
            score += 6.0

        # 3. Quality & Title Clarity (25 pts)
        title = str(row.get("title") or "").strip()
        if 8 <= len(title) <= 50:
            score += 10.0
        if any(senior in title.lower() for senior in ["senior", "lead", "staff", "principal", "manager", "architect"]):
            score += 6.0
        if any(tech in title.lower() for tech in ["engineer", "developer", "analyst", "scientist", "designer"]):
            score += 5.0
        if "â" in title or "–" in title or "|" in title or len(title) > 60:
            score -= 4.0

        # 4. Location Clarity (10 pts)
        loc = str(row.get("location") or "")
        if any(city in loc for city in ["Bengaluru", "Bangalore", "Mumbai", "Hyderabad", "Pune", "Delhi", "Gurgaon", "Noida", "Chennai"]):
            score += 8.0
        elif loc.strip() != "":
            score += 4.0

        return max(0.0, min(100.0, score))

    def select_top_jobs(
        self,
        df: pd.DataFrame,
        category: Optional[str] = None,
        top_n: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filters and selects the top richest jobs strictly within the given category.
        If category is None, automatically detects the dominant category.
        Returns: (top_jobs_list, category_metadata)
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to ML ranker.")
            return [], {}

        # Tag each job with its detected category
        annotated = []
        for idx, row in df.iterrows():
            title = str(row.get("title") or "")
            meta_desc = f"{row.get('company_description', '')} {row.get('skills', '')}"
            detected_cat = self.detect_job_category(title, meta_desc)
            rec = row.to_dict()
            rec["_cat"] = detected_cat
            rec["richness_score"] = self.calculate_richness_score(row)
            annotated.append(rec)

        annotated_df = pd.DataFrame(annotated)

        # Determine target category
        if category and category.lower() in self.categories:
            target_cat = category.lower()
        else:
            target_cat = annotated_df["_cat"].value_counts().index[0]
            logger.info(f"🎯 Auto-selected dominant category for batch: [{target_cat.upper()}]")

        cat_meta = self.categories[target_cat]
        cat_df = annotated_df[annotated_df["_cat"] == target_cat].copy()

        if cat_df.empty:
            logger.warning(f"No jobs found for category '{target_cat}'.")
            return [], cat_meta

        # Sort by richness score descending
        cat_df = cat_df.sort_values(by="richness_score", ascending=False)

        # Select with company diversity (max 2 roles per company)
        selected: List[Dict[str, Any]] = []
        company_counts: Dict[str, int] = {}

        for _, row in cat_df.iterrows():
            comp = str(row.get("company") or "").strip().lower()
            if company_counts.get(comp, 0) < 2:
                company_counts[comp] = company_counts.get(comp, 0) + 1
                
                title = str(row.get("title") or "")
                title_l1, title_l2 = self.format_card_title(title)
                skills_badges = self.extract_top_skills(title, target_cat, row.get("skills"))

                item = row.to_dict()
                item.pop("_cat", None)
                item["theme_color"] = cat_meta["color"]
                item["theme_frame"] = cat_meta["frame"]
                item["category_label"] = cat_meta["label"]
                item["skills_badges"] = skills_badges
                item["title_line1"] = title_l1
                item["title_line2"] = title_l2
                item["clean_company"] = re.sub(r"\s+", " ", str(row.get("company") or "Company")).strip()
                item["clean_location"] = str(row.get("location") or "Bengaluru, India").replace("KA, IN", "Bengaluru, Karnataka, India").replace("IN", "India")
                item["clean_site"] = str(row.get("site") or "Indeed").capitalize()
                item["salary_str"] = str(row.get("salary_display") or "₹ Not Disclosed")

                selected.append(item)

            if len(selected) == top_n:
                break

        # Assign carousel indices
        total_slides = len(selected) + 2
        for i, item in enumerate(selected):
            item["slide_index"] = i + 1
            item["total_slides"] = total_slides

        logger.info(f"🏆 Selected {len(selected)} pure '{cat_meta['label']}' jobs with {cat_meta['color'].upper()} theme.")
        return selected, cat_meta
