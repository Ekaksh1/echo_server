"""Simple TCP echo client using raw sockets."""
from __future__ import annotations

import argparse
import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
BUFFER_SIZE = 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple TCP echo client.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host to connect to.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port to connect to.")
    return parser.parse_args()


def recv_until_newline(sock: socket.socket) -> str:
    chunks: list[bytes] = []
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        chunks.append(chunk)
        if b"\n" in chunk:
            break
    return b"".join(chunks).decode("utf-8", errors="replace")


def send_message(sock: socket.socket, message: str) -> str:
    payload = f"{message}\n".encode("utf-8")
    sock.sendall(payload)
    return recv_until_newline(sock).rstrip("\n")


def interactive_session(sock: socket.socket) -> None:
    print("Type a custom message and press Enter. Submit an empty line or 'quit' to exit.")
    while True:
        try:
            message = input("Message> ")
        except EOFError:
            print("\nClient closed.")
            break
        except KeyboardInterrupt:
            print("\nClient stopped.")
            break
        if not message or message.lower() == "quit":
            break
        echoed = send_message(sock, message)
        print(f"Echo> {echoed}")


def main() -> None:
    args = parse_args()
    try:
        with socket.create_connection((args.host, args.port)) as sock:
            print(f"Connected to {args.host}:{args.port}")
            interactive_session(sock)
    except ConnectionRefusedError:
        print(f"Could not connect to {args.host}:{args.port}. Is the server running?")
    except KeyboardInterrupt:
        print("\nClient stopped.")


if __name__ == "__main__":
    main()
