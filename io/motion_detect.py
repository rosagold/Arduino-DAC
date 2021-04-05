import numpy as np
import cv2


def open_cam(w, h):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    return cap


if __name__ == '__main__':
    cap = open_cam(400, 600)
    _, frame1 = cap.read()

    while cap.isOpened():
        frame0 = frame1
        _, frame1 = cap.read()
        diff = cv2.absdiff(frame0, frame1)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (15, 15), 0)
        _, thresh = cv2.threshold(blur, 15, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=5)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cv2.drawContours(frame0, contours, -1, (0, 255, 0), 2)
        cv2.imshow('test1', blur)
        cv2.imshow('out', frame0)

        # escape
        if key := cv2.waitKey(10) == 27:
            break
