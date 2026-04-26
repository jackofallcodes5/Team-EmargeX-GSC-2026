# Setup and Run Commands

Follow this step-by-step guide to install, configure, and launch the Sentinel Dispatch AI system from a fresh start.

## 1. Prepare Environment & Dependencies

Open your terminal or PowerShell in the root project directory (`c:\Challenge`):

```bash
# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# On Windows:
.\.venv\Scripts\activate
# On Mac/Linux:
# source .venv/bin/activate

# 3. Install all required dependencies
pip install -r requirements.txt
```

## 2. Setup the MySQL Database

1. Open your local MySQL instance (via MySQL Workbench or command line).
2. Execute the included SQL setup script to create the `sentinel_db` database and its tables:

```bash
# Connect to MySQL and run the script:
mysql -u root -p < database_setup.sql
```

## 3. Configure Environment Variables

Create or edit the `.env` file in the root directory to contain the following keys. Make sure you replace the placeholders with your actual API keys and passwords.

```env
# Primary AI Key (for conversation extraction and TTS responses)
GEMINI_API_KEY="your_api_key_here"

# Secondary AI Key (for parallel location-to-coordinate processing)
GEMINI_API_KEY_2="your_api_key_here" 

# MySQL Setup
DB_HOST="localhost"
DB_USER="root"
DB_PASSWORD="your_mysql_password_here"
DB_NAME="sentinel_db"
```
*(Note: You can use the same Gemini API key for both fields if you don't have two separate keys).*

## 4. Launch the Application

Ensure your virtual environment is still activated, then run the main GUI application:

```bash
python gui_main.py
```

### Important Notes on First Run:
* **Model Downloads:** The first time you execute the script, it will automatically download the required VOSK machine-learning models (approx 100MB). This may take a minute or two before the UI opens.
* **Audio Feedback:** The system uses your default microphone and speakers. If you aren't wearing headphones, the system's own Text-To-Speech (TTS) output might loop back into the microphone, causing the AI to transcribe itself. **Headphones are highly recommended!**
