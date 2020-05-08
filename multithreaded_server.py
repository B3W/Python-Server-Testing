import socket
import time
import threading

_g_SETOPT_VAL = 1
_g_initialized = False
_g_done = False
_g_RECV_BUF_SZ = 1024


def thread_logic(tid, sock, addr):
    # Print connection info
    print(f"STHREAD{tid}: New connection from IP- {addr[0]}, PORT- {addr[1]}")

    sock_info = sock.getsockname()
    print("STHREAD%d: Socket created to serve connection: (%s, %d)"
          % (tid, sock_info[0], sock_info[1]))

    # Wait for data from connection
    buf = sock.recv(_g_RECV_BUF_SZ)  # Blocking call

    if buf:
        # Something was received
        print(f"STHREAD{tid}: Received dummy data [{buf}]")

        #  Send response
        sock.sendto(b'101', addr)

    time.sleep(0.5)  # Add in processing delay
    sock.close()
    print(f"STHREAD{tid}: Finished")


def server_logic():
    thread_list = []
    thread_cnt = 0

    while not _g_done:
        # Wait for connection
        try:
            sock, addr = g_server.accept()
        except socket.timeout:
            continue

        # Spawn thread to handle new connection
        thread = threading.Thread(target=thread_logic,
                                  args=(thread_cnt, sock, addr))
        thread.start()

        thread_list.append(thread)  # Track all threads
        thread_cnt += 1

    for t in thread_list:
        t.join()

    print("SERVER: Server stopped")


def init(port):
    global g_server
    global _g_server_thread
    global _g_initialized

    SOCKET_TIMEOUT = 0.5

    if _g_initialized:
        raise RuntimeError('Server already initialized')

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
