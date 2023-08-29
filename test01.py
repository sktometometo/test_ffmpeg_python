import cv2
import ffmpeg
import numpy as np
import threading
import time
import sys


def write_data(process, raw_bytes):
    process.stdin.write(raw_bytes)


def read_stderr(process):
    while True:
        line = process.stderr.readline()
        if line:
            print("ffmpeg error:", line.decode("utf-8").strip())
        else:
            break


def main():
    cap = cv2.VideoCapture(0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    process = (
        ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="bgr24", s="{}x{}".format(width, height)
        )
        .output(
            "pipe:", format="rawvideo", pix_fmt="bgr24", s="{}x{}".format(width, height)
        )
        .overwrite_output()
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    stderr_thread = threading.Thread(target=read_stderr, args=(process,))
    stderr_thread.start()

    time.sleep(1.0)

    while True:
        ret, frame = cap.read()

        raw_bytes = frame.tobytes()
        print(f"raw size: {len(raw_bytes)}")

        thread = threading.Thread(target=write_data, args=(process, raw_bytes))
        thread.start()

        encoded_bytes = process.stdout.read(width * height * 3)
        print(f"encoded size: {len(encoded_bytes)}")
        encoded_frame = np.frombuffer(encoded_bytes, dtype=np.uint8).reshape(
            height, width, 3
        )

        cv2.imshow("test", encoded_frame)
        c = cv2.waitKey(1)
        if c != -1:
            break

    cap.release()
    cv2.destroyAllWindows()
    sys.exit(1)


if __name__ == "__main__":
    main()
