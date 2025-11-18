import random
import threading
import time

import cv2
import pygame
import pygame as pg

import getquestion as gq
import hand as hd


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
                "question": "人工智能（AI）的主要目标是什么？",
                "options": [
                    "A 取代所有人类工作",
                    "B 模拟、延伸和扩展人类智能",
                    "C 制造具有情感的机器人",
                    "D 实现计算机硬件的高速发展",
                ],
                "correct": 1,
            },
            {
                "question": "以下哪项是机器学习的定义？",
                "options": [
                    "A 计算机通过数据自动改进性能",
                    "B 人类教计算机如何使用",
                    "C 只有用于预测股票市场",
                    "D 一种编程语言",
                ],
                "correct": 0,
            },
            {
                "question": "神经网络在AI中常用于什么？",
                "options": [
                    "A 模式识别和预测",
                    "B 连接互联网",
                    "C 存储大量数据",
                    "D 只有用于游戏AI",
                ],
                "correct": 0,
            },
            {
                "question": '谁提出了"图灵测试"来评估机器智能？',
                "options": [
                    "A 艾伦·图灵",
                    "B 约翰·麦卡锡",
                    "C 马文·明斯基",
                    "D 比尔·盖茨",
                ],
                "correct": 0,
            },
            {
                "question": "弱人工智能指的是什么？",
                "options": [
                    "A 专门用于特定任务的AI",
                    "B 拥有自我意识的AI",
                    "C 比人类更聪明的AI",
                    "D 只能在科幻中存在的AI",
                ],
                "correct": 0,
            },
            {
                "question": "AI在自动驾驶汽车中主要发挥什么作用？",
                "options": [
                    "A 感知环境并做出决策",
                    "B 制造汽车零件",
                    "C 提供娱乐系统",
                    "D 只有用于导航地图",
                ],
                "correct": 0,
            },
            {
                "question": "自然语言处理（NLP）允许计算机做什么？",
                "options": [
                    "A 理解和生成人类语言",
                    "B 处理自然现象",
                    "C 管理语言学校",
                    "D 只有用于聊天机器人",
                ],
                "correct": 0,
            },
            {
                "question": "计算机视觉是AI的一个领域，专注于什么？",
                "options": [
                    "A 从图像和视频中提取信息",
                    "B 提高摄像头质量",
                    "C 保护计算机视觉健康",
                    "D 只有用于监控系统",
                ],
                "correct": 0,
            },
            {
                "question": "以下哪项是AI的潜在风险？",
                "options": [
                    "A 就业岗位被自动化取代",
                    "B 计算机速度变慢",
                    "C 软件bug增加",
                    "D 只有影响制造业",
                ],
                "correct": 0,
            },
            {
                "question": "强化学习在AI中是什么？",
                "options": [
                    "A 通过奖励和惩罚学习最优行为",
                    "B 加强计算机硬件",
                    "C 只有用于玩游戏",
                    "D 一种记忆增强技术",
                ],
                "correct": 0,
            },
            {
                "question": "深度学习是什么？",
                "options": [
                    "A 一种简单的算法",
                    "B 使用多层神经网络的机器学习方法",
                    "C 只有用于自然语言处理",
                    "D 一种数据库技术",
                ],
                "correct": 1,
            },
            {
                "question": "AI在医疗领域常用于什么？",
                "options": [
                    "A 诊断疾病和辅助治疗",
                    "B 制造医疗器械",
                    "C 只有用于手术机器人",
                    "D 管理医院财务",
                ],
                "correct": 0,
            },
            {
                "question": "专家系统是什么？",
                "options": [
                    "A 模拟人类专家决策的AI系统",
                    "B 只有用于法律领域",
                    "C 一种操作系统",
                    "D 专家使用的软件",
                ],
                "correct": 0,
            },
            {
                "question": '谁通常被称为"人工智能之父"？',
                "options": [
                    "A 艾伦·图灵",
                    "B 约翰·麦卡锡",
                    "C 马文·明斯基",
                    "D 比尔·盖茨",
                ],
                "correct": 1,
            },
            {
                "question": "监督学习是什么？",
                "options": [
                    "A 使用标签数据训练模型",
                    "B 只有用于分类任务",
                    "C 无监督的学习方法",
                    "D 人类监督下的学习",
                ],
                "correct": 0,
            },
            {
                "question": "AI在语音识别中主要做什么？",
                "options": [
                    "A 将语音转换为文本",
                    "B 提高语音音量",
                    "C 只有用于虚拟助手",
                    "D 生成音乐",
                ],
                "correct": 0,
            },
            {
                "question": "生成对抗网络（GAN）用于什么？",
                "options": [
                    "A 生成新数据，如图像",
                    "B 对抗网络攻击",
                    "C 只有用于游戏AI",
                    "D 一种安全协议",
                ],
                "correct": 0,
            },
            {
                "question": "AI在推荐系统中的应用是什么？",
                "options": [
                    "A 根据用户偏好推荐物品",
                    "B 只有用于电子商务",
                    "C 推荐朋友",
                    "D 推荐电影仅限",
                ],
                "correct": 0,
            },
            {
                "question": "无监督学习是什么？",
                "options": [
                    "A 使用无标签数据发现模式",
                    "B 没有人类干预的学习",
                    "C 只有用于聚类",
                    "D 一种失败的学习方法",
                ],
                "correct": 0,
            },
            {
                "question": "AI在图像识别中常见用途是什么？",
                "options": [
                    "A 识别物体和场景",
                    "B 只有用于人脸识别",
                    "C 美化图像",
                    "D 存储图像",
                ],
                "correct": 0,
            },
        ]
        self.question_ready = False
        self.question_thread = None

    def gen_question(self):
        """在后台线程中生成问题"""
        try:
            self.question = gq.convert(gq.get_question())
            self.question_ready = True
        except Exception as e:
            print(f"生成问题失败: {e}")
            self.question = random.choice(self.questions)
            self.question_ready = True

    def start_question_generation(self):
        """启动问题生成线程"""
        if not self.question_thread or not self.question_thread.is_alive():
            self.question_ready = False
            self.question_thread = threading.Thread(target=self.gen_question)
            self.question_thread.daemon = True
            self.question_thread.start()

    def get_random_question(self):
        """获取题目，如果问题还没准备好则使用备用问题"""
        if self.question_ready and self.question:
            return self.question
        else:
            return random.choice(self.questions)

    def check_answer(self, question, selected_option):
        """检查答案是否正确"""
        return question["correct"] == selected_option

    def reset(self):
        self.question = None
        self.question_ready = False


class SnakeGame:
    def __init__(self, width=640, height=480, scale_factor=1.0):
        self.scale_factor = scale_factor
        self.base_width = width
        self.base_height = height
        self.width = int(width * scale_factor)
        self.height = int(height * scale_factor)

        self.max_speed = 8 * scale_factor
        self.pinch_threshold = 20 * scale_factor
        self.pinch_cooldown = 0.5
        self.last_pinch_time = 0
        self.obstacles = []
        self.current_level = 1
        self.max_level = 10
        self.question_manager = QuestionManager()
        self.max_revive_chances = 3
        self.current_revive_chances = self.max_revive_chances
        self.current_question = None
        self.revive_in_progress = False

        pg.font.init()
        font_size_large = max(24, int(36 * scale_factor))
        font_size_medium = max(18, int(24 * scale_factor))
        font_size_small = max(14, int(18 * scale_factor))

        self.font_large = pg.font.SysFont("simhei", font_size_large)
        self.font_medium = pg.font.SysFont("simhei", font_size_medium)
        self.font_small = pg.font.SysFont("simhei", font_size_small)

        self.cursor_color = (255, 255, 0)
        self.pinch_active = False

        self.question_manager.start_question_generation()

        self.reset_game()

    def reset_game(self):
        self.question_manager.reset()
        start_x, start_y = self.width // 2, self.height // 2
        self.snake_pos = [(start_x, start_y)]

        segment_distance = 20 * self.scale_factor
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
        self.last_head_pos = self.snake_pos[0]

        self.current_revive_chances = self.max_revive_chances
        self.revive_in_progress = False

    def generate_obstacles(self):
        self.obstacles = []
        base_count = 2 + self.current_level * random.randint(5, 10)

        safe_radius = 150 * self.scale_factor
        safe_center = (self.width // 2, self.height // 2)

        for _ in range(base_count):
            min_size = (
                20 + self.current_level * random.randint(1, 5)
            ) * self.scale_factor
            max_size = (
                40 + self.current_level * random.randint(5, 10)
            ) * self.scale_factor
            width = random.randint(int(min_size), int(max_size))
            height = random.randint(int(min_size), int(max_size))

            max_attempts = 50
            obstacle_placed = False

            for attempt in range(max_attempts):
                x = random.randint(50, self.width - width - 50)
                y = random.randint(50, self.height - height - 50)

                obstacle_center = (x + width // 2, y + height // 2)
                distance_to_safe = (
                    (obstacle_center[0] - safe_center[0]) ** 2
                    + (obstacle_center[1] - safe_center[1]) ** 2
                ) ** 0.5

                if distance_to_safe < safe_radius:
                    continue

                overlap_with_snake = any(
                    self.distance((x + width // 2, y + height // 2), pos)
                    < (min(width, height) // 2 + 50 * self.scale_factor)
                    for pos in self.snake_pos
                )

                overlap_with_food = self.distance(
                    (x + width // 2, y + height // 2), self.food_pos
                ) < (min(width, height) // 2 + 30 * self.scale_factor)

                overlap_with_obstacles = any(
                    self.distance(
                        (x + width // 2, y + height // 2),
                        (obs.x + obs.width // 2, obs.y + obs.height // 2),
                    )
                    < (
                        min(width, height) // 2
                        + min(obs.width, obs.height) // 2
                        + 20 * self.scale_factor
                    )
                    for obs in self.obstacles
                )

                if (
                    not overlap_with_snake
                    and not overlap_with_food
                    and not overlap_with_obstacles
                ):
                    obstacle_type = "rectangle"
                    if random.random() < self.current_level * 0.08:
                        obstacle_type = "circle"

                    obstacle = Obstacle(x, y, width, height, obstacle_type)
                    self.obstacles.append(obstacle)
                    obstacle_placed = True
                    break

            if not obstacle_placed:
                continue

        if self.current_level >= 5:
            border_width = 10 * self.scale_factor
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
            cross_width = 20 * self.scale_factor
            cross_height = 100 * self.scale_factor
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
        max_attempts = 100  # 增加最大尝试次数
        for attempt in range(max_attempts):
            food_pos = (
                random.randint(50, self.width - 50),
                random.randint(50, self.height - 50),
            )
            if all(
                self.distance(food_pos, pos) > 50 * self.scale_factor
                for pos in self.snake_pos
            ) and not any(obs.contains_point(food_pos) for obs in self.obstacles):
                return food_pos

        return (self.width // 4, self.height // 4)

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
        self.snake_pos.insert(0, new_head)

        if len(self.snake_pos) > self.snake_length:
            self.snake_pos.pop()

    def check_collision_with_segment(
        self, point, segment_start, segment_end, threshold=8
    ):
        """检查点是否与线段碰撞"""
        segment_length = self.distance(segment_start, segment_end)

        if segment_length == 0:
            return self.distance(point, segment_start) < threshold

        t = (
            (point[0] - segment_start[0]) * (segment_end[0] - segment_start[0])
            + (point[1] - segment_start[1]) * (segment_end[1] - segment_start[1])
        ) / (segment_length * segment_length)

        t = max(0, min(1, t))

        projection = (
            segment_start[0] + t * (segment_end[0] - segment_start[0]),
            segment_start[1] + t * (segment_end[1] - segment_start[1]),
        )

        return self.distance(point, projection) < threshold

    def check_self_collision(self, head_pos):
        """检查蛇头是否与蛇身碰撞"""
        for i, pos in enumerate(self.snake_pos):
            if i < 3:  # 跳过前3个节点
                continue
            if self.distance(head_pos, pos) < 12 * self.scale_factor:
                return True

        for i in range(1, len(self.snake_pos) - 3):  # 跳过前几个线段
            if self.check_collision_with_segment(
                head_pos, self.snake_pos[i], self.snake_pos[i + 1]
            ):
                return True

        return False

    def revive_player(self):
        """复活玩家 - 保留分数和关卡，只重置蛇的位置"""
        if self.current_revive_chances > 0:
            start_x, start_y = self.width // 2, self.height // 2
            self.snake_pos = [(start_x, start_y)]

            segment_distance = 20 * self.scale_factor
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
        if current_time - self.last_move_time < 0.05:
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
        x = max(20 * self.scale_factor, min(self.width - 20 * self.scale_factor, x))
        y = max(20 * self.scale_factor, min(self.height - 20 * self.scale_factor, y))
        finger_pos = (x, y)

        current_head = self.snake_pos[0]
        dx = finger_pos[0] - current_head[0]
        dy = finger_pos[1] - current_head[1]
        dist = self.distance(current_head, finger_pos)

        if dist < 3 * self.scale_factor:
            return

        move_dist = min(dist, self.max_speed)

        dir_x = dx / dist
        dir_y = dy / dist

        new_head = (
            int(current_head[0] + dir_x * move_dist),
            int(current_head[1] + dir_y * move_dist),
        )

        new_x, new_y = new_head
        new_x = max(
            15 * self.scale_factor, min(self.width - 15 * self.scale_factor, new_x)
        )
        new_y = max(
            15 * self.scale_factor, min(self.height - 15 * self.scale_factor, new_y)
        )
        new_head = (new_x, new_y)

        # 检查是否撞到障碍物
        for obstacle in self.obstacles:
            if obstacle.contains_point(new_head):
                self.game_over = True
                return

        # 检查是否撞到边界
        if (
            new_head[0] < 5 * self.scale_factor
            or new_head[0] > self.width - 5 * self.scale_factor
            or new_head[1] < 5 * self.scale_factor
            or new_head[1] > self.height - 5 * self.scale_factor
        ):
            self.game_over = True
            return

        # 检查是否与自身碰撞
        if self.check_self_collision(new_head):
            self.game_over = True
            return

        self.update_snake_position(new_head)

        if self.distance(new_head, self.food_pos) < 25 * self.scale_factor:
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
        for obstacle in self.obstacles:
            obstacle.draw(screen)

        if len(self.snake_pos) > 1:
            for i in range(len(self.snake_pos) - 1):
                start_pos = self.snake_pos[i]
                end_pos = self.snake_pos[i + 1]

                color_ratio = i / len(self.snake_pos)
                color = (0, int(200 * (1 - color_ratio)), 0)

                line_width = max(6, int(12 * self.scale_factor))
                pg.draw.line(screen, color, start_pos, end_pos, line_width)

        if self.snake_pos:
            head_pos = self.snake_pos[0]
            head_radius = max(8, int(12 * self.scale_factor))
            pg.draw.circle(screen, (0, 255, 0), head_pos, head_radius)  # 蛇头
            pg.draw.circle(screen, (255, 255, 255), head_pos, head_radius, 2)  # 边框

        food_radius = max(8, int(12 * self.scale_factor))
        pg.draw.circle(screen, (255, 0, 0), self.food_pos, food_radius)
        pg.draw.circle(screen, (255, 255, 255), self.food_pos, food_radius, 2)

        if finger_pos:
            cursor_radius = max(15, int(20 * self.scale_factor))
            pg.draw.circle(screen, (255, 255, 0), finger_pos, cursor_radius, 3)
            pg.draw.circle(screen, (255, 255, 0), finger_pos, 5)

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

        if self.last_finger_pos is None:
            hint_text = self.font_medium.render(
                "请把手放在画面内!", True, (255, 255, 0)
            )
            screen.blit(hint_text, (self.width // 2 - 150, self.height - 40))

    def draw_cursor(self, screen, finger_pos):
        """绘制触摸光标"""
        if finger_pos:
            color = (
                (0, 255, 0) if self.pinch_active else (255, 255, 0)
            )  # 绿色当捏合，黄色默认
            cursor_radius = max(12, int(15 * self.scale_factor))
            pg.draw.circle(screen, color, finger_pos, cursor_radius, 3)
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
        button_width = max(150, int(200 * self.scale_factor))
        button_height = max(40, int(60 * self.scale_factor))
        start_button_rect = (
            self.width // 2 - button_width // 2,
            self.height // 2 - 30,
            button_width,
            button_height,
        )
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

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if start_button_hover:
                buttons_clicked.append("start")

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
                finger_radius = max(8, int(10 * self.scale_factor))
                pg.draw.circle(
                    screen, (255, 0, 0), index_pos, finger_radius, 2
                )  # 食指 - 红色
                pg.draw.circle(
                    screen, (255, 255, 0), thumb_pos, finger_radius, 2
                )  # 拇指 - 黄色

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

        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked

    def draw_revive_question_screen(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制复活问题屏幕"""
        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        title_text = self.font_large.render("复活挑战!", True, (255, 255, 0))
        screen.blit(title_text, (self.width // 2 - title_text.get_width() // 2, 50))

        revive_text = self.font_medium.render(
            f"剩余复活次数: {self.current_revive_chances}", True, (255, 255, 255)
        )
        screen.blit(revive_text, (self.width // 2 - revive_text.get_width() // 2, 100))

        option_rects = []  # 初始化option_rects，防止未定义错误
        if self.current_question:
            question_text = self.font_medium.render(
                self.current_question["question"], True, (255, 255, 255)
            )
            screen.blit(
                question_text, (self.width // 2 - question_text.get_width() // 2, 150)
            )

            options = self.current_question["options"]
            option_height = max(35, int(50 * self.scale_factor))
            option_width = max(300, int(400 * self.scale_factor))
            start_y = 200

            for i, option in enumerate(options):
                option_rect = (
                    self.width // 2 - option_width // 2,
                    start_y + i * (option_height + 10),
                    option_width,
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
        else:
            no_question_text = self.font_medium.render(
                "正在加载题目...", True, (255, 255, 255)
            )
            screen.blit(
                no_question_text,
                (self.width // 2 - no_question_text.get_width() // 2, 150),
            )

        selected_option = None
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            for option_idx, rect in option_rects:
                if self.is_point_in_rect(index_pos, rect) or (
                    mouse_pos and self.is_point_in_rect(mouse_pos, rect)
                ):
                    selected_option = option_idx
                    break

        if index_pos:
            self.draw_cursor(screen, index_pos)

        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return selected_option

    def draw_game_over(
        self, screen, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        self.draw(screen, index_pos)

        overlay = pg.Surface((self.width, self.height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

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

        button_width = max(150, int(200 * self.scale_factor))
        button_height = max(40, int(60 * self.scale_factor))
        restart_button_rect = (
            self.width // 2 - button_width // 2,
            self.height // 2 + 40,
            button_width,
            button_height,
        )
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

        menu_button_rect = (
            self.width // 2 - button_width // 2,
            self.height // 2 + 120,
            button_width,
            button_height,
        )
        menu_hover = self.is_point_in_rect(index_pos, menu_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, menu_button_rect)
        )
        self.draw_button(
            screen,
            "返回主菜单",
            (menu_button_rect[0], menu_button_rect[1]),
            (menu_button_rect[2], menu_button_rect[3]),
            is_hovered=menu_hover,
        )

        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            if restart_hover:
                buttons_clicked.append("restart")
            elif menu_hover:
                buttons_clicked.append("menu")

        if index_pos:
            self.draw_cursor(screen, index_pos)

        if mouse_pos:
            pg.draw.circle(screen, (255, 255, 0), mouse_pos, 8)

        return buttons_clicked


class Game:
    def __init__(self, scale_factor=1.0):
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

        original_size = self.hand.get_img_size()
        self.scale_factor = scale_factor
        self.winsize = (
            int(original_size[0] * scale_factor),
            int(original_size[1] * scale_factor),
        )
        self.screen = pg.display.set_mode(self.winsize)
        self.clock = pg.time.Clock()
        self.quit = False

        self.snake_game = SnakeGame(original_size[0], original_size[1], scale_factor)

        self.game_state = "start_screen"
        self.mouse_clicked = False

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
            frame_surface = self.cv2_to_pygame(cv2.flip(processed_img, 1))

            if self.scale_factor != 1.0:
                frame_surface = pg.transform.scale(frame_surface, self.winsize)

            self.screen.blit(frame_surface, (0, 0))

            index_pos, thumb_pos = self.get_finger_positions(landmarks)

            mouse_pos = pg.mouse.get_pos()
            mouse_click = getattr(self, "mouse_clicked", False)
            self.mouse_clicked = False  # 重置点击状态

            self.handle_game_states(index_pos, thumb_pos, mouse_pos, mouse_click)

            pg.display.flip()
            self.clock.tick(60)

    def cv2_to_pygame(self, cv2_img):
        """将OpenCV图像转换为Pygame表面"""
        rgb_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        rotated_img = cv2.transpose(rgb_img)
        return pg.surfarray.make_surface(rotated_img)

    def get_finger_positions(self, landmarks):
        """获取食指和拇指坐标"""
        index_pos = None
        thumb_pos = None

        if landmarks and len(landmarks) > 0:
            img_height, img_width = self.winsize[1], self.winsize[0]

            original_index_pos = landmarks[0][8]  # 食指指尖
            original_thumb_pos = landmarks[0][4]  # 拇指指尖

            index_pos = (
                img_width - int(original_index_pos[0] * self.scale_factor),
                int(original_index_pos[1] * self.scale_factor),
            )
            thumb_pos = (
                img_width - int(original_thumb_pos[0] * self.scale_factor),
                int(original_thumb_pos[1] * self.scale_factor),
            )

        return index_pos, thumb_pos

    def handle_keyboard(self, event):
        """处理键盘输入"""
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
            self.snake_game.pinch_threshold += 5 * self.scale_factor
            print(f"捏合阈值调整为: {self.snake_game.pinch_threshold}")
        elif event.key == pg.K_y:  # 减小捏合阈值
            self.snake_game.pinch_threshold = max(
                10 * self.scale_factor,
                self.snake_game.pinch_threshold - 5 * self.scale_factor,
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
                    self.game_state = "playing"

        elif self.game_state == "playing":
            if not self.snake_game.game_over:
                self.snake_game.update(index_pos, thumb_pos)
                self.snake_game.draw(self.screen, index_pos)
            else:
                if self.snake_game.current_revive_chances > 0:
                    self.snake_game.current_question = (
                        self.snake_game.question_manager.get_random_question()
                    )
                    self.snake_game.revive_in_progress = True
                    self.game_state = "revive_question"
                else:
                    self.game_state = "game_over"

        elif self.game_state == "revive_question":
            selected_option = self.snake_game.draw_revive_question_screen(
                self.screen, index_pos, thumb_pos, mouse_pos, mouse_click
            )

            if selected_option is not None:
                if self.snake_game.question_manager.check_answer(
                    self.snake_game.current_question, selected_option
                ):
                    self.snake_game.revive_player()
                    self.game_state = "playing"

                    self.snake_game.current_revive_chances -= 1
                    print("回答正确! 已复活。")
                else:
                    print(
                        f"回答错误! 剩余复活次数: {self.snake_game.current_revive_chances}"
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
                elif button == "menu":
                    self.game_state = "start_screen"

    def __del__(self):
        pg.quit()


def main():
    # 设置放大系数
    scale_factor = 1.0

    game = Game(scale_factor=scale_factor)

    print("贪吃蛇游戏说明:")
    print("- 移动食指来控制蛇头")
    print("- 食指和拇指捏合可以点击按钮，也可以用鼠标点击")
    print("- 吃到红色食物可以增加分数")
    print("- 避免撞到边界、自己和蓝色障碍物")
    print("- 游戏共有10关，难度递增")
    print("- 每吃5个食物进入下一关")
    print("- 有3次复活机会，答对问题可以复活")
    print(f"- 当前放大系数: {scale_factor}")
    print(f"- 捏合阈值: {game.snake_game.pinch_threshold}")

    while not game.quit:
        game.loop()

    pygame.quit()


if __name__ == "__main__":
    main()
