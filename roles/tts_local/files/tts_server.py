from flask import Flask, request
from time import perf_counter
import subprocess
import queue
import logging
import threading
import uuid
import shlex
import tempfile

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
tts_q = queue.Queue(maxsize=200)

flaskLogger = logging.getLogger("request_Handler")


def tts_worker():
    logger = logging.getLogger("tts_Worker")

    while True:
        speed, text, req_id = tts_q.get()
        logger.info("Processing request with id %s", req_id)

        t = perf_counter()

        logger.warning(
            "Ignoring speed argument with value '%s' for request id %s, reason: not implemented",
            speed,
            req_id,
        )

        try:
            with tempfile.TemporaryFile("w+") as tf:
                tf.write(shlex.quote(text))
                tf.seek(0)  # XXX: implies flush under CPython
                # tf.flush()
                subprocess.run(
                    [
                        "RHVoice-test",
                        "-p",
                        "Letícia-F123",
                    ],
                    stdin=tf,
                )
        except subprocess.CalledProcessError:
            # internal issue, requires some attention
            logger.error(
                "request with id %s failed: Text-To-Speech job ended with nonzero status, text='%s',speed='%s'",
                req_id,
                text,
                speed,
                exc_info=True,
            )
        else:
            logger.info("Succesfully processed request with id %s", req_id)
        finally:
            t_stop = perf_counter()
            tts_q.task_done()
            logger.info("Elapsed: %d", t_stop - t)


worker_thread = threading.Thread(target=tts_worker, daemon=True)
worker_thread.start()


@app.route("/")
def speak():
    req_id = uuid.uuid1()
    flaskLogger.info("Enqueuing request %s", req_id)

    speed = request.args.get("speed")
    if not speed:
        speed = "350"
    text = request.args.get("text")
    if not text:
        # warning because this is probably a user issue
        flaskLogger.warning(
            "Malformed request with id %s, missing 'text' parameter", req_id
        )
        return 'Missing "text" parameter', 400
    try:
        tts_q.put((speed, text, req_id), timeout=5)
        flaskLogger.info(
            "Succesfully enqueued request with id %s, params: %s '%s'",
            req_id,
            speed,
            text,
        )
        return "request queued", 204
    except queue.Full:
        flaskLogger.error("Could not enqueue request with id %s, queue is full", req_id)
        return "queue is full", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
