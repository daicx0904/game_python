import cv2

camera_list = []
for i in range(10):  # 假设最多有10个摄像头
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        camera_list.append(i)  # 添加可用摄像头的索引
        cap.release()  # 释放摄像头
print("可用摄像头ID:", camera_list)
