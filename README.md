# 🏥 AI-Powered Hospital Management Chatbot

An intelligent hospital management system with a conversational AI interface powered by Ollama, featuring patient registration, doctor search, appointment booking, and AI-powered consultation processing with automated prescription generation.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)
![Ollama](https://img.shields.io/badge/Ollama-qwen2.5:3b-orange.svg)

## ✨ Features

### 🤖 AI Chatbot Interface
- Natural language processing using Ollama (qwen2.5:3b)
- Intent classification for 14 different hospital operations
- Context-aware responses with human-friendly language
- Real-time chat interface with quick action buttons

### 👥 Patient Management
- Patient registration with complete medical history
- Profile viewing and updates
- Blood group and allergy tracking
- Emergency contact management

### 👨‍⚕️ Doctor Management
- Doctor search by specialization, name, or department
- Detailed doctor profiles with availability
- Department-wise organization

### 📅 Appointment System
- Smart appointment booking with conflict detection
- View upcoming and past appointments
- Reschedule and cancel appointments
- Automated appointment reminders

### 🎙️ AI Consultation Agent
- **Audio transcription** using Whisper
- **Speaker diarization** (Doctor/Patient separation)
- **Prescription extraction** using Ollama NLP
- **Automated PDF generation** for prescriptions
- **Email delivery** to patients
- Supports multiple audio formats (WAV, MP3, M4A, FLAC)

### 📊 Medical Records
- Medical history tracking
- Prescription management
- Lab report storage
- Health summary generation

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│            (Chat Interface + Quick Actions)              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Chat Server (Port 3333)                     │
│         FastAPI + Ollama NLP + MCP Controller            │
└────────┬───────────────────────────────────┬────────────┘
         │                                   │
         ↓                                   ↓
┌────────────────────┐          ┌──────────────────────────┐
│   MongoDB Atlas    │          │  Consultation Agent      │
│  (Hospital Data)   │          │      (Port 8001)         │
│  - Patients        │          │  - Whisper Transcription │
│  - Doctors         │          │  - Speaker Diarization   │
│  - Appointments    │          │  - Ollama Extraction     │
│  - Prescriptions   │          │  - PDF Generation        │
│  - Lab Reports     │          │  - Email Delivery        │
└────────────────────┘          └──────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance async web framework
- **MongoDB** - NoSQL database for healthcare data
- **Motor** - Async MongoDB driver
- **Ollama** - Local LLM (qwen2.5:3b) for NLP
- **LangChain** - LLM orchestration

### Consultation Agent
- **Whisper** - Audio transcription
- **Pyannote** - Speaker diarization
- **ReportLab** - PDF generation
- **SMTP** - Email delivery

### Frontend
- **React 18** - UI framework
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Axios** - HTTP client

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (or local MongoDB)
- Ollama installed locally
- FFmpeg (for audio processing)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hospital-chatbot.git
cd hospital-chatbot
```

### 2. Install Ollama and Model
```bash
# Install Ollama (Windows)
winget install Ollama.Ollama

# Pull the model
ollama pull qwen2.5:3b
```

### 3. Install FFmpeg (for audio processing)
```bash
# Windows (using Chocolatey)
choco install ffmpeg

# Or download from: https://www.gyan.dev/ffmpeg/builds/
```

### 4. Backend Setup
```bash
cd hospital-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 5. Consultation Agent Setup
```bash
cd consultation-agent

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 6. Frontend Setup
```bash
cd hospital-chatbot-ui

# Install dependencies
npm install
```

## ⚙️ Configuration

### Backend `.env` (`hospital-mcp/.env`)
```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=hospital_db
CONSULTATION_AGENT_URL=http://localhost:8001
OLLAMA_MODEL=qwen2.5:3b
```

### Consultation Agent `.env` (`consultation-agent/.env`)
```env
OLLAMA_MODEL=qwen2.5:3b
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=hospital_db
MCP_BASE_URL=http://localhost:3333
WHISPER_MODEL=base
PYANNOTE_AUTH_TOKEN=your_huggingface_token
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
SMTP_USE_TLS=true
```

## 🎯 Running the Application

### Terminal 1: Start Ollama
```bash
ollama serve
```

### Terminal 2: Start Chat Server
```bash
cd hospital-mcp
python chat_server.py
```

Server will start at: `http://localhost:3333`

### Terminal 3: Start Consultation Agent (Optional)
```bash
cd consultation-agent
python agent_main.py
```

Agent will start at: `http://localhost:8001`

### Terminal 4: Start React Frontend
```bash
cd hospital-chatbot-ui
npm start
```

Frontend will open at: `http://localhost:3000`

## 📖 Usage Examples

### Register a Patient
```
register patient John Doe, 35 years old, male, contact 9876543210, email john@example.com, blood group O+
```

### Search for Doctors
```
find cardiologists
```

### Book an Appointment
```
book appointment for patient ID 69ad1523355efac52b5ad151 with Dr. Sarah Johnson on 2026-03-20 at 14:00 for chest pain
```

### View Appointments
```
show my appointments for patient 69ad1523355efac52b5ad151
```

### Process Consultation Audio
```
process consultation for appointment 67890abc with audio file consultation_1.wav
```

## 🗂️ Project Structure
```
hospital-chatbot/
├── hospital-mcp/                 # Backend server
│   ├── ai_mcp/
│   │   └── mcp/
│   │       ├── controller.py     # Request router
│   │       ├── intent_classifier.py
│   │       ├── action_router.py
│   │       ├── executor.py       # Tool executor
│   │       └── direct_client.py  # MongoDB client
│   ├── chat_server.py           # FastAPI server
│   ├── .env
│   └── requirements.txt
│
├── consultation-agent/          # AI consultation processor
│   ├── agent_main.py           # FastAPI server
│   ├── transcription.py        # Whisper integration
│   ├── diarization.py          # Speaker separation
│   ├── prescription_extractor.py # Ollama NLP
│   ├── pdf_generator.py        # PDF creation
│   ├── email_sender.py         # SMTP delivery
│   ├── mcp_client.py           # Appointment context
│   ├── audio_samples/          # Sample audio files
│   ├── generated_prescriptions/ # Output PDFs
│   ├── .env
│   └── requirements.txt
│
└── hospital-chatbot-ui/        # React frontend
    ├── src/
    │   ├── components/
    │   │   └── ChatInterface.jsx
    │   ├── App.js
    │   └── index.js
    ├── package.json
    └── tailwind.config.js
```

## 🔧 API Endpoints

### Chat Server (Port 3333)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Main chat interface |
| `/tool/register_patient` | POST | Register new patient |
| `/tool/search_doctors` | POST | Search doctors |
| `/tool/book_appointment` | POST | Book appointment |
| `/tool/get_my_appointments` | POST | Get patient appointments |
| `/tool/get_patient_profile` | POST | Get patient profile |
| `/tool/update_patient_profile` | POST | Update patient info |
| `/tool/cancel_appointment` | POST | Cancel appointment |
| `/tool/reschedule_appointment` | POST | Reschedule appointment |
| `/tool/get_medical_history` | POST | Get medical records |
| `/tool/get_prescriptions` | POST | Get prescriptions |
| `/tool/get_lab_reports` | POST | Get lab reports |
| `/tool/get_appointment_reminders` | POST | Get upcoming appointments |
| `/tool/get_health_summary` | POST | Get health summary |
| `/health` | GET | Health check |

### Consultation Agent (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/consultation/process` | POST | Process consultation audio |
| `/health` | GET | Health check |

## 🧪 Testing

### Health Checks
```powershell
# Chat server
Invoke-RestMethod -Uri "http://localhost:3333/health"

# Consultation agent
Invoke-RestMethod -Uri "http://localhost:8001/health"
```

### Register Patient
```powershell
$body = @{
    query = "register patient Jane Smith, 28 years old, female, contact 9123456789"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3333/chat" -Method Post -Body $body -ContentType "application/json"
```

### Search Doctors
```powershell
$body = @{
    query = "find cardiologists"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3333/chat" -Method Post -Body $body -ContentType "application/json"
```

## 🐛 Troubleshooting

### Ollama Not Responding
```bash
# Check if Ollama is running
ollama list

# Restart Ollama
ollama serve
```

### FFmpeg Not Found
```bash
# Install FFmpeg
choco install ffmpeg

# Verify installation
ffmpeg -version
```

### MongoDB Connection Error
- Check your `MONGODB_URI` in `.env`
- Ensure IP whitelist includes your IP in MongoDB Atlas

### Port Already in Use
```bash
# Find process using port 3333
netstat -ano | findstr :3333

# Kill the process
taskkill /PID  /F
```

## 📊 Sample Data

The system includes sample doctors in the database:

- **Dr. Sarah Johnson** - Cardiology
- **Dr. Robert Williams** - Cardiology  
- **Dr. Emily Davis** - Pediatrics
- **Dr. Michael Brown** - Orthopedics
- **Dr. Lisa Anderson** - Dermatology
- **Dr. James Wilson** - Neurology

## 🔐 Security Notes

- Never commit `.env` files to version control
- Use environment variables for sensitive data
- Enable MongoDB IP whitelisting
- Use HTTPS in production
- Implement authentication for production use

## 🚧 Future Enhancements

- [ ] User authentication (JWT)
- [ ] Video consultation support
- [ ] Multi-language support
- [ ] Push notifications
- [ ] Insurance integration
- [ ] Billing system
- [ ] Admin dashboard
- [ ] Mobile app (React Native)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 👥 Contributors

- **Your Name** - Initial work

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [OpenAI Whisper](https://github.com/openai/whisper) - Audio transcription
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [React](https://react.dev/) - UI framework

## 📞 Support

For issues and questions:
- Email: iharishpandian2006@gmail.com

---

Made with ❤️ using AI and open-source technologies