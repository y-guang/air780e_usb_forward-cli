## AT Command Syntax

All commands in this manual must start with AT or at and end with a carriage return `<CR>`.

Responses are returned immediately after the command, in the format:`<CR><LF><response content><CR><LF>`

Example message from AIR780E:

```bash
# send
41 54 2B 43 47 4D 49 0D 0A
# reply
41 54 2B 43 47 4D 49 0D 0A
0D 0A
2B 43 47 4D 49 3A 20 22 41 69 72 4D 32 4D 22 0D 0A
0D 0A
4F 4B 0D 0A
```

## Framework

- Ubuntu 24.04 LTS
- uv + python 3.12

## Style guide

- Minimal Design. It's a lightweight cli tools rather than complete framework.
- use modern python syntax (type hinting assuming python 3.12+)