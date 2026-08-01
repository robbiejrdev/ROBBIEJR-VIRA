# ROBBIEJR VIRA

A polished, multi-protocol reverse shell and reconnaissance toolkit built in Python.

## Overview

`VIRA/main.py` supports interactive reverse shell operations over:

- `tcp`
- `udp`
- `async` (asyncio-based)

It includes styled CLI feedback, file upload/download support, directory navigation, and delete commands.

## Features

- beautiful banner and colored terminal UI
- transport modes: TCP, UDP, and asyncio
- reverse shell client/server support
- file transfer: `upload` / `download`
- delete support: `delete` / `del`
- remote `cd` command handling
- async command output marker for reliable streaming

## Requirements

- Python 3.8+
- Linux / macOS / compatible terminal supporting ANSI colors

## Install

No install step is required. Run the script directly from the `VIRA/` folder.

## Quick Start

Start the server:

```bash
python3 VIRA/main.py --mode tcp --listen
```

Start an async server:

```bash
python3 VIRA/main.py --mode async --listen
```

Connect with the client:

```bash
python3 VIRA/main.py --mode tcp --connect 127.0.0.1 --port 9999
```

Connect with async mode:

```bash
python3 VIRA/main.py --mode async --connect 127.0.0.1 --port 9999
```

## Example Commands

Inside the shell prompt:

- `ls`
- `pwd`
- `cd /path/to/folder`
- `upload localfile.txt`
- `download remotefile.txt`
- `delete secret.txt`
- `del secret.txt`
- `clear`
- `exit`

## Command-Line Options

- `-q`, `--dont-load-banner` - suppress banner output
- `-pr`, `--proxies` - load proxies file (future use)
- `-l`, `--listen` - start in server/listen mode
- `-c`, `--connect` - target host to connect to as client
- `-t`, `--target` - alternate client host option
- `-p`, `--port` - port to use (default `9999`)
- `-a`, `--auto` - automatic reconnaissance flag
- `-m`, `--manual` - manual reconnaissance flag
- `-ml`, `--mode` - protocol mode: `tcp`, `udp`, or `async`

## Notes

- `async` mode uses `asyncio` and has the fastest interactive behavior.
- Upload/download commands send files in a raw stream and rely on the server acknowledging readiness.
- `delete` / `del` remove a remote file from the current server working directory.

## License

MIT License

## Repository Structure

- `VIRA/main.py` — main reverse shell toolkit
- `main.c` — separate C file in repository root
