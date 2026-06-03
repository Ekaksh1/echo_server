
"""Minimal Winsock helpers built on ctypes.

This module intentionally avoids the Python ``socket`` module so the project
can keep all network setup in ctypes while still using normal TCP connections.
"""
from __future__ import annotations

import ctypes
import ipaddress
import os
from ctypes import wintypes


if os.name != "nt":
    raise RuntimeError("winsock_ctypes is only supported on Windows")


AF_INET = 2
SOCK_STREAM = 1
IPPROTO_TCP = 6
SOL_SOCKET = 0xFFFF
SO_REUSEADDR = 0x0004
INVALID_SOCKET = ctypes.c_size_t(-1).value
SOCKET_ERROR = -1


class WSADATA(ctypes.Structure):
    _fields_ = [
        ("wVersion", wintypes.WORD),
        ("wHighVersion", wintypes.WORD),
        ("szDescription", ctypes.c_char * 257),
        ("szSystemStatus", ctypes.c_char * 129),
        ("iMaxSockets", wintypes.USHORT),
        ("iMaxUdpDg", wintypes.USHORT),
        ("lpVendorInfo", ctypes.c_char_p),
    ]


class IN_ADDR(ctypes.Structure):
    _fields_ = [("S_addr", wintypes.ULONG)]


class SOCKADDR_IN(ctypes.Structure):
    _fields_ = [
        ("sin_family", wintypes.USHORT),
        ("sin_port", wintypes.USHORT),
        ("sin_addr", IN_ADDR),
        ("sin_zero", ctypes.c_ubyte * 8),
    ]


SocketHandle = int

_ws2_32 = ctypes.WinDLL("Ws2_32.dll", use_last_error=True)

_ws2_32.WSAStartup.argtypes = [wintypes.WORD, ctypes.POINTER(WSADATA)]
_ws2_32.WSAStartup.restype = ctypes.c_int
_ws2_32.WSACleanup.argtypes = []
_ws2_32.WSACleanup.restype = ctypes.c_int
_ws2_32.WSAGetLastError.argtypes = []
_ws2_32.WSAGetLastError.restype = ctypes.c_int

_ws2_32.socket.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
_ws2_32.socket.restype = ctypes.c_size_t

_ws2_32.setsockopt.argtypes = [
    ctypes.c_size_t,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int,
]
_ws2_32.setsockopt.restype = ctypes.c_int

_ws2_32.bind.argtypes = [ctypes.c_size_t, ctypes.POINTER(SOCKADDR_IN), ctypes.c_int]
_ws2_32.bind.restype = ctypes.c_int

_ws2_32.listen.argtypes = [ctypes.c_size_t, ctypes.c_int]
_ws2_32.listen.restype = ctypes.c_int

_ws2_32.accept.argtypes = [ctypes.c_size_t, ctypes.POINTER(SOCKADDR_IN), ctypes.POINTER(ctypes.c_int)]
_ws2_32.accept.restype = ctypes.c_size_t

_ws2_32.connect.argtypes = [ctypes.c_size_t, ctypes.POINTER(SOCKADDR_IN), ctypes.c_int]
_ws2_32.connect.restype = ctypes.c_int

_ws2_32.recv.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_ws2_32.recv.restype = ctypes.c_int

_ws2_32.send.argtypes = [ctypes.c_size_t, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
_ws2_32.send.restype = ctypes.c_int

_ws2_32.shutdown.argtypes = [ctypes.c_size_t, ctypes.c_int]
_ws2_32.shutdown.restype = ctypes.c_int

_ws2_32.closesocket.argtypes = [ctypes.c_size_t]
_ws2_32.closesocket.restype = ctypes.c_int


def _wsa_error(operation: str) -> OSError:
    # Gets the last Windows socket error code and wraps it in a Python OSError
    # Used to provide meaningful error messages when Winsock operations fail
    code = int(_ws2_32.WSAGetLastError())
    return OSError(code, f"{operation} failed with WSA error {code}")


def _swap_u16(value: int) -> int:
    # Converts a 16-bit integer between little-endian and big-endian byte order
    # Needed because network protocols use big-endian (network byte order)
    return int.from_bytes(value.to_bytes(2, "little"), "big")


def _ipv4_to_u32(host: str) -> int:
    # Converts an IPv4 address string (like "127.0.0.1") to a 32-bit unsigned integer
    # Used internally by Winsock to represent IP addresses
    return int.from_bytes(ipaddress.IPv4Address(host).packed, "little")


def _u32_to_ipv4(value: int) -> str:
    # Converts a 32-bit unsigned integer back to an IPv4 address string
    # Reverse of _ipv4_to_u32, used when receiving peer address information
    return str(ipaddress.IPv4Address(value.to_bytes(4, "little")))


def _make_sockaddr_in(host: str, port: int) -> SOCKADDR_IN:
    # Constructs a SOCKADDR_IN structure from an IP address and port
    # This structure is required by Winsock for bind(), connect(), and accept() calls
    # Handles byte order conversion for both port and IP address
    return SOCKADDR_IN(
        sin_family=AF_INET,
        sin_port=_swap_u16(port),
        sin_addr=IN_ADDR(S_addr=_ipv4_to_u32(host)),
        sin_zero=(ctypes.c_ubyte * 8)(),
    )


class WinsockSession:
    """Small context manager for WSAStartup/WSACleanup."""

    def __init__(self) -> None:
        self._started = False
        self._data = WSADATA()

    def __enter__(self) -> "WinsockSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        # Initializes the Winsock library (must be called before any socket operations)
        # WSAStartup fills in version info and system capabilities
        # 0x0202 requests Winsock 2.2 support
        if self._started:
            return
        result = int(_ws2_32.WSAStartup(0x0202, ctypes.byref(self._data)))
        if result != 0:
            raise OSError(result, f"WSAStartup failed with code {result}")
        self._started = True

    def close(self) -> None:
        # Cleans up Winsock (must be called when done to release system resources)
        # Releases all sockets and networking resources
        if self._started:
            _ws2_32.WSACleanup()
            self._started = False

    def create_tcp_socket(self) -> SocketHandle:
        # Creates a TCP socket (AF_INET=IPv4, SOCK_STREAM=TCP, IPPROTO_TCP=TCP protocol)
        # Returns a socket handle to use in other operations
        sock = int(_ws2_32.socket(AF_INET, SOCK_STREAM, IPPROTO_TCP))
        if sock == INVALID_SOCKET:
            raise _wsa_error("socket")
        return sock

    def close_socket(self, sock: SocketHandle) -> None:
        # Closes a socket and releases its resources
        # Safe to call even if socket is invalid
        if sock == INVALID_SOCKET:
            return
        if _ws2_32.closesocket(sock) == SOCKET_ERROR:
            raise _wsa_error("closesocket")

    def shutdown_socket(self, sock: SocketHandle, how: int = 2) -> None:
        # Gracefully closes a socket connection (how=2 means both send and receive)
        # Called before close_socket to properly terminate connections
        if sock == INVALID_SOCKET:
            return
        if _ws2_32.shutdown(sock, how) == SOCKET_ERROR:
            raise _wsa_error("shutdown")

    def set_reuseaddr(self, sock: SocketHandle) -> None:
        # Enables SO_REUSEADDR option to allow reusing the same port immediately
        # Without this, the socket stays in TIME_WAIT and can't rebind for a few minutes
        opt = ctypes.c_int(1)
        result = _ws2_32.setsockopt(
            sock,
            SOL_SOCKET,
            SO_REUSEADDR,
            ctypes.cast(ctypes.byref(opt), ctypes.c_void_p),
            ctypes.sizeof(opt),
        )
        if result == SOCKET_ERROR:
            raise _wsa_error("setsockopt(SO_REUSEADDR)")

    def bind(self, sock: SocketHandle, host: str, port: int) -> None:
        # Binds a socket to a specific IP address and port (for listening/server sockets)
        # After binding, the socket is ready to listen for incoming connections
        address = _make_sockaddr_in(host, port)
        if _ws2_32.bind(sock, ctypes.byref(address), ctypes.sizeof(address)) == SOCKET_ERROR:
            raise _wsa_error("bind")

    def listen(self, sock: SocketHandle, backlog: int = 1) -> None:
        # Marks a socket as listening for incoming connections
        # backlog=1 means at most 1 connection can wait in the queue before being accepted
        if _ws2_32.listen(sock, backlog) == SOCKET_ERROR:
            raise _wsa_error("listen")

    def accept(self, sock: SocketHandle) -> tuple[SocketHandle, str, int]:
        # Accepts an incoming client connection on a listening socket
        # Blocks until a client connects, then returns the client socket and their address info
        peer = SOCKADDR_IN()
        peer_len = ctypes.c_int(ctypes.sizeof(peer))
        client = int(_ws2_32.accept(sock, ctypes.byref(peer), ctypes.byref(peer_len)))
        if client == INVALID_SOCKET:
            raise _wsa_error("accept")
        peer_host = _u32_to_ipv4(int(peer.sin_addr.S_addr))
        peer_port = _swap_u16(int(peer.sin_port))
        return client, peer_host, peer_port

    def connect(self, sock: SocketHandle, host: str, port: int) -> None:
        # Connects a client socket to a remote server at the given host and port
        # Blocks until connection succeeds or fails
        address = _make_sockaddr_in(host, port)
        if _ws2_32.connect(sock, ctypes.byref(address), ctypes.sizeof(address)) == SOCKET_ERROR:
            raise _wsa_error("connect")

    def send_all(self, sock: SocketHandle, data: bytes) -> None:
        # Sends all data through a socket, looping until everything is sent
        # Handles partial sends (when not all data sends at once)
        # Raises an error if send fails or returns 0 bytes
        view = memoryview(data)
        sent_total = 0
        while sent_total < len(view):
            chunk = view[sent_total:]
            buffer = ctypes.create_string_buffer(bytes(chunk))
            sent = int(_ws2_32.send(sock, ctypes.cast(buffer, ctypes.c_void_p), len(chunk), 0))
            if sent == SOCKET_ERROR:
                raise _wsa_error("send")
            if sent == 0:
                raise OSError("send returned 0 bytes")
            sent_total += sent

    def recv_some(self, sock: SocketHandle, size: int = 4096) -> bytes:
        # Receives up to 'size' bytes from a socket (non-blocking for small amounts)
        # Returns empty bytes if the connection is closed by the peer
        buffer = ctypes.create_string_buffer(size)
        received = int(_ws2_32.recv(sock, ctypes.cast(buffer, ctypes.c_void_p), size, 0))
        if received == SOCKET_ERROR:
            raise _wsa_error("recv")
        return buffer.raw[:received]


def create_socket(family: int = AF_INET, sock_type: int = SOCK_STREAM, proto: int = IPPROTO_TCP) -> SocketHandle:
    # Module-level function to create a socket directly without using WinsockSession
    # Default parameters create an IPv4 TCP socket
    sock = int(_ws2_32.socket(family, sock_type, proto))
    if sock == INVALID_SOCKET:
        raise _wsa_error("socket")
    return sock


def setsockopt(sock: SocketHandle, level: int, optname: int, value: int) -> None:
    # Module-level function to set socket options (like SO_REUSEADDR)
    # Used to configure socket behavior and parameters
    opt = ctypes.c_int(value)
    result = _ws2_32.setsockopt(
        sock,
        level,
        optname,
        ctypes.byref(opt),
        ctypes.sizeof(opt),
    )
    if result == SOCKET_ERROR:
        raise _wsa_error("setsockopt")