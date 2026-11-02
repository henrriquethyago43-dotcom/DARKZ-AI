
import os
import json
import requests
from flask import Flask, request, jsonify, render_template_string, send_from_directory

app = Flask(__name__)

MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "memory",
    "chat_history.json"
)

os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#c21c1c">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="/manifest.json">
<title>DARKZ AI</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:radial-gradient(circle at 50% 25%,#240707,#080808 55%);
 color:white;font-family:Arial,sans-serif;min-height:100vh
}
header{
 text-align:center;padding:25px 10px 15px;color:#ff3030;
 font-size:30px;font-weight:bold;letter-spacing:7px;
 text-shadow:0 0 15px #ff2020
}
.circle{
 width:155px;height:155px;border-radius:50%;margin:28px auto;
 border:2px solid #ff3030;display:flex;align-items:center;
 justify-content:center;font-size:55px;color:#fff;
 box-shadow:0 0 15px #ff2020, inset 0 0 25px #8b1010;
 animation:pulse 2s infinite ease-in-out;position:relative
}
.circle:before,.circle:after{
 content:"";position:absolute;border:1px solid #a51b1b;
 border-radius:50%;inset:-12px;animation:spin 8s linear infinite
}
.circle:after{inset:-23px;border-style:dashed;animation-direction:reverse}
@keyframes pulse{
 0%,100%{box-shadow:0 0 15px #ff2020,inset 0 0 20px #8b1010}
 50%{box-shadow:0 0 38px #ff2020,inset 0 0 35px #c21c1c}
}
@keyframes spin{to{transform:rotate(360deg)}}
#status{
 text-align:center;color:#ff7777;font-size:12px;
 letter-spacing:3px;margin:12px
}
#chat{
 height:38vh;overflow-y:auto;padding:15px;
 border-top:1px solid #421010;border-bottom:1px solid #421010;
 background:#090909aa
}
.msg{
 padding:13px;margin:10px 0;border-radius:12px;
 background:linear-gradient(120deg,#1c1111,#111);
 border-left:3px solid #ff3030;
 box-shadow:0 0 10px #300909;
 white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.5
}
input{
 flex:1;min-width:0;padding:15px;background:#151515;
 color:white;border:1px solid #762020;border-radius:10px;
 outline:none
}
input:focus{border-color:#ff3030;box-shadow:0 0 10px #8b1010}
button{
 padding:14px;background:#b71919;color:white;border:0;
 border-radius:10px;font-weight:bold
}
button:active{background:#ff3030}
.controls{display:flex;gap:7px;padding:12px}

body.state-listening .circle {
 animation-duration:.45s;
 box-shadow:0 0 45px #ff3030,inset 0 0 35px #ff3030;
}
body.state-thinking .circle {
 animation-duration:.7s;
 box-shadow:0 0 55px #ff3030,inset 0 0 45px #c21c1c;
}
body.state-speaking .circle {
 animation-duration:1.1s;
 box-shadow:0 0 65px #ff3030,inset 0 0 40px #ff2020;
}
.system-panel {
 display:flex;justify-content:center;gap:9px;flex-wrap:wrap;
 padding:12px;margin:8px 12px 15px;
 border:1px solid #421010;border-radius:12px;
 background:#100b0b;
}
.system-item {
 color:#ff7777;font-size:10px;letter-spacing:1px;
 padding:7px;
}
.system-item span {color:#fff}

</style>
</head>
<body>
<header>DARKZ AI</header>
<div class="circle"><span>◉</span></div>
<div id="status">SISTEMA INICIALIZADO</div>
<div class="system-panel">
 <div class="system-item">IA: <span>ONLINE</span></div>
 <div class="system-item">MEMÓRIA: <span>ATIVA</span></div>
 <div class="system-item">VOZ: <span>ATIVA</span></div>
</div>

<div id="chat">
<div class="msg">DARKZ: Olá! Sua memória está ativa.</div>
</div>
<div class="controls">
<input id="msg" placeholder="Fale comigo...">
<button id="micBtn" onclick="listen()">🎙️</button>
<button id="sendBtn" onclick="send()">ENVIAR</button>
</div>
<script>

function setState(state){
 const status=document.getElementById('status');
 document.body.classList.remove(
  'state-listening','state-thinking','state-speaking'
 );
 const labels={
  online:'SISTEMA ONLINE',
  listening:'DARKZ ESTÁ OUVINDO...',
  thinking:'DARKZ ESTÁ PENSANDO...',
  speaking:'DARKZ ESTÁ RESPONDENDO...'
 };
 if(state!=='online') document.body.classList.add('state-'+state);
 status.textContent=labels[state] || labels.online;
}

async function send(){
 const input=document.getElementById('msg');
 const chat=document.getElementById('chat');
 const status=document.getElementById('status');
 const button=document.getElementById('sendBtn');
 const message=input.value.trim();
 if(!message)return;

 chat.innerHTML+='<div class="msg">VOCÊ: '+escapeHTML(message)+'</div>';
 input.value='';
 button.disabled=true;
 setState('thinking');

 try {
  const r=await fetch('/chat',{
   method:'POST',
   headers:{'Content-Type':'application/json'},
   body:JSON.stringify({message})
  });
  const data=await r.json();
  chat.innerHTML+='<div class="msg">DARKZ: '+escapeHTML(data.reply || 'Sem resposta.')+'</div>';
  falar(data.reply || 'Sem resposta.');
 } catch(e) {
  setState('online');
  chat.innerHTML+='<div class="msg">DARKZ: Erro de conexão.</div>';
 }

 button.disabled=false;
 chat.scrollTop=chat.scrollHeight;
}

function falar(texto){
 if(!window.speechSynthesis){setState('online');return;}
 window.speechSynthesis.cancel();
 const voz=new SpeechSynthesisUtterance(texto);
 voz.onstart=()=>setState('speaking');
 voz.onend=()=>setState('online');
 voz.onerror=()=>setState('online');
 voz.lang="pt-BR";
 voz.rate=0.95;
 voz.pitch=0.85;
 const vozes=window.speechSynthesis.getVoices();
 const pt=vozes.find(v=>v.lang.toLowerCase().startsWith("pt-br"));
 if(pt) voz.voice=pt;
 window.speechSynthesis.speak(voz);
}

function escapeHTML(s){
 return String(s).replace(/[&<>"']/g,c=>({
 '&':'&amp;','<':'&lt;','>':'&gt;',
 '"':'&quot;',"'":'&#39;'
 }[c]));
}function listen(){
 const status=document.getElementById('status');

 const SpeechRecognition =
 window.SpeechRecognition || window.webkitSpeechRecognition;

 if(!SpeechRecognition){
  status.textContent='RECONHECIMENTO DE VOZ INDISPONIVEL';
  return;
 }

 const recognition=new SpeechRecognition();
 recognition.lang='pt-BR';
 recognition.continuous=false;
 recognition.interimResults=false;

 recognition.onstart=()=>{
  setState('listening');
 };

 recognition.onresult=(event)=>{
  document.getElementById('msg').value=
  event.results[0][0].transcript;
  send();
 };

 recognition.onerror=()=>{
  setState('online');
 };

 recognition.onend=()=>{
  if(document.body.classList.contains('state-listening'))setState('online');
 };

 recognition.start();
}

document.getElementById('msg').addEventListener('keydown',e=>{
 if(e.key==='Enter')send();
});
</script>
</body>
</html>
"""

def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
            return history if isinstance(history, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_memory(history):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)

@app.route("/manifest.json")
def manifest():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "manifest.json",
        mimetype="application/manifest+json"
    )

@app.route("/logo-darkz.png")
def logo_darkz():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "logo-darkz.png",
        mimetype="image/png"
    )

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify(reply="Não recebi sua mensagem.")

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        return jsonify(reply="Chave OpenRouter não carregada.")

    history = load_memory()

    history.append({
        "role": "user",
        "content": message
    })

    # Usa as últimas 20 mensagens como contexto
    recent_history = history[-20:]

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openrouter/free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Você é DARKZ, um assistente inteligente, "
                            "prestativo e direto. Responda em português "
                            "brasileiro. Use o histórico da conversa "
                            "para manter o contexto e lembrar do que "
                            "o usuário contou anteriormente."
                        )
                    }
                ] + recent_history
            },
            timeout=90
        )

        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        history.append({
            "role": "assistant",
            "content": reply
        })

        save_memory(history[-100:])

        return jsonify(reply=reply)

    except requests.exceptions.RequestException as e:
        print("ERRO OPENROUTER:", str(e))
        return jsonify(
            reply="Falha na conexão com a IA. Verifique a internet ou os limites da API."
        )

    except Exception as e:
        print("ERRO DARKZ:", str(e))
        return jsonify(reply="Erro ao processar sua mensagem.")

if __name__ == "__main__":
    print("DARKZ AI INICIADO - MEMORIA ATIVA")
    app.run(host="127.0.0.1", port=5000, debug=False)
