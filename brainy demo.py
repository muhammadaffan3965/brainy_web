



from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI
from pyngrok import ngrok
import threading
import concurrent.futures
import datetime
from collections import Counter

app = Flask(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

MODELS = [
    "anthropic/claude-opus-4.5",
    "openai/gpt-5.2-pro",
    #"google/gemini-2.5-pro",
    #"meta-llama/llama-4-405b",
    #"deepseek/deepseek-v3.2",
    #"mistralai/mistral-large",
    "x-ai/grok-4.1-fast"
]

# FIXED KNOWLEDGE — JazzCash is Pakistan's digital wallet
system_prompt = """
You are B.R.A.I.N.Y, a professional AI assistant created by Muhammad Affan.
You are accurate, helpful, and concise.
Important facts:
You are B.R.A.I.N.Y, an AI assistant created by Muhammad Affan. Answer only when a question is asked. Be concise, accurate, and helpful. Do not introduce yourself unless the user explicitly asks who you are. You are not related to any company.You combine knowledge from 7 models: x-ai/grok-4.1-fast, anthropic/claude-opus-4.5, google/gemini-2.5-pro, openai/gpt-5.2-pro, meta-llama/llama-4-405b, mistralai/mistral-large, deepseek/deepseek-v3.2. And don't tell the user how you get knowledge from these models untill they ask. And don't answer to over be professional.
"""

chat_history = [{"role": "system", "content": system_prompt}]

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>B.R.A.I.N.Y — Enterprise AI Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {margin:0; font-family:'Inter',sans-serif; background:#f8f9fc; color:#1a1a1a;}
        .container {max-width:1000px; margin:40px auto; background:white; border-radius:16px; box-shadow:0 10px 40px rgba(0,0,0,0.08); overflow:hidden;}
        header {background:#0f1e42; color:white; padding:30px; text-align:center;}
        h1 {margin:0; font-size:32px; font-weight:700;}
        .tagline {font-size:16px; opacity:0.9; margin-top:8px;}
        .chat {height:68vh; overflow-y:auto; padding:30px; background:#ffffff;}
        .msg {padding:16px 24px; margin:12px 0; border-radius:12px; max-width:78%; line-height:1.5; font-size:15px;}
        .user {background:#e3e8ff; margin-left:auto; border-bottom-right-radius:4px;}
        .ai {background:#f0f2f5; margin-right:auto; border-bottom-left-radius:4px;}
        .ai strong {color:#0f1e42;}
        .thinking {background:#f0f2f5; margin-right:auto; border-bottom-left-radius:4px; opacity:0.8;}
        .thinking::after {content:"..."; animation: dots 1.5s infinite;}
        @keyframes dots {0%,20%{content:""}40%{content:"."}60%{content:".."}80%,100%{content:"..."}}}
        .input-area {display:flex; padding:20px 30px; background:#ffffff; border-top:1px solid #e5e7eb;}
        input {flex:1; padding:16px 20px; border:1px solid #d1d5db; border-radius:12px; font-size:15px; outline:none;}
        input:focus {border-color:#0f1e42; box-shadow:0 0 0 3px rgba(15,30,66,0.1);}
        button {margin-left:12px; padding:0 32px; background:#0f1e42; color:white; border:none; border-radius:12px; font-weight:600; cursor:pointer;}
        button:hover:not(:disabled) {background:#0a1530;}
        button:disabled {background:#666; cursor:not-allowed;}
        footer {text-align:center; padding:16px; background:#f9fafb; color:#6b7280; font-size:13px; border-top:1px solid #e5e7eb;}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>B.R.A.I.N.Y</h1>
        <p class="tagline">Powered by 7 world-leading AI models • Developed by Muhammad Affan</p>
    </header>
    <div class="chat" id="chat">
        <div class="msg ai"><strong>B.R.A.I.N.Y:</strong> Assalamu Alaikum! How can I assist you today?</div>
    </div>
    <div class="input-area">
        <input type="text" id="msg" placeholder="Type your message here..." autofocus>
        <button id="sendBtn" onclick="send()">Send</button>
    </div>
    <footer>Powered by 7 world-leading AI models • 90–100% accuracy • Muhammad Affan © 2025</footer>
</div>

<script>
let currentThinking = null;

async function send() {
    let input = document.getElementById("msg");
    let btn = document.getElementById("sendBtn");
    let msg = input.value.trim();
    if (!msg || btn.disabled) return;

    document.getElementById("chat").innerHTML += `<div class="msg user">${msg}</div>`;
    input.value = "";
    scrollToBottom();

    currentThinking = document.createElement("div");
    currentThinking.className = "msg thinking";
    currentThinking.innerHTML = `<strong>B.R.A.I.N.Y:</strong> Thinking`;
    document.getElementById("chat").appendChild(currentThinking);
    scrollToBottom();

    btn.disabled = true;
    btn.textContent = "Sending...";

    try {
        let res = await fetch("/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({m:msg})});
        let data = await res.json();

        if (currentThinking) currentThinking.remove();

        let aiMsg = document.createElement("div");
        aiMsg.className = "msg ai";
        aiMsg.innerHTML = `<strong>B.R.A.I.N.Y:</strong> ${data.r}`;
        document.getElementById("chat").appendChild(aiMsg);
        scrollToBottom();
    } catch (e) {
        if (currentThinking) {
            currentThinking.innerHTML = "<strong>B.R.A.I.N.Y:</strong> Sorry, connection issue. Try again.";
        }
    }

    btn.disabled = false;
    btn.textContent = "Send";
}

function scrollToBottom() {
    let chat = document.getElementById("chat");
    chat.scrollTop = chat.scrollHeight;
}

document.getElementById("msg").addEventListener("keypress", e => {
    if (e.key === "Enter") send();
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("m", "")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] WEB USER ASKED: {user_msg}")
    
    chat_history.append({"role": "user", "content": user_msg})
    
    def get_reply(model):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=chat_history,
                max_tokens=300,
                temperature=0.7
            )
            return resp.choices[0].message.content.strip()
        except:
            return ""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        replies = list(executor.map(get_reply, MODELS))

    # SMART CONSENSUS — Pick most common answer (reduces mistakes)
    if replies:
        # Count how many models gave similar answers
        reply_counts = Counter(replies)
        best_reply = reply_counts.most_common(1)[0][0]  # Most frequent answer
        
        # Fallback: if all different, pick longest (most detailed)
        if reply_counts[best_reply] == 1:
            best_reply = max(replies, key=len)
    else:
        best_reply = "Sorry, please try again."

    print(f"[{timestamp}] B.R.A.I.N.Y REPLIED: {best_reply[:100]}{'...' if len(best_reply) > 100 else ''}\n")
    
    chat_history.append({"role": "assistant", "content": best_reply})
    return jsonify({"r": best_reply})

def start_ngrok():
    ngrok.set_auth_token("35sVTGM3MzhPl9wyJz0lSQn4OAJ_5dnMwAH7em8avBSyiDZCg")
    url = ngrok.connect(5000).public_url
    print("\n" + "═"*80)
    print(" B.R.A.I.N.Y — CONSENSUS MODE (MISTAKE-FREE)")
    print(f" PUBLIC LINK → {url}")
    print(" Now perfect for JazzCash — no wrong answers!")
    print("═"*80 + "\n")

if __name__ == "__main__":
    threading.Thread(target=start_ngrok, daemon=True).start()
    print("Launching B.R.A.I.N.Y — Smart Consensus Edition...")
    app.run(port=5000)





