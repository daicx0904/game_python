# import mediapipe.python as mp

import time

import cv2
import mediapipe as mp


class HandBind:
    def __init__(
        self,
        camera_id: int = 0,
        handdraw: bool = False,
        draw_fps: bool = False,
        draw_index: bool = False,
        verbose: bool = False,
        max_hands: int = 2,
        detection_confidence: float = 0.5,
        tracking_confidence: float = 0.5,
    ):

        self.handdraw = handdraw
        self.draw_fps = draw_fps
        self.draw_index = draw_index
        self.verbose = verbose
        self._released = False

        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 {camera_id}")

        self.hand = mp.solutions.hands
        self.hands = self.hand.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        self.mp_draw = mp.solutions.drawing_utils
        self.handLmsStyle = self.mp_draw.DrawingSpec(thickness=2, color=(0, 0, 255))
        self.handConStyle = self.mp_draw.DrawingSpec(thickness=2, color=(0, 255, 0))

        self.frame_count = 0
        self.fps = 0
        self.start_time = time.time()

    def fps_calculate(self, img) -> None:
        """计算并显示FPS"""
        if not self.draw_fps:
            return

        self.frame_count += 1
        elapsed_time = time.time() - self.start_time

        if elapsed_time >= 1:
            self.fps = self.frame_count / elapsed_time
            self.frame_count = 0
            self.start_time = time.time()

        cv2.putText(
            img,
            f"FPS: {self.fps:.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    def process_frame(self):
        """处理单帧图像并返回处理后的图像和手部关键点坐标"""
        if self._released:
            return False, None, []

        ret, img = self.cap.read()
        if not ret:
            return False, None, []

        imgrgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.hands.process(imgrgb)

        img_height, img_width = img.shape[:2]
        hand_landmarks_list = []

        if result.multi_hand_landmarks:
            for hand_idx, handLms in enumerate(result.multi_hand_landmarks):
                if self.handdraw:
                    self.mp_draw.draw_landmarks(
                        img,
                        handLms,
                        self.hand.HAND_CONNECTIONS,
                        self.handLmsStyle,
                        self.handConStyle,
                    )

                current_hand_landmarks = []

                for i, lm in enumerate(handLms.landmark):
                    x_pos, y_pos = int(lm.x * img_width), int(lm.y * img_height)

                    current_hand_landmarks.append((x_pos, y_pos))

                    if self.draw_index:
                        cv2.putText(
                            img,
                            str(i),
                            (x_pos - 15, y_pos + 5),
                            cv2.FONT_HERSHEY_COMPLEX,
                            0.3,
                            (0, 255, 255),
                            1,
                        )

                    if self.verbose and hand_idx == 0:
                        print(f"Hand {hand_idx}, Landmark {i}: ({x_pos}, {y_pos})")

                hand_landmarks_list.append(current_hand_landmarks)

        # img = cv2.flip(img, 1)
        self.fps_calculate(img)

        return True, img, hand_landmarks_list

    def get_img_size(self) -> tuple[int, int]:
        """返回摄像头的宽度和高度"""
        return int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(
            self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        )

    def __release(self):
        if self._released:
            return

        self._released = True

        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()

        if hasattr(self, "hands") and self.hands:
            try:
                self.hands.close()
            except Exception as e:
                print(f"关闭 MediaPipe hands 时出现警告: {e}")

        cv2.destroyAllWindows()
        print("资源已释放")

    def __del__(self):
        """释放资源"""
        if not self._released:
            self.__release()
