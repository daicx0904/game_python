import cv2

from game import hand as hb


def main():
    """测试函数"""
    try:
        hand_bind = hb.HandBind(
            camera_id=0,
            handdraw=True,  # 绘制手部连线
            draw_fps=True,  # 绘制FPS
            draw_index=False,  # 绘制关键点编号
            verbose=False,  # 不在控制台打印坐标
        )

        # 显示摄像头分辨率
        width, height = hand_bind.get_camera_resolution()
        print(f"摄像头分辨率: {width}x{height}")

        print("按 'q' 退出程序")
        print("按 'd' 切换手部连线绘制")
        print("按 'f' 切换FPS显示")
        print("按 'i' 切换关键点编号显示")

        while True:
            success, processed_img, landmarks = hand_bind.process_frame()

            if success:
                # landmarks 是一个列表，每个元素代表一只手的关键点坐标
                # 每个手的坐标是一个包含21个(x, y)元组的列表
                if landmarks:
                    for hand_index, hand_landmarks in enumerate(landmarks):
                        print(f"检测到手 {hand_index}: {len(hand_landmarks)} 个关键点")

                cv2.imshow("Hand Detection - GPU Accelerated", processed_img)

            # 键盘控制
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("d"):
                hand_bind.handdraw = not hand_bind.handdraw
                print(f"手部连线绘制: {'开启' if hand_bind.handdraw else '关闭'}")
            elif key == ord("f"):
                hand_bind.draw_fps = not hand_bind.draw_fps
                print(f"FPS显示: {'开启' if hand_bind.draw_fps else '关闭'}")
            elif key == ord("i"):
                hand_bind.draw_index = not hand_bind.draw_index
                print(f"关键点编号显示: {'开启' if hand_bind.draw_index else '关闭'}")

    except Exception as e:
        print(f"初始化失败: {e}")
    finally:
        if "hand_bind" in locals():
            hand_bind.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
