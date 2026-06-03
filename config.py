"""Configuration settings for the echo server and client.

This module contains all configurable parameters to avoid hardcoding values.
"""
from __future__ import annotations

# Server Configuration
SERVER_HOST = "127.0.0.1"  # Server listening address
SERVER_PORT = 65432  # Server listening port
SERVER_BACKLOG = 1  # Max queued connections waiting to be accepted

# Buffer Configuration
MAX_BUFFER_SIZE = 65536  # Maximum buffer size (64 KB) - prevents memory exhaustion
MAX_MESSAGE_SIZE = 4096  # Maximum single message size
RECV_CHUNK_SIZE = 4096  # Size of data chunks to receive at once

# Timeout Configuration (in seconds)
GRACEFUL_SHUTDOWN_TIMEOUT = 5.0  # Time to wait for clients before force shutdown
CLIENT_IDLE_TIMEOUT = 300.0  # Disconnect idle clients after 5 minutes
CONNECT_TIMEOUT = 10.0  # Time to wait for server connection in client

# Client Configuration
CLIENT_HOST = "127.0.0.1"  # Client target host
CLIENT_PORT = 65432  # Client target port
CLIENT_CONNECT_TIMEOUT = 10.0  # Max time to wait for server connection

# RFC Protocol Ports (non-privileged defaults so no admin required)
# You can change these to the standard ports (7, 9, 17, 23) if running as admin
ECHO_PORT = 7007
DISCARD_PORT = 7009
QOTD_PORT = 7017
TELNET_PORT = 7023
