"""A tiny compatibility wrapper exposing a Python-like socket API backed by winsock_ctypes.

This module intentionally keeps the same top-level name `socket` so code can
use `from pywinsock_compat import socket` and interact with it much like the
standard library socket module.

Only the operations needed by the echo demo are implemented.
"""
from __future__ import annotations

from typing import Tuple

import winsock_ctypes as w


AF_INET = w.AF_INET
SOCK_STREAM = 1
SOCK_RAW = 3
IPPROTO_TCP = 6
IPPROTO_RAW = 255
SOL_SOCKET = w.SOL_SOCKET
SO_REUSEADDR = w.SO_REUSEADDR


_global_ws = w.WinsockSession()
_global_ws.start()


class socket:
    """Minimal socket-like object backed by `winsock_ctypes`."""

    def __init__(self, family: int = AF_INET, sock_type: int = SOCK_STREAM, proto: int = 0) -> None:
        # Initialize a socket with the given address family, socket type, and protocol
        # Stores parameters and creates the underlying Winsock socket via winsock_ctypes
        self._family = family
        self._sock_type = sock_type
        self._proto = proto
        self._sock = w.create_socket(family, sock_type, proto)

    @classmethod
    def _from_handle(cls, handle: int) -> "socket":
        # Creates a socket instance from an existing Winsock socket handle
        # Used internally by accept() to wrap accepted client connections
        obj = cls.__new__(cls)
        obj._family = AF_INET
        obj._sock_type = SOCK_STREAM
        obj._proto = IPPROTO_TCP
        obj._sock = handle
        return obj

    def setsockopt(self, level: int, optname: int, value: int) -> None:
        # Sets socket options (e.g., SO_REUSEADDR) using the underlying Winsock layer
        w.setsockopt(self._sock, level, optname, value)

    def bind(self, address: Tuple[str, int]) -> None:
        # Binds the socket to a (host, port) address for listening
        host, port = address
        _global_ws.bind(self._sock, host, port)

    def listen(self, backlog: int = 1) -> None:
        # Marks the socket as listening for incoming connections
        # backlog specifies the max number of queued connections
        _global_ws.listen(self._sock, backlog)

    def accept(self) -> Tuple["socket", Tuple[str, int]]:
        # Accepts an incoming client connection
        # Returns a tuple of (client_socket, (peer_host, peer_port))
        client_handle, peer_host, peer_port = _global_ws.accept(self._sock)
        return socket._from_handle(client_handle), (peer_host, peer_port)

    def connect(self, address: Tuple[str, int]) -> None:
        # Connects the socket to a remote (host, port) address
        host, port = address
        _global_ws.connect(self._sock, host, port)

    def send(self, data: bytes) -> int:
        # Sends data through the socket and returns the number of bytes sent
        # Ensures all data is sent by using send_all internally
        _global_ws.send_all(self._sock, data)
        return len(data)

    def recv(self, bufsize: int = 4096) -> bytes:
        # Receives up to bufsize bytes from the socket
        # Returns empty bytes if the connection is closed
        return _global_ws.recv_some(self._sock, size=bufsize)

    def shutdown(self, how: int = 2) -> None:
        # Gracefully shuts down the socket connection (how=2 means both send and receive)
        _global_ws.shutdown_socket(self._sock, how)

    def close(self) -> None:
        # Closes the socket and releases resources
        # Safe to call multiple times on the same socket
        if getattr(self, "_sock", w.INVALID_SOCKET) != w.INVALID_SOCKET:
            _global_ws.close_socket(self._sock)
            self._sock = w.INVALID_SOCKET

    def fileno(self) -> int:
        # Returns the underlying Winsock socket handle (file descriptor number)
        # Used for compatibility with standard socket interface
        return self._sock


def socketpair() -> Tuple[socket, socket]:
    # Creates a pair of connected sockets (not implemented for Winsock)
    # Raises NotImplementedError as this feature is not supported on Windows
    raise NotImplementedError("socketpair() is not supported by pywinsock_compat")


def socket_factory(family: int = AF_INET, sock_type: int = SOCK_STREAM, proto: int = 0) -> socket:
    # Factory function to create socket instances
    # Provides an alternative way to construct sockets with default parameters
    return socket(family, sock_type, proto)


__all__ = [
    "socket",
    "socket_factory",
    "AF_INET",
    "SOCK_STREAM",
    "SOCK_RAW",
    "IPPROTO_TCP",
    "IPPROTO_RAW",
    "SOL_SOCKET",
    "SO_REUSEADDR",
]
