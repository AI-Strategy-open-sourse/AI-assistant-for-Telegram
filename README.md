# AI-assistant-for-Telegram
This bot helps to form technical specifications for software development. Works in Telegram.

# Installation
1. Clone the repository:
```bash
git clone <URL-repo>
cd transcribe_bot
```

2. Create a virtual environment and activate it (Use python 3.11):
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

# Configuration
Add the ready account session to the as_human_userbot/sessions folder.
After installing and configuring dependencies, you can run the bot:
```bash
python as_human_bot.py
```

Add to env: 
```python
OPENAI_API_KEY = '' PROXY="" ASSISTANT=""
```
