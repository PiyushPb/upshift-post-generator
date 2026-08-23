import datetime
from typing import List, Dict, Any

CATEGORY_HASHTAGS = {
    "data": [
        "#analyticsjobs", "#careers", "#careerupdates", "#dataanalyst",
        "#dataanalytics", "#datascience", "#hiringnow", "#jobopenings",
        "#jobsearch", "#jobsinindia", "#powerbijobs", "#sqljobs",
        "#machinelearning", "#aijobs", "#techjobs"
    ],
    "engineering": [
        "#softwareengineer", "#developerjobs", "#frontend", "#backend",
        "#fullstack", "#coding", "#techjobs", "#hiringnow",
        "#jobopenings", "#jobsearch", "#jobsinindia", "#careers",
        "#pythonjobs", "#reactjobs", "#engineeringjobs"
    ],
    "devops": [
        "#devopsjobs", "#cloudengineer", "#awsjobs", "#kubernetes",
        "#sre", "#cloudcomputing", "#techjobs", "#hiringnow",
        "#jobopenings", "#jobsearch", "#jobsinindia", "#careers",
        "#infrastructure", "#sysadmin"
    ],
    "product": [
        "#productmanager", "#productdesign", "#uiuxjobs", "#uxdesign",
        "#uidesign", "#techjobs", "#hiringnow", "#jobopenings",
        "#jobsearch", "#jobsinindia", "#careers", "#productmanagement"
    ]
}

class CaptionGenerator:
    """Generates Instagram-friendly caption.txt and WhatsApp/Telegram shareable lists."""

    @staticmethod
    def generate_instagram_caption(
        top_jobs: List[Dict[str, Any]],
        category_meta: Dict[str, Any],
        location_str: str = "Bengaluru",
        post_id: str = "UP-0823"
    ) -> str:
        """Constructs an Instagram-compliant caption without links and with clean spacing."""
        now = datetime.datetime.now()
        date_formatted = now.strftime("%d %b %Y")
        cat_label = category_meta.get("label", "Software Engineering")
        cat_key = category_meta.get("color", "blue")
        # Map color to hashtag key
        cat_map = {"pink": "data", "blue": "engineering", "green": "devops", "yellow": "product"}
        tag_key = cat_map.get(cat_key, "engineering")

        # Distinct roles list
        roles = []
        for j in top_jobs:
            title = j.get("title", "")
            if title and title not in roles:
                roles.append(title)
            if len(roles) >= 4:
                break
        roles_str = ", ".join(roles)

        # Sources
        sources = list(set([str(j.get("clean_site") or "Indeed").capitalize() for j in top_jobs]))
        sources_str = ", ".join(sources)

        # Hashtags
        tags_list = CATEGORY_HASHTAGS.get(tag_key, CATEGORY_HASHTAGS["engineering"])
        hashtags_str = " ".join(tags_list)

        caption_lines = [
            "Upshift helps you discover active job opportunities across multiple roles and industries. We curate publicly listed openings to make job discovery simple and accessible.",
            "",
            "Job Details",
            f"📍 Location: {location_str}",
            f"💼 Role Category: {cat_label}",
            f"🧠 Job Roles: {roles_str}",
            f"📅 Posted On: {date_formatted}",
            f"🌐 Source Platforms: {sources_str}",
            f"Post ID: {post_id}",
            "",
            "Disclaimer",
            "Upshift is an independent job discovery page. We are not a recruiter, hiring agency, or employer representative. All jobs are sourced from publicly available listings and redirect to official application pages.",
            "",
            "📬 Apply via official links — join our social's (link(s) in bio).",
            "",
            hashtags_str
        ]

        return "\n".join(caption_lines)

    @staticmethod
    def generate_share_links_list(
        top_jobs: List[Dict[str, Any]],
        category_meta: Dict[str, Any],
        location_str: str = "Bengaluru",
        post_id: str = "UP-0823"
    ) -> str:
        """Constructs a clean numbered text list with company names and application links for WhatsApp & Telegram."""
        now = datetime.datetime.now()
        date_formatted = now.strftime("%d %B %Y")
        cat_label = category_meta.get("label", "Software Engineering")

        lines = [
            f"🚀 *{cat_label} Opportunities* — *Upshift Curated*",
            f"📍 Location: {location_str}",
            f"📅 Date: {date_formatted}",
            f"🆔 Post Ref: #{post_id}",
            "",
            "Here are the direct official application links for today's curated batch:",
            ""
        ]

        for idx, job in enumerate(top_jobs, start=1):
            title = job.get("title", "Role")
            company = job.get("clean_company", "Company")
            salary = job.get("salary_str", "₹ Not Disclosed")
            job_url = job.get("job_url_direct") or job.get("job_url") or ""

            lines.append(f"{idx}. *{title}* — *{company}*")
            if salary and salary != "₹ Not Disclosed":
                lines.append(f"   💰 {salary}")
            lines.append(f"   🔗 Apply: {job_url}")
            lines.append("")

        lines.append("─────────────────────────")
        lines.append("📬 Join @upshift.app for daily verified tech job opportunities across India!")

        return "\n".join(lines)
