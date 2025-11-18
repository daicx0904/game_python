# 增加了完整的答题复活机制（全中文界面）
import json
import os
import random
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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


class ChineseTextRenderer:
    """中文字体渲染器"""

    def __init__(self):
        self.fonts = {}
        self.default_font_paths = [
            "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
            "C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑
            "C:/Windows/Fonts/simsun.ttc",  # Windows 宋体
            "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux 文泉驿
            "./simhei.ttf",  # 当前目录下的字体文件
        ]
        self.load_fonts()

        # 如果所有字体都加载失败，创建备用方案
        if not self.fonts:
            self.create_fallback_fonts()

    def create_fallback_fonts(self):
        """创建备用字体"""
        print("警告: 所有字体加载失败，使用备用方案")
        try:
            # 使用PIL的默认字体
            self.fonts[20] = ImageFont.load_default()
            self.fonts[25] = ImageFont.load_default()
            self.fonts[30] = ImageFont.load_default()
            self.fonts[40] = ImageFont.load_default()
            self.fonts[50] = ImageFont.load_default()
            print("备用字体创建成功")
        except Exception as e:
            print(f"备用字体创建失败: {e}")

    def load_fonts(self):
        """加载字体"""
        font_loaded = False

        for font_path in self.default_font_paths:
            if os.path.exists(font_path):
                try:
                    # 加载不同大小的字体
                    self.fonts[20] = ImageFont.truetype(font_path, 20)
                    self.fonts[25] = ImageFont.truetype(font_path, 25)
                    self.fonts[30] = ImageFont.truetype(font_path, 30)
                    self.fonts[40] = ImageFont.truetype(font_path, 40)
                    self.fonts[50] = ImageFont.truetype(font_path, 50)
                    print(f"成功加载字体: {font_path}")
                    font_loaded = True
                    break
                except Exception as e:
                    print(f"加载字体失败 {font_path}: {e}")

        # 如果系统字体都失败，尝试使用PIL内置字体
        if not font_loaded:
            try:
                # 尝试加载PIL的默认字体
                self.fonts[20] = ImageFont.load_default()
                self.fonts[25] = ImageFont.load_default()
                self.fonts[30] = ImageFont.load_default()
                self.fonts[40] = ImageFont.load_default()
                self.fonts[50] = ImageFont.load_default()
                print("使用PIL默认字体")
            except Exception as e:
                print(f"加载PIL默认字体失败: {e}")

    def put_text(self, img, text, position, font_size=30, color=(255, 255, 255)):
        """在图像上绘制文本"""
        # 如果字体不可用，使用OpenCV的简单文本绘制
        if font_size not in self.fonts or self.fonts[font_size] is None:
            try:
                font_scale = font_size / 30.0
                thickness = max(1, int(font_scale * 2))
                cv2.putText(
                    img,
                    text,
                    position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    thickness,
                )
                return img
            except:
                return img

        try:
            # 确保图像是3通道的
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # 将OpenCV图像转换为PIL图像
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)

            # 绘制文本
            draw.text(position, text, font=self.fonts[font_size], fill=color)

            # 转换回OpenCV格式
            result_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            return result_img
        except Exception as e:
            print(f"PIL文本绘制失败，使用OpenCV备用方案: {e}")
            # 如果绘制失败，使用OpenCV的简单文本
            try:
                font_scale = font_size / 30.0
                thickness = max(1, int(font_scale * 2))
                cv2.putText(
                    img,
                    text,
                    position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    color,
                    thickness,
                )
            except:
                pass
            return img

    def get_text_size(self, text, font_size=30):
        """获取文本尺寸"""
        if font_size not in self.fonts or self.fonts[font_size] is None:
            # 估算文本大小
            return (len(text) * font_size, font_size + 10)

        try:
            # 尝试使用PIL获取文本尺寸
            bbox = self.fonts[font_size].getbbox(text)
            return (bbox[2] - bbox[0], bbox[3] - bbox[1])
        except:
            # 备用方案
            return (len(text) * font_size, font_size + 10)


class QuestionManager:
    """题目管理器，支持本地题库和未来扩展LLM API"""

    def __init__(self, filename="questions.json"):
        self.filename = filename
        self.questions = self.load_questions()

    def load_questions(self):
        """从JSON文件加载题目"""
        default_questions = [
            {
                "question": "Python中哪个关键字用于定义函数？",
                "options": ["A. def", "B. function", "C. define", "D. func"],
                "correct_answer": 0,
            },
            {
                "question": "以下哪个不是Python的基本数据类型？",
                "options": ["A. int", "B. string", "C. array", "D. float"],
                "correct_answer": 2,
            },
            {
                "question": "在Python中，如何表示注释？",
                "options": ["A. //", "B. /* */", "C. #", "D. --"],
                "correct_answer": 2,
            },
            {
                "question": "哪个符号用于字典的定义？",
                "options": ["A. {}", "B. []", "C. ()", "D. <>"],
                "correct_answer": 0,
            },
            {
                "question": "Python中列表的索引从什么开始？",
                "options": ["A. 0", "B. 1", "C. -1", "D. 任意数字"],
                "correct_answer": 0,
            },
            {
                "question": "哪个函数用于获取列表长度？",
                "options": ["A. size()", "B. length()", "C. len()", "D. count()"],
                "correct_answer": 2,
            },
            {
                "question": "Python中使用哪个关键字进行循环？",
                "options": ["A. for", "B. loop", "C. while", "D. 以上都是"],
                "correct_answer": 3,
            },
            {
                "question": "哪个模块用于处理日期和时间？",
                "options": ["A. time", "B. datetime", "C. date", "D. 以上都是"],
                "correct_answer": 3,
            },
        ]

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                # 如果文件损坏，创建默认题库
                self.save_questions(default_questions)
                return default_questions
        else:
            # 创建默认题库
            self.save_questions(default_questions)
            return default_questions

    def save_questions(self, questions=None):
        """保存题目到JSON文件"""
        if questions is None:
            questions = self.questions

        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False

    def get_random_question(self):
        """随机获取一道题目"""
        if self.questions:
            return random.choice(self.questions)
        return None

    def add_question(self, question, options, correct_answer):
        """添加新题目"""
        new_question = {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
        }
        self.questions.append(new_question)
        return self.save_questions()

    def validate_answer(self, question, selected_option):
        """验证答案是否正确"""
        return question["correct_answer"] == selected_option


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
        self.max_speed = 8  # 最大移动速度（像素/帧）
        self.min_distance = 50  # 增加蛇身节点之间的最小距离，使蛇身更长
        self.user_manager = UserManager()
        self.question_manager = QuestionManager()  # 新增题目管理器
        self.text_renderer = ChineseTextRenderer()  # 中文字体渲染器
        self.pinch_threshold = 20  # 捏合检测阈值
        self.pinch_cooldown = 0.5  # 捏合冷却时间（秒）
        self.last_pinch_time = 0  # 上次捏合时间
        self.obstacles = []  # 障碍物列表
        self.current_level = 1  # 当前关卡
        self.max_level = 10  # 最大关卡数
        self.max_revive_chances = 3  # 最大复活次数
        self.reset_game()

    def reset_game(self):
        # 蛇的初始位置和长度
        self.snake_pos = [(self.width // 2, self.height // 2)]
        self.snake_length = 3  # 初始长度设为3，让游戏更容易开始

        # 生成第一个食物
        self.food_pos = self.generate_food()

        # 生成障碍物（根据当前关卡）
        self.generate_obstacles()

        # 游戏状态
        self.score = 0
        self.game_over = False
        self.revive_chances = self.max_revive_chances  # 重置复活次数
        self.last_finger_pos = None  # 记录上次手指位置
        self.last_thumb_pos = None  # 记录拇指位置

        # 复活答题相关
        self.revive_question = None
        self.showing_revive_question = False

    def generate_obstacles(self):
        """根据当前关卡生成障碍物"""
        self.obstacles = []

        # 基础障碍物数量随关卡增加
        base_count = 2 + self.current_level

        for _ in range(base_count):
            # 障碍物大小随关卡增加
            min_size = 20 + self.current_level * 5
            max_size = 40 + self.current_level * 8
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

    def update(self, finger_pos, thumb_pos=None):
        """更新游戏状态"""
        if self.game_over or self.showing_revive_question:
            return

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
        if dist < 5:
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
        new_x = max(10, min(self.width - 10, new_x))
        new_y = max(10, min(self.height - 10, new_y))
        new_head = (new_x, new_y)

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

        # 检查游戏结束条件（撞墙）
        x, y = new_head
        if x < 5 or x > self.width - 5 or y < 5 or y > self.height - 5:
            self.handle_game_over()
            return

        # 检查游戏结束条件（撞到自己）
        # 使用更智能的碰撞检测，只检查距离足够远的身体部分
        if not ate_food:
            for i, pos in enumerate(self.snake_pos):
                # 跳过头部本身和前几个靠近头部的节点
                if i < 5:  # 跳过前5个节点，包括头部
                    continue

                # 只检查距离头部足够远的节点
                if self.distance(new_head, pos) < 15:
                    self.handle_game_over()
                    return

        # 检查游戏结束条件（撞到障碍物）
        for obstacle in self.obstacles:
            if obstacle.contains_point(new_head):
                self.handle_game_over()
                return

    def handle_game_over(self):
        """处理游戏结束，检查是否有复活机会"""
        if self.revive_chances > 0:
            # 有复活机会，显示答题界面
            self.showing_revive_question = True
            self.revive_question = self.question_manager.get_random_question()
        else:
            # 没有复活机会，直接结束游戏
            self.game_over = True
            # 保存分数
            if self.user_manager.current_user:
                self.user_manager.update_score(
                    self.user_manager.current_user,
                    self.score,
                    self.current_level,
                )

    def revive_player(self):
        """复活玩家"""
        self.revive_chances -= 1
        self.showing_revive_question = False
        self.revive_question = None

        # 重置蛇的位置，保持当前关卡和分数
        self.snake_pos = [(self.width // 2, self.height // 2)]
        self.snake_length = max(3, self.snake_length - 1)  # 复活后长度稍微减少作为惩罚

        # 重新生成食物
        self.food_pos = self.generate_food()

        # 游戏继续
        self.game_over = False

    def draw(self, img, finger_pos=None):
        """在图像上绘制游戏元素"""
        # 绘制障碍物
        for obstacle in self.obstacles:
            obstacle.draw(img)

        # 绘制蛇身
        for i, pos in enumerate(self.snake_pos):
            # 蛇头用不同颜色
            if i == 0:
                color = (0, 255, 0)  # 蛇头亮绿色
                radius = 15  # 增加蛇头半径
            else:
                # 蛇身颜色渐变
                color_ratio = i / len(self.snake_pos)
                color = (0, int(200 * (1 - color_ratio)), 0)
                radius = 13  # 增加蛇身半径

            cv2.circle(img, pos, radius, color, -1)
            cv2.circle(img, pos, radius, (255, 255, 255), 1)  # 白色边框

            # 绘制蛇身连接线（更粗的线）
            if i > 0:
                cv2.line(img, self.snake_pos[i - 1], pos, (0, 160, 0), 10)

        # 绘制食物
        cv2.circle(img, self.food_pos, 15, (0, 0, 255), -1)  # 增加食物大小
        cv2.circle(img, self.food_pos, 12, (255, 255, 255), 3)

        # 高亮食指指尖位置
        if finger_pos:
            cv2.circle(img, finger_pos, 20, (255, 255, 0), 3)  # 黄色圆圈
            cv2.circle(img, finger_pos, 5, (255, 255, 0), -1)  # 实心点

        # 绘制分数、关卡和游戏信息
        img = self.text_renderer.put_text(
            img, f"分数: {self.score}", (10, 30), 30, (255, 255, 255)
        )
        img = self.text_renderer.put_text(
            img,
            f"关卡: {self.current_level}/{self.max_level}",
            (10, 70),
            30,
            (255, 255, 255),
        )

        # 显示复活次数
        img = self.text_renderer.put_text(
            img,
            f"复活机会: {self.revive_chances}/{self.max_revive_chances}",
            (10, 110),
            25,
            (255, 255, 255),
        )

        # 显示当前用户
        if self.user_manager.current_user:
            img = self.text_renderer.put_text(
                img,
                f"用户: {self.user_manager.current_user}",
                (10, 150),
                25,
                (255, 255, 255),
            )

        # 如果没有检测到手，显示提示
        if self.last_finger_pos is None:
            img = self.text_renderer.put_text(
                img,
                "请将手展示给摄像头!",
                (self.width // 2 - 180, self.height - 30),
                25,
                (0, 255, 255),
            )

        return img

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
        text_size = self.text_renderer.get_text_size(text, 25)
        text_x = x + (w - text_size[0]) // 2
        text_y = y + (h + text_size[1]) // 2

        # 绘制文本
        img = self.text_renderer.put_text(
            img, text, (text_x, text_y), 25, (255, 255, 255)
        )

        return (x, y, w, h)

    def draw_revive_question_screen(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制复活答题界面"""
        if not self.revive_question:
            return []

        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制标题
        img = self.text_renderer.put_text(
            img, "复活挑战", (self.width // 2 - 100, 80), 40, (0, 255, 255)
        )

        # 显示剩余复活次数
        img = self.text_renderer.put_text(
            img,
            f"剩余复活机会: {self.revive_chances}/{self.max_revive_chances}",
            (self.width // 2 - 150, 130),
            30,
            (255, 255, 255),
        )

        # 绘制问题
        question = self.revive_question["question"]
        # 问题文本换行处理
        words = question.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            # 检查文本宽度
            text_width = self.text_renderer.get_text_size(test_line, 30)[0]

            if text_width < self.width - 100:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "

        if current_line:
            lines.append(current_line)

        # 绘制问题文本
        for i, line in enumerate(lines):
            img = self.text_renderer.put_text(
                img,
                line,
                (self.width // 2 - (self.width - 100) // 2, 180 + i * 40),
                30,
                (255, 255, 255),
            )

        # 绘制选项按钮
        options = self.revive_question["options"]
        buttons = []
        button_height = 50
        start_y = 250

        for i, option in enumerate(options):
            button_rect = (
                self.width // 2 - 200,
                start_y + i * (button_height + 15),
                400,
                button_height,
            )
            is_hovered = self.is_point_in_rect(index_pos, button_rect) or (
                mouse_pos and self.is_point_in_rect(mouse_pos, button_rect)
            )
            self.draw_button(
                img,
                option,
                (button_rect[0], button_rect[1]),
                (button_rect[2], button_rect[3]),
                is_hovered,
            )
            buttons.append((i, button_rect))

        # 检测按钮点击
        buttons_clicked = []
        pinch_detected = self.is_pinch_gesture(index_pos, thumb_pos)

        if pinch_detected or mouse_click:
            for option_idx, rect in buttons:
                if self.is_point_in_rect(index_pos, rect) or (
                    mouse_pos and self.is_point_in_rect(mouse_pos, rect)
                ):
                    buttons_clicked.append(option_idx)

        # 显示操作提示
        img = self.text_renderer.put_text(
            img,
            "答对题目即可复活！使用手势或鼠标选择。",
            (self.width // 2 - 280, self.height - 50),
            25,
            (255, 255, 0),
        )

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked

    def draw_start_screen(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制启动画面"""
        # 创建半透明覆盖层
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制标题
        img = self.text_renderer.put_text(
            img,
            "贪吃蛇游戏",
            (self.width // 2 - 120, self.height // 2 - 120),
            50,
            (0, 255, 0),
        )
        img = self.text_renderer.put_text(
            img,
            "手势与鼠标控制版",
            (self.width // 2 - 140, self.height // 2 - 70),
            30,
            (255, 255, 255),
        )

        # 绘制开始按钮
        start_button_rect = (self.width // 2 - 100, self.height // 2 - 30, 200, 60)
        start_button_hover = self.is_point_in_rect(index_pos, start_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, start_button_rect)
        )
        self.draw_button(
            img,
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
        self.draw_button(
            img,
            "选择用户",
            (user_button_rect[0], user_button_rect[1]),
            (user_button_rect[2], user_button_rect[3]),
            is_hovered=user_button_hover,
        )

        # 绘制积分榜
        img = self.text_renderer.put_text(
            img,
            "排行榜:",
            (self.width // 2 - 50, self.height // 2 + 150),
            30,
            (255, 255, 0),
        )

        top_scores = self.user_manager.get_top_scores(5)
        for i, user in enumerate(top_scores):
            score_text = (
                f"{i+1}. {user['user']}: {user['score']} (关卡{user.get('level', 0)})"
            )
            img = self.text_renderer.put_text(
                img,
                score_text,
                (self.width // 2 - 100, self.height // 2 + 180 + i * 30),
                25,
                (255, 255, 255),
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
        img = self.text_renderer.put_text(
            img,
            "使用手势或鼠标进行交互",
            (self.width // 2 - 180, self.height - 80),
            25,
            (255, 255, 0),
        )
        img = self.text_renderer.put_text(
            img,
            "手势: 捏合点击 | 鼠标: 左键点击",
            (self.width // 2 - 200, self.height - 50),
            25,
            (255, 255, 0),
        )

        # 显示捏合提示和调试信息
        if index_pos and thumb_pos:
            dist = self.distance(index_pos, thumb_pos)

            # 显示详细调试信息
            debug_text = [
                f"食指: {index_pos}",
                f"拇指: {thumb_pos}",
                f"距离: {dist:.1f}",
                f"阈值: {self.pinch_threshold}",
                f"捏合: {'是' if pinch_detected else '否'}",
                f"悬停开始: {start_button_hover}",
                f"悬停用户: {user_button_hover}",
                f"点击按钮: {buttons_clicked}",
            ]

            for i, text in enumerate(debug_text):
                img = self.text_renderer.put_text(
                    img, text, (10, 100 + i * 25), 20, (255, 255, 255)
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
                img = self.text_renderer.put_text(
                    img, "检测到捏合!", (self.width // 2 - 80, 30), 30, (0, 255, 0)
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
        img = self.text_renderer.put_text(
            img, "选择用户", (self.width // 2 - 80, 80), 40, (0, 255, 0)
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
                f"{user['user']} (关卡{user.get('level', 0)})",
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
            img,
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
        img = self.text_renderer.put_text(
            img,
            "使用手势或鼠标进行交互",
            (self.width // 2 - 180, self.height - 120),
            25,
            (255, 255, 0),
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
        img = self.text_renderer.put_text(
            img, "创建新用户", (self.width // 2 - 100, 80), 40, (0, 255, 0)
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
            img = self.text_renderer.put_text(
                img,
                current_text,
                (input_box[0] + 10, input_box[1] + 35),
                30,
                (255, 255, 255),
            )
        else:
            img = self.text_renderer.put_text(
                img,
                "输入用户名...",
                (input_box[0] + 10, input_box[1] + 35),
                25,
                (150, 150, 150),
            )

        # 绘制确认按钮
        confirm_button_rect = (self.width // 2 - 150, 190, 140, 50)
        confirm_hover = self.is_point_in_rect(index_pos, confirm_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, confirm_button_rect)
        )
        self.draw_button(
            img,
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
            img,
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

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked, input_box

    def draw_game_over(
        self, img, index_pos, thumb_pos, mouse_pos=None, mouse_click=False
    ):
        """绘制游戏结束画面"""
        # 先绘制游戏画面
        img = self.draw(img, index_pos)

        # 添加半透明覆盖层
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)

        # 绘制游戏结束文本
        img = self.text_renderer.put_text(
            img,
            "游戏结束",
            (self.width // 2 - 100, self.height // 2 - 100),
            50,
            (0, 0, 255),
        )
        img = self.text_renderer.put_text(
            img,
            f"分数: {self.score}",
            (self.width // 2 - 60, self.height // 2 - 50),
            30,
            (255, 255, 255),
        )
        img = self.text_renderer.put_text(
            img,
            f"达到关卡: {self.current_level}",
            (self.width // 2 - 100, self.height // 2 - 20),
            30,
            (255, 255, 255),
        )

        # 显示当前用户
        if self.user_manager.current_user:
            img = self.text_renderer.put_text(
                img,
                f"用户: {self.user_manager.current_user}",
                (self.width // 2 - 80, self.height // 2 + 10),
                25,
                (255, 255, 255),
            )

        # 绘制重新开始按钮
        restart_button_rect = (self.width // 2 - 100, self.height // 2 + 40, 200, 60)
        restart_hover = self.is_point_in_rect(index_pos, restart_button_rect) or (
            mouse_pos and self.is_point_in_rect(mouse_pos, restart_button_rect)
        )
        self.draw_button(
            img,
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
            img,
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

        # 绘制鼠标位置（如果使用鼠标）
        if mouse_pos:
            cv2.circle(img, mouse_pos, 8, (0, 255, 255), -1)  # 黄色圆点表示鼠标

        return buttons_clicked


def test():
    # 在函数内部声明全局变量
    global mouse_position, mouse_clicked

    print("初始化手部检测模块...")
    # 初始化手部检测
    try:
        hand = hd.HandBind(
            camera_id=0,
            handdraw=True,
            draw_fps=True,
            draw_index=False,
            verbose=False,
            max_hands=1,
        )
    except Exception as e:
        print(f"手部检测初始化失败: {e}")
        print("请确保已安装必要的依赖库")
        return

    print("初始化贪吃蛇游戏...")
    # 初始化贪吃蛇游戏
    game = SnakeGame()

    # 测试字体渲染器
    print("测试字体渲染器...")
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img = game.text_renderer.put_text(
        test_img, "测试", (10, 50), 30, (255, 255, 255)
    )
    print("字体渲染器测试完成")

    # 设置鼠标回调
    cv2.namedWindow("贪吃蛇游戏 - 手势与鼠标控制")
    cv2.setMouseCallback("贪吃蛇游戏 - 手势与鼠标控制", mouse_callback)

    print("贪吃蛇游戏说明:")
    print("- 移动食指来控制蛇头")
    print("- 食指和拇指捏合可以点击按钮，也可以用鼠标点击")
    print("- 吃到红色食物可以增加分数")
    print("- 避免撞到边界、自己和蓝色障碍物")
    print("- 游戏共有10关，难度递增")
    print("- 每吃5个食物进入下一关")
    print("- 每局游戏有3次复活机会")
    print("- 复活需要答对选择题")
    print("- 捏合阈值:", game.pinch_threshold)

    # 游戏状态 - 使用单个状态变量来管理
    game_state = "start_screen"  # 可以是: "start_screen", "user_selection", "new_user", "playing", "game_over", "revive_question"
    new_user_text = ""
    last_key_time = 0

    # 添加一些调试用户
    if not game.user_manager.users:
        game.user_manager.add_user("玩家1")
        game.user_manager.add_user("玩家2")
        game.user_manager.add_user("玩家3")

    print("开始游戏主循环...")

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
            processed_img = cv2.flip(processed_img, 1)

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

                for button in buttons_clicked:
                    if button == "start":
                        if game.user_manager.current_user:
                            game_state = "playing"
                            print("开始游戏")
                        else:
                            # 如果没有当前用户，转到用户选择
                            game_state = "user_selection"
                            print("请先选择用户")
                    elif button == "select_user":
                        game_state = "user_selection"
                        print("转到用户选择界面")

            elif game_state == "user_selection":
                buttons_clicked = game.draw_user_selection_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    mouse_position,
                    current_mouse_click,
                )

                for button in buttons_clicked:
                    if button[0] == "select":
                        game.user_manager.current_user = button[1]
                        game_state = "playing"  # 直接开始游戏
                        print(f"选择用户: {button[1]}")
                    elif button[0] == "new_user":
                        game_state = "new_user"
                        new_user_text = ""
                        print("创建新用户")
                    elif button[0] == "back":
                        game_state = "start_screen"
                        print("返回开始界面")

            elif game_state == "new_user":
                buttons_clicked, input_box = game.draw_new_user_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    new_user_text,
                    mouse_position,
                    current_mouse_click,
                )

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
                                    print(f"新用户创建: {new_user_text}")
                        elif 32 <= key <= 126:  # 可打印字符
                            if len(new_user_text) < 15:  # 限制用户名长度
                                new_user_text += chr(key)

                for button in buttons_clicked:
                    if button[0] == "confirm" and button[1]:
                        if game.user_manager.add_user(button[1]):
                            game.user_manager.current_user = button[1]
                            game_state = "playing"
                            print(f"通过按钮创建新用户: {button[1]}")
                    elif button[0] == "cancel":
                        game_state = "user_selection"
                        print("取消创建新用户")

            elif game_state == "playing":
                if not game.game_over and not game.showing_revive_question:
                    # 更新游戏状态
                    game.update(index_pos, thumb_pos)

                    # 在图像上绘制游戏（传入食指位置用于高亮显示）
                    processed_img = game.draw(processed_img, index_pos)

                    # 检查是否进入复活答题状态
                    if game.showing_revive_question:
                        game_state = "revive_question"
                else:
                    # 游戏结束，更新分数并切换到游戏结束状态
                    if game.user_manager.current_user:
                        game.user_manager.update_score(
                            game.user_manager.current_user,
                            game.score,
                            game.current_level,
                        )
                        print(
                            f"游戏结束. 分数: {game.score}. 关卡: {game.current_level}. 用户: {game.user_manager.current_user}"
                        )
                    game_state = "game_over"

            elif game_state == "revive_question":
                # 绘制复活答题界面
                options_clicked = game.draw_revive_question_screen(
                    processed_img,
                    index_pos,
                    thumb_pos,
                    mouse_position,
                    current_mouse_click,
                )

                # 处理答题结果
                if options_clicked:
                    selected_option = options_clicked[0]
                    correct = game.question_manager.validate_answer(
                        game.revive_question, selected_option
                    )

                    if correct:
                        print("答题正确！复活成功！")
                        game.revive_player()
                        game_state = "playing"
                    else:
                        print("答题错误！复活失败！")
                        game.showing_revive_question = False
                        game.revive_question = None

                        # 如果还有复活机会，继续显示答题界面
                        if game.revive_chances > 0:
                            game.handle_game_over()
                            if game.showing_revive_question:
                                game_state = "revive_question"
                            else:
                                game_state = "game_over"
                        else:
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

                for button in buttons_clicked:
                    if button == "restart":
                        # 重置游戏（从第一关开始）
                        game.current_level = 1
                        game.reset_game()
                        game_state = "playing"
                        print("从第一关重新开始游戏")
                    elif button == "select_user":
                        game_state = "user_selection"
                        print("从游戏结束界面转到用户选择")

            # 显示图像
            cv2.imshow("贪吃蛇游戏 - 手势与鼠标控制", processed_img)

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
