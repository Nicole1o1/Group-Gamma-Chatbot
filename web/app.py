"""Gamma Chatbot – Flask web application."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from web.db import (
    init_db, create_user, verify_user, get_user_by_id,
    save_chat, get_user_chats,
    get_total_users, get_total_chats, get_frequent_questions,
    get_recent_chats, get_chats_per_day, get_avg_answer_length,
)
from rag.pipeline import RAGPipeline
from rag.generator import generate_answer
from web.whatsapp_infobip import (
    extract_inbound_text_messages,
    is_whatsapp_configured,
    load_whatsapp_config,
    send_whatsapp_text,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "gamma-chatbot-secret-key-change-in-production"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Pipeline (loaded once)
pipeline = None


def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = RAGPipeline()
    return pipeline


def build_answer(question: str) -> str:
    """Run retrieval + generation for one question."""
    pipe = get_pipeline()
    context = pipe.retrieve(question)
    if not context:
        from rag.fallback import build_fallback_response

        return build_fallback_response(question)
    return generate_answer(question, context, pipe.config.llm_model)


class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict["id"]
        self.username = user_dict["username"]
        self.role = user_dict["role"]


@login_manager.user_loader
def load_user(user_id):
    data = get_user_by_id(int(user_id))
    if data:
        return User(data)
    return None


# ── Auth routes ──────────────────────────────────────────────────

@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("dashboard"))
        return redirect(url_for("chat"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user_data = verify_user(username, password)
        if user_data:
            login_user(User(user_data))
            return redirect(url_for("index"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        role = request.form.get("role", "student")
        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif role not in ("student", "admin"):
            flash("Invalid role.", "error")
        else:
            user_id = create_user(username, password, role)
            if user_id:
                user_data = get_user_by_id(user_id)
                login_user(User(user_data))
                return redirect(url_for("index"))
            else:
                flash("Username already taken.", "error")
    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ── Student chat ─────────────────────────────────────────────────

@app.route("/chat")
@login_required
def chat():
    history = get_user_chats(current_user.id)
    return render_template("chat.html", history=history)


@app.route("/api/ask", methods=["POST"])
@login_required
def api_ask():
    data = request.get_json()
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    answer = build_answer(question)
    save_chat(current_user.id, question, answer)
    return jsonify({"answer": answer})


@app.route("/api/whatsapp/status")
def whatsapp_status():
    cfg = load_whatsapp_config()
    return jsonify(
        {
            "configured": is_whatsapp_configured(),
            "base_url": cfg["base_url"],
            "sender": cfg["sender"],
        }
    )


@app.route("/webhooks/infobip/whatsapp", methods=["POST"])
def infobip_whatsapp_webhook():
    # Optional shared-secret validation for webhook protection
    expected_token = os.getenv("INFOBIP_WEBHOOK_TOKEN", "").strip()
    if expected_token:
        provided = request.headers.get("X-Webhook-Token", "").strip()
        if provided != expected_token:
            return jsonify({"error": "Unauthorized webhook token"}), 401

    if not is_whatsapp_configured():
        return jsonify({"error": "WhatsApp integration not configured"}), 500

    payload = request.get_json(silent=True) or {}
    inbound = extract_inbound_text_messages(payload)
    if not inbound:
        return jsonify({"status": "ignored", "reason": "no text messages"}), 200

    processed = []
    for msg in inbound:
        question = msg["text"]
        recipient = msg["from"]
        answer = build_answer(question)
        status_code, provider_response = send_whatsapp_text(recipient, answer)
        processed.append(
            {
                "to": recipient,
                "status_code": status_code,
                "ok": 200 <= status_code < 300,
                "provider": provider_response,
            }
        )

    return jsonify({"status": "processed", "count": len(processed), "results": processed}), 200


# ── Admin dashboard ──────────────────────────────────────────────

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        flash("Access denied.", "error")
        return redirect(url_for("chat"))
    stats = {
        "total_users": get_total_users(),
        "total_chats": get_total_chats(),
        "avg_answer_len": get_avg_answer_length(),
        "faq": get_frequent_questions(10),
        "recent": get_recent_chats(20),
        "daily": get_chats_per_day(14),
    }
    return render_template("dashboard.html", stats=stats)


if __name__ == "__main__":
    init_db()
    print("Loading pipeline...")
    get_pipeline()
    print("Pipeline ready. Starting Gamma Chatbot...")
    app.run(host="0.0.0.0", port=7860, debug=False)
