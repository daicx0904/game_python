# TODO: 增加答题复活机制
import json
import os
import random
import time

import cv2

import hand as hd

mouse_position = (0, 0)
mouse_clicked = False


def mouse_callback(event, x, y, flags, param):
    """鼠标事件回调函数"""
    global mouse_position, mouse_clicked
    mouse_position = (x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        mouse_clicked = True
    elif event == cv2.EVENT_LBUTTONUP:
        mouse_clicked = False


class UserManager:
    def __init__(self, filename="users.json"):
        self.filename = filename
        self.users = self.load_users()
        self.current_user = None

    def load_users(self):
        """从JSON文件加载用户数据"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_users(self):
        """保存用户数据到JSON文件"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def get_user(self, username):
        """获取指定用户"""
        for user in self.users:
            if user["user"] == username:
                return user
        return None

    def add_user(self, username):
        """添加新用户"""
        if not self.get_user(username):
            self.users.append({"user": username, "score": 0, "level": 0})
            self.save_users()
            return True
        return False

    def update_score(self, username, score, level):
        """更新用户分数和关卡（只保留最高分和最高关卡）"""
        user = self.get_user(username)
        if user:
            if score > user["score"] or level > user["level"]:
                user["score"] = max(user["score"], score)
                user["level"] = max(user["level"], level)
                self.save_users()
                return True
        return False

    def get_top_scores(self, count=5):
        """获取前N名用户"""
        sorted_users = sorted(self.users, key=lambda x: x["score"], reverse=True)
        return sorted_users[:count]


class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type="rectangle"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.color = (100, 100, 255)  # 蓝色障碍物

    def contains_point(self, point):
        """检查点是否在障碍物内"""
        x, y = point
        if self.type == "rectangle":
            return (
                self.x <= x <= self.x + self.width
                and self.y <= y <= self.y + self.height
            )
        elif self.type == "circle":
            center_x = self.x + self.width // 2
            center_y = self.y + self.height // 2
            radius = min(self.width, self.height) // 2
            return ((x - center_x) ** 2 + (y - center_y) ** 2) <= radius**2
        return False

    def draw(self, img):
        """绘制障碍物"""
        if self.type == "rectangle":
            cv2.rectangle(
                img,
                (self.x, self.y),
                (self.x + self.width, self.y + self.height),
                self.color,
                -1,
            )
            cv2.rectangle(
                img,
                (self.x, self.y),
                (self.x + self.width, self.y + self.height),
                (255, 255, 255),
                2,
            )
        elif self.type == "circle":
            center = (self.x + self.width // 2, self.y + self.height // 2)
            radius = min(self.width, self.height) // 2
            cv2.circle(img, center, radius, self.color, -1)
            cv2.circle(img, center, radius, (255, 255, 255), 2)


class SnakeGame:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.max_speed = 6  # 降低最大移动速度，防止蛇头跳过蛇身
        self.min_distance = 25  # 蛇身节点之间的最小距离
        self.user_manager = UserManager()
        self.pinch_threshold = 10  # 捏合检测阈值
        self.pinch_cooldown = 0.5  # 捏合冷却时间（秒）
        self.last_pinch_time = 0  # 上次捏合时间
        self.obstacles = []  # 障碍物列表
        self.current_level = 1  # 当前关卡
        self.max_level = 10  # 最大关卡数
        self.reset_game()

    def reset_game(self):
        # 蛇的初始位置和长度 - 确保初始蛇身不会重叠
        start_x, start_y = self.width // 2, self.height // 2
        self.snake_pos = [(start_x, start_y)]

        # 初始蛇身 - 确保蛇身节点之间有足够的距离
        for i in range(1, 3):
            self.snake_pos.append((start_x - i * self.min_distance, start_y))

        self.snake_length = 3  # 初始长度设为3

        # 生成第一个食物
        self.food_pos = self.generate_food()

        # 生成障碍物（根据当前关卡）
        self.generate_obstacles()

        # 游戏状态
        self.score = 0
        self.game_over = False
        self.last_finger_pos = None  # 记录上次手指位置
        self.last_thumb_pos = None  # 记录拇指位置
        self.last_move_time = time.time()  # 记录上次移动时间

    def generate_obstacles(self):
        """根据当前关卡生成障碍物"""
        self.obstacles = []

        # 基础障碍物数量随关卡增加
        base_count = 2 + self.current_level * random.randint(5, 15)

        for _ in range(base_count):
            # 障碍物大小随关卡增加
            min_size = 20 + self.current_level * random.randint(5, 10)
            max_size = 40 + self.current_level * random.randint(15, 20)
            width = random.randint(min_size, max_size)
            height = random.randint(min_size, max_size)

            # 随机位置
            x = random.randint(50, self.width - width - 50)
            y = random.randint(50, self.height - height - 50)

            # 随机选择障碍物类型（随着关卡增加，圆形障碍物出现概率增加）
            obstacle_type = "rectangle"
            if random.random() < self.current_level * 0.08:  # 最高80%概率出现圆形
                obstacle_type = "circle"

            obstacle = Obstacle(x, y, width, height, obstacle_type)

            # 确保障碍物不与蛇的初始位置和食物重叠
            if not any(
                obstacle.contains_point(pos) for pos in self.snake_pos
            ) and not obstacle.contains_point(self.food_pos):
                self.obstacles.append(obstacle)

        # 在高关卡添加特殊障碍物模式
        if self.current_level >= 5:
            # 添加边界障碍物
            border_width = 10
            self.obstacles.append(Obstacle(0, 0, self.width, border_width))
            self.obstacles.append(Obstacle(0, 0, border_width, self.height))
            self.obstacles.append(
                Obstacle(0, self.height - border_width, self.width, border_width)
            )
            self.obstacles.append(
                Obstacle(self.width - border_width, 0, border_width, self.height)
            )

        if self.current_level >= 8:
            # 添加十字形障碍物
            center_x, center_y = self.width // 2, self.height // 2
            cross_width, cross_height = 20, 100
            self.obstacles.append(
                Obstacle(
                    center_x - cross_width // 2,
                    center_y - cross_height // 2,
                    cross_width,
                    cross_height,
                )
            )
            self.obstacles.append(
                Obstacle(
                    center_x - cross_height // 2,
                    center_y - cross_width // 2,
                    cross_height,
                    cross_width,
                )
            )

    def generate_food(self):
        """在随机位置生成食物，确保不在蛇身上和障碍物上"""
        while True:
            food_pos = (
                random.randint(50, self.width - 50),
                random.randint(50, self.height - 50),
            )
            # 检查食物是否与蛇身重叠
            if all(
                self.distance(food_pos, pos) > 40 for pos in self.snake_pos
            ) and not any(obs.contains_point(food_pos) for obs in self.obstacles):
                return food_pos

    def distance(self, pos1, pos2):
        """计算两点之间的欧几里得距离"""
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def is_pinch_gesture(self, index_pos, thumb_pos):
        """检测食指和拇指是否捏合"""
        if index_pos is None or thumb_pos is None:
            return False

        dist = self.distance(index_pos, thumb_pos)
        current_time = time.time()

        # 检查是否在冷却时间内
        if current_time - self.last_pinch_time < self.pinch_cooldown:
            return False

        # 检查距离是否小于阈值
        if dist < self.pinch_threshold:
            self.last_pinch_time = current_time
            return True

        return False

    def is_point_in_rect(self, point, rect):
        """检测点是否在矩形内"""
        if point is None:
            return False
        x, y = point
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def update_snake_position(self):
        """更新蛇身位置，确保蛇身节点之间有足够的距离"""
        # 更新蛇身节点位置
        for i in range(len(self.snake_pos) - 1, 0, -1):
            # 计算当前节点与前一个节点的距离
            prev_pos = self.snake_pos[i - 1]
            current_pos = self.snake_pos[i]
            dist = self.distance(prev_pos, current_pos)

            if dist > self.min_distance:
                # 如果距离太大，移动当前节点靠近前一个节点
                dx = prev_pos[0] - current_pos[0]
                dy = prev_pos[1] - current_pos[1]
                angle = math.atan2(dy, dx) if dx != 0 or dy != 0 else 0

                new_x = current_pos[0] + int(
                    math.cos(angle) * (dist - self.min_distance) * 0.5
                )
                new_y = current_pos[1] + int(
                    math.sin(angle) * (dist - self.min_distance) * 0.5
                )
                self.snake_pos[i] = (new_x, new_y)

    def update(self, finger_pos, thumb_pos=None):
        """更新游戏状态"""
        if self.game_over:
            return

        # 添加移动冷却时间，防止移动过快
        current_time = time.time()
        if current_time - self.last_move_time < 0.03:  # 约30FPS的移动速度
            return
        self.last_move_time = current_time

        # 如果没有检测到手指，使用上次的位置或中心位置
        if finger_pos is None:
            if self.last_finger_pos:
                finger_pos = self.last_finger_pos
            else:
                # 如果没有手指位置，蛇头保持在当前位置
                return
        else:
            self.last_finger_pos = finger_pos

        # 记录拇指位置
        if thumb_pos:
            self.last_thumb_pos = thumb_pos

        # 限制手指位置在屏幕范围内
        x, y = finger_pos
        x = max(20, min(self.width - 20, x))
        y = max(20, min(self.height - 20, y))
        finger_pos = (x, y)

        # 计算蛇头到目标位置的方向和距离
        current_head = self.snake_pos[0]
        dx = finger_pos[0] - current_head[0]
        dy = finger_pos[1] - current_head[1]
        dist = self.distance(current_head, finger_pos)

        # 如果距离很小，直接移动到目标位置
        if dist < 3:
            new_head = finger_pos
        else:
            # 限制移动速度
            if dist > self.max_speed:
                # 如果距离超过最大速度，按最大速度移动
                ratio = self.max_speed / dist
                dx = int(dx * ratio)
                dy = int(dy * ratio)

            # 计算新的蛇头位置
            new_head = (current_head[0] + dx, current_head[1] + dy)

        # 限制新位置在屏幕范围内
        new_x, new_y = new_head
        new_x = max(15, min(self.width - 15, new_x))
        new_y = max(15, min(self.height - 15, new_y))
        new_head = (new_x, new_y)

        # 检查新的头部位置是否会与蛇身重叠
        will_collide = False
        for i, pos in enumerate(self.snake_pos):
            # 跳过头部本身和前几个靠近头部的节点
            if i < 3:  # 跳过前3个节点，包括头部
                continue

            # 检查是否会与蛇身重叠
            if self.distance(new_head, pos) < 12:  # 碰撞阈值
                will_collide = True
                break

        if will_collide:
            # 如果会碰撞，保持当前位置或寻找安全方向
            # 这里我们简单地保持当前位置
            return

        # 更新蛇头位置
        self.snake_pos.insert(0, new_head)

        # 检查是否吃到食物
        ate_food = False
        if self.distance(new_head, self.food_pos) < 25:
            # 分数计算：基础分数 + 关卡加成
            base_score = 10
            level_bonus = self.current_level * 5  # 每关增加5分奖励
            self.score += base_score + level_bonus
            self.snake_length += 1

            # 每吃5个食物进入下一关
            if (
                self.score % (5 * (base_score + level_bonus)) == 0
                and self.current_level < self.max_level
            ):
                self.current_level += 1
                self.generate_obstacles()  # 生成新关卡的障碍物

            self.food_pos = self.generate_food()
            ate_food = True

        # 保持蛇身长度（如果没吃到食物，移除尾部）
        if not ate_food and len(self.snake_pos) > self.snake_length:
            self.snake_pos.pop()

        # 更新蛇身位置，确保节点间距离合适
        self.update_snake_position()

        # 检查游戏结束条件（撞墙）
        x, y = new_head
        if x < 5 or x > self.width - 5 or y < 5 or y > self.height - 5:
            self.game_over = True

        # 检查游戏结束条件（撞到自己）
        # 使用更精确的碰撞检测
        if not ate_food:
            for i, pos in enumerate(self.snake_pos):
                # 跳过头部本身和前几个靠近头部的节点
                if i < 3:  # 跳过前3个节点，包括头部
                    continue

                # 精确碰撞检测
                if self.distance(new_head, pos) < 12:
                    self.game_over = True
                    break

        # 检查游戏结束条件（撞到障碍物）
        for obstacle in self.obstacles:
            if obstacle.contains_point(new_head):
                self.game_over = True
                break

    def draw(self, img, finger_pos=None):
        """在图像上绘制游戏元素"""
        # 绘制障碍物
        for obstacle in self.obstacles:
            obstacle.draw(img)

        # 绘制蛇身 - 确保蛇身节点之间有视觉连接
        for i, pos in enumerate(self.snake_pos):
            # 蛇头用不同颜色
            if i == 0:
                color = (0, 255, 0)  # 蛇头亮绿色
                radius = 12  # 蛇头半径
            else:
                # 蛇身颜色渐变
                color_ratio = i / len(self.snake_pos)
                color = (0, int(200 * (1 - color_ratio)), 0)
                radius = 10  # 蛇身半径

            cv2.circle(img, pos, radius, color, -1)
            cv2.circle(img, pos, radius, (255, 255, 255), 1)  # 白色边框

            # 绘制蛇身连接线（更平滑的连接）
            if i > 0:
                prev_pos = self.snake_pos[i - 1]
                # 计算连接线的中点，使连接更平滑
                mid_x = (prev_pos[0] + pos[0]) // 2
                mid_y = (prev_pos[1] + pos[1]) // 2

                # 绘制两条连接线，使蛇身看起来连续
                cv2.line(img, prev_pos, (mid_x, mid_y), (0, 160, 0), 8)
                cv2.line(img, (mid_x, mid_y), pos, (0, 140, 0), 8)

        # 绘制食物
        cv2.circle(img, self.food_pos, 12, (0, 0, 255), -1)  # 食物大小
        cv2.circle(img, self.food_pos, 10, (255, 255, 255), 2)

        # 高亮食指指尖位置
        if finger_pos:
            cv2.circle(img, finger_pos, 20, (255, 255, 0), 3)  # 黄色圆圈
            cv2.circle(img, finger_pos, 5, (255, 255, 0), -1)  # 实心点

        # 绘制分数、关卡和游戏信息
        cv2.putText(
            img,
            f"Score: {self.score}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            img,
            f"Level: {self.current_level}/{self.max_level}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # 显示当前用户
        if self.user_manager.current_user:
            cv2.putText(
                img,
                f"User: {self.user_manager.current_user}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        # 如果没有检测到手，显示提示
        if self.last_finger_pos is None:
            cv2.putText(
                img,
                "Show your hand to camera!",
                (self.width // 2 - 180, self.height - 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

    def draw_button(self, img, text, position, size, is_hovered=False):
        """绘制按钮"""
        x, y = position
        w, h = size

        # 按钮颜色
        color = (0, 150, 255) if is_hovered else (0, 100, 200)

        # 绘制按钮背景
        cv2.rectangle(img, (x, y), (x + w, y + h), color, -1)
        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 2)

        # 计算文本位置（居中）
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2

        # 绘制文本
        cv2.putText(
            img,
            text,
            (text_x, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        return (x, y, w, h)

    def draw_start_screen(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制启动画面"""
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制标题
        cv2.putText(
            img,
            "SNAKE GAME",
            (self.width // 2 - 150, self.height // 2 - 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0),
            3,
        )
        cv2.putText(
            img,
            "Hand & Mouse Controlled",
            (self.width // 2 - 170, self.height // 2 - 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # 绘制开始按钮
        start_button_rect = (self.width // 2 - 100, self.height // 2 - 30, 200, 60)
        start_button_hover = self.is_point_in_rect(index_pos, start_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, start_button_rect)
        )
        start_button = self.draw_button(
            img,
            "START",
            (start_button_rect[0], start_button_rect[1]),
            (start_button_rect[2], start_button_rect[3]),
            is_hovered=start_button_hover,
        )

        # 绘制用户选择按钮
        user_button_rect = (self.width // 2 - 100, self.height // 2 + 50, 200, 60)
        user_button_hover = self.is_point_in_rect(index_pos, user_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, user_button_rect)
        )
        user_button = self.draw_button(
            img,
            "SELECT USER",
            (user_button_rect[0], user_button_rect[1]),
            (user_button_rect[2], user_button_rect[3]),
            is_hovered=user_button_hover,
        )

        # 绘制积分榜
        cv2.putText(
            img,
            "TOP SCORES:",
            (self.width // 2 - 80, self.height // 2 + 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2,
        )

        top_scores = self.user_manager.get_top_scores(5)
        for i, user in enumerate(top_scores):
            score_text = (
                f"{i+1}. {user['user']}: {user['score']} (Lv.{user.get('level', 0)})"
            )
            cv2.putText(
                img,
                score_text,
                (self.width // 2 - 100, self.height // 2 + 180 + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1,
            )

        # 检测按钮点击（食指和拇指捏合或鼠标点击）
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if start_button_hover:
                buttons_clicked.append("start")
            elif user_button_hover:
                buttons_clicked.append("select_user")

        # 显示操作提示
        cv2.putText(
            img,
            "Use hand gestures OR mouse to interact",
            (self.width // 2 - 200, self.height - 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            img,
            "Hand: Pinch to click | Mouse: Left click",
            (self.width // 2 - 180, self.height - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        # 显示捏合提示和调试信息
        if index_pos and thumb_pos:
            dist = self.distance(index_pos, thumb_pos)

            # 显示详细调试信息
            debug_text = [
                f"Index: {index_pos}",
                f"Thumb: {thumb_pos}",
                f"Distance: {dist:.1f}",
                f"Threshold: {self.pinch_threshold}",
                f"Pinch: {'YES' if pinch_detected else 'NO'}",
                f"Hover Start: {start_button_hover}",
                f"Hover User: {user_button_hover}",
                f"Buttons Clicked: {buttons_clicked}",
            ]

            for i, text in enumerate(debug_text):
                cv2.putText(
                    img,
                    text,
                    (10, 100 + i * 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                )

            # 在手指位置绘制圆圈
            cv2.circle(img, index_pos, 10, (255, 0, 0), 2)  # 食指 - 蓝色
            cv2.circle(img, thumb_pos, 10, (0, 255, 255), 2)  # 拇指 - 黄色

            # 如果距离接近阈值，绘制连接线
            if dist < self.pinch_threshold * 2:
                line_color = (
                    (0, 255, 0) if dist < self.pinch_threshold else (0, 165, 255)
                )  # 绿色或橙色
                cv2.line(img, index_pos, thumb_pos, line_color, 2)

            # 如果捏合成功，显示提示
            if pinch_detected:
                cv2.putText(
                    img,
                    "PINCH DETECTED!",
                    (self.width // 2 - 100, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked

    def draw_user_selection_screen(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制用户选择画面"""
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制标题
        cv2.putText(
            img,
            "SELECT USER",
            (self.width // 2 - 120, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            2,
        )

        # 绘制用户列表
        users = self.user_manager.users
        buttons = []
        button_height = 50
        start_y = 120

        for i, user in enumerate(users):
            button_rect = (
                self.width // 2 - 150,
                start_y + i * (button_height + 10),
                300,
                button_height,
            )
            is_hovered = self.is_point_in_rect(index_pos, button_rect) or (
                mouse_pos and self.is_point_in_rect(mouse_pos, button_rect)
            )
            self.draw_button(
                img,
                f"{user['user']} (Lv.{user.get('level', 0)})",
                (button_rect[0], button_rect[1]),
                (button_rect[2], button_rect[3]),
                is_hovered,
            )
            buttons.append((user["user"], button_rect))

        # 绘制新用户按钮
        new_user_button_rect = (
            self.width // 2 - 150,
            start_y + len(users) * (button_height + 10) + 20,
            300,
            button_height,
        )
        new_user_hover = self.is_point_in_rect(index_pos, new_user_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, new_user_button_rect)
        )
        self.draw_button(
            img,
            "NEW USER",
            (new_user_button_rect[0], new_user_button_rect[1]),
            (new_user_button_rect[2], new_user_button_rect[3]),
            new_user_hover,
        )

        # 绘制返回按钮
        back_button_rect = (self.width // 2 - 80, self.height - 80, 160, 50)
        back_hover = self.is_point_in_rect(index_pos, back_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, back_button_rect)
        )
        self.draw_button(
            img,
            "BACK",
            (back_button_rect[0], back_button_rect[1]),
            (back_button_rect[2], back_button_rect[3]),
            back_hover,
        )

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            for username, rect in buttons:
                if self.is_point_in_rect(index_pos, rect) or (
                    mouse_pos and self.is_point_in_rect(mouse_pos, rect)
                ):
                    buttons_clicked.append(("select", username))

            if new_user_hover:
                buttons_clicked.append(("new_user",))

            if back_hover:
                buttons_clicked.append(("back",))

        # 显示操作提示
        cv2.putText(
            img,
            "Use hand gestures OR mouse to interact",
            (self.width // 2 - 200, self.height - 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked

    def draw_new_user_screen(
        self,
        img,
        index_pos,
        thumb_pos,
        current_text="",
        mouse_pos=None,
        mouse_click=False,
    ):
        """绘制新用户注册画面"""
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制标题
        cv2.putText(
            img,
            "CREATE NEW USER",
            (self.width // 2 - 140, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 255, 0),
            2,
        )

        # 绘制输入框
        input_box = (self.width // 2 - 150, 120, 300, 50)
        cv2.rectangle(
            img,
            (input_box[0], input_box[1]),
            (input_box[0] + input_box[2], input_box[1] + input_box[3]),
            (255, 255, 255),
            2,
        )

        # 绘制当前文本
        if current_text:
            cv2.putText(
                img,
                current_text,
                (input_box[0] + 10, input_box[1] + 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )
        else:
            cv2.putText(
                img,
                "Enter username...",
                (input_box[0] + 10, input_box[1] + 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (150, 150, 150),
                1,
            )

        # 绘制确认按钮
        confirm_button_rect = (self.width // 2 - 150, 190, 140, 50)
        confirm_hover = self.is_point_in_rect(index_pos, confirm_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, confirm_button_rect)
        )
        self.draw_button(
            img,
            "CONFIRM",
            (confirm_button_rect[0], confirm_button_rect[1]),
            (confirm_button_rect[2], confirm_button_rect[3]),
            confirm_hover,
        )

        # 绘制取消按钮
        cancel_button_rect = (self.width // 2 + 10, 190, 140, 50)
        cancel_hover = self.is_point_in_rect(index_pos, cancel_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, cancel_button_rect)
        )
        self.draw_button(
            img,
            "CANCEL",
            (cancel_button_rect[0], cancel_button_rect[1]),
            (cancel_button_rect[2], cancel_button_rect[3]),
            cancel_hover,
        )

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if confirm_hover:
                buttons_clicked.append(("confirm", current_text))
            elif cancel_hover:
                buttons_clicked.append(("cancel",))

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked, input_box

    def draw_game_over(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制游戏结束画面"""
        # 先绘制游戏画面
        self.draw(img, index_pos)

        # 添加半透明覆盖层
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制游戏结束文本
        cv2.putText(
            img,
            "GAME OVER",
            (self.width // 2 - 150, self.height // 2 - 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            3,
        )
        cv2.putText(
            img,
            f"Score: {self.score}",
            (self.width // 2 - 80, self.height // 2 - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            img,
            f"Reached Level: {self.current_level}",
            (self.width // 2 - 120, self.height // 2 - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )

        # 显示当前用户
        if self.user_manager.current_user:
            cv2.putText(
                img,
                f"User: {self.user_manager.current_user}",
                (self.width // 2 - 80, self.height // 2 + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

        # 绘制重新开始按钮
        restart_button_rect = (self.width // 2 - 100, self.height // 2 + 40, 200, 60)
        restart_hover = self.is_point_in_rect(index_pos, restart_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, restart_button_rect)
        )
        restart_button = self.draw_button(
            img,
            "RESTART",
            (restart_button_rect[0], restart_button_rect[1]),
            (restart_button_rect[2], restart_button_rect[3]),
            is_hovered=restart_hover,
        )

        # 绘制用户选择按钮
        user_button_rect = (self.width // 2 - 100, self.height // 2 + 120, 200, 60)
        user_hover = self.is_point_in_rect(index_pos, user_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, user_button_rect)
        )
        user_button = self.draw_button(
            img,
            "SELECT USER",
            (user_button_rect[0], user_button_rect[1]),
            (user_button_rect[2], user_button_rect[3]),
            is_hovered=user_hover,
        )

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if restart_hover:
                buttons_clicked.append("restart")
            elif user_hover:
                buttons_clicked.append("select_user")

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked


def test():
    # 在函数内部声明全局变量
    global mouse_position, mouse_clicked

    # 初始化手部检测
    hand = hd.HandBind(
        camera_id=0,
        handdraw=True,
        draw_fps=True,
        draw_index=False,  # 关闭关键点编号显示，避免干扰游戏
        verbose=False,
        max_hands=1,  # 只检测一只手，提高性能
    )

    # 初始化贪吃蛇游戏
    game = SnakeGame()

    # 设置鼠标回调
    cv2.namedWindow("Snake Game - Hand & Mouse Control")
    cv2.setMouseCallback("Snake Game - Hand & Mouse Control", mouse_callback)

    print("贪吃蛇游戏说明:")
    print("- 移动食指来控制蛇头")
    print("- 食指和拇指捏合可以点击按钮，也可以用鼠标点击")
    print("- 吃到红色食物可以增加分数")
    print("- 避免撞到边界、自己和蓝色障碍物")
    print("- 游戏共有10关，难度递增")
    print("- 每吃5个食物进入下一关")
    print("- 捏合阈值:", game.pinch_threshold)

    # 游戏状态 - 使用单个状态变量来管理
    game_state = "start_screen"  # 可以是: "start_screen", "user_selection", "new_user", "playing", "game_over"
    new_user_text = ""
    last_key_time = 0

    # 添加一些调试用户
    if not game.user_manager.users:
        game.user_manager.add_user("Player1")
        game.user_manager.add_user("Player2")
        game.user_manager.add_user("Player3")

    while True:
        success, processed_img, landmarks = hand.process_frame()

        if success:
            # 获取摄像头画面尺寸
            img_height, img_width = processed_img.shape[:2]

            # 如果游戏尺寸与摄像头尺寸不一致，更新游戏尺寸
            if game.width != img_width or game.height != img_height:
                game.width = img_width
                game.height = img_height
                game.reset_game()

            # 镜像画面 - 水平翻转
            # processed_img = cv2.flip(processed_img, 1)

            # 获取食指和拇指坐标
            index_pos = None
            thumb_pos = None
            if landmarks and len(landmarks) > 0:
                # landmarks[0] 表示第一只手，[8] 表示食指指尖，[4] 表示拇指指尖
                original_index_pos = landmarks[0][8]
                original_thumb_pos = landmarks[0][4]

                # 镜像手指坐标（因为画面已经水平翻转）
                index_pos = (img_width - original_index_pos[0], original_index_pos[1])
                thumb_pos = (img_width - original_thumb_pos[0], original_thumb_pos[1])

            # 重置鼠标点击状态（每次循环只处理一次点击）
            current_mouse_click = mouse_clicked
            mouse_clicked = False

            # 根据游戏状态显示不同界面
            if game_state == "start_screen":
                buttons_clicked = game.draw_start_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    mouse_position,
                    current_mouse_click,
                )
                # print(f"Start Screen - Buttons Clicked: {buttons_clicked}")  # 调试输出

                for button in buttons_clicked:
                    if button == "start":
                        if game.user_manager.current_user:
                            game_state = "playing"
                            # print(
                            #     "Starting game with user:",
                            #     game.user_manager.current_user,
                            # )
                        else:
                            # 如果没有当前用户，转到用户选择
                            game_state = "user_selection"
                            # print("No user selected, going to user selection")
                    elif button == "select_user":
                        game_state = "user_selection"
                        # print("Going to user selection")

            elif game_state == "user_selection":
                buttons_clicked = game.draw_user_selection_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    mouse_position,
                    current_mouse_click,
                )
                # print(
                #     f"User Selection - Buttons Clicked: {buttons_clicked}"
                # )  # 调试输出

                for button in buttons_clicked:
                    if button[0] == "select":
                        game.user_manager.current_user = button[1]
                        game_state = "playing"  # 直接开始游戏
                        # print(f"User selected: {button[1]}")
                    elif button[0] == "new_user":
                        game_state = "new_user"
                        new_user_text = ""
                        # print("Going to new user creation")
                    elif button[0] == "back":
                        game_state = "start_screen"
                        # print("Going back to start screen")

            elif game_state == "new_user":
                buttons_clicked, input_box = game.draw_new_user_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    new_user_text,
                    mouse_position,
                    current_mouse_click,
                )
                # print(
                #     f"New User Screen - Buttons Clicked: {buttons_clicked}"
                # )  # 调试输出

                # 处理键盘输入（用户名输入）
                current_time = time.time()
                if current_time - last_key_time > 0.1:  # 防止按键重复
                    key = cv2.waitKey(1) & 0xFF
                    if key != 255:  # 有按键按下
                        last_key_time = current_time
                        if key == 8:  # 退格键
                            new_user_text = new_user_text[:-1]
                        elif key == 13:  # 回车键
                            if new_user_text:
                                if game.user_manager.add_user(new_user_text):
                                    game.user_manager.current_user = new_user_text
                                    game_state = "playing"
                                    print(f"New user created: {new_user_text}")
                        elif 32 <= key <= 126:  # 可打印字符
                            if len(new_user_text) < 15:  # 限制用户名长度
                                new_user_text += chr(key)

                for button in buttons_clicked:
                    if button[0] == "confirm" and button[1]:
                        if game.user_manager.add_user(button[1]):
                            game.user_manager.current_user = button[1]
                            game_state = "playing"
                            print(f"New user created via button: {button[1]}")
                    elif button[0] == "cancel":
                        game_state = "user_selection"
                        print("Canceling new user creation")

            elif game_state == "playing":
                if not game.game_over:
                    # 更新游戏状态
                    game.update(index_pos, thumb_pos)

                    # 在图像上绘制游戏（传入食指位置用于高亮显示）
                    game.draw(processed_img, index_pos)
                else:
                    # 游戏结束，更新分数并切换到游戏结束状态
                    if game.user_manager.current_user:
                        game.user_manager.update_score(
                            game.user_manager.current_user,
                            game.score,
                            game.current_level,
                        )
                        print(
                            f"Game over. Score: {game.score}. Level: {game.current_level}. User: {game.user_manager.current_user}"
                        )
                    game_state = "game_over"

            elif game_state == "game_over":
                # 绘制游戏结束画面
                buttons_clicked = game.draw_game_over(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    mouse_position,
                    current_mouse_click,
                )
                # print(f"Game Over - Buttons Clicked: {buttons_clicked}")  # 调试输出

                for button in buttons_clicked:
                    if button == "restart":
                        # 重置游戏（从第一关开始）
                        game.current_level = 1
                        game.reset_game()
                        game_state = "playing"
                        print("Restarting game from level 1")
                    elif button == "select_user":
                        game_state = "user_selection"
                        print("Going to user selection from game over")

            # 显示图像
            cv2.imshow("Snake Game - Hand & Mouse Control", processed_img)

            # 键盘控制
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("r") and game_state == "game_over":
                game.current_level = 1
                game.reset_game()
                game_state = "playing"
            elif key == ord(" ") and game_state == "start_screen":  # 空格键开始游戏
                game_state = "playing"
            elif key == ord("t"):  # 临时按键：调整捏合阈值
                game.pinch_threshold += 5
                print(f"捏合阈值调整为: {game.pinch_threshold}")
            elif key == ord("y"):  # 临时按键：减小捏合阈值
                game.pinch_threshold = max(10, game.pinch_threshold - 5)
                print(f"捏合阈值调整为: {game.pinch_threshold}")
            elif key == ord("b") and game_state == "playing":  # 返回开始画面
                game_state = "start_screen"
            elif key == ord("n") and game_state == "playing":  # 下一关（调试用）
                if game.current_level < game.max_level:
                    game.current_level += 1
                    game.generate_obstacles()
                    print(f"跳到第 {game.current_level} 关")

    # 释放资源
    hand.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test()
