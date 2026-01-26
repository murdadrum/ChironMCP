how do I restart/stop my local :8000?

On macOS, the quickest way is:

Find the PID using port 8000:
lsof -nP -iTCP:8000 -sTCP:LISTEN
Stop it:
kill <PID>
If it won’t stop: kill -9 <PID>
Alternative (if it’s uvicorn/uv run):

pkill -f "chiron_mcp_server.server"
(or whatever command string you launched it with)
If you want, tell me the output of lsof and I’ll point to the exact PID.

Last login: Sat Jan 24 18:50:28 on ttys014
murdadrum@murdabook2000 ~ % lsof -nP -iTCP:8000 -sTCP:LISTEN
COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
Python 53550 murdadrum 6u IPv4 0xad151f9cfbaa525a 0t0 TCP 127.0.0.1:8000 (LISTEN)
murdadrum@murdabook2000 ~ % kill 53550
murdadrum@murdabook2000 ~ % lsof -nP -iTCP:8000 -sTCP:LISTEN
murdadrum@murdabook2000 ~ %
