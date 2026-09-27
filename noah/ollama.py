"""Small, local-only Ollama adapter. It has no database or credential access."""

import http.client
import json
import socket
import subprocess


HOST = "127.0.0.1"
PORT = 11435
MODEL = "gemma4:12b-it-qat"


class OllamaUnavailable(Exception):
    pass


class OllamaTimeout(Exception):
    pass


class OllamaUnsafeBinding(Exception):
    pass


class OllamaInvalidResponse(Exception):
    pass


def require_loopback_listener():
    """Fail closed if the dedicated Windows listener is absent or network-facing."""
    try:
        result = subprocess.run(
            [r"C:\Windows\System32\netstat.exe", "-ano", "-p", "tcp"],
            capture_output=True, text=True, timeout=3, check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise OllamaUnsafeBinding("Ollama listener could not be verified") from error

    listeners = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) < 4 or fields[0].upper() != "TCP" or fields[3].upper() != "LISTENING":
            continue
        address, separator, port = fields[1].rpartition(":")
        if separator and port == str(PORT):
            listeners.append(address.strip("[]"))
    if not listeners or any(address not in {HOST, "::1"} for address in listeners):
        raise OllamaUnsafeBinding("Ollama listener is not loopback-only")


class OllamaClient:
    def complete(self, messages, schema, max_tokens):
        require_loopback_listener()
        payload = json.dumps({
            "model": MODEL,
            "messages": messages,
            "format": schema,
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "num_predict": max_tokens, "num_ctx": 4096, "num_gpu": 0},
        }, ensure_ascii=False).encode("utf-8")
        connection = http.client.HTTPConnection(HOST, PORT, timeout=60)
        try:
            connection.request("POST", "/api/chat", body=payload,
                headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            raw = response.read(65537)
            if response.status != 200:
                raise OllamaUnavailable("Ollama request failed")
            if len(raw) > 65536:
                raise OllamaInvalidResponse("Ollama response is too large")
            result = json.loads(raw)
            content = result["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Missing model content")
            output = json.loads(content)
            if not isinstance(output, dict):
                raise ValueError("Model output is not an object")
            return output
        except (socket.timeout, TimeoutError) as error:
            raise OllamaTimeout("Ollama request timed out") from error
        except (OSError, http.client.HTTPException) as error:
            raise OllamaUnavailable("Ollama connection failed") from error
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise OllamaInvalidResponse("Ollama returned invalid structured output") from error
        finally:
            connection.close()
