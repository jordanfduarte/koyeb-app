import json
import os
import ssl
import time
from flask import Flask, jsonify, request
from websocket import create_connection

app = Flask(__name__)

# URL idêntica à do código JS
ACHEX_WSS_URL = "wss://ws.achex.ca/"
USER_ID = "jordan@1107"
USER_PASS = "142536"
TARGET_ID = "arduino@1107"


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  ws = None
  try:
    # 1. Trata o parâmetro 'comando' recebido
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Conecta ao WebSocket simetrizando o handshake do navegador
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    ws = create_connection(
        ACHEX_WSS_URL,
        timeout=10,
        sslopt={"cert_reqs": ssl.CERT_NONE, "check_hostname": False},
        header=["Origin: https://ws.achex.ca"],
    )

    # 3. Envia o payload de autenticação exatamente como no JS (socket.send)
    auth_payload = json.dumps({"setID": USER_ID, "passwd": USER_PASS})
    ws.send(auth_payload)

    # 4. Aguarda a resposta do servidor ("auth": "ok") assim como no eventListener('message')
    autenticado = False
    inicio = time.time()

    while time.time() - inicio < 5:  # Timeout de 5s para autenticar
      resposta_raw = ws.recv()
      if resposta_raw:
        resposta = json.loads(resposta_raw)
        # Verifica se o servidor retornou "auth": "ok"
        if (
            resposta.get("auth")
            and str(resposta.get("auth")).lower() == "ok"
        ):
          autenticado = True
          break

    if not autenticado:
      raise Exception("Servidor Achex não confirmou a autenticação (auth != ok)")

    # 5. Envia o comando direcionado ao ESP8266 após a confirmação
    control_payload = json.dumps({"to": TARGET_ID, "value": valor_comando})
    ws.send(control_payload)

    # 6. Aguarda brevemente a entrega e fecha a conexão
    time.sleep(0.5)
    ws.close()

    return (
        jsonify({
            "status": "success",
            "comando_enviado": valor_comando,
            "destinatario": TARGET_ID,
            "remetente": USER_ID,
            "message": "Comando autenticado e enviado via WSS com sucesso!",
        }),
        200,
    )

  except Exception as e:
    if ws:
      try:
        ws.close()
      except Exception:
        pass
    return (
        jsonify({
            "status": "error",
            "message": f"Erro na conexão WebSocket: {str(e)}",
        }),
        500,
    )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
