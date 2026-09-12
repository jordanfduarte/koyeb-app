import json
import os
import time
from flask import Flask, jsonify, request
import websocket

app = Flask(__name__)

# Configurações do WebSocket Achex
WS_URL = "ws://ws.achex.ca:4010"


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_websocket():
  try:
    # 1. Captura o parâmetro 'comando' enviado via GET na URL
    # Se não for passado nada na URL, assume 'l1-1' como padrão
    # 1. Captura o parâmetro 'comando' e aplica as substituições (.replace)
    # Primeiro troca '-' por '=', depois troca 'AND' por '&'
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Abre a conexão WebSocket (timeout de 5 segundos)
    ws = websocket.create_connection(WS_URL, timeout=5)

    # 3. Prepara e envia o primeiro JSON (Autenticação/setID)
    cmd_auth = {"setID": "jordan@1107", "passwd": "142536"}
    ws.send(json.dumps(cmd_auth))

    # 4. Espera 1 segundo
    time.sleep(1)

    # 5. Monta o segundo JSON usando o valor recebido no GET
    cmd_control = {"to": "arduino@1107", "value": valor_comando}
    ws.send(json.dumps(cmd_control))

    # 6. Espera mais 2 segundos
    time.sleep(2)

    # 7. Encerra a conexão WebSocket
    ws.close()

    # 8. Retorna HTTP 200 Sucesso para o cliente
    return (
        jsonify({
            "status": "success",
            "comando_enviado": valor_comando,
            "message": (
                "Comando enviado via WebSocket e conexão encerrada com"
                " sucesso!"
            ),
        }),
        200,
    )

  except Exception as e:
    # Retorna erro HTTP 500 caso ocorra falha na conexão ou timeout
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)