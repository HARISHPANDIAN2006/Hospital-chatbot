import json
import os
import re
from langchain_ollama import OllamaLLM
from dotenv import load_dotenv

try:
    from mcp.direct_client import DirectMCPClient
except (ModuleNotFoundError, ImportError):
    from direct_client import DirectMCPClient

load_dotenv()


class MCPExecutor:
    def __init__(self):
        self.client = DirectMCPClient()
        self.llm = None
        
        try:
            ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
            self.llm = OllamaLLM(model=ollama_model)
            print(f"✅ Using Ollama ({ollama_model}) for NLP extraction")
        except Exception as e:
            print(f"⚠️ Ollama not available: {e}")
            self.llm = None

    def _extract_patient_rule_based(self, query: str) -> dict:
        """Fallback rule-based extraction for patient registration"""
        q = query
        data = {
            "name": None,
            "age": None,
            "gender": None,
            "contact": None,
            "email": None,
            "address": None,
            "blood_group": None,
            "allergies": None,
        }

        name_match = re.search(r"(?:named|name is|patient)\s+([a-zA-Z .'-]{2,60})", q, re.IGNORECASE)
        if name_match:
            data["name"] = name_match.group(1).strip(" ,.")

        age_match = re.search(r"\b(\d{1,3})\s*(?:years?|yrs?)?\s*old\b|\bage\s*(?:is)?\s*(\d{1,3})", q, re.IGNORECASE)
        if age_match:
            data["age"] = int(next(g for g in age_match.groups() if g))

        gender_match = re.search(r"\b(male|female|other)\b", q, re.IGNORECASE)
        if gender_match:
            data["gender"] = gender_match.group(1).capitalize()

        contact_match = re.search(r"(?:contact|phone|mobile)\s*(?:is|:)?\s*(\+?\d[\d -]{7,}\d)", q, re.IGNORECASE)
        if not contact_match:
            contact_match = re.search(r"\b(\+?\d[\d -]{9,}\d)\b", q)
        if contact_match:
            data["contact"] = contact_match.group(1).strip()

        email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", q)
        if email_match:
            data["email"] = email_match.group(0)

        blood_match = re.search(r"\b(a|b|ab|o)[+-]\b", q, re.IGNORECASE)
        if blood_match:
            data["blood_group"] = blood_match.group(0).upper()

        allergies_match = re.search(r"(?:allerg(?:y|ies)\s*(?:is|are|:)?\s*)([^,.]+)", q, re.IGNORECASE)
        if allergies_match:
            data["allergies"] = allergies_match.group(1).strip()

        address_match = re.search(r"(?:address\s*(?:is|:)?\s*)(.+)", q, re.IGNORECASE)
        if address_match:
            data["address"] = address_match.group(1).strip().rstrip(".")

        return data

    def _extract_appointment_rule_based(self, query: str) -> dict:
        """Fallback rule-based extraction for appointment booking"""
        q = query
        data = {
            "patient_id": None,
            "doctor_id": None,
            "doctor_name": None,
            "specialization": None,
            "date": None,
            "time": None,
            "reason": None,
            "symptoms": None,
        }

        pid = re.search(r"(?:patient\s*id|patient)\s*(?:is|:)?\s*([a-fA-F0-9]{24}|\w[\w-]{4,})", q, re.IGNORECASE)
        if pid:
            data["patient_id"] = pid.group(1)

        did = re.search(r"(?:doctor\s*id|dr\s*id)\s*(?:is|:)?\s*([a-fA-F0-9]{24}|\w[\w-]{4,})", q, re.IGNORECASE)
        if did:
            data["doctor_id"] = did.group(1)

        dname = re.search(r"(?:with|doctor|dr\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", q)
        if dname:
            name = dname.group(1).strip()
            if not name.lower().startswith("id"):
                data["doctor_name"] = f"Dr. {name}" if not name.lower().startswith("dr") else name

        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", q)
        if date_match:
            data["date"] = date_match.group(1)

        time_match = re.search(r"\b([01]\d|2[0-3]):([0-5]\d)\b", q)
        if time_match:
            data["time"] = f"{time_match.group(1)}:{time_match.group(2)}"

        spec_match = re.search(
            r"\b(cardiology|cardiologist|dermatology|dermatologist|neurology|neurologist|pediatrics|pediatrician|orthopedics|orthopedic|gynecology|gynecologist|psychiatry|psychiatrist|general medicine)\b",
            q,
            re.IGNORECASE,
        )
        if spec_match:
            data["specialization"] = spec_match.group(1)

        # Better reason extraction - looks for "for [reason]" at the end
        reason_match = re.search(r"(?:for|reason\s*(?:is|:))\s+([^,.]+?)(?:\s*$|\.)", q, re.IGNORECASE)
        if reason_match:
            data["reason"] = reason_match.group(1).strip()

        symptoms_match = re.search(r"(?:symptoms?\s*(?:are|:))\s+([^,.]+)", q, re.IGNORECASE)
        if symptoms_match:
            data["symptoms"] = symptoms_match.group(1).strip()

        return data

    def extract_patient_with_ollama(self, query: str) -> dict:
        """Use Ollama to extract patient registration details"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract patient registration details from this query: "{query}"

Return ONLY a valid JSON object with these fields (use null for missing fields):
{{
    "name": "patient full name or null",
    "age": "number or null",
    "gender": "Male/Female/Other or null",
    "contact": "phone number or null",
    "email": "email or null",
    "address": "address or null",
    "blood_group": "blood group or null",
    "allergies": "allergies or null"
}}

Return ONLY the JSON, no other text."""

        response = self.llm.invoke(prompt)
        response = response.strip()
        
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        for key in data:
            if data[key] == "null" or data[key] == "None":
                data[key] = None
        
        if data.get("age") is not None:
            data["age"] = int(data["age"])
        
        return data

    def extract_appointment_with_ollama(self, query: str):
        """Use Ollama to extract appointment details from natural language"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract appointment booking details from this query: "{query}"

Pay special attention to:
- "for patient ID [id]" or "patient [id]" → patient_id
- "with Dr. [name]" or "doctor [name]" → doctor_name
- "on [date]" → date in YYYY-MM-DD format
- "at [time]" → time in HH:MM 24-hour format
- "for [reason]" at the END → reason (e.g., "for chest pain" means reason is "chest pain")

Return ONLY valid JSON:
{{
    "patient_id": "patient ID or null",
    "doctor_id": "doctor ID or null",
    "doctor_name": "doctor name or null",
    "specialization": "medical specialization or null",
    "date": "appointment date in YYYY-MM-DD format or null",
    "time": "appointment time in HH:MM format (24-hour) or null",
    "reason": "reason for appointment (extract from 'for [reason]') or null",
    "symptoms": "symptoms or null"
}}

Examples:
Query: "book appointment for patient 123 with Dr. John on 2026-03-20 at 14:00 for headache"
Output: {{"patient_id":"123", "doctor_name":"Dr. John", "date":"2026-03-20", "time":"14:00", "reason":"headache"}}

Query: "book appointment for patient 456 with cardiologist on 2026-03-25 at 10:30 for chest pain"
Output: {{"patient_id":"456", "specialization":"cardiology", "date":"2026-03-25", "time":"10:30", "reason":"chest pain"}}

Return ONLY the JSON, no other text."""

        response = self.llm.invoke(prompt)
        response = response.strip()
        
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        response = response.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(response)
            # Convert string "null" to None
            for key in data:
                if data[key] == "null" or data[key] == "None":
                    data[key] = None
            
            # Debug print
            print(f"📋 Extracted appointment data: {data}")
            
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON: {response}")
            raise Exception(f"Could not parse LLM response: {str(e)}")

    def extract_patient_id(self, query: str):
        """Extract patient ID from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract patient ID from: "{query}"
Return ONLY valid JSON: {{"patient_id": "ID or null"}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        if data.get("patient_id") == "null":
            data["patient_id"] = None
        return data

    def extract_doctor_id(self, query: str):
        """Extract doctor ID from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract doctor ID from: "{query}"
Return ONLY valid JSON: {{"doctor_id": "ID or null"}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        if data.get("doctor_id") == "null":
            data["doctor_id"] = None
        return data

    def extract_appointment_id(self, query: str):
        """Extract appointment ID from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract appointment ID from: "{query}"
Return ONLY valid JSON: {{"appointment_id": "ID or null"}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        if data.get("appointment_id") == "null":
            data["appointment_id"] = None
        return data

    def extract_reschedule_details(self, query: str):
        """Extract reschedule details from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract reschedule details from: "{query}"
Return ONLY valid JSON: {{"appointment_id": "ID or null", "new_date": "YYYY-MM-DD or null", "new_time": "HH:MM or null"}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        for key in data:
            if data[key] == "null":
                data[key] = None
        return data

    def extract_update_profile_details(self, query: str):
        """Extract profile update details from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract patient profile update details from: "{query}"
Return ONLY valid JSON with patient_id and fields to update: 
{{"patient_id": "ID or null", "updates": {{"field": "value"}}}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        for key in data:
            if data[key] == "null":
                data[key] = None
        return data

    def extract_consultation_details(self, query: str):
        """Extract consultation processing details from query"""
        if not self.llm:
            raise Exception("Ollama not configured")
        
        prompt = f"""Extract consultation processing details from: "{query}"
Return ONLY valid JSON:
{{"appointment_id": "ID or null", "audio_filename": "filename or null", "send_email": true/false}}
Return ONLY the JSON."""

        response = self.llm.invoke(prompt).strip()
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        response = response.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(response)
        for key in data:
            if data[key] == "null":
                data[key] = None
        return data

    def generate_human_response(self, result: dict, intent: str) -> str:
        """Generate human-friendly response from MCP result"""
        if not self.llm:
            return json.dumps(result, indent=2)

        prompt = f"""You are a friendly hospital chatbot assistant. Convert this technical response into a natural, human-friendly message.

Intent: {intent}
Technical Response: {json.dumps(result)}

Rules:
1. Be warm, professional, and conversational
2. If successful, confirm the action
3. If error, explain the problem clearly and suggest next step
4. Include important IDs, names, dates when present
5. Keep it concise (2-4 sentences)
6. Use emojis sparingly (1-2 max)

Human-friendly response:"""

        try:
            response = self.llm.invoke(prompt)
            return response.strip() or json.dumps(result, indent=2)
        except Exception:
            return json.dumps(result, indent=2)

    async def execute(self, intent: str, query: str):
        """Execute MCP tool based on intent"""
        
        # === REGISTER PATIENT ===
        if intent == "REGISTER_PATIENT":
            try:
                if self.llm:
                    print("🤖 Extracting patient details...")
                    try:
                        details = self.extract_patient_with_ollama(query)
                    except Exception:
                        details = self._extract_patient_rule_based(query)
                else:
                    details = self._extract_patient_rule_based(query)

                required = ["name", "age", "gender", "contact"]
                missing = [f for f in required if not details.get(f)]

                if missing:
                    missing_info = {
                        "error": f"Missing required information: {', '.join(missing)}",
                        "missing_fields": missing,
                        "example": "Try saying: 'Register patient named Sarah Smith, 28 years old, female, contact 9876543210'",
                    }
                    return {
                        "human_response": self.generate_human_response(missing_info, intent),
                        "raw_data": missing_info,
                    }

                details = {k: v for k, v in details.items() if v is not None}

                print(f"Registering patient: {details.get('name')}...")
                result = await self.client.call("register_patient", details)
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }

            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        # === SEARCH DOCTORS ===
        elif intent == "SEARCH_DOCTORS":
            try:
                specialty = query.lower()
                specialty = specialty.replace("search doctors", "").replace("find doctors", "").strip()
                
                result = await self.client.call("search_doctors", {"specialization": specialty})
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }
            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        # === BOOK APPOINTMENT ===
        elif intent == "BOOK_APPOINTMENT":
            try:
                if self.llm:
                    print("🤖 Extracting appointment details...")
                    try:
                        details = self.extract_appointment_with_ollama(query)
                    except Exception as e:
                        print(f"Ollama extraction failed: {e}, using rule-based")
                        details = self._extract_appointment_rule_based(query)
                else:
                    details = self._extract_appointment_rule_based(query)

                missing_fields = []
                if not details.get("patient_id"):
                    missing_fields.append("patient ID")
                if not details.get("doctor_id") and not details.get("doctor_name") and not details.get("specialization"):
                    missing_fields.append("doctor name or specialization")
                if not details.get("date"):
                    missing_fields.append("appointment date (YYYY-MM-DD)")
                if not details.get("time"):
                    missing_fields.append("appointment time (HH:MM)")
                if not details.get("reason"):
                    missing_fields.append("reason for appointment")

                if missing_fields:
                    missing_info = {
                        "error": f"Missing required information: {', '.join(missing_fields)}",
                        "missing_fields": missing_fields,
                        "example": "Try saying: 'Book appointment for patient ID 67890abc with Dr. Sarah Johnson on 2026-03-20 at 14:00 for chest pain'",
                    }
                    return {
                        "human_response": self.generate_human_response(missing_info, intent),
                        "raw_data": missing_info,
                    }

                # Find doctor if not provided
                if not details.get("doctor_id"):
                    if details.get("doctor_name"):
                        print(f"\nSearching for doctor: {details['doctor_name']}")
                        doctor_result = await self.client.call("search_doctors", {"name": details["doctor_name"]})
                        if doctor_result.get("doctors") and len(doctor_result["doctors"]) > 0:
                            details["doctor_id"] = doctor_result["doctors"][0]["_id"]
                            print(f"Found: {doctor_result['doctors'][0]['name']}")
                        else:
                            error_result = {"error": f"No doctor found with name '{details['doctor_name']}'"}
                            return {
                                "human_response": self.generate_human_response(error_result, intent),
                                "raw_data": error_result,
                            }
                    elif details.get("specialization"):
                        print(f"\nSearching for {details['specialization']} doctors...")
                        doctor_result = await self.client.call("search_doctors", {"specialization": details["specialization"]})
                        if doctor_result.get("doctors") and len(doctor_result["doctors"]) > 0:
                            details["doctor_id"] = doctor_result["doctors"][0]["_id"]
                            print(f"Found: {doctor_result['doctors'][0]['name']}")
                        else:
                            error_result = {"error": f"No {details['specialization']} doctors found"}
                            return {
                                "human_response": self.generate_human_response(error_result, intent),
                                "raw_data": error_result,
                            }

                appointment_data = {
                    "patient_id": details["patient_id"],
                    "doctor_id": details["doctor_id"],
                    "appointment_date": details["date"],
                    "appointment_time": details["time"],
                    "reason": details["reason"],
                }
                if details.get("symptoms"):
                    appointment_data["symptoms"] = details["symptoms"]

                print("\nBooking appointment...")
                result = await self.client.call("book_appointment", appointment_data)
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }

            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        # === GET PATIENT PROFILE ===
        elif intent == "GET_PATIENT_PROFILE":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view the profile. Please provide the patient ID.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_patient_profile", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === UPDATE PATIENT PROFILE ===
        elif intent == "UPDATE_PATIENT_PROFILE":
            try:
                details = self.extract_update_profile_details(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to update the profile.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("update_patient_profile", details)
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET DOCTOR INFO ===
        elif intent == "GET_DOCTOR_INFO":
            try:
                details = self.extract_doctor_id(query)
                if not details.get("doctor_id"):
                    return {
                        "human_response": "I need a doctor ID to get their information.",
                        "raw_data": {"error": "Missing doctor_id"}
                    }
                
                result = await self.client.call("get_doctor_info", {"doctor_id": details["doctor_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET MY APPOINTMENTS ===
        elif intent == "GET_MY_APPOINTMENTS":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view appointments.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_my_appointments", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === RESCHEDULE APPOINTMENT ===
        elif intent == "RESCHEDULE_APPOINTMENT":
            try:
                details = self.extract_reschedule_details(query)
                if not details.get("appointment_id"):
                    return {
                        "human_response": "I need an appointment ID to reschedule.",
                        "raw_data": {"error": "Missing appointment_id"}
                    }
                
                result = await self.client.call("reschedule_appointment", details)
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === CANCEL APPOINTMENT ===
        elif intent == "CANCEL_APPOINTMENT":
            try:
                details = self.extract_appointment_id(query)
                if not details.get("appointment_id"):
                    return {
                        "human_response": "I need an appointment ID to cancel.",
                        "raw_data": {"error": "Missing appointment_id"}
                    }
                
                result = await self.client.call("cancel_appointment", {"appointment_id": details["appointment_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET MEDICAL HISTORY ===
        elif intent == "GET_MEDICAL_HISTORY":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view medical history.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_medical_history", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET PRESCRIPTIONS ===
        elif intent == "GET_PRESCRIPTIONS":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view prescriptions.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_prescriptions", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET LAB REPORTS ===
        elif intent == "GET_LAB_REPORTS":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view lab reports.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_lab_reports", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET APPOINTMENT REMINDERS ===
        elif intent == "GET_APPOINTMENT_REMINDERS":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to view appointment reminders.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_appointment_reminders", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === GET HEALTH SUMMARY ===
        elif intent == "GET_HEALTH_SUMMARY":
            try:
                details = self.extract_patient_id(query)
                if not details.get("patient_id"):
                    return {
                        "human_response": "I need a patient ID to generate health summary.",
                        "raw_data": {"error": "Missing patient_id"}
                    }
                
                result = await self.client.call("get_health_summary", {"patient_id": details["patient_id"]})
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === PROCESS CONSULTATION ===
        elif intent == "PROCESS_CONSULTATION":
            try:
                details = self.extract_consultation_details(query)
                
                if not details.get("appointment_id"):
                    return {
                        "human_response": "I need an appointment ID to process the consultation. Please provide the appointment ID.",
                        "raw_data": {"error": "Missing appointment_id"}
                    }
                
                result = await self.client.call("process_consultation", details)
                return {"human_response": self.generate_human_response(result, intent), "raw_data": result}
            except Exception as e:
                error_result = {"error": str(e)}
                return {"human_response": self.generate_human_response(error_result, intent), "raw_data": error_result}

        # === UNKNOWN INTENT ===
        else:
            return {
                "human_response": "I can help with registering patients, searching doctors, booking appointments, and managing medical records.",
                "raw_data": {"error": "Unsupported intent"},
            }