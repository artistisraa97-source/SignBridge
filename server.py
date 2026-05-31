import json
import os
import subprocess
import sys
import threading
import time

from http.server import (
    ThreadingHTTPServer,
    SimpleHTTPRequestHandler
)

from urllib.parse import urlparse

# =========================================
# CONFIG
# =========================================

SCRIPT_NAME = "predict_words.py"

VIDEOS_DIR = "assets/videos"

OUTPUT_VIDEO = "assets/videos/final_translation.mp4"

# =========================================
# PYTHON EXECUTABLE
# =========================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VENV_PYTHON = os.path.join(
    BASE_DIR,
    "clean_env",
    "Scripts",
    "python.exe"
)

PYTHON_EXECUTABLE = (
    VENV_PYTHON
    if os.path.exists(VENV_PYTHON)
    else sys.executable
)

# =========================================
# GLOBALS
# =========================================

process = None

output_lines = []

lock = threading.Lock()

# =========================================
# CLEANUP PROCESS
# =========================================

def cleanup_process():

    global process

    if process and process.poll() is None:

        try:

            process.terminate()

            process.wait(timeout=3)

        except subprocess.TimeoutExpired:

            process.kill()

            process.wait()

        except Exception:
            pass

    process = None

# =========================================
# STORE OUTPUT
# =========================================

def append_output(line):

    global output_lines

    line = line.strip()

    if not line:
        return

    with lock:

        output_lines.append(line)

        # keep last 100 lines
        if len(output_lines) > 100:

            output_lines = output_lines[-100:]

# =========================================
# READ PROCESS OUTPUT
# =========================================

def read_output(proc):

    try:

        for line in proc.stdout:

            print(line.strip())

            append_output(line)

    except Exception as e:

        append_output(f"ERROR: {e}")

# =========================================
# COMBINE VIDEOS
# =========================================

def combine_videos(sentence):

    try:

        words = sentence.strip().lower().split()

        if not words:

            return {
                "success": False,
                "error": "Empty sentence"
            }

        video_files = []

        missing_words = []

        for word in words:

            clean_word = ''.join(
                c for c in word
                if c.isalnum()
            )

            video_path = os.path.join(
                VIDEOS_DIR,
                f"{clean_word}.mp4"
            )

            if os.path.exists(video_path):

                video_files.append(video_path)

            else:

                missing_words.append(clean_word)

        if not video_files:

            return {
                "success": False,
                "error":
                    f"No videos found for: {', '.join(missing_words)}"
            }

        # =====================================
        # CREATE CONCAT FILE
        # =====================================

        concat_file = "temp_concat.txt"

        with open(concat_file, "w", encoding="utf-8") as f:

            for video in video_files:

                abs_path = os.path.abspath(video)

                f.write(f"file '{abs_path}'\n")

        # =====================================
        # RUN FFMPEG
        # =====================================

        result = subprocess.run(
            [
                "ffmpeg",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_file,
                "-c",
                "copy",
                "-y",
                OUTPUT_VIDEO
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # delete temp file
        if os.path.exists(concat_file):

            os.remove(concat_file)

        if (
            result.returncode == 0
            and
            os.path.exists(OUTPUT_VIDEO)
        ):

            return {
                "success": True,
                "video_url":
                    "/assets/videos/final_translation.mp4",

                "sentence":
                    " ".join(words),

                "missing_words":
                    missing_words if missing_words else []
            }

        else:

            return {
                "success": False,
                "error": "FFmpeg failed",
                "details": result.stderr
            }

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "error": "FFmpeg timeout"
        }

    except FileNotFoundError:

        return {
            "success": False,
            "error": "FFmpeg not installed"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# =========================================
# HTTP HANDLER
# =========================================

class Handler(SimpleHTTPRequestHandler):

    # =====================================
    # JSON RESPONSE
    # =====================================

    def _json(self, data, status=200):

        payload = json.dumps(data).encode()

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(payload))
        )

        self.end_headers()

        self.wfile.write(payload)

    # =====================================
    # GET
    # =====================================

    def do_GET(self):

        global process

        path = urlparse(self.path).path

        # =================================
        # START REALTIME
        # =================================

        if path == "/realtime/start":

            with lock:

                cleanup_process()

                output_lines.clear()

                try:

                    process = subprocess.Popen(
                        [
                            PYTHON_EXECUTABLE,
                            "-u",
                            SCRIPT_NAME,
                            "--headless"
                        ],

                        stdout=subprocess.PIPE,

                        stderr=subprocess.STDOUT,

                        text=True,

                        bufsize=1,

                        cwd=BASE_DIR
                    )

                    threading.Thread(
                        target=read_output,
                        args=(process,),
                        daemon=True
                    ).start()

                    self._json({
                        "running": True,
                        "message": "Realtime started"
                    })

                except Exception as e:

                    self._json({
                        "running": False,
                        "message": str(e)
                    }, 500)

            return

        # =================================
        # STOP
        # =================================

        if path == "/realtime/stop":

            with lock:

                cleanup_process()

                self._json({
                    "running": False,
                    "message": "Stopped"
                })

            return

        # =================================
        # STATUS
        # =================================

        if path == "/realtime/status":

            with lock:

                running = (
                    process is not None
                    and
                    process.poll() is None
                )

                self._json({

                    "running": running,

                    "message":
                        "running"
                        if running
                        else "stopped",

                    "output":
                        "\n".join(output_lines[-30:])
                })

            return

        return super().do_GET()

    # =====================================
    # POST
    # =====================================

    def do_POST(self):

        path = urlparse(self.path).path

        # =================================
        # COMBINE VIDEOS
        # =================================

        if path == "/combine-videos":

            try:

                content_length = int(
                    self.headers.get(
                        "Content-Length",
                        0
                    )
                )

                body = self.rfile.read(
                    content_length
                ).decode("utf-8")

                data = json.loads(body)

                sentence = data.get(
                    "sentence",
                    ""
                ).strip()

                if not sentence:

                    self._json({
                        "success": False,
                        "error": "No sentence"
                    }, 400)

                    return

                result = combine_videos(sentence)

                self._json(result)

            except Exception as e:

                self._json({
                    "success": False,
                    "error": str(e)
                }, 500)

            return

        self.send_error(404)

# =========================================
# START SERVER
# =========================================

if __name__ == "__main__":

    os.chdir(BASE_DIR)

    PORT = 8000

    print(
        f"Using Python: {PYTHON_EXECUTABLE}"
    )

    if PYTHON_EXECUTABLE != sys.executable:

        print(
            "Using virtual environment"
        )

    server = ThreadingHTTPServer(
        ("0.0.0.0", PORT),
        Handler
    )

    print("\n=================================")
    print("SERVER RUNNING")
    print("=================================")

    print(
        f"http://127.0.0.1:{PORT}/translate.html"
    )

    print("\nEndpoints:")

    print("/realtime/start")
    print("/realtime/stop")
    print("/realtime/status")
    print("/combine-videos")

    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print("\nStopping server...")

        cleanup_process()

        server.shutdown()