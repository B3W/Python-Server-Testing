import socket
# import singlethreaded_server as server
import multithreaded_server as server
# import select_server as server
import time
import threading

_g_SETOPT_VAL = 1
_g_RECV_BUF_SZ_BYTES = 1024
_g_CLIENT_SPAWN_DELAY_S = 0.1


def client_connection(cli_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Configure
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, _g_SETOPT_VAL)
        s.settimeout(2.0)

        # Create connection
        s.connect(server_addr)
        print(f"CLIENT{cli_id}: Connection Complete; Sending Data")

        # Send data to server
        s.send(bytes([cli_id]))

        # Wait for response then close
        try:
            buf, addr = s.recvfrom(_g_RECV_BUF_SZ_BYTES)
            print(f"CLIENT{cli_id}: Response from server [{buf}]")

        except socket.timeout:
            print(f"CLIENT{cli_id}: Timed out")

    print(f"CLIENT{cli_id}: Connection Closed")


if __name__ == '__main__':
    server_port = 3535
    server_addr = ('127.0.0.1', server_port)
    cli_cnt = 5

    print("MAIN: START")
    start_time = time.clock()

    # Startup server on separate thread
    server.init(server_port)
    server.start()

    # Create specified number of clients
    print("MAIN: SPAWNING CLIENTS")
    client_threads = []

    for i in range(cli_cnt):
        # Spawn thread for each new client connection
        print(f"MAIN: CREATING CLIENT THREAD {i}")
        thread = threading.Thread(target=client_connection, args=(i,))
        thread.start()

        client_threads.append(thread)

        # Wait to spawn next thread
        time.sleep(_g_CLIENT_SPAWN_DELAY_S)

    # Wait for client threads to terminate
    for i in range(cli_cnt):
        client_threads[i].join()

    print("MAIN: CLIENT THREADS TERMINATED")

    # Signal server to exit
    server.signal_stop()

    end_time = time.clock()
    elapsed_time = end_time - start_time

    print("MAIN: END")
    print(f"MAIN: Time Elapsed - {elapsed_time:.4f}s")
