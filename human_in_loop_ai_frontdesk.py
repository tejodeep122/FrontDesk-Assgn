# human_in_loop_ai_frontdesk

# Directory structure:
# - app/
#   - main.py (entrypoint)
#   - ai_agent.py (AI agent simulation)
#   - db.py (DB layer)
#   - supervisor_ui.py (simple Flask UI)
#   - knowledge_base.py (learned answers)
#   - request_model.py (data model)
# - README.md
# - requirements.txt

# ========== app/main.py ==========
from app.ai_agent import AIAgent
from app.supervisor_ui import start_supervisor_ui
import threading

if __name__ == "__main__":
    agent = AIAgent()

    def simulate_call(question):
        agent.handle_call(question)

    # Start UI in separate thread
    threading.Thread(target=start_supervisor_ui).start()

    # Simulate incoming call
    simulate_call("What are your business hours?")
    simulate_call("Do you offer pet grooming?")

# ========== app/ai_agent.py ==========
from app.db import create_help_request, update_help_request_status
from app.knowledge_base import KnowledgeBase
import uuid

class AIAgent:
    def __init__(self):
        self.kb = KnowledgeBase()

    def handle_call(self, question):
        answer = self.kb.lookup(question)
        if answer:
            print(f"AI: {answer}")
        else:
            print("AI: Let me check with my supervisor and get back to you.")
            req_id = str(uuid.uuid4())
            create_help_request(req_id, question)
            print(f"[TEXT TO SUPERVISOR]: Hey, I need help answering: '{question}' (Request ID: {req_id})")

    def respond_to_user(self, req_id, answer):
        print(f"[TEXT TO CUSTOMER]: {answer} (in response to {req_id})")
        self.kb.learn(req_id, answer)
        update_help_request_status(req_id, "Resolved")

# ========== app/db.py ==========
import time

HELP_REQUESTS = {}  # In-memory DB

# Format: {
#   req_id: {question, status, timestamp, answer}
# }

def create_help_request(req_id, question):
    HELP_REQUESTS[req_id] = {
        "question": question,
        "status": "Pending",
        "timestamp": time.time(),
        "answer": None
    }

def get_all_requests():
    return HELP_REQUESTS

def update_help_request_status(req_id, status):
    if req_id in HELP_REQUESTS:
        HELP_REQUESTS[req_id]["status"] = status

def save_answer(req_id, answer):
    if req_id in HELP_REQUESTS:
        HELP_REQUESTS[req_id]["answer"] = answer

# ========== app/supervisor_ui.py ==========
from flask import Flask, request, render_template_string, redirect
from app.db import get_all_requests, update_help_request_status, save_answer
from app.ai_agent import AIAgent

app = Flask(__name__)
agent = AIAgent()

HTML_TEMPLATE = '''
<h1>Supervisor Panel</h1>
{% for req_id, req in requests.items() %}
    <div style="margin-bottom: 20px;">
        <b>ID:</b> {{ req_id }}<br>
        <b>Question:</b> {{ req['question'] }}<br>
        <b>Status:</b> {{ req['status'] }}<br>
        {% if req['status'] == 'Pending' %}
        <form method="POST" action="/respond">
            <input type="hidden" name="req_id" value="{{ req_id }}">
            <input type="text" name="answer" placeholder="Type your answer here" required>
            <button type="submit">Submit Answer</button>
        </form>
        {% else %}
            <b>Answer:</b> {{ req['answer'] }}<br>
        {% endif %}
    </div>
{% endfor %}
'''

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, requests=get_all_requests())

@app.route("/respond", methods=["POST"])
def respond():
    req_id = request.form["req_id"]
    answer = request.form["answer"]
    save_answer(req_id, answer)
    agent.respond_to_user(req_id, answer)
    return redirect("/")

def start_supervisor_ui():
    app.run(debug=False, port=5001)

# ========== app/knowledge_base.py ==========
from app.db import get_all_requests

class KnowledgeBase:
    def __init__(self):
        self.facts = {}
        self.load_facts()

    def load_facts(self):
        for req_id, req in get_all_requests().items():
            if req["status"] == "Resolved":
                self.facts[req["question"].lower()] = req["answer"]

    def lookup(self, question):
        return self.facts.get(question.lower())

    def learn(self, req_id, answer):
        for qid, req in get_all_requests().items():
            if qid == req_id:
                self.facts[req["question"].lower()] = answer
                break

# ========== app/request_model.py ==========
# (Note: This file is a placeholder in case you want to use a class-based model later.)

# ========== README.md ==========
# Human-in-the-Loop AI Supervisor (Frontdesk Engineering Test)

## Setup
```bash
pip install -r requirements.txt
python app/main.py
```

Then open `http://localhost:5001` to access the Supervisor UI.

## Features
- Simulated AI agent receives questions
- If unknown, escalates to supervisor via console log
- Supervisor can respond via UI
- AI immediately replies to customer and learns the answer

## Design Decisions
- In-memory DB for speed; switch to DynamoDB/Firestore for production
- Modular files: AI agent, DB, UI, and knowledge base separated
- Simple timeout not implemented, but easy to add via timestamp

# ========== requirements.txt ==========
flask==2.3.3
