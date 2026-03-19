from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

from main import (
    register_patient, get_patient_profile, update_patient_profile,
    search_doctors, get_doctor_info, book_appointment,
    get_my_appointments, get_appointment_context, reschedule_appointment, cancel_appointment,
    get_medical_history, get_prescriptions, get_lab_reports,
    get_appointment_reminders, get_health_summary
)

# Make ai_mcp package importable when running from hospital-mcp folder.
AI_MCP_PATH = Path(__file__).resolve().parent.parent / "ai_mcp"
if str(AI_MCP_PATH) not in sys.path:
    sys.path.insert(0, str(AI_MCP_PATH))
AI_MCP_MCP_PATH = AI_MCP_PATH / "mcp"
if str(AI_MCP_MCP_PATH) not in sys.path:
    sys.path.insert(0, str(AI_MCP_MCP_PATH))

app = FastAPI(title="Hospital MCP HTTP Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/tool/register_patient")
async def register_patient_endpoint(request: Request):
    try:
        body = await request.json()
        print(f"Received: {body}")
        result = await register_patient(**body)
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_patient_profile")
async def get_patient_profile_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_patient_profile(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/update_patient_profile")
async def update_patient_profile_endpoint(request: Request):
    try:
        body = await request.json()
        result = await update_patient_profile(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/search_doctors")
async def search_doctors_endpoint(request: Request):
    try:
        body = await request.json()
        print(f"Search doctors - Received body: {body}")  # ← Add this
        result = await search_doctors(**body)
        print(f"Search doctors - Result: {result}")  # ← Add this
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

        

@app.post("/tool/get_doctor_info")
async def get_doctor_info_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_doctor_info(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/book_appointment")
async def book_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        result = await book_appointment(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_my_appointments")
async def get_my_appointments_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_my_appointments(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_appointment_context")
async def get_appointment_context_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_appointment_context(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/reschedule_appointment")
async def reschedule_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        result = await reschedule_appointment(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/cancel_appointment")
async def cancel_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        result = await cancel_appointment(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_medical_history")
async def get_medical_history_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_medical_history(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_prescriptions")
async def get_prescriptions_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_prescriptions(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_lab_reports")
async def get_lab_reports_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_lab_reports(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_appointment_reminders")
async def get_appointment_reminders_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_appointment_reminders(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_health_summary")
async def get_health_summary_endpoint(request: Request):
    try:
        body = await request.json()
        result = await get_health_summary(**body)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Hospital MCP Server"}


from fastapi.middleware.cors import CORSMiddleware

# Add after app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")

        try:
            from mcp.controller import MCPController
            from mcp.executor import MCPExecutor
        except ModuleNotFoundError:
            from controller import MCPController
            from executor import MCPExecutor
        
        mcp = MCPController()
        mcp_executor = MCPExecutor()
        
        action = mcp.decide(query)
        
        if action == "RUN_MCP":
            result = mcp_executor.execute(
                intent=mcp.intent_classifier.classify(query),
                query=query
            )
            return result
        else:
            return {
                "human_response": "I can help you with registering patients, searching doctors, and booking appointments!",
                "raw_data": {}
            }
            
    except Exception as e:
        return {
            "human_response": f"Sorry, I encountered an error: {str(e)}",
            "raw_data": {"error": str(e)}
        }


if __name__ == "__main__":
    print("Starting HTTP server on http://localhost:3333")
    uvicorn.run(app, host="localhost", port=3333)
