import socket
import time
import threading

_g_SETOPT_VAL = 1
_g_initialized = False
_g_done = False


def server_logic():
    RECV_BUF_SZ = 1024

    while not _g_done:
        # Wait for connection
        try:
            sock, addr = g_server.accept()
        except socket.timeout:
            continue

        print(f"SERVER: New connection from IP - {addr[0]}, PORT - {addr[1]}")

        # Print connection info
        sock_info = sock.getsockname()
        print("SERVER: Socket created to serve connection: (%s, %d)"
              % (sock_info[0], sock_info[1]))

        # Wait for data from connection
        buf = sock.recv(RECV_BUF_SZ)  # Blocking call

        if buf:
            # Something was received
            print(f"SERVER: Received dummy data [{buf}]")
            time.sleep(0.25)  # Add in processing delay

            #  Send response
            sock.sendto(b'100', addr)

        sock.close()


def init(port):
    global g_server
    global _g_server_thread
    global _g_initialized

    SOCKET_TIMEOUT = 0.5

    if _g_initialized:
        raise RuntimeError("Server already initialized")

    # Configure the server
    g_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    g_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, _g_SETOPT_VAL)
    g_server.settimeout(SOCKET_TIMEOUT)  # Timeout for non-blocking socket

    server_addr = ('', port)  # Listen on all interfaces

    g_server.bind(server_addr)  # Bind to the socket
    g_server.listen(5)  # Allow queue of 5 clients

    _g_server_thread = threading.Thread(target=server_logic)

    _g_initialized = True
    print("SERVER: Initialized")


def start():
    if not _g_initialized:
        raise RuntimeError("Server not initialized")

    _g_server_thread.start()
    print("SERVER: Thread started")


def signal_stop():
    global _g_done
    _g_done = True

    _g_server_thread.join()  # Wait to return until server is closed
    print("SERVER: Thread stopped")
