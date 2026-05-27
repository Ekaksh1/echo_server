# TCP Echo Server

This folder contains a tiny raw-socket TCP echo demo:

- `server.py` starts a single-client echo server.
- `client.py` connects to the server and echoes messages back.

## Run it

Open two terminals in this folder.

Start the server:

```powershell
python server.py
```

Start the client in the second terminal:

```powershell
python client.py
```

After it connects, type your custom message at the `Message>` prompt and press Enter.
The server sends the same text back.

To exit safely, type `quit` or press `Ctrl+C` in either terminal.
If the client starts before the server, it will print a friendly connection message instead of a traceback.

Optional host and port arguments are available on both scripts:

```powershell
python server.py --host 127.0.0.1 --port 65432
python client.py --host 127.0.0.1 --port 65432
```