import re
import datetime
from typing import Dict, Any, List, Optional
import requests
from src.utils.logger import logger
from src.utils.counter import PostCounter

class FirebaseClient:
    """
    Lightweight REST API client for Firebase Firestore with strict sequential ID templates.
    Optimized for GitHub Actions and local execution with zero heavy SDK dependencies.
    """

    def __init__(
        self,
        project_id: str = "upshiftjobs",
        api_key: str = "AIzaSyC2gQprgxVB_zEY_MLWaY08mC9__w2pySQ"
    ):
        self.project_id = project_id
        self.api_key = api_key
        self.base_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/(default)/documents"

    @staticmethod
    def generate_slug(text: str) -> str:
        """Creates a clean URL/DB-safe slug."""
        text = str(text or "").lower()
        slug = re.sub(r"[^\w\s-]", "", text)
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
        return slug[:40]

    @staticmethod
    def generate_job_id(post_id: str, rank: int, company: str) -> str:
        """
        Strict Sequential Job ID Template:
        Format: job_{post_id_slug}_{rank:02d}_{company_slug}
        Example: job_up_0001_01_okta
        """
        pid_clean = post_id.lower().replace("-", "_")
        comp_slug = FirebaseClient.generate_slug(company) or "company"
        return f"job_{pid_clean}_{rank:02d}_{comp_slug}"

    @staticmethod
    def generate_batch_id(post_id: str, category: str, date_obj: Optional[datetime.datetime] = None) -> str:
        """
        Strict Sequential Batch ID Template:
        Format: batch_{category}_{post_id_slug}_{YYYYMMDD}
        Example: batch_engineering_up_0001_20260823
        """
        dt = date_obj or datetime.datetime.now()
        cat_slug = FirebaseClient.generate_slug(category) or "general"
        pid_clean = post_id.lower().replace("-", "_")
        date_str = dt.strftime("%Y%m%d")
        return f"batch_{cat_slug}_{pid_clean}_{date_str}"

    def _to_firestore_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Converts Python dict to Firestore REST API typed fields format."""
        fields = {}
        for k, v in data.items():
            if v is None:
                fields[k] = {"nullValue": None}
            elif isinstance(v, bool):
                fields[k] = {"booleanValue": v}
            elif isinstance(v, (int, float)):
                if isinstance(v, int):
                    fields[k] = {"integerValue": str(v)}
                else:
                    fields[k] = {"doubleValue": float(v)}
            elif isinstance(v, list):
                array_items = []
                for item in v:
                    if isinstance(item, str):
                        array_items.append({"stringValue": item})
                    elif isinstance(item, (int, float)):
                        array_items.append({"doubleValue": float(item)})
                    else:
                        array_items.append({"stringValue": str(item)})
                fields[k] = {"arrayValue": {"values": array_items}}
            elif isinstance(v, dict):
                fields[k] = {"mapValue": {"fields": self._to_firestore_fields(v)}}
            else:
                fields[k] = {"stringValue": str(v)}
        return fields

    def save_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Creates or updates a document in Firestore via REST API."""
        url = f"{self.base_url}/{collection}/{doc_id}?key={self.api_key}"
        payload = {"fields": self._to_firestore_fields(data)}

        try:
            res = requests.patch(url, json=payload, timeout=10)
            if res.status_code in [200, 201]:
                return True
            else:
                err_msg = res.json().get("error", {}).get("message", res.text)
                if "Firestore API has not been used" in err_msg or "PERMISSION_DENIED" in err_msg:
                    logger.warning(
                        "⚠️ Firestore API is not yet enabled for project 'upshiftjobs'. "
                        "Please enable Cloud Firestore in Firebase Console -> Build -> Firestore Database."
                    )
                else:
                    logger.warning(f"⚠️ Firestore ({res.status_code}): {err_msg}")
                return False
        except Exception as e:
            logger.error(f"❌ Firestore save error for {collection}/{doc_id}: {e}")
            return False

    def save_batch_post(
        self,
        batch_id: str,
        category: str,
        location: str,
        top_jobs: List[Dict[str, Any]],
        post_id: str
    ) -> bool:
        """
        Saves a space-efficient curated batch record and all its individual jobs to Firebase.
        """
        logger.info(f"🔥 Saving curated batch [{batch_id}] ({post_id}) with {len(top_jobs)} jobs to Firebase Firestore...")
        now_iso = datetime.datetime.now().isoformat()

        job_ids = []
        for idx, job in enumerate(top_jobs, start=1):
            company = str(job.get("clean_company") or job.get("company") or "Company")
            title = str(job.get("title") or "Role")
            url = str(job.get("job_url_direct") or job.get("job_url") or "")
            job_id = self.generate_job_id(post_id=post_id, rank=idx, company=company)
            job_ids.append(job_id)

            job_doc = {
                "job_id": job_id,
                "post_id": post_id,
                "batch_id": batch_id,
                "batch_rank": idx,
                "title": title,
                "company": company,
                "location": str(job.get("clean_location") or job.get("location") or location),
                "salary": str(job.get("salary_str") or "₹ Not Disclosed"),
                "job_url": url,
                "site": str(job.get("clean_site") or job.get("site") or "Indeed"),
                "skills": job.get("skills_badges", []),
                "category": category,
                "theme_color": str(job.get("theme_color") or "blue"),
                "richness_score": float(job.get("richness_score", 0.0)),
                "saved_at": now_iso
            }
            self.save_document("jobs", job_id, job_doc)

        batch_doc = {
            "batch_id": batch_id,
            "post_id": post_id,
            "category": category,
            "location": location,
            "total_jobs": len(top_jobs),
            "job_ids": job_ids,
            "status": "PUBLISHED",
            "created_at": now_iso
        }
        success = self.save_document("batches", batch_id, batch_doc)
        if success:
            logger.info(f"✅ Successfully stored batch [{batch_id}] in Firebase Firestore.")
        return success
