# ai_mcp/tools/doctors_tool.py

import csv
from pathlib import Path


class DoctorsTool:
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.doctors = self._load_doctors()

    def _load_doctors(self):
        with open(self.csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    def find_by_specialization(self, query: str):
        q = query.lower()
        return [
            d for d in self.doctors
            if q in d.get("specialization", "").lower()
        ]

    def find_by_department(self, department: str):
        dept = department.lower()
        return [
            d for d in self.doctors
            if dept in d.get("department", "").lower()
        ]

    def list_all(self):
        return self.doctors
