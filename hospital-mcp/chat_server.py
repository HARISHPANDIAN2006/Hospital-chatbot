from fastapi import FastAPI, Request, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
import shutil

load_dotenv()

# Add ai_mcp to Python path
AI_MCP_PATH = Path(__file__).parent.parent / "ai_mcp"
sys.path.insert(0, str(AI_MCP_PATH))
AI_MCP_MCP_PATH = AI_MCP_PATH / "mcp"
sys.path.insert(0, str(AI_MCP_MCP_PATH))

app = FastAPI(title="Hospital Chat Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/hospital_db")

# ========== CHAT ENDPOINT ==========

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")
        
        print(f"Received query: {query}")
        
        # Import AI MCP modules
        try:
            from mcp.controller import MCPController
            from mcp.executor import MCPExecutor
        except ModuleNotFoundError:
            from controller import MCPController
            from executor import MCPExecutor
        
        mcp = MCPController()
        
        # Create executor
        mcp_executor = MCPExecutor()
        
        action = mcp.decide(query)
        print(f"Action decided: {action}")
        
        if action == "RUN_MCP":
            result = await mcp_executor.execute(
                intent=mcp.intent_classifier.classify(query),
                query=query
            )
            print(f"MCP Result: {result}")
            return result
        else:
            return {
                "human_response": "I can help you with:\n• Registering new patients\n• Searching for doctors\n• Booking appointments\n\nWhat would you like to do?",
                "raw_data": {"action": action}
            }
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        return {
            "human_response": f"Sorry, I encountered an error: {str(e)}",
            "raw_data": {"error": str(e)}
        }

@app.post("/upload-consultation-audio")
async def upload_consultation_audio(
    file: UploadFile = File(...),
    appointment_id: str = ""
):
    """Upload consultation audio file"""
    try:
        consultation_audio_dir = Path("../consultation-agent/audio_samples")
        consultation_audio_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"consultation_{appointment_id}.wav" if appointment_id else file.filename
        file_path = consultation_audio_dir / filename
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "success": True,
            "message": f"Audio uploaded: {filename}",
            "filename": filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Hospital Chat Server is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Hospital Chat Server"}

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 Hospital Chat Server - PostgreSQL Edition")
    print("=" * 60)
    print("Starting server on http://localhost:3333")
    print("React app should connect to this server")
    print(f"Database: PostgreSQL (localhost:5432/hospital_db)")
    print("=" * 60)
    print("\n📋 Available Tools:")
    print("  • register_patient")
    print("  • get_patient_profile")
    print("  • update_patient_profile")
    print("  • search_doctors")
    print("  • get_doctor_info")
    print("  • book_appointment")
    print("  • get_my_appointments")
    print("  • reschedule_appointment")
    print("  • cancel_appointment")
    print("  • get_medical_history")
    print("  • get_prescriptions")
    print("  • get_lab_reports")
    print("  • get_appointment_reminders")
    print("  • get_health_summary")
    print("  • process_consultation")
    print("=" * 60)
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=3333,
        timeout_keep_alive=120
    )