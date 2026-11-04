"""Start the offline Cendrix chat app on loopback."""

from __future__ import annotations

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.interface.server import create_server


def main() -> None:
    server = create_server()
    print(f"Cendrix AI is ready at http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCendrix AI stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
