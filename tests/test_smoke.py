import json
import threading
import urllib.request

from mixed_method_ontology.__main__ import create_server


def test_healthz() -> None:
    server = create_server(0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        port = server.server_address[1]
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz") as response:
            assert response.status == 200
            assert json.load(response) == {"status": "ok"}
    finally:
        server.shutdown()
