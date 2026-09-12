import json
import os
import ssl
import threading
import time
from flask import Flask, jsonify, request
from websocket import create_connection

app = Flask(__name__)

ACHEX_WSS_URL = "wss://ws.achex.ca/"
USER_ID = "jordan@1107"
USER_PASS = "142536"
TARGET_ID = "arduino@1107"


def criar_contexto_ssl_permissivo():
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  try:
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
  except Exception:
    ctx.set_ciphers("ALL")
  return ctx


def tarefa_websocket_background(valor_comando):
  """Executa a conexão e o envio do comando em background numa Thread separada."""
  ws = None
  try:
    ssl_context = criar_contexto_ssl_permissivo()
    ws = create_connection(
        ACHEX_WSS_URL,
        timeout=5,
        sslopt={"context": ssl_context},
        header=["Origin: https://ws.achex.ca"],
    )

    # 1. Autentica
    ws.send(json.dumps({"setID": USER_ID, "passwd": USER_PASS}))

    # 2. Aguarda auth: ok
    inicio_auth = time.time()
    while time.time() - inicio_auth < 3:
      resposta_raw = ws.recv()
      if resposta_raw:
        resposta = json.loads(resposta_raw)
        if (
            resposta.get("auth")
            and str(resposta.get("auth")).lower() == "ok"
        ):
          break

    # 3. Envia comando ao ESP8266
    ws.send(json.dumps({"to": TARGET_ID, "value": valor_comando}))
    time.sleep(0.3)
    ws.close()
  except Exception as e:
    print(f"Erro na thread background: {e}")
    if ws:
      try:
        ws.close()
      except Exception:
        pass


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  raw_comando = request.args.get("comando", default="l1=1")
  valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

  # Dispara a conexão WebSocket em segundo plano (não trava o Flask)
  thread = threading.Thread(
      target=tarefa_websocket_background, args=(valor_comando,)
  )
  thread.start()

  # Responde imediatamente (latência < 100ms)
  return (
      jsonify({
          "status": "success",
          "comando_enviado": valor_comando,
          "message": "Comando enviado para processamento em background!",
      }),
      200,
  )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
