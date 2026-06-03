"""RFC Protocol Implementations for TCP Servers.

Implements four important RFCs:
1. RFC 862 - Echo Protocol: Echoes back any data received
2. RFC 864 - Discard Protocol: Discards all data without response
3. RFC 865 - Quote of the Day (QOTD): Sends random quote and closes
4. RFC 854 - Telnet Protocol: Interactive command protocol with negotiation
"""
from __future__ import annotations

import random
import time
from enum import Enum
from typing import Callable

import config
from winsock_ctypes import WinsockSession


# ============================================================================
# RFC 862 - Echo Protocol (Port 7)
# ============================================================================
# Description: The Echo Protocol is a service that simply echoes back to the
# client any data it receives. Used for testing connectivity.
# Reference: https://tools.ietf.org/html/rfc862

class EchoProtocol:
    """RFC 862 Echo Protocol implementation."""
    
    PORT = config.ECHO_PORT
    DESCRIPTION = "Echo Protocol (RFC 862)"
    
    @staticmethod
    def handle_connection(ws: WinsockSession, client: int, peer_host: str, peer_port: int, initial_data: bytes = b"") -> None:
        """Handle RFC 862 echo protocol - echo all received data back to client."""
        buffer = bytearray(initial_data)
        
        try:
            while True:
                chunk = ws.recv_some(client, size=config.RECV_CHUNK_SIZE)
                if not chunk:
                    break
                
                if len(buffer) + len(chunk) > config.MAX_BUFFER_SIZE:
                    print(f"[RFC 862] Buffer overflow - disconnecting")
                    break
                
                buffer.extend(chunk)
                
                print(f"[SERVER] Received: {bytes(buffer).decode('utf-8', errors='replace').strip()}")
                
                try:
                    ws.send_all(client, bytes(buffer))
                    buffer.clear()
                except OSError as e:
                    print(f"[RFC 862] Send error: {e}")
                    break
        
        except OSError as e:
            print(f"[RFC 862] Error: {e}")
        finally:
            ws.close_socket(client)


# ============================================================================
# RFC 864 - Discard Protocol (Port 9)
# ============================================================================
# Description: The Discard Protocol is a service that receives a stream of
# data and discards it, without sending any response back.
# Reference: https://tools.ietf.org/html/rfc864

class DiscardProtocol:
    """RFC 864 Discard Protocol implementation."""
    
    PORT = config.DISCARD_PORT
    DESCRIPTION = "Discard Protocol (RFC 864)"
    
    @staticmethod
    def handle_connection(ws: WinsockSession, client: int, peer_host: str, peer_port: int) -> None:
        """Handle RFC 864 discard protocol - discard all received data without response."""
        try:
            while True:
                chunk = ws.recv_some(client, size=config.RECV_CHUNK_SIZE)
                if not chunk:
                    break
        except OSError as e:
            print(f"[RFC 864] Error: {e}")
        finally:
            ws.close_socket(client)


# ============================================================================
# RFC 865 - Quote of the Day Protocol (Port 17)
# ============================================================================
# Description: The Quote of the Day Protocol is a service that sends a short
# message or quote to the client and immediately closes the connection.
# Reference: https://tools.ietf.org/html/rfc865

class QuoteOfTheDayProtocol:
    """RFC 865 Quote of the Day (QOTD) Protocol implementation."""
    
    PORT = config.QOTD_PORT
    DESCRIPTION = "Quote of the Day Protocol (RFC 865)"
    
    QUOTES = [
        "The best way to predict the future is to invent it. - Alan Kay",
        "Life is what happens when you're busy making other plans. - John Lennon",
        "The only true wisdom is in knowing you know nothing. - Socrates",
        "Innovation distinguishes between a leader and a follower. - Steve Jobs",
        "In the middle of difficulty lies opportunity. - Albert Einstein",
        "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
        "It is during our darkest moments that we must focus to see the light. - Aristotle",
        "The only way to do great work is to love what you do. - Steve Jobs",
        "Life is either a daring adventure or nothing at all. - Helen Keller",
        "Success is not final, failure is not fatal. - Winston Churchill",
    ]
    
    @staticmethod
    def handle_connection(ws: WinsockSession, client: int, peer_host: str, peer_port: int) -> None:
        """Handle RFC 865 QOTD protocol - send quote and close."""
        quote = random.choice(QuoteOfTheDayProtocol.QUOTES)
        message = f"{quote}\n"
        
        try:
            ws.send_all(client, message.encode('utf-8'))
        except OSError as e:
            print(f"[RFC 865] Send error: {e}")
        finally:
            ws.close_socket(client)


# ============================================================================
# RFC 854 - Telnet Protocol (Port 23)
# ============================================================================
# Description: The Telnet Protocol provides a way for a user to interact
# with a remote system via a command-based interface. It includes option
# negotiation and supports various terminal modes.
# Reference: https://tools.ietf.org/html/rfc854

class TelnetCommand(Enum):
    """Telnet protocol commands."""
    SE = 240      # End of subnegotiation
    NOP = 241     # No operation
    WILL = 251    # Will perform option
    WONT = 252    # Will not perform option
    DO = 253      # Do perform option
    DONT = 254    # Don't perform option
    IAC = 255     # Interpret as Command


class TelnetOption(Enum):
    """Telnet protocol options."""
    ECHO = 1
    SUPPRESS_GO_AHEAD = 3
    STATUS = 5
    LINEMODE = 34


class TelnetProtocol:
    """RFC 854 Telnet Protocol implementation."""
    
    PORT = config.TELNET_PORT
    DESCRIPTION = "Telnet Protocol (RFC 854)"
    
    COMMANDS = {
        "help": "Available commands: help, time, quit",
        "time": lambda: f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "quit": "Goodbye!",
    }
    
    @staticmethod
    def handle_connection(ws: WinsockSession, client: int, peer_host: str, peer_port: int) -> None:
        """Handle RFC 854 Telnet protocol - interactive command interface."""
        
        try:
            # Send welcome message
            welcome = "Welcome to Telnet Server (RFC 854)\nType 'help' for commands\n"
            ws.send_all(client, welcome.encode('utf-8') + b"telnet> ")
            
            buffer = bytearray()
            
            while True:
                chunk = ws.recv_some(client, size=config.RECV_CHUNK_SIZE)
                if not chunk:
                    break
                
                if len(buffer) + len(chunk) > config.MAX_BUFFER_SIZE:
                    break
                
                buffer.extend(chunk)
                
                # Process commands line by line
                while True:
                    # Look for line ending (\r\n for Telnet, \n fallback)
                    nl = buffer.find(b"\r\n")
                    if nl == -1:
                        nl = buffer.find(b"\n")
                        if nl == -1:
                            break
                        line = bytes(buffer[:nl])
                        del buffer[:nl + 1]
                    else:
                        line = bytes(buffer[:nl])
                        del buffer[:nl + 2]
                    
                    command = line.decode('utf-8', errors='replace').strip().lower()
                    
                    if not command:
                        continue
                    
                    print(f"[SERVER] Received: {command}")
                    
                    response = ""
                    
                    if command == "quit":
                        response = "Goodbye!\n"
                        ws.send_all(client, response.encode('utf-8'))
                        return
                    
                    elif command == "help":
                        response = "Available commands: help, time, quit\n"
                    
                    elif command == "time":
                        response = f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    else:
                        response = f"Unknown command: {command}. Type 'help' for available commands.\n"
                    
                    ws.send_all(client, response.encode('utf-8') + b"telnet> ")
        
        except OSError as e:
            print(f"[RFC 854] Error: {e}")
        finally:
            ws.close_socket(client)


# ============================================================================
# Protocol Router
# ============================================================================

class ProtocolRouter:
    """Routes connections to appropriate RFC protocol handlers based on port."""
    
    # Build mapping using the configured ports so the server can run without admin
    PROTOCOLS = {
        EchoProtocol.PORT: EchoProtocol,
        DiscardProtocol.PORT: DiscardProtocol,
        QuoteOfTheDayProtocol.PORT: QuoteOfTheDayProtocol,
        TelnetProtocol.PORT: TelnetProtocol,
    }
    
    @staticmethod
    def get_handler(port: int) -> type | None:
        """Get the protocol handler for a given port."""
        return ProtocolRouter.PROTOCOLS.get(port)
    
    @staticmethod
    def list_protocols() -> list[tuple[int, str]]:
        """List all available protocols."""
        return [(port, proto.DESCRIPTION) for port, proto in ProtocolRouter.PROTOCOLS.items()]
