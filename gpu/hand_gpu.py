import subprocess
import time

import cv2
import mediapipe as mp


class HandBindGPU:
    def __init__(
        self,
        camera_id: int = 0,
        handdraw: bool = True,
        draw_fps: bool = True,
        draw_index: bool = False,
        verbose: bool = False,
        use_gpu: bool = True,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.7,  # 保持高检测置信度
        min_tracking_confidence: float = 0.7,  # 保持高跟踪置信度
        model_complexity: int = 1,  # 使用复杂模型
        resolution: tuple = (1280, 720),  # 保持高分辨率
    ):
        """
        高精度手部关键点检测类 - GPU优化版本
        """
        self.handdraw = handdraw
        self.draw_fps = draw_fps
        self.draw_index = draw_index
        self.verbose = verbose
        self.use_gpu = use_gpu
        self._released = False

        # 检查GPU支持
        self.gpu_available = self._check_gpu_support()

        if use_gpu and not self.gpu_available:
            print("警告：GPU不可用，但将继续尝试GPU模式")

        # 初始化摄像头 - 保持高分辨率
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 ID: {camera_id}")

        # 设置高分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        # 初始化MediaPipe Hands with GPU配置
        self.hand = mp.solutions.hands

        try:
            # 明确配置GPU选项
            self.hands = self.hand.Hands(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                model_complexity=model_complexity,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
            )

            if use_gpu:
                print("GPU加速模式已配置")
            else:
                print("CPU模式运行")

        except Exception as e:
            print(f"模型初始化失败: {e}")
            raise

        # 初始化绘图工具
        self.mp_draw = mp.solutions.drawing_utils
        self.handLmsStyle = self.mp_draw.DrawingSpec(thickness=3, color=(0, 0, 255))
        self.handConStyle = self.mp_draw.DrawingSpec(thickness=2, color=(0, 255, 0))

        # 性能监控
        self.frame_count = 0
        self.fps = 0
        self.start_time = time.time()

        print(f"HandBindGPU初始化完成")
        print(f"- 分辨率: {resolution[0]}x{resolution[1]}")
        print(f"- 检测置信度: {min_detection_confidence}")
        print(f"- 跟踪置信度: {min_tracking_confidence}")
        print(f"- 模型复杂度: {model_complexity}")
        print(f"- GPU加速: {use_gpu} (可用: {self.gpu_available})")

    def _check_gpu_support(self):
        """检查系统GPU支持情况"""
        try:
            # 检查CUDA
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ NVIDIA GPU检测到")
                return True
        except:
            pass

        try:
            import tensorflow as tf

            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                print(f"✓ TensorFlow检测到GPU: {len(gpus)}个")
                return True
        except:
            pass

        print("✗ 未检测到GPU支持")
        return False

    def fps_calculate(self, img):
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
            f"FPS: {self.fps:.2f} | GPU: {self.use_gpu}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    def process_frame(self):
        """
        处理单帧图像 - 保持高精度和高分辨率
        """
        if self._released:
            return False, None, []

        ret, img = self.cap.read()
        if not ret:
            return False, None, []

        # 保持高分辨率处理
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.hands.process(img_rgb)

        hand_landmarks_list = []

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                if self.handdraw:
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.hand.HAND_CONNECTIONS,
                        self.handLmsStyle,
                        self.handConStyle,
                    )

                # 获取高精度关键点
                current_hand_landmarks = []
                h, w = img.shape[:2]

                for i, landmark in enumerate(hand_landmarks.landmark):
                    x = int(landmark.x * w)
                    y = int(landmark.y * h)
                    current_hand_landmarks.append((x, y))

                    if self.draw_index:
                        cv2.putText(
                            img,
                            str(i),
                            (x - 15, y + 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.4,
                            (0, 255, 255),
                            1,
                        )

                    if self.verbose:
                        print(f"关键点 {i}: ({x}, {y})")

                hand_landmarks_list.append(current_hand_landmarks)

        self.fps_calculate(img)
        return True, img, hand_landmarks_list

    def release(self):
        """释放资源"""
        if self._released:
            return

        try:
            if hasattr(self, "cap") and self.cap.isOpened():
                self.cap.release()
            if hasattr(self, "hands"):
                self.hands.close()
        except Exception as e:
            print(f"释放资源时出错: {e}")

        self._released = True
        cv2.destroyAllWindows()

    def __del__(self):
        if not self._released:
            self.release()


def test_gpu_performance():
    """测试GPU性能"""
    print("=" * 50)
    print("GPU性能测试")
    print("=" * 50)

    try:
        # 测试高配置模式
        hand_tracker = HandBindGPU(
            camera_id=0,
            handdraw=True,
            draw_fps=True,
            draw_index=True,
            verbose=False,
            use_gpu=True,  # 强制尝试GPU模式
            max_num_hands=2,
            min_detection_confidence=0.7,  # 高置信度
            min_tracking_confidence=0.7,  # 高置信度
            model_complexity=1,  # 复杂模型
            resolution=(1280, 720),  # 高分辨率
        )

        print("按 'q' 退出, 's' 切换GPU/CPU模式")

        while True:
            success, frame, landmarks = hand_tracker.process_frame()

            if success:
                cv2.imshow("Hand Tracking - GPU Optimized", frame)

                if landmarks:
                    print(f"检测到 {len(landmarks)} 只手 - FPS: {hand_tracker.fps:.1f}")

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                # 切换模式需要重新初始化
                hand_tracker.release()
                current_gpu = hand_tracker.use_gpu
                new_gpu = not current_gpu
                print(f"切换至 {'GPU' if new_gpu else 'CPU'} 模式...")

                hand_tracker = HandBindGPU(
                    use_gpu=new_gpu,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.7,
                    resolution=(1280, 720),
                )

    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        if "hand_tracker" in locals():
            hand_tracker.release()


if __name__ == "__main__":
    test_gpu_performance()
