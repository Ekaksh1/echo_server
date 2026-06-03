"""RFC Protocol Test Client (renamed to client.py).

Tests each RFC protocol implementation:
- RFC 862: Echo - sends data and receives echo
- RFC 864: Discard - sends data and verifies silent discard
- RFC 865: QOTD - receives quote and closes
- RFC 854: Telnet - interactive command protocol
"""
from __future__ import annotations

import time

import config
from winsock_ctypes import WinsockSession


def test_echo_protocol(host: str = "127.0.0.1", port: int = config.SERVER_PORT) -> None:
    """Test RFC 862 Echo Protocol interactively."""
    print("\n" + "="*60)
    print("Interactive Echo Test (RFC 862)")
    print("="*60)
    print(f"Connecting to {host}:{port}...")
    
    ws = WinsockSession()
    ws.start()
    sock = ws.create_tcp_socket()
    
    try:
        ws.connect(sock, host, port)
        # Send protocol prefix for unified server
        ws.send_all(sock, b"ECHO:")
        print("Connected! Type messages to send to server. Type 'quit' to exit.\n")
        
        while True:
            try:
                msg = input("You: ")
            except EOFError:
                break
            
            if msg.lower() == 'quit':
                break
            
            ws.send_all(sock, msg.encode('utf-8') + b"\n")
            
            try:
                response = ws.recv_some(sock, size=4096)
                print(f"Echo: {response.decode('utf-8', errors='replace').strip()}")
            except OSError as e:
                print(f"Error receiving echo: {e}")
                break
        
        print("\n✓ Echo connection closed")
    
    except Exception as e:
        print(f"✗ Echo error: {e}")
    finally:
        ws.close_socket(sock)


def test_discard_protocol(host: str = "127.0.0.1", port: int = config.SERVER_PORT) -> None:
    """Test RFC 864 Discard Protocol."""
    ws = WinsockSession()
    ws.start()
    sock = ws.create_tcp_socket()
    
    try:
        ws.connect(sock, host, port)
        # Send protocol prefix for unified server
        ws.send_all(sock, b"DISCARD:")
        test_data = b"This data will be discarded silently\n" * 3
        ws.send_all(sock, test_data)
        
        time.sleep(1)
        
        try:
            response = ws.recv_some(sock, size=1024)
            if response:
                print("✗ Discard: unexpected response")
                return
        except OSError:
            pass
        
        print("✓ Discard: OK")
    
    except Exception as e:
        print(f"✗ Discard: {e}")
    finally:
        ws.close_socket(sock)


def test_qotd_protocol(host: str = "127.0.0.1", port: int = config.SERVER_PORT) -> None:
    """Test RFC 865 Quote of the Day Protocol."""
    ws = WinsockSession()
    ws.start()
    sock = ws.create_tcp_socket()
    
    try:
        ws.connect(sock, host, port)
        # Send protocol prefix for unified server
        ws.send_all(sock, b"QOTD:")
        buffer = bytearray()
        
        while True:
            chunk = ws.recv_some(sock, size=1024)
            if not chunk:
                break
            buffer.extend(chunk)
            if b'\n' in buffer:
                break
        
        quote = buffer.decode('utf-8', errors='replace').strip()
        if quote:
            print("✓ QOTD: OK")
        else:
            print("✗ QOTD: no quote received")
    
    except Exception as e:
        print(f"✗ QOTD: {e}")
    finally:
        ws.close_socket(sock)


def test_telnet_protocol(host: str = "127.0.0.1", port: int = config.SERVER_PORT) -> None:
    """Test RFC 854 Telnet Protocol."""
    print("\n" + "="*60)
    print("Testing RFC 854 - Telnet Protocol")
    print("="*60)
    
    ws = WinsockSession()
    ws.start()
    sock = ws.create_tcp_socket()
    
    try:
        print(f"Connecting to {host}:{port}...")
        ws.connect(sock, host, port)
        # Send protocol prefix for unified server
        ws.send_all(sock, b"TELNET:")
        print("Connected!")
        
        # Receive welcome message
        buffer = bytearray()
        print("\nReceiving welcome message...")
        
        while True:
            chunk = ws.recv_some(sock, size=1024)
            if not chunk:
                break
            buffer.extend(chunk)
            
            if b'telnet>' in buffer:
                break
        
        welcome = buffer.decode('utf-8', errors='replace')
        print(welcome.replace('telnet> ', '\ntelnet> '))
        
        # Interactive command loop
        while True:
            try:
                cmd = input("telnet> ")
            except EOFError:
                break
            
            ws.send_all(sock, cmd.encode('utf-8') + b"\n")
            
            if cmd.strip().lower() == "quit":
                break
            
            # Receive response
            buffer = bytearray()
            while True:
                chunk = ws.recv_some(sock, size=1024)
                if not chunk:
                    break
                buffer.extend(chunk)
                
                if b'telnet>' in buffer:
                    break
            
            response = buffer.decode('utf-8', errors='replace')
            print(response.replace('telnet> ', '\n'))
        
        print("✓ Telnet protocol test complete!")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ws.close_socket(sock)
        print("\nTest complete")


def main() -> None:
    """Run all RFC protocol tests on unified server."""
    print("\n" + "="*60)
    print("RFC Protocol Test Suite (Unified Server)")
    print("="*60)
    print("\nMake sure the server is running on the unified port:")
    print(f"  Default port: {config.SERVER_PORT}")
    
    time.sleep(2)
    
    try:
        test_echo_protocol()
        test_discard_protocol()
        test_qotd_protocol()
        test_telnet_protocol()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
    
    print("\n" + "="*60)
    print("All tests complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
