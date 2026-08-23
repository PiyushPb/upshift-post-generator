import html
from typing import Dict, Any

class TelegramFormatter:
    """Formats cleaned job postings into clean Telegram HTML messages."""

    @staticmethod
    def format_post(job: Dict[str, Any]) -> str:
        title = html.escape(str(job.get("title") or "Job Opportunity"))
        company = html.escape(str(job.get("company") or "Hiring Company"))
        location = html.escape(str(job.get("location") or "India"))
        site = html.escape(str(job.get("site") or "Job Board").capitalize())
        salary = html.escape(str(job.get("salary_display") or "₹ Not Disclosed"))
        job_url = job.get("job_url_direct") or job.get("job_url") or ""
        job_type = str(job.get("job_type") or "").capitalize()
        skills = job.get("skills")

        # Format hashtags
        tags = ["#Hiring", "#JobAlert", "#IndiaJobs"]
        if "software" in title.lower() or "developer" in title.lower() or "engineer" in title.lower():
            tags.append("#TechJobs")
        if "data" in title.lower():
            tags.append("#DataJobs")
        if job.get("is_remote"):
            tags.append("#Remote")

        tag_str = " ".join(tags)

        lines = [
            f"🚀 <b>{title}</b>",
            f"🏢 <b>Company:</b> {company}",
            f"📍 <b>Location:</b> {location}",
            f"💰 <b>Salary:</b> {salary}",
        ]

        if job_type and job_type != "None":
            lines.append(f"⏱ <b>Type:</b> {job_type}")

        if skills and pd_not_null(skills) and str(skills).strip() != "nan":
            lines.append(f"🛠 <b>Skills:</b> {html.escape(str(skills)[:150])}")

        lines.append(f"🌐 <b>Source:</b> {site}")
        lines.append("")
        if job_url:
            lines.append(f"👉 <a href=\"{job_url}\"><b>Apply Here</b></a>")
        lines.append("")
        lines.append(f"<i>{tag_str}</i>")

        return "\n".join(lines)


def pd_not_null(val) -> bool:
    import pandas as pd
    return bool(pd.notnull(val))
