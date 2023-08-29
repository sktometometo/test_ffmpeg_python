import cv2
import ffmpeg
import threading
import time
import sys
import queue


class EncodedVideoRecorder:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        self.process = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="bgr24",
                s="{}x{}".format(self.width, self.height),
            )
            .output(
                "pipe:",
                format="webm",
                vcodec="libvpx-vp9",
                lossless=1,
                pix_fmt="yuv420p",
                s="{}x{}".format(self.width, self.height),
                r=self.fps,
            )
            .overwrite_output()
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )

        self.queue_raw_bytes = queue.Queue()
        self.queue_encoded_bytes = queue.Queue()

        self.running = True

        self.stderr_thread = threading.Thread(target=self.read_stderr)
        self.feed_encoding_thread = threading.Thread(target=self.feed_encode_data)
        self.get_encoding_thread = threading.Thread(target=self.get_encode_data)
        self.record_thread = threading.Thread(target=self.read_camera)
        self.save_file_thread = threading.Thread(target=self.save_file)

    def start(self):
        self.stderr_thread.start()
        self.feed_encoding_thread.start()
        self.get_encoding_thread.start()
        self.record_thread.start()
        self.save_file_thread.start()

    def stop(self):
        self.running = False

    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def read_camera(self):
        while self.running:
            ret, frame = self.cap.read()
            raw_bytes = frame.tobytes()
            self.queue_raw_bytes.put(raw_bytes)
            print("Read camera")

    def read_stderr(self):
        while self.running:
            line = self.process.stderr.readline()
            if line:
                print("ffmpeg error:", line.decode("utf-8").strip())
            else:
                break

    def feed_encode_data(self):
        while self.running:
            raw_bytes = self.queue_raw_bytes.get()
            self.process.stdin.write(raw_bytes)
            print(f"Encoding {len(raw_bytes)} bytes")

    # We have to separate stdout read1 from write since there seems some buffering and flushing
    # in process stdin/stdout.
    def get_encode_data(self):
        while self.running:
            encoded_bytes = self.process.stdout.read1()
            self.queue_encoded_bytes.put(encoded_bytes)
            print(f"Encoded to {len(encoded_bytes)} bytes")

    def save_file(self):
        with open("./hoge.webm", "wb") as f:
            while self.running:
                encoded_bytes = self.queue_encoded_bytes.get()
                f.write(encoded_bytes)
                print("Write bytes to file")


def main():
    r = EncodedVideoRecorder()
    time.sleep(1.0)
    r.start()
    while True:
        time.sleep(1.0)
        print(
            f"Input queue: {r.queue_raw_bytes.qsize()}, Encoded queue: {r.queue_encoded_bytes.qsize()}"
        )
        if cv2.waitKey(1) != -1:
            break
    r.stop()


if __name__ == "__main__":
    main()
