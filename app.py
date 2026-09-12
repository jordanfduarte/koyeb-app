import json
import os
import time
from flask import Flask, jsonify, request
from websocket import create_connection

app = Flask(__name__)

# Configurações do WebSocket WSS da Achex (espelhado do ESP8266)
ACHEX_WSS_URL = "wss://ws.achex.ca:443/"
USER_ID = "jordan@1107"
USER_PASS = "142536"
TARGET_ID = "arduino@1107"


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  ws = None
  try:
    # 1. Trata o parâmetro 'comando' recebido via GET/POST
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Conecta ao WebSocket Seguro (WSS) na porta 443
    ws = create_connection(ACHEX_WSS_URL, timeout=5)

    # 3. Autentica a API Python no servidor Achex (setID)
    auth_payload = json.dumps({"setID": USER_ID, "passwd": USER_PASS})
    ws.send(auth_payload)

    # Pequena pausa para garantir a autenticação no servidor
    time.sleep(0.5)

    # 4. Envia a mensagem direcionada ao ESP8266 (to: "arduino@1107")
    control_payload = json.dumps({"to": TARGET_ID, "value": valor_comando})
    ws.send(control_payload)

    # 5. Aguarda 1 segundo antes de encerrar a conexão
    time.sleep(1)

    # 6. Fecha o WebSocket de forma limpa
    ws.close()

    return (
        jsonify({
            "status": "success",
            "comando_enviado": valor_comando,
            "destinatario": TARGET_ID,
            "remetente": USER_ID,
            "message": "Comando enviado via WebSocket WSS com sucesso!",
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
