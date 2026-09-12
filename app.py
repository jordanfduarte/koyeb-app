import json
import os
import ssl
import time
from flask import Flask, jsonify, request
import websocket

app = Flask(__name__)

# URL do WebSocket seguro na porta 443
WS_URL = "wss://ws.achex.ca:443"


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  try:
    # 1. Captura parâmetro 'comando' e faz as substituições (- por = / AND por &)
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Conecta via WebSocket Seguro (wss://) com SSL configurado
    ws = websocket.create_connection(
        WS_URL,
        timeout=5,
        sslopt={"cert_reqs": ssl.CERT_NONE},  # Ignora erros de certificado SSL se houver
    )

    # 3. Envia o primeiro JSON (Autenticação)
    cmd_auth = {"setID": "jordan@1107", "passwd": "142536"}
    ws.send(json.dumps(cmd_auth))

    # 4. Aguarda 1 segundo
    time.sleep(1)

    # 5. Envia o segundo JSON (Comando para o Arduino)
    cmd_control = {"to": "arduino@1107", "value": valor_comando}
    ws.send(json.dumps(cmd_control))

    # 6. Aguarda 2 segundos
    time.sleep(2)

    # 7. Encerra a conexão
    ws.close()

    # 8. Retorna HTTP 200 OK
    return (
        jsonify({
            "status": "success",
            "comando_enviado": valor_comando,
            "message": (
                "Comando enviado via WebSocket (WSS:443) e conexão encerrada com"
                " sucesso!"
            ),
        }),
        200,
    )

  except Exception as e:
    # Retorna erro HTTP 500 caso haja falha
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
