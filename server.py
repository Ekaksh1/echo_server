"""Multi-protocol RFC server supporting RFC 862, 864, 865, and 854.

This server implements four important RFCs on a single port:
- RFC 862 (Echo) - send "ECHO:" followed by data
- RFC 864 (Discard) - send "DISCARD:" (discards all data)
- RFC 865 (QOTD) - send "QOTD:" (receives a quote)
- RFC 854 (Telnet) - send "TELNET:" followed by commands

All protocols are accessible on a single port for unified access.
"""
from __future__ import annotations

import argparse
import signal
import threading
import time

import config
from rfc_protocols import EchoProtocol, DiscardProtocol, QuoteOfTheDayProtocol, TelnetProtocol
from rich.console import Console
from winsock_ctypes import WinsockSession

console = Console()


# Global flag for graceful shutdown
_shutdown_event = threading.Event()


def handle_shutdown_signal(signum, frame):
    """Signal handler for SIGINT (Ctrl+C) and SIGTERM."""
    print("\n[MAIN] Shutting down...")
    _shutdown_event.set()


def serve_single_port(host: str, port: int) -> None:
    """Serve all RFC protocols on a single port with protocol selection."""
    
    ws = WinsockSession()
    try:
        ws.start()
    except OSError as e:
        print(f"[ERROR] Failed to initialize Winsock: {e}")
        return
    
    listener = ws.create_tcp_socket()
    
    try:
        try:
            ws.set_reuseaddr(listener)
            ws.bind(listener, host, port)
            ws.listen(listener, config.SERVER_BACKLOG)
        except OSError as e:
            print(f"[ERROR] Failed to bind server on {host}:{port}: {e}")
            return
        
        print(f"[MAIN] Multi-protocol server listening on {host}:{port}")
        print("[MAIN] Send protocol prefix: ECHO:, DISCARD:, QOTD:, or TELNET:")
        
        while not _shutdown_event.is_set():
            try:
                client, peer_host, peer_port = ws.accept(listener)
                print(f"[SERVER] Client connected: {peer_host}:{peer_port}")
                console.print("[bold green]RFC is working[/bold green]")
                
                try:
                    # Read protocol identifier first (up to 8 bytes max prefix length)
                    prefix_data = ws.recv_some(client, size=8)
                    if not prefix_data:
                        ws.close_socket(client)
                        continue
                    
                    prefix = bytes(prefix_data).decode('utf-8', errors='replace')
                    print(f"[SERVER] Protocol selection: {prefix.strip()}")
                    
                    # Route to appropriate protocol handler
                    if prefix.strip() == "ECHO:":
                        EchoProtocol.handle_connection(ws, client, peer_host, peer_port, b"")
                    elif prefix.strip() == "DISCARD:":
                        DiscardProtocol.handle_connection(ws, client, peer_host, peer_port)
                    elif prefix.strip() == "QOTD:":
                        QuoteOfTheDayProtocol.handle_connection(ws, client, peer_host, peer_port)
                    elif prefix.strip() == "TELNET:":
                        TelnetProtocol.handle_connection(ws, client, peer_host, peer_port)
                    else:
                        # No protocol prefix - treat as raw Echo input (backwards compatibility)
                        EchoProtocol.handle_connection(ws, client, peer_host, peer_port, prefix_data)
                        
                except Exception as e:
                    print(f"[ERROR] Handler error: {e}")
                finally:
                    try:
                        ws.close_socket(client)
                    except OSError:
                        pass
            
            except OSError as e:
                if _shutdown_event.is_set():
                    break
                print(f"[ERROR] Accept error: {e}")
                time.sleep(0.1)
        
        ws.close_socket(listener)
        print("[MAIN] Server stopped")
    finally:
        try:
            ws.close_socket(listener)
            ws.close()
        except OSError:
            pass


def main() -> None:
    """Entry point: start unified multi-protocol server on single port."""
    parser = argparse.ArgumentParser(
        description="Multi-protocol RFC server on single port (RFC 862, 864, 865, 854)"
    )
    parser.add_argument(
        "--host",
        default=config.SERVER_HOST,
        help=f"Server host (default: {config.SERVER_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.SERVER_PORT,
        help=f"Server port (default: {config.SERVER_PORT})"
    )
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown_signal)
    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    
    print(f"[MAIN] Starting unified server on {args.host}:{args.port}")
    print("[MAIN] Available protocols: ECHO:, DISCARD:, QOTD:, TELNET:")
    
    serve_single_port(args.host, args.port)


if __name__ == "__main__":
    main()
