"""Simple single-client TCP echo server using raw sockets."""
from __future__ import annotations

import argparse
import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
BUFFER_SIZE = 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple TCP echo server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on.")
    return parser.parse_args()


def serve_once(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(1)

        print(f"Echo server listening on {host}:{port}")
        print("Waiting for one client...")

        conn, address = server_socket.accept()
        with conn:
            print(f"Connected by {address[0]}:{address[1]}")
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    print("Client disconnected.")
                    break
                message = data.decode("utf-8", errors="replace").rstrip("\n")
                print(f"Received: {message}")
                conn.sendall(data)


def main() -> None:
    args = parse_args()
    try:
        serve_once(args.host, args.port)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except OSError as exc:
        print(f"Server error: {exc}")


if __name__ == "__main__":
    main()
