import cv2
import mediapipe as mp


# 极简版本
def simple_hand_detection():
    print("启动极简手部检测...")

    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # 初始化 MediaPipe Hands
    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    print("按 'q' 退出")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # 水平翻转
            frame = cv2.flip(frame, 1)

            # 转换颜色空间并处理
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            # 绘制检测结果
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS
                    )

            # 显示帧
            cv2.imshow("Simple Hand Detection", frame)

            # 退出条件
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        print(f"错误: {e}")
    finally:
        cap.release()
        hands.close()
        cv2.destroyAllWindows()
        print("程序结束")


if __name__ == "__main__":
    simple_hand_detection()
