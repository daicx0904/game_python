import cv2

import hand as hd


def test():
    freetype = cv2.freetype.createFreeType2()
    freetype.loadFontData(fontFileName="simhei.ttf", id=0)
    hand = hd.HandBind(
        camera_id=0,
        handdraw=True,
        draw_fps=True,
        draw_index=True,
        verbose=False,
    )
    while True:
        success, processed_img, landmarks = hand.process_frame()

        if success:
            if landmarks:
                print(landmarks[0][8])
            # for hand_index, hand_landmarks in enumerate(landmarks):
            # print(f"Hand {hand_index} has {len(hand_landmarks)} landmarks")

            cv2.imshow("Video Frame", processed_img)

        if cv2.waitKey(1) == ord("q"):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    test()
