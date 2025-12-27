import os
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify

load_dotenv()

EVOLUTION_API_KEY = os.getenv('EVOLUTION_API_KEY')
EVOLUTION_API_URL = os.getenv('EVOLUTION_API_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-nano')
PROMPT = os.getenv('PROMPT', 'Responda de forma educada e objetiva.')
INSTANCE_NAME = os.getenv('INSTANCE_NAME', 'default')

app = Flask(__name__)

print("🚀 Bot iniciado!")
print(f"📡 Evolution API URL: {EVOLUTION_API_URL}")
print(f"🤖 Modelo OpenAI: {OPENAI_MODEL}")
print(f"📱 Instância: {INSTANCE_NAME}")

# Função para gerar resposta usando OpenAI
def gerar_resposta(mensagem):
    from openai import OpenAI
    print(f"🧠 Gerando resposta para: {mensagem[:50]}...")
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": mensagem}]
        )
        resposta = completion.choices[0].message.content
        print(f"   Resposta gerada: {resposta[:50]}...")
        return resposta
    except Exception as e:
        print(f"   Erro ao gerar resposta com OpenAI: {e}")
        return "Desculpe, não foi possível gerar uma resposta no momento."

# Função para enviar mensagem via Evolution API
def enviar_mensagem(numero, mensagem):
    print(f"📤 Enviando resposta para {numero}...")
    url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "number": numero,
        "text": mensagem
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"   Status: {response.status_code} - {response.text[:100]}")
        return response.status_code == 201 or response.status_code == 200
    except Exception as e:
        print(f"   Erro ao enviar: {e}")
        return False

# Webhook para receber mensagens da Evolution API
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print(f"📥 Webhook recebido: {data}")
    
    try:
        # Verifica se é uma mensagem recebida
        if data.get('event') == 'messages.upsert':
            message_data = data.get('data', {})
            
            # Ignora mensagens enviadas por mim mesmo
            if message_data.get('key', {}).get('fromMe'):
                return jsonify({"status": "ignored", "reason": "own message"}), 200
            
            # Extrai o número do remetente e o texto da mensagem
            remote_jid = message_data.get('key', {}).get('remoteJid', '')
            numero = remote_jid.replace('@s.whatsapp.net', '').replace('@g.us', '')
            
            # Extrai o texto da mensagem
            message = message_data.get('message', {})
            texto = message.get('conversation') or message.get('extendedTextMessage', {}).get('text', '')
            
            if texto:
                print(f"💬 Mensagem de {numero}: {texto}")
                
                # Gera resposta com IA
                resposta = gerar_resposta(texto)
                
                # Envia resposta
                enviar_mensagem(numero, resposta)
                
                return jsonify({"status": "processed"}), 200
            
        return jsonify({"status": "ignored"}), 200
    
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Rota de health check
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "online", "bot": "WhatsApp AI Agent"}), 200

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    print(f"🌐 Servidor rodando na porta {port}")
    app.run(host='0.0.0.0', port=port)
