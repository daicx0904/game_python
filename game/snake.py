import json
import os
import random
import threading
import time

import cv2
import pygame
import pygame as pg

import getquestion as gq
import hand as hd


class UserManager:
    def __init__(self, filename="users.json"):
        self.filename = filename
        self.users = self.load_users()
        self.current_user = None

    def load_users(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_users(self):
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def get_user(self, username):
        for user in self.users:
            if user["user"] == username:
                return user
        return None

    def add_user(self, username):
        if not self.get_user(username):
            self.users.append(
                {"user": username, "score": 0, "level": 0, "revive_count": 0}
            )
            self.save_users()
            return True
        return False

    def update_score(self, username, score, level, revive_count=0):
        user = self.get_user(username)
        if user:
            if score > user["score"] or level > user["level"]:
                user["score"] = max(user["score"], score)
                user["level"] = max(user["level"], level)
                user["revive_count"] = max(user.get("revive_count", 0), revive_count)
                self.save_users()
                return True
        return False

    def get_top_scores(self, count=5):
        sorted_users = sorted(self.users, key=lambda x: x["score"], reverse=True)
        return sorted_users[:count]


class Obstacle:
    def __init__(self, x, y, width, height, obstacle_type="rectangle"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.type = obstacle_type
        self.color = (100, 100, 255)

    def contains_point(self, point):
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

    def draw(self, screen):
        if self.type == "rectangle":
            pg.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
            pg.draw.rect(
                screen, (255, 255, 255), (self.x, self.y, self.width, self.height), 2
            )
        elif self.type == "circle":
            center = (self.x + self.width // 2, self.y + self.height // 2)
            radius = min(self.width, self.height) // 2
            pg.draw.circle(screen, self.color, center, radius)
            pg.draw.circle(screen, (255, 255, 255), center, radius, 2)


class QuestionManager:
    def __init__(self):
        self.question: None | str = None
        self.questions = [
            {
                "question": "Python中哪个关键字用于定义函数？",
                "options": ["A. function", "B. def", "C. define", "D. func"],
                "correct": 1,
            },
            {
                "question": "下列哪个是Pygame的初始化函数？",
                "options": [
                    "A. pygame.start()",
                    "B. pygame.init()",
                    "C. pygame.begin()",
                    "D. pygame.run()",
                ],
                "correct": 1,
            },
        ]

    def gen_question(self):
        self.question = gq.convert(gq.get_question())

    def get_random_question(self):
        """获取题目"""
        return self.question
        # return random.choice(self.questions)

    def check_answer(self, question, selected_option):
        """检查答案是否正确"""
        return question["correct"] == selected_option

    def reset(self):
        self.question = None


class SnakeGame:
    def __init__(self, width=640, height=480):
        self.width = width
        self.height = height
        self.max_speed = 8
        self.user_manager = UserManager()
        self.pinch_threshold = 30
        self.pinch_cooldown = 0.5
        self.last_pinch_time = 0
        self.obstacles = []
        self.current_level = 1
        self.max_level = 10
        self.question_manager = QuestionManager()
        self.max_revive_chances = 3  # 最大复活次数
        self.current_revive_chances = self.max_revive_chances  # 当前剩余复活次数
        self.current_question = None
        self.revive_in_progress = False  # 标记是否正在进行复活挑战
        self.reset_game()
        threading.Thread(target=self.question_manager.gen_question)

        # 初始化字体
        pg.font.init()
        self.font_large = pg.font.SysFont("simhei", 36)  # 改为中文字体
        self.font_medium = pg.font.SysFont("simhei", 24)
        self.font_small = pg.font.SysFont("simhei", 18)

        # 触摸光标状态
        self.cursor_color = (255, 255, 0)  # 默认黄色
        self.pinch_active = False

    def reset_game(self):
        self.question_manager.reset()
        # 使用列表套元组存储蛇的每个节点坐标
        start_x, start_y = self.width // 2, self.height // 2
        self.snake_pos = [(start_x, start_y)]

        # 初始蛇身 - 确保节点之间有固定距离
        segment_distance = 20  # 节点间距
        for i in range(1, 3):
            self.snake_pos.append((start_x - i * segment_distance, start_y))

        self.snake_length = 3
        self.food_pos = self.generate_food()
        self.generate_obstacles()

        self.score = 0
        self.game_over = False
        self.last_finger_pos = None
        self.last_thumb_pos = None
        self.last_move_time = time.time()
        self.last_head_pos = self.snake_pos[0]  # 记录上次蛇头位置

        # 重置复活次数（开始新游戏时重置）
        self.current_revive_chances = self.max_revive_chances
        self.revive_in_progress = False

    def generate_obstacles(self):
        self.obstacles = []
        base_count = 2 + self.current_level * random.randint(5, 15)

        for _ in range(base_count):
            min_size = 20 + self.current_level * random.randint(5, 10)
            max_size = 40 + self.current_level * random.randint(15, 20)
            width = random.randint(min_size, max_size)
            height = random.randint(min_size, max_size)

            x = random.randint(50, self.width - width - 50)
            y = random.randint(50, self.height - height - 50)

            obstacle_type = "rectangle"
            if random.random() < self.current_level * 0.08:
                obstacle_type = "circle"

            obstacle = Obstacle(x, y, width, height, obstacle_type)

            if not any(
                obstacle.contains_point(pos) for pos in self.snake_pos
            ) and not obstacle.contains_point(self.food_pos):
                self.obstacles.append(obstacle)

        if self.current_level >= 5:
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
        while True:
            food_pos = (
                random.randint(50, self.width - 50),
                random.randint(50, self.height - 50),
            )
            if all(
                self.distance(food_pos, pos) > 40 for pos in self.snake_pos
            ) and not any(obs.contains_point(food_pos) for obs in self.obstacles):
                return food_pos

    def distance(self, pos1, pos2):
        return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5

    def is_pinch_gesture(self, index_pos, thumb_pos):
        if index_pos is None or thumb_pos is None:
            self.pinch_active = False
            return False

        dist = self.distance(index_pos, thumb_pos)
        current_time = time.time()

        if current_time - self.last_pinch_time < self.pinch_cooldown:
            return False

        if dist < self.pinch_threshold:
            self.last_pinch_time = current_time
            self.pinch_active = True
            return True
        else:
            self.pinch_active = False

        return False

    def is_point_in_rect(self, point, rect):
        if point is None:
            return False
        x, y = point
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def update_snake_position(self, new_head):
        """更新蛇身位置 - 使用经典的跟随算法"""
        # 将新蛇头插入列表开头
        self.snake_pos.insert(0, new_head)

        # 如果蛇身长度超过设定长度，移除尾部
        if len(self.snake_pos) > self.snake_length:
            self.snake_pos.pop()

    def check_collision_with_segment(
        self, point, segment_start, segment_end, threshold=8
    ):
        """检查点是否与线段碰撞"""
        # 计算线段长度
        segment_length = self.distance(segment_start, segment_end)

        # 如果线段长度为0，直接检查点与线段起点的距离
        if segment_length == 0:
            return self.distance(point, segment_start) < threshold

        # 计算点到线段的投影比例
        t = (
            (point[0] - segment_start[0]) * (segment_end[0] - segment_start[0])
            + (point[1] - segment_start[1]) * (segment_end[1] - segment_start[1])
        ) / (segment_length * segment_length)

        # 限制投影比例在[0,1]范围内
        t = max(0, min(1, t))

        # 计算投影点
        projection = (
            segment_start[0] + t * (segment_end[0] - segment_start[0]),
            segment_start[1] + t * (segment_end[1] - segment_start[1]),
        )

        # 计算点到投影点的距离
        return self.distance(point, projection) < threshold

    def check_self_collision(self, head_pos):
        """检查蛇头是否与蛇身碰撞"""
        # 检查与节点的碰撞（跳过前几个节点）
        for i, pos in enumerate(self.snake_pos):
            if i < 3:  # 跳过前3个节点
                continue
            if self.distance(head_pos, pos) < 12:
                return True

        # 检查与线段的碰撞（跳过前几个线段）
        for i in range(1, len(self.snake_pos) - 3):  # 跳过前几个线段
            if self.check_collision_with_segment(
                head_pos, self.snake_pos[i], self.snake_pos[i + 1]
            ):
                return True

        return False

    def revive_player(self):
        """复活玩家 - 保留分数和关卡，只重置蛇的位置"""
        if self.current_revive_chances > 0:
            # 重置蛇的位置但不重置分数和关卡
            start_x, start_y = self.width // 2, self.height // 2
            self.snake_pos = [(start_x, start_y)]

            segment_distance = 20
            for i in range(1, 3):
                self.snake_pos.append((start_x - i * segment_distance, start_y))

            self.snake_length = 3
            self.food_pos = self.generate_food()

            self.game_over = False
            self.revive_in_progress = False
            self.last_finger_pos = None
            self.last_thumb_pos = None
            self.last_move_time = time.time()
            self.last_head_pos = self.snake_pos[0]

            return True
        return False

    def update(self, finger_pos, thumb_pos=None):
        if self.game_over or self.revive_in_progress:
            return

        current_time = time.time()
        if current_time - self.last_move_time < 0.05:  # 控制移动频率
            return
        self.last_move_time = current_time

        if finger_pos is None:
            if self.last_finger_pos:
                finger_pos = self.last_finger_pos
            else:
                return
        else:
            self.last_finger_pos = finger_pos

        if thumb_pos:
            self.last_thumb_pos = thumb_pos

        x, y = finger_pos
        x = max(20, min(self.width - 20, x))
        y = max(20, min(self.height - 20, y))
        finger_pos = (x, y)

        current_head = self.snake_pos[0]
        dx = finger_pos[0] - current_head[0]
        dy = finger_pos[1] - current_head[1]
        dist = self.distance(current_head, finger_pos)

        # 只有移动足够远时才更新位置
        if dist < 3:
            return

        # 限制移动速度
        move_dist = min(dist, self.max_speed)

        # 计算移动方向
        dir_x = dx / dist
        dir_y = dy / dist

        # 计算新的蛇头位置
        new_head = (
            int(current_head[0] + dir_x * move_dist),
            int(current_head[1] + dir_y * move_dist),
        )

        # 限制新位置在屏幕范围内
        new_x, new_y = new_head
        new_x = max(15, min(self.width - 15, new_x))
        new_y = max(15, min(self.height - 15, new_y))
        new_head = (new_x, new_y)

        # 检查是否撞到障碍物
        for obstacle in self.obstacles:
            if obstacle.contains_point(new_head):
                self.game_over = True
                return

        # 检查是否撞到边界
        if (
            new_head[0] < 5
            or new_head[0] > self.width - 5
            or new_head[1] < 5
            or new_head[1] > self.height - 5
        ):
            self.game_over = True
            return

        # 检查是否与自身碰撞
        if self.check_self_collision(new_head):
            self.game_over = True
            return

        # 更新蛇的位置
        self.update_snake_position(new_head)

        # 检查是否吃到食物
        if self.distance(new_head, self.food_pos) < 25:
            base_score = 10
            level_bonus = self.current_level * 5
            self.score += base_score + level_bonus
            self.snake_length += 1

            if (
                self.score % (5 * (base_score + level_bonus)) == 0
                and self.current_level < self.max_level
            ):
                self.current_level += 1
                self.generate_obstacles()

            self.food_pos = self.generate_food()

    def draw(self, screen, finger_pos=None):
        # 绘制障碍物
        for obstacle in self.obstacles:
            obstacle.draw(screen)

        # 绘制蛇身 - 使用线段连接所有节点
        if len(self.snake_pos) > 1:
            # 绘制所有连接线段
            for i in range(len(self.snake_pos) - 1):
                start_pos = self.snake_pos[i]
                end_pos = self.snake_pos[i + 1]

                # 线段颜色渐变
                color_ratio = i / len(self.snake_pos)
                color = (0, int(200 * (1 - color_ratio)), 0)

                # 绘制线段
                pg.draw.line(screen, color, start_pos, end_pos, 12)

        # 绘制蛇头
        if self.snake_pos:
            head_pos = self.snake_pos[0]
            pg.draw.circle(screen, (0, 255, 0), head_pos, 12)  # 蛇头
            pg.draw.circle(screen, (255, 255, 255), head_pos, 12, 2)  # 边框

        # 绘制食物
        pg.draw.circle(screen, (255, 0, 0), self.food_pos, 12)
        pg.draw.circle(screen, (255, 255, 255), self.food_pos, 12, 2)

        # 高亮食指指尖位置
        if finger_pos:
            pg.draw.circle(screen, (255, 255, 0), finger_pos, 20, 3)
            pg.draw.circle(screen, (255, 255, 0), finger_pos, 5)

        # 绘制分数、关卡和游戏信息
        score_text = self.font_medium.render(
            f"分数: {self.score}", True, (255, 255, 255)
        )
        level_text = self.font_medium.render(
            f"关卡数: {self.current_level}/{self.max_level}", True, (255, 255, 255)
        )
        revive_text = self.font_medium.render(
            f"复活次数: {self.current_revive_chances}", True, (255, 255, 255)
        )
        screen.blit(score_text, (10, 10))
        screen.blit(level_text, (10, 40))
        screen.blit(revive_text, (10, 70))

        if self.user_manager.current_user:
            user_text = self.font_small.render(
                f"用户: {self.user_manager.current_user}", True, (255, 255, 255)
            )
            screen.blit(user_text, (10, 100))

        if self.last_finger_pos is None:
            hint_text = self.font_medium.render(
                "请把手放在画面内!", True, (255, 255, 0)
            )
            screen.blit(hint_text, (self.width // 2 - 150, self.height - 40))

    def draw_cursor(self, screen, finger_pos):
        """绘制触摸光标"""
        if finger_pos:
            # 根据捏合状态改变颜色
            color = (
                (0, 255, 0) if self.pinch_active else (255, 255, 0)
            )  # 绿色当捏合，黄色默认
            pg.draw.circle(screen, color, finger_pos, 15, 3)
            pg.draw.circle(screen, color, finger_pos, 5)

    def draw_button(self, screen, text, position, size, is_hovered=False):
        x, y = position
        w, h = size

        color = (0, 150, 255) if is_hovered else (0, 100, 200)
        pg.draw.rect(screen, color, (x, y, w, h))
        pg.draw.rect(screen, (255, 255, 255), (x, y, w, h), 2)

        text_surface = self.font_medium.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + w // 2, y + h // 2))
        screen.blit(text_surface, text_rect)

        return (x, y, w, h)

    def draw_start_screen(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        # 绘制半透明背景
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 绘制标题
        title_text = self.font_large.render("贪吃蛇", True, (0, 255, 0))
        screen.blit(
            title_text,
            (self.width // 2 - title_text.get_width() // 2, self.height // 2 - 120),
        )

        # 绘制开始按钮
        start_button_rect = (self.width // 2 - 100, self.height // 2 - 30, 200, 60)
        start_button_hover = self.is_point_in_rect(index_pos, start_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, start_button_rect)
        )
        start_button = self.draw_button(
            screen,
            "开始游戏",
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
            screen,
            "选择用户",
            (user_button_rect[0], user_button_rect[1]),
            (user_button_rect[2], user_button_rect[3]),
            is_hovered=user_button_hover,
        )

        # 绘制积分榜
        top_title = self.font_medium.render("排行榜:", True, (255, 255, 0))
        screen.blit(top_title, (self.width // 2 - 80, self.height // 2 + 150))

        top_scores = self.user_manager.get_top_scores(5)
        for i, user in enumerate(top_scores):
            score_text = (
                f"{i+1}. {user['user']}: {user['score']} (Lv.{user.get('level', 0)})"
            )
            score_surface = self.font_small.render(score_text, True, (255, 255, 255))
            screen.blit(
                score_surface, (self.width // 2 - 100, self.height // 2 + 180 + i * 25)
            )

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if start_button_hover:
                buttons_clicked.append("start")
            elif user_button_hover:
                buttons_clicked.append("select_user")

        # 显示操作提示
        hint1 = self.font_small.render("使用手势或鼠标进行交互", True, (255, 255, 0))
        hint2 = self.font_small.render(
            "手势: 捏合点击 | 鼠标: 左键点击", True, (255, 255, 0)
        )
        screen.blit(hint1, (self.width // 2 - hint1.get_width() // 2, self.height - 80))
        screen.blit(hint2, (self.width // 2 - hint2.get_width() // 2, self.height - 50))

        # 绘制触摸光标
        if index_pos:
            self.draw_cursor(screen, index_pos)

            # 显示捏合提示和调试信息
            if thumb_pos:
                dist = self.distance(index_pos, thumb_pos)

                # 在手指位置绘制圆圈
                pg.draw.circle(screen, (255, 0, 0), index_pos, 10, 2)  # 食指 - 红色
                pg.draw.circle(screen, (255, 255, 0), thumb_pos, 10, 2)  # 拇指 - 黄色

                # 如果距离接近阈值，绘制连接线
                if dist < self.pinch_threshold * 2:
                    line_color = (
                        (0, 255, 0) if dist < self.pinch_threshold else (255, 165, 0)
                    )
                    pg.draw.line(screen, line_color, index_pos, thumb_pos, 2)

                # 如果捏合成功，显示提示
                if pinch_detected:
                    pinch_text = self.font_medium.render("已点击!", True, (0, 255, 0))
                    screen.blit(
                        pinch_text, (self.width // 2 - pinch_text.get_width() // 2, 30)
                    )

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked

    def draw_user_selection_screen(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 绘制标题
        title_text = self.font_large.render("选择用户", True, (0, 255, 0))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        # 绘制用户列表
        users = self.user_manager.users
        buttons = []
        button_height = 50
        start_y = 100

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
                screen,
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
            screen,
            "新建用户",
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
            screen,
            "返回",
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
        hint_text = self.font_small.render(
            "使用手势或鼠标进行交互", True, (255, 255, 0)
        )
        screen.blit(
            hint_text, (self.width // 2 - hint_text.get_width() // 2, self.height - 120)
        )

        # 绘制触摸光标
        if index_pos:
            self.draw_cursor(screen, index_pos)

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked

    def draw_new_user_screen(
        self,
        screen,
        index_pos,
        thumb_pos,
        current_text="",
        mouse_pos=None,
        mouse_click=False,
    ):
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 绘制标题
        title_text = self.font_large.render("创建新用户", True, (0, 255, 0))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        # 绘制输入框
        input_box = (self.width // 2 - 150, 120, 300, 50)
        pg.draw.rect(
            screen,
            (255, 255, 255),
            (input_box[0], input_box[1], input_box[2], input_box[3]),
            2,
        )

        # 绘制当前文本
        if current_text:
            text_surface = self.font_medium.render(current_text, True, (255, 255, 255))
            screen.blit(text_surface, (input_box[0] + 10, input_box[1] + 15))
        else:
            placeholder = self.font_medium.render(
                "输入用户名...", True, (150, 150, 150)
            )
            screen.blit(placeholder, (input_box[0] + 10, input_box[1] + 15))

        # 绘制确认按钮
        confirm_button_rect = (self.width // 2 - 150, 190, 140, 50)
        confirm_hover = self.is_point_in_rect(index_pos, confirm_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, confirm_button_rect)
        )
        self.draw_button(
            screen,
            "确认",
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
            screen,
            "取消",
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

        # 绘制触摸光标
        if index_pos:
            self.draw_cursor(screen, index_pos)

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked, input_box

    def draw_revive_question_screen(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制复活问题屏幕"""
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # 绘制标题
        title_text = self.font_large.render("复活挑战!", True, (255, 255, 0))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        # 绘制剩余复活次数
        revive_text = self.font_medium.render(
            f"剩余复活次数: {self.current_revive_chances}", True, (255, 255, 255)
        )
        screen.blit(revive_text, (self.width // 2 - revive_text.get_width() // 2, 100))

        # 绘制问题
        if self.current_question:
            question_text = self.font_medium.render(
                self.current_question["question"], True, (255, 255, 255)
            )
            screen.blit(
                question_text, (self.width // 2 - question_text.get_width() // 2, 150)
            )

            # 绘制选项
            options = self.current_question["options"]
            option_rects = []
            option_height = 50
            start_y = 200

            for i, option in enumerate(options):
                option_rect = (
                    self.width // 2 - 200,
                    start_y + i * (option_height + 10),
                    400,
                    option_height,
                )
                is_hovered = self.is_point_in_rect(index_pos, option_rect) or (
                    mouse_pos and self.is_point_in_rect(mouse_pos, option_rect)
                )
                self.draw_button(
                    screen,
                    option,
                    (option_rect[0], option_rect[1]),
                    (option_rect[2], option_rect[3]),
                    is_hovered,
                )
                option_rects.append((i, option_rect))

        # 检测选项点击
        selected_option = None
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            for option_idx, rect in option_rects:
                if self.is_point_in_rect(index_pos, rect) or (
                    mouse_pos and self.is_point_in_rect(mouse_pos, rect)
                ):
                    selected_option = option_idx
                    break

        # 绘制触摸光标
        if index_pos:
            self.draw_cursor(screen, index_pos)

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return selected_option

    def draw_game_over(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        # 先绘制游戏画面
        self.draw(screen, index_pos)

        # 添加半透明覆盖层
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # 绘制游戏结束文本
        game_over_text = self.font_large.render("游戏结束", True, (255, 0, 0))
        score_text = self.font_medium.render(
            f"分数: {self.score}", True, (255, 255, 255)
        )
        level_text = self.font_medium.render(
            f"达到关卡: {self.current_level}", True, (255, 255, 255)
        )

        screen.blit(
            game_over_text,
            (self.width // 2 - game_over_text.get_width() // 2, self.height // 2 - 100),
        )
        screen.blit(
            score_text,
            (self.width // 2 - score_text.get_width() // 2, self.height // 2 - 50),
        )
        screen.blit(
            level_text,
            (self.width // 2 - level_text.get_width() // 2, self.height // 2 - 20),
        )

        # 显示当前用户
        if self.user_manager.current_user:
            user_text = self.font_medium.render(
                f"用户: {self.user_manager.current_user}", True, (255, 255, 255)
            )
            screen.blit(
                user_text,
                (self.width // 2 - user_text.get_width() // 2, self.height // 2 + 10),
            )

        # 显示复活次数信息
        if self.current_revive_chances == 0:
            no_revive_text = self.font_medium.render(
                "复活次数已用尽", True, (255, 0, 0)
            )
            screen.blit(
                no_revive_text,
                (
                    self.width // 2 - no_revive_text.get_width() // 2,
                    self.height // 2 + 80,
                ),
            )

        # 绘制重新开始按钮
        restart_button_rect = (self.width // 2 - 100, self.height // 2 + 40, 200, 60)
        restart_hover = self.is_point_in_rect(index_pos, restart_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, restart_button_rect)
        )
        self.draw_button(
            screen,
            "重新开始",
            (restart_button_rect[0], restart_button_rect[1]),
            (restart_button_rect[2], restart_button_rect[3]),
            is_hovered=restart_hover,
        )

        # 绘制用户选择按钮
        user_button_rect = (self.width // 2 - 100, self.height // 2 + 120, 200, 60)
        user_hover = self.is_point_in_rect(index_pos, user_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, user_button_rect)
        )
        self.draw_button(
            screen,
            "选择用户",
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

        # 绘制触摸光标
        if index_pos:
            self.draw_cursor(screen, index_pos)

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked


class Game:
    def __init__(self):
        pg.init()
        pg.display.set_caption("贪吃蛇游戏 - 手势与鼠标控制")

        self.hand = hd.HandBind(
            camera_id=0,
            handdraw=True,
            draw_fps=True,
            draw_index=False,
            verbose=False,
            max_hands=1,
        )

        self.winsize = self.hand.get_img_size()
        self.screen = pg.display.set_mode(self.winsize)
        self.clock = pg.time.Clock()
        self.quit = False

        self.snake_game = SnakeGame(self.winsize[0], self.winsize[1])

        # 游戏状态
        self.game_state = "start_screen"
        self.new_user_text = ""
        self.last_key_time = 0
        self.mouse_clicked = False

        # 添加一些调试用户
        if not self.snake_game.user_manager.users:
            self.snake_game.user_manager.add_user("玩家1")
            self.snake_game.user_manager.add_user("玩家2")
            self.snake_game.user_manager.add_user("玩家3")

    def loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit = True
                return
            elif event.type == pg.KEYDOWN:
                self.handle_keyboard(event)
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    self.mouse_clicked = True

        success, processed_img, landmarks = self.hand.process_frame()

        if success:
            # 将OpenCV图像转换为Pygame表面
            frame_surface = self.cv2_to_pygame(cv2.flip(processed_img, 1))
            self.screen.blit(frame_surface, (0, 0))

            # 获取手指坐标
            index_pos, thumb_pos = self.get_finger_positions(landmarks)

            # 获取鼠标状态
            mouse_pos = pg.mouse.get_pos()
            mouse_click = getattr(self, "mouse_clicked", False)
            self.mouse_clicked = False  # 重置点击状态

            # 根据游戏状态处理
            self.handle_game_states(index_pos, thumb_pos, mouse_pos, mouse_click)

            pg.display.flip()
            self.clock.tick(60)

    def cv2_to_pygame(self, cv2_img):
        """将OpenCV图像转换为Pygame表面"""
        # 将BGR转换为RGB
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        # 转置图像（旋转90度）
        rotated_img = cv2.transpose(rgb_img)
        # 创建Pygame表面
        return pg.surfarray.make_surface(rotated_img)

    def get_finger_positions(self, landmarks):
        """获取食指和拇指坐标"""
        index_pos = None
        thumb_pos = None

        if landmarks and len(landmarks) > 0:
            img_height, img_width = self.winsize[1], self.winsize[0]

            # 获取原始坐标
            original_index_pos = landmarks[0][8]  # 食指指尖
            original_thumb_pos = landmarks[0][4]  # 拇指指尖

            # 镜像坐标（因为摄像头画面是镜像的）
            index_pos = (img_width - original_index_pos[0], original_index_pos[1])
            thumb_pos = (img_width - original_thumb_pos[0], original_thumb_pos[1])

        return index_pos, thumb_pos

    def handle_keyboard(self, event):
        """处理键盘输入"""
        current_time = time.time()

        if self.game_state == "new_user":
            if current_time - self.last_key_time > 0.1:  # 防止按键重复
                self.last_key_time = current_time

                if event.key == pg.K_BACKSPACE:
                    self.new_user_text = self.new_user_text[:-1]
                elif event.key == pg.K_RETURN:
                    if self.new_user_text:
                        if self.snake_game.user_manager.add_user(self.new_user_text):
                            self.snake_game.user_manager.current_user = (
                                self.new_user_text
                            )
                            self.game_state = "playing"
                            print(f"新用户已创建: {self.new_user_text}")
                elif event.key == pg.K_ESCAPE:
                    self.game_state = "user_selection"
                else:
                    # 处理字母和数字输入
                    if len(self.new_user_text) < 15:
                        char = event.unicode
                        if char.isalnum() or char in ["_", "-"]:
                            self.new_user_text += char

        # 全局快捷键
        if event.key == pg.K_q:
            self.quit = True
        elif event.key == pg.K_r and self.game_state == "game_over":
            self.snake_game.current_level = 1
            self.snake_game.reset_game()
            self.game_state = "playing"
        elif event.key == pg.K_SPACE and self.game_state == "start_screen":
            self.game_state = "playing"
        elif event.key == pg.K_b and self.game_state == "playing":
            self.game_state = "start_screen"
        elif event.key == pg.K_t:  # 调整捏合阈值
            self.snake_game.pinch_threshold += 5
            print(f"捏合阈值调整为: {self.snake_game.pinch_threshold}")
        elif event.key == pg.K_y:  # 减小捏合阈值
            self.snake_game.pinch_threshold = max(
                10, self.snake_game.pinch_threshold - 5
            )
            print(f"捏合阈值调整为: {self.snake_game.pinch_threshold}")

    def handle_game_states(self, index_pos, thumb_pos, mouse_pos, mouse_click):
        """处理不同的游戏状态"""
        if self.game_state == "start_screen":
            buttons_clicked = self.snake_game.draw_start_screen(
                self.screen, index_pos, thumb_pos, mouse_pos, mouse_click
            )

            for button in buttons_clicked:
                if button == "start":
                    if self.snake_game.user_manager.current_user:
                        self.game_state = "playing"
                    else:
                        self.game_state = "user_selection"
                elif button == "select_user":
                    self.game_state = "user_selection"

        elif self.game_state == "user_selection":
            buttons_clicked = self.snake_game.draw_user_selection_screen(
                self.screen, index_pos, thumb_pos, mouse_pos, mouse_click
            )

            for button in buttons_clicked:
                if button[0] == "select":
                    self.snake_game.user_manager.current_user = button[1]
                    self.game_state = "playing"
                elif button[0] == "new_user":
                    self.game_state = "new_user"
                    self.new_user_text = ""
                elif button[0] == "back":
                    self.game_state = "start_screen"

        elif self.game_state == "new_user":
            buttons_clicked, input_box = self.snake_game.draw_new_user_screen(
                self.screen,
                index_pos,
                thumb_pos,
                self.new_user_text,
                mouse_pos,
                mouse_click,
            )

            for button in buttons_clicked:
                if button[0] == "confirm" and button[1]:
                    if self.snake_game.user_manager.add_user(button[1]):
                        self.snake_game.user_manager.current_user = button[1]
                        self.game_state = "playing"
                elif button[0] == "cancel":
                    self.game_state = "user_selection"

        elif self.game_state == "playing":
            if not self.snake_game.game_over:
                self.snake_game.update(index_pos, thumb_pos)
                self.snake_game.draw(self.screen, index_pos)
            else:
                # 检查是否有复活机会
                if self.snake_game.current_revive_chances > 0:
                    # 进入复活问题状态
                    self.snake_game.current_question = (
                        self.snake_game.question_manager.get_random_question()
                    )
                    self.snake_game.revive_in_progress = True
                    self.game_state = "revive_question"
                else:
                    # 没有复活机会，直接游戏结束
                    if self.snake_game.user_manager.current_user:
                        self.snake_game.user_manager.update_score(
                            self.snake_game.user_manager.current_user,
                            self.snake_game.score,
                            self.snake_game.current_level,
                            self.snake_game.current_revive_chances,
                        )
                    self.game_state = "game_over"

        elif self.game_state == "revive_question":
            # 显示复活问题
            selected_option = self.snake_game.draw_revive_question_screen(
                self.screen, index_pos, thumb_pos, mouse_pos, mouse_click
            )

            if selected_option is not None:
                # 检查答案
                if self.snake_game.question_manager.check_answer(
                    self.snake_game.current_question, selected_option
                ):
                    # 答对了，复活玩家
                    self.snake_game.revive_player()
                    self.game_state = "playing"

                    self.snake_game.current_revive_chances -= 1
                    print("回答正确! 已复活。")
                else:
                    # 答错了，减少复活次数并直接游戏结束
                    # self.snake_game.current_revive_chances -= 1
                    print(
                        f"回答错误! 剩余复活次数: {self.snake_game.current_revive_chances}"
                    )

                    # 直接游戏结束
                    if self.snake_game.user_manager.current_user:
                        self.snake_game.user_manager.update_score(
                            self.snake_game.user_manager.current_user,
                            self.snake_game.score,
                            self.snake_game.current_level,
                            self.snake_game.current_revive_chances,
                        )
                    self.game_state = "game_over"

        elif self.game_state == "game_over":
            buttons_clicked = self.snake_game.draw_game_over(
                self.screen, index_pos, thumb_pos, mouse_pos, mouse_click
            )

            for button in buttons_clicked:
                if button == "restart":
                    self.snake_game.current_level = 1
                    self.snake_game.reset_game()
                    self.game_state = "playing"
                elif button == "select_user":
                    self.game_state = "user_selection"

    def __del__(self):
        pg.quit()


def main():
    game = Game()

    print("贪吃蛇游戏说明:")
    print("- 移动食指来控制蛇头")
    print("- 食指和拇指捏合可以点击按钮，也可以用鼠标点击")
    print("- 吃到红色食物可以增加分数")
    print("- 避免撞到边界、自己和蓝色障碍物")
    print("- 游戏共有10关，难度递增")
    print("- 每吃5个食物进入下一关")
    print("- 有3次复活机会，答对问题可以复活")
    print("- 捏合阈值:", game.snake_game.pinch_threshold)

    while not game.quit:
        game.loop()

    pygame.quit()


if __name__ == "__main__":
    main()
