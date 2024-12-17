import cv2

# url = "rtsp://admin:KameraNr4@192.168.178.51:554/ch1/main/av_stream"
url = "rtsp://admin:KameraNr1@192.168.178.38:554/ch1/main/av_stream"
#"rtsp://<Username>:<Password>@<IP Address>:<Port>/cam/realmonitor?channel=1&subtype=0"

cam = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
flag, frame = cam.read()
print(flag, frame)
if flag:
    # Following example from 
    # https://github.com/god233012yamil/Streaming-IP-Cameras-Using-PyQt-and-OpenCV
    # Get the frame height, width, channels, and bytes per line
    height, width, channels = frame.shape
    bytes_per_line = width * channels
    # image from BGR (cv2 default color format) to RGB (Qt default color format)
    cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('test', cv_image)
    cv2.waitKey(0)
flag, frame = cam.read()
if flag:
    # Following example from 
    # https://github.com/god233012yamil/Streaming-IP-Cameras-Using-PyQt-and-OpenCV
    # Get the frame height, width, channels, and bytes per line
    height, width, channels = frame.shape
    bytes_per_line = width * channels
    # image from BGR (cv2 default color format) to RGB (Qt default color format)
    cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('test', cv_image)
    cv2.waitKey(0)

cv2.destroyAllWindows()