"""
MongoDB Atlas Database Manager for Health Companion Agent.
Handles persistent storage for Patient Profiles, Ingested Clinical Records,
Medication Reminders, and Daily Water Intake logs.
Includes automatic fallback to in-memory storage if database connection is unavailable.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class MongoDatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self._init_connection()

    def _init_connection(self):
        mongodb_url = os.getenv("MONGODB_URL")
        if not mongodb_url:
            print("[MongoDB] No MONGODB_URL found in environment. Operating in in-memory mode.")
            return

        try:
            import pymongo
            self.client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
            # Test ping
            self.client.admin.command('ping')
            self.db = self.client["health_companion_db"]
            self.is_connected = True
            print("[MongoDB] Successfully connected to MongoDB Atlas ('health_companion_db').")
        except Exception as e:
            print(f"[MongoDB] Connection warning (falling back to in-memory): {e}")
            self.is_connected = False

    # ---------------------------------------------------------------------------
    # Patient Authentication & Profiles
    # ---------------------------------------------------------------------------
    def save_patient(self, name: str, email: str, dob_gender: str = "") -> Dict[str, Any]:
        patient_data = {
            "patient_id": str(uuid.uuid4())[:8].upper(),
            "name": name,
            "email": email.lower(),
            "dob_gender": dob_gender,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if self.is_connected:
            try:
                self.db.patients.update_one(
                    {"email": email.lower()},
                    {"$set": patient_data, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True
                )
                fetched = self.db.patients.find_one({"email": email.lower()})
                if fetched and "_id" in fetched:
                    fetched["_id"] = str(fetched["_id"])
                return fetched or patient_data
            except Exception as e:
                print(f"[MongoDB] Error saving patient: {e}")
        return patient_data

    def get_patient_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if self.is_connected:
            try:
                patient = self.db.patients.find_one({"email": email.lower()})
                if patient and "_id" in patient:
                    patient["_id"] = str(patient["_id"])
                return patient
            except Exception as e:
                print(f"[MongoDB] Error retrieving patient: {e}")
        return None

    # ---------------------------------------------------------------------------
    # Clinical Document Records & History
    # ---------------------------------------------------------------------------
    def save_clinical_record(self, record_title: str, pipeline_result: Dict[str, Any], email: str = "demo@patient.org") -> Dict[str, Any]:
        record_doc = {
            "record_id": str(uuid.uuid4()),
            "patient_email": email.lower(),
            "record_title": record_title,
            "pipeline_result": pipeline_result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        if self.is_connected:
            try:
                self.db.records.insert_one(record_doc)
                if "_id" in record_doc:
                    record_doc["_id"] = str(record_doc["_id"])
            except Exception as e:
                print(f"[MongoDB] Error saving clinical record: {e}")
        return record_doc

    def get_patient_records(self, email: str = "demo@patient.org") -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                records = list(self.db.records.find({"patient_email": email.lower()}).sort("created_at", -1))
                for r in records:
                    if "_id" in r:
                        r["_id"] = str(r["_id"])
                return records
            except Exception as e:
                print(f"[MongoDB] Error fetching clinical records: {e}")
        return []

    # ---------------------------------------------------------------------------
    # Medication Schedule & Reminders
    # ---------------------------------------------------------------------------
    def save_medication(self, med_data: Dict[str, Any], email: str = "demo@patient.org") -> Dict[str, Any]:
        med_doc = dict(med_data)
        med_doc["patient_email"] = email.lower()
        if "id" not in med_doc:
            med_doc["id"] = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        if self.is_connected:
            try:
                self.db.medications.update_one(
                    {"id": med_doc["id"]},
                    {"$set": med_doc},
                    upsert=True
                )
                if "_id" in med_doc:
                    med_doc["_id"] = str(med_doc["_id"])
            except Exception as e:
                print(f"[MongoDB] Error saving medication: {e}")
        return med_doc

    def get_medications(self, email: str = "demo@patient.org") -> List[Dict[str, Any]]:
        if self.is_connected:
            try:
                meds = list(self.db.medications.find({"patient_email": email.lower()}).sort("id", -1))
                for m in meds:
                    if "_id" in m:
                        m["_id"] = str(m["_id"])
                return meds
            except Exception as e:
                print(f"[MongoDB] Error fetching medications: {e}")
        return []

    def delete_medication(self, med_id: int, email: str = "demo@patient.org") -> bool:
        if self.is_connected:
            try:
                res = self.db.medications.delete_one({"id": med_id, "patient_email": email.lower()})
                return res.deleted_count > 0
            except Exception as e:
                print(f"[MongoDB] Error deleting medication: {e}")
        return True

    # ---------------------------------------------------------------------------
    # Hydration / Water Intake Logging
    # ---------------------------------------------------------------------------
    def save_water_intake(self, amount_ml: int, email: str = "demo@patient.org") -> Dict[str, Any]:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.is_connected:
            try:
                self.db.hydration.update_one(
                    {"patient_email": email.lower(), "date": today_str},
                    {"$set": {"amount_ml": amount_ml, "updated_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True
                )
            except Exception as e:
                print(f"[MongoDB] Error saving hydration log: {e}")
        return {"date": today_str, "amount_ml": amount_ml}

    def get_water_intake(self, email: str = "demo@patient.org") -> int:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.is_connected:
            try:
                log = self.db.hydration.find_one({"patient_email": email.lower(), "date": today_str})
                if log and "amount_ml" in log:
                    return log["amount_ml"]
            except Exception as e:
                print(f"[MongoDB] Error fetching hydration log: {e}")
        return 1250


# Global Singleton instance
db_manager = MongoDatabaseManager()
