import json
import os
import ssl
import time
from flask import Flask, jsonify, request
from websocket import create_connection

app = Flask(__name__)

ACHEX_WSS_URL = "wss://ws.achex.ca/"
USER_ID = "jordan@1107"
USER_PASS = "142536"
TARGET_ID = "arduino@1107"


def criar_contexto_ssl_permissivo():
  """Cria um contexto SSL que aceita ciphers legados da Achex no OpenSSL moderno do Python."""
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  # Permite ciphers legados usados por servidores antigos
  try:
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
  except Exception:
    ctx.set_ciphers("ALL")
  return ctx


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  ws = None
  try:
    # 1. Trata o parâmetro 'comando'
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Conecta ao WebSocket passando o contexto SSL customizado
    ssl_context = criar_contexto_ssl_permissivo()

    ws = create_connection(
        ACHEX_WSS_URL,
        timeout=8,
        sslopt={"context": ssl_context},
        header=["Origin: https://ws.achex.ca"],
    )

    # 3. Autenticação (setID)
    auth_payload = json.dumps({"setID": USER_ID, "passwd": USER_PASS})
    ws.send(auth_payload)

    # 4. Aguarda o 'auth: ok' do servidor Achex
    autenticado = False
    inicio_auth = time.time()

    while time.time() - inicio_auth < 4:
      resposta_raw = ws.recv()
      if resposta_raw:
        resposta = json.loads(resposta_raw)
        if (
            resposta.get("auth")
            and str(resposta.get("auth")).lower() == "ok"
        ):
          autenticado = True
          break

    if not autenticado:
      raise Exception("Servidor Achex não autorizou a conexão (auth != ok).")

    # 5. Envia o comando para o ESP8266
    control_payload = json.dumps({"to": TARGET_ID, "value": valor_comando})
    ws.send(control_payload)

    # 6. Aguarda o retorno do ESP8266
    resposta_esp = None
    inicio_espera = time.time()

    while time.time() - inicio_espera < 5:
      try:
        msg_raw = ws.recv()
        if msg_raw:
          dados = json.loads(msg_raw)
          if "value" in dados:
            resposta_esp = dados.get("value")
            break
      except Exception:
        break

    # 7. Encerra a conexão
    ws.close()

    if resposta_esp:
      return (
          jsonify({
              "status": "success",
              "comando_enviado": valor_comando,
              "resposta_esp8266": resposta_esp,
              "message": "Comando entregue e confirmado pelo ESP8266!",
          }),
          200,
      )
    else:
      return (
          jsonify({
              "status": "warning",
              "comando_enviado": valor_comando,
              "resposta_esp8266": None,
              "message": (
                  "Comando enviado, mas o ESP8266 não respondeu a tempo."
              ),
          }),
          202,
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
            "message": f"Erro na operação: {str(e)}",
        }),
        500,
    )


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
