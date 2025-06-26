from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys
import re
import socket
import json
import subprocess
import ssl
import psutil
import datetime

HOST = 'localhost'
PORT = 8080

def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:       
        st.connect(('10.255.255.255', 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        st.close()
    return IP

def full_stack():
    import traceback, sys
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
         stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr

def send_to_backend(action, path, data):
    with socket.create_connection(("localhost", 9009)) as sock:
        msg = json.dumps({"action": action, "path": path, "data": data}) + "\n"
        sock.sendall(msg.encode("utf-8"))

        # Receive full response until newline
        chunks = []
        while True:
            chunk = sock.recv(4096).decode("utf-8")
            if not chunk:
                break
            chunks.append(chunk)
            if "\n" in chunk:
                break

        full_msg = "".join(chunks)
        jsn = json.loads(full_msg.strip())
        response = json.dumps(jsn)
        return response

def cmdWrapper(action, path, data):
    with open("post.json", "w") as f:
        f.write(data)
    cmd = f"python -u handler.py {action} {path}"
    syms, err, exitCode = command(cmd)
    output = syms.decode("utf-8")
    jsn = ""
    lines = output.split("\n")
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        print(line)
        try:
            jsn = json.loads(line)
        except:
            pass
        idx += 1
    print(jsn)
    response = json.dumps(jsn)
    return response

def command(cmd, work_dir=None, showOutput=False):
    # f"bash -c '{cmd}'"
    process = subprocess.Popen(cmd,
                    cwd=work_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True)
    lines = []
    if showOutput:
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline().decode()
            if nextline == '' and process.poll() is not None:
                break
            lines.append(nextline)
            sys.stdout.write(nextline)
            sys.stdout.flush()
    syms, err = process.communicate(timeout=10)
    if len(syms) == 0:
        syms = "\n".join(lines)
    exitCode = process.returncode
    return syms, err, exitCode

def startHandler():
    procs = []
    # Find a process by name
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['name'] == "python.exe" and "handler.py" in proc.info["cmdline"]:
            procs.append(proc)
    if len(procs) > 0:
        proc = procs[0]
        proc.terminate()
        try:
            proc.wait(timeout=3)
            print(f"Terminated: {proc.info}")
        except psutil.TimeoutExpired:
            print(f"Timeout - killing: {proc.info}")
            proc.kill()

        dt = datetime.datetime.now()
        print(f"{dt} - starting server.py...")
        subprocess.Popen(
            'start "handler.py" python -u handler.py',
            cwd="C:\\projects\\InteractiveBrokers\\",
            shell=True
        )


class AccountSummaryHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            # Request summary (blocking call)
            response = send_to_backend("GET", self.path, [])
            if "Not connected" in response:
                self.send_response(503)
                startHandler()
            else:
                self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

    def do_POST(self):
        length = int(self.headers['content-length'])
        field_data = self.rfile.read(length).decode("utf-8")

        try:
            # Request summary (blocking call)
            response = send_to_backend("POST", self.path, field_data)
            if "Not connected" in response:
                self.send_response(503)
                startHandler()
            else:
                self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

    def do_DELETE(self):
        try:
            # Request summary (blocking call)
            response = send_to_backend("DELETE", self.path, [])
            if "Not connected" in response:
                self.send_response(503)
                startHandler()
            else:
                self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(bytes(response, "utf-8"))

        except Exception as e:
            print(full_stack())
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = json.dumps({'error': str(e)}).encode('utf-8')
            self.wfile.write(error_msg)

def run_server():
    HOST = extract_ip()
    server = HTTPServer((HOST, PORT), AccountSummaryHandler)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="ibkr\\cert.pem", keyfile="ibkr\\key.pem")

    # Wrap the socket using context
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print(f"Serving on http://{HOST}:{PORT}")
    server.serve_forever()


# === Models ===
class OrderRequest():
    symbol: str
    exchange: str = 'SMART'
    currency: str = 'USD'
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float = None  # for LIMIT order
    orderType: str = 'LMT'  # 'LMT' or 'MKT'

class CancelRequest():
    orderId: int

# === Routes ===

if __name__ == '__main__':
    run_server()


