import json
import os
import socket
import time
from flask import Flask, jsonify, request

app = Flask(__name__)

# Configurações do Socket TCP da Achex
ACHEX_HOST = "ws.achex.ca"
ACHEX_PORT = 4010


@app.route("/ligar-luz", methods=["GET", "POST"])
def enviar_comando_socket_tcp():
  try:
    # 1. Captura o parâmetro 'comando' e aplica as substituições (- por = / AND por &)
    raw_comando = request.args.get("comando", default="l1=1")
    valor_comando = raw_comando.replace("-", "=").replace("AND", "&")

    # 2. Abre a conexão Socket TCP com timeout de 5 segundos
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((ACHEX_HOST, ACHEX_PORT))

    # 3. Envia o primeiro JSON (Autenticação/setID) + quebra de linha \n
    cmd_auth = (
        json.dumps({"setID": "jordan@1107", "passwd": "142536"}, separators=(",", ":"))
        + "\n"
    )
    s.sendall(cmd_auth.encode("utf-8"))

    # 4. Aguarda 1 segundo
    time.sleep(1)

    # 5. Envia o segundo JSON (Comando para o Arduino) + quebra de linha \n
    cmd_control = (
        json.dumps(
            {"to": "arduino@1107", "value": valor_comando}, separators=(",", ":")
        )
        + "\n"
    )
    s.sendall(cmd_control.encode("utf-8"))

    # 6. Aguarda mais 2 segundos
    time.sleep(2)

    # 7. Fecha a conexão Socket
    s.close()

    # 8. Retorna HTTP 200 OK para o Make
    return (
        jsonify({
            "status": "success",
            "comando_enviado": valor_comando,
            "message": "Comando enviado via TCP Socket puro com sucesso!",
        }),
        200,
    )

  except Exception as e:
    # Retorna HTTP 500 caso o socket caia ou feche
    return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
