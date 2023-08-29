import cv2
import ffmpeg
import threading
import time
import sys


def write_data(process, raw_bytes):
    print(f"Write {len(raw_bytes)} bytes.")
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
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    process = (
        ffmpeg.input(
            "pipe:", format="rawvideo", pix_fmt="bgr24", s="{}x{}".format(width, height)
        )
        .output(
            "pipe:",
            format="webm",
            vcodec="libvpx",
            pix_fmt="yuv420p",
            s="{}x{}".format(width, height),
            r=fps,
        )
        .overwrite_output()
        .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
    )

    stderr_thread = threading.Thread(target=read_stderr, args=(process,))
    stderr_thread.start()

    time.sleep(1.0)

    with open("./hoge.webm", "wb") as f:
        while True:
            ret, frame = cap.read()

            raw_bytes = frame.tobytes()
            print(f"raw size: {len(raw_bytes)}")

            thread = threading.Thread(target=write_data, args=(process, raw_bytes))
            thread.start()

            encoded_bytes = process.stdout.read1()
            print(f"encoded size: {len(encoded_bytes)}")

            f.write(encoded_bytes)

            cv2.imshow("test", frame)
            c = cv2.waitKey(1)
            if c != -1:
                break

    cap.release()
    cv2.destroyAllWindows()
    sys.exit(1)


if __name__ == "__main__":
    main()
