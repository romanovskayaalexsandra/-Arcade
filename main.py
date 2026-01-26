"""
===========================================================================
ПОДЗЕМЕЛЬЕ АВАНТЮРИСТОВ - 2D ПЛАТФОРМЕР
===========================================================================
Создание компьютерной игры на языке Python (библиотека Arcade)
"""

import arcade          # Библиотека для создания игр
import time            # Для работы со временем
import json            # Для сохранения данных
import os              # Для работы с файлами
import random          # Для случайных чисел
import math            # Для математики

# =====================================================
# НАСТРОЙКИ ИГРЫ
# =====================================================
# Размеры окна
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Подземелье авантюристов"

# Игровые константы
TILE = 64              # Размер квадратной плитки
PLAYER_SPEED = 5       # Скорость игрока
JUMP_SPEED = 18        # Высота прыжка
GRAVITY = 1            # Сила тяжести
CAMERA_SPEED = 0.1     # Плавность движения камеры
MAX_HP = 100           # Максимальное здоровье

# Урон и время
SPIKE_DAMAGE = 10      # Урон от шипов
SPIKE_COOLDOWN = 1.0   # Время между уроном

# Цвета и файлы
BG_COLOR = arcade.color.DARK_BROWN   # Цвет фона
RECORDS_FILE = "records.json"        # Файл для рекордов

# =====================================================
# КАРТЫ УРОВНЕЙ
# =====================================================
"""
КАК РАБОТАЮТ КАРТЫ:
Буквами обозначены разные объекты на уровне
ПРОСТОЙ УРОВЕНЬ (уровень 1):
1 - стена     P - игрок     C - монета
K - ключ      d - верх двери  E - середина двери
0 - пусто
"""
LEVEL_1 = [
    "11111111111d1",
    "1P000000000E1",
    "1011101110111",
    "100000C000001",
    "1011110111101",
    "1C00000000K01",
    "1111111111111",
]

"""
СЛОЖНЫЙ УРОВЕНЬ (уровень 2):
1,2,s,g - разные стены   L,T - лестница
S - шипы     B - бомба    C - монета
D - алмаз    K - ключ     M,F - враги
m - гриб     d,E - дверь  P - игрок
"""
LEVEL_2 = [
    "11111111111111",
    "1000m0s000d001",
    "1000111000E001",
    "10000g00011101",
    "1FD02200C00001",
    "11100001100001",
    "100000C0M00T01",
    "10011111111L01",
    "1m000000000L01",
    "12200000000L01",
    "1000C0000BKL01",
    "10011100011101",
    "1P000mSSS0C001",
    "11111211111111",
]

# =====================================================
# ФАКЕЛ ДЛЯ СТАРТОВОГО ЭКРАНА
# =====================================================
class Torch(arcade.Sprite):
    """
    Анимированный факел для украшения экрана.
    Меняет картинки, чтобы создать эффект мерцания.
    """
    def __init__(self):
        super().__init__(scale=1)
        # Три картинки для анимации
        self.frames = [
            arcade.load_texture(":resources:/images/tiles/torchOff.png"),
            arcade.load_texture(":resources:/images/tiles/torch1.png"),
            arcade.load_texture(":resources:/images/tiles/torch2.png"),
        ]
        self.index = 0          # Номер текущей картинки
        self.texture = self.frames[0]  # Текущая картинка

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Обновляет анимацию факела.
        
        Аргумент:
            delta_time: время с прошлого кадра
        """
        # Меняем картинку плавно
        self.index = (self.index + 0.1) % len(self.frames)
        self.texture = self.frames[int(self.index)]

# =====================================================
# СИСТЕМА ЧАСТИЦ (ДЛЯ ЭФФЕКТОВ)
# =====================================================
class Particle(arcade.SpriteCircle):
    """
    Одна маленькая частица для спецэффектов.
    Используется для взрывов, искр и других красот.
    """
    def __init__(self, x, y, color, size=3, velocity=None, lifetime=1.0):
        super().__init__(size, color)
        # Координаты частицы
        self.center_x = x
        self.center_y = y
        # Сколько живет частица
        self.lifetime = lifetime
        self.age = 0
        # Скорость движения
        self.velocity_x = 0
        self.velocity_y = 0
        
        # Если скорость задана - берем ее
        if velocity:
            self.velocity_x, self.velocity_y = velocity
        else:
            # Иначе делаем случайное направление
            angle = random.uniform(0, 2 * math.pi)  # Угол
            speed = random.uniform(10, 30)          # Скорость
            self.velocity_x = math.cos(angle) * speed
            self.velocity_y = math.sin(angle) * speed
    
    def update_particle(self, delta_time):
        """
        Обновляет состояние частицы.
        """
        # Увеличиваем возраст
        self.age += delta_time
        
        # Если прожила достаточно - удаляем
        if self.age >= self.lifetime:
            self.remove_from_sprite_lists()
            return
        
        # Замедляем частицу (как в воздухе)
        self.velocity_x *= 0.95
        self.velocity_y *= 0.95
        
        # Гравитация тянет вниз
        self.velocity_y -= 0.5
        
        # Двигаем частицу
        self.center_x += self.velocity_x * delta_time * 60
        self.center_y += self.velocity_y * delta_time * 60
        
        # Частица постепенно исчезает
        alpha = int(255 * (1 - self.age / self.lifetime))
        self.alpha = alpha

class ParticleSystem:
    """
    Управляет всеми частицами вместе.
    """
    def __init__(self):
        self.particles = arcade.SpriteList()  # Все частицы
        self.time_since_last_update = 0       # Таймер
        self.update_interval = 1/60           # Обновлять 60 раз в секунду
    
    def create_explosion(self, x, y, color=arcade.color.ORANGE, count=20):
        """
        Создает эффект взрыва.
        """
        for _ in range(count):
            particle = Particle(x, y, color, 
                               size=random.randint(2, 5),
                               lifetime=random.uniform(0.5, 1.5))
            self.particles.append(particle)
    
    def create_sparkle(self, x, y, color=arcade.color.GOLD, count=10):
        """
        Создает эффект искр.
        """
        for _ in range(count):
            particle = Particle(x, y, color,
                               size=random.randint(1, 3),
                               lifetime=random.uniform(0.3, 0.8))
            self.particles.append(particle)
    
    def update(self, delta_time):
        """
        Обновляет все частицы.
        """
        self.time_since_last_update += delta_time
        if self.time_since_last_update >= self.update_interval:
            for particle in self.particles:
                if hasattr(particle, 'update_particle'):
                    particle.update_particle(self.time_since_last_update)
            self.time_since_last_update = 0
    
    def draw(self):
        """
        Рисует все частицы.
        """
        self.particles.draw()

# =====================================================
# ФИЗИЧЕСКИЙ ДВИЖОК
# =====================================================
class PhysicsObject(arcade.Sprite):
    """
    Базовый класс для объектов с физикой.
    Добавляет гравитацию, трение и столкновения.
    """
    def __init__(self, texture, scale=1.0):
        super().__init__(texture, scale)
        # Скорость по осям
        self.velocity_x = 0
        self.velocity_y = 0
        # На земле ли объект
        self.on_ground = False
        # Физические параметры
        self.gravity = 0.5      # Сила тяжести
        self.friction = 0.8     # Трение (замедление)
        self.bounce_factor = 0.5  # Отскок от стен
    
    def update_physics(self, walls):
        """
        Применяет физику к объекту.
        """
        # Падаем вниз из-за гравитации
        self.velocity_y -= self.gravity
        
        # Замедляемся из-за трения
        self.velocity_x *= self.friction
        
        # Запоминаем старую позицию
        old_x = self.center_x
        old_y = self.center_y
        
        # Двигаемся
        self.center_x += self.velocity_x
        self.center_y += self.velocity_y
        
        # Считаем, что мы не на земле
        self.on_ground = False
        
        # Проверяем столкновения со стенами
        hit_list = arcade.check_for_collision_with_list(self, walls)
        
        for wall in hit_list:
            # С какой стороны столкнулись
            dx = self.center_x - wall.center_x
            dy = self.center_y - wall.center_y
            
            # Если больше по горизонтали - стукнулись сбоку
            if abs(dx) > abs(dy):
                if dx > 0:  # Справа от стены
                    self.left = wall.right
                else:       # Слева от стены
                    self.right = wall.left
                # Отскакиваем от стены
                self.velocity_x = -self.velocity_x * self.bounce_factor
            
            # Если больше по вертикали - сверху или снизу
            else:
                if dy > 0:  # Ударились головой
                    self.bottom = wall.top
                    self.velocity_y = 0
                else:       # Встали на землю
                    self.top = wall.bottom
                    self.velocity_y = -self.velocity_y * self.bounce_factor
                    self.on_ground = True  # Теперь на земле
        
        # Ограничиваем скорость, чтобы не летали слишком быстро
        max_speed = 10
        self.velocity_x = max(-max_speed, min(max_speed, self.velocity_x))
        self.velocity_y = max(-max_speed, min(max_speed, self.velocity_y))

# =====================================================
# ВРАГИ С ИСКУССТВЕННЫМ ИНТЕЛЛЕКТОМ
# =====================================================
class Enemy(PhysicsObject):
    """
    Враги, которые ходят сами по себе.
    Простой ИИ для патрулирования территории.
    """
    def __init__(self, texture, scale=0.5, move_speed=1.0):
        super().__init__(texture, scale)
        self.move_speed = move_speed      # Скорость врага
        self.move_direction = 1           # 1 = вправо, -1 = влево
        self.move_timer = 0               # Таймер
        self.move_interval = random.uniform(1.0, 3.0)  # Когда менять направление
    
    def update_ai(self, delta_time, walls):
        """
        Обновляет поведение врага.
        """
        # Увеличиваем таймер
        self.move_timer += delta_time
        
        # Если время пришло - меняем направление
        if self.move_timer >= self.move_interval:
            self.move_direction *= -1  # Меняем на противоположное
            self.move_timer = 0
            self.move_interval = random.uniform(1.0, 3.0)
        
        # Двигаем врага
        self.velocity_x = self.move_speed * self.move_direction
        
        # Обновляем физику
        self.update_physics(walls)
        
        # Иногда подпрыгивает
        if self.on_ground and random.random() < 0.01:
            self.velocity_y = random.uniform(3, 6)

# =====================================================
# АНИМИРОВАННАЯ МОНЕТА
# =====================================================
class AnimatedCoin(PhysicsObject):
    """
    Монета, которая красиво вращается и плавает.
    """
    def __init__(self, x, y):
        super().__init__(":resources:/images/items/gold_1.png", 0.4)
        # Кадры для анимации вращения
        self.frames = [
            arcade.load_texture(":resources:/images/items/gold_1.png"),
            arcade.load_texture(":resources:/images/items/gold_2.png"),
            arcade.load_texture(":resources:/images/items/gold_3.png"),
            arcade.load_texture(":resources:/images/items/gold_4.png"),
        ]
        self.index = 0                  # Текущий кадр
        self.texture = self.frames[0]   # Текущая картинка
        self.center_x = x
        self.center_y = y
        self.float_timer = 0            # Для плавания
        self.float_height = 2           # Высота плавания
        self.original_y = y             # Начальная высота
        self.collected = False          # Собрана ли монета
    
    def update_animation(self, delta_time: float = 1 / 60):
        """
        Обновляет анимацию монеты.
        """
        # Меняем кадр для вращения
        self.index = (self.index + 0.15) % len(self.frames)
        self.texture = self.frames[int(self.index)]
        
        # Плавающее движение вверх-вниз
        self.float_timer += delta_time
        # Синус дает плавное движение
        self.center_y = self.original_y + math.sin(self.float_timer * 2) * self.float_height

# =====================================================
# БОМБА
# =====================================================
class Bomb(arcade.Sprite):
    """
    Бомба, которая взрывается при касании.
    """
    def __init__(self, x, y):
        super().__init__(":resources:/images/tiles/bomb.png", 0.5)
        self.center_x = x
        self.center_y = y
        self.active = True       # Еще не взорвалась
        
    def explode(self, particle_system):
        """
        Взрыв бомбы.
        """
        self.active = False
        # Создаем эффект взрыва
        particle_system.create_explosion(self.center_x, self.center_y, 
                                        arcade.color.ORANGE_RED, 30)
        self.remove_from_sprite_lists()  # Удаляем бомбу

# =====================================================
# СИСТЕМА РЕКОРДОВ
# =====================================================
def load_records():
    """
    Загружает рекорды из файла.
    Если файла нет - возвращает пустой словарь.
    """
    if not os.path.exists(RECORDS_FILE):
        return {}
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_record(level, coins, diamonds, saved_mouse, saved_frog, time_sec):
    """
    Сохраняет новый рекорд, если он лучше старого.
    
    Возвращает:
        (рекорд, новый_ли_рекорд)
    """
    records = load_records()
    
    # Считаем очки:
    # Монета = 10 очков, алмаз = 50 очков
    # Спасение врага = 100 очков
    score = coins * 10 + diamonds * 50
    if saved_mouse:
        score += 100
    if saved_frog:
        score += 100
    
    # Берем старый рекорд для этого уровня
    current_best = records.get(f"level_{level}")
    
    # Проверяем, новый ли это рекорд
    is_new = False
    if not current_best:                     # Если рекорда еще нет
        is_new = True
    elif score > current_best["score"]:      # Если очков больше
        is_new = True
    elif score == current_best["score"] and time_sec < current_best["time"]:
        is_new = True  # Очков столько же, но время меньше
    
    # Сохраняем, если это новый рекорд
    if is_new:
        records[f"level_{level}"] = {
            "score": score,
            "coins": coins,
            "diamonds": diamonds,
            "saved_mouse": saved_mouse,
            "saved_frog": saved_frog,
            "time": time_sec
        }
        with open(RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
    
    return records.get(f"level_{level}", {}), is_new

# =====================================================
# СТАРТОВЫЙ ЭКРАН
# =====================================================
class StartView(arcade.View):
    """
    Первый экран игры с названием и факелом.
    """
    def __init__(self):
        super().__init__()
        self.torch = Torch()  # Создаем факел
    
    def on_show(self):
        """Вызывается при показе экрана."""
        arcade.set_background_color(BG_COLOR)
    
    def on_draw(self):
        """Рисует стартовый экран."""
        arcade.start_render()
        w, h = self.window.width, self.window.height

        # Название игры
        arcade.draw_text(
            "ПОДЗЕМЕЛЬЕ АВАНТЮРИСТОВ",
            w // 2,
            h // 2 + 40,  # Над факелом
            arcade.color.GOLD,
            28,
            anchor_x="center"
        )

        # Факел ПОД надписью
        self.torch.center_x = w // 2
        self.torch.center_y = h // 2 - 10  # Под надписью
        self.torch.draw()

        # Инструкция
        arcade.draw_text(
            "Клик мышью — начать",
            w // 2,
            h // 2 - 80,  # Под факелом
            arcade.color.WHITE,
            16,
            anchor_x="center"
        )
    
    def on_update(self, delta_time):
        """Обновляет анимацию факела."""
        self.torch.update_animation(delta_time)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """При клике переходит к выбору персонажа."""
        self.window.show_view(CharacterSelectView())

# =====================================================
# ВЫБОР ПЕРСОНАЖА
# =====================================================
class CharacterSelectView(arcade.View):
    """
    Экран выбора персонажа: мужчина или женщина.
    """
    def on_show(self):
        arcade.set_background_color(BG_COLOR)
        # Создаем картинки персонажей
        self.male = arcade.Sprite(
            ":resources:/images/animated_characters/male_adventurer/maleAdventurer_idle.png",
            0.8  # Размер
        )
        self.female = arcade.Sprite(
            ":resources:/images/animated_characters/female_adventurer/femaleAdventurer_idle.png",
            0.8
        )

    def on_draw(self):
        arcade.start_render()
        w, h = self.window.width, self.window.height

        # Заголовок
        arcade.draw_text(
            "ВЫБЕРИ ПЕРСОНАЖА",
            w // 2,
            h - 80,
            arcade.color.WHITE,
            24,
            anchor_x="center"
        )

        # Размещаем персонажей
        self.male.center_x, self.male.center_y = w // 3, h // 2    # Слева
        self.female.center_x, self.female.center_y = w * 2 // 3, h // 2  # Справа

        # Рисуем персонажей
        self.male.draw()
        self.female.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        """Проверяет, по какому персонажу кликнули."""
        if self.male.collides_with_point((x, y)):
            self.window.show_view(LevelSelectView("male"))
        elif self.female.collides_with_point((x, y)):
            self.window.show_view(LevelSelectView("female"))

# =====================================================
# ВЫБОР УРОВНЯ
# =====================================================
class LevelSelectView(arcade.View):
    """
    Экран выбора уровня: 1 (легкий) или 2 (сложный).
    """
    def __init__(self, character):
        super().__init__()
        self.character = character  # Запоминаем персонажа
        self.level1_rect = None     # Область кнопки "Уровень 1"
        self.level2_rect = None     # Область кнопки "Уровень 2"

    def on_show(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        arcade.start_render()
        w, h = self.window.width, self.window.height

        # Заголовок
        arcade.draw_text(
            "ВЫБЕРИ УРОВЕНЬ",
            w // 2,
            h - 60,
            arcade.color.WHITE,
            28,
            anchor_x="center"
        )

        # Кнопка "Уровень 1"
        level1_x = w // 2
        level1_y = h // 2 + 40
        level1_width = w - 100
        level1_height = 60
        
        # Рисуем кнопку
        arcade.draw_rectangle_filled(
            level1_x, level1_y,
            level1_width, level1_height,
            arcade.color.DARK_GRAY
        )
        arcade.draw_rectangle_outline(
            level1_x, level1_y,
            level1_width, level1_height,
            arcade.color.GOLD, 2
        )
        
        # Запоминаем координаты кнопки для проверки клика
        self.level1_rect = {
            "left": level1_x - level1_width // 2,
            "right": level1_x + level1_width // 2,
            "top": level1_y + level1_height // 2,
            "bottom": level1_y - level1_height // 2
        }

        # Текст на кнопке
        arcade.draw_text(
            "УРОВЕНЬ 1",
            level1_x,
            level1_y,
            arcade.color.GOLD,
            24,
            anchor_x="center",
            anchor_y="center"
        )

        # Кнопка "Уровень 2"
        level2_x = w // 2
        level2_y = h // 2 - 40
        level2_width = w - 100
        level2_height = 60
        
        # Рисуем кнопку
        arcade.draw_rectangle_filled(
            level2_x, level2_y,
            level2_width, level2_height,
            arcade.color.DARK_GRAY
        )
        arcade.draw_rectangle_outline(
            level2_x, level2_y,
            level2_width, level2_height,
            arcade.color.GOLD, 2
        )
        
        # Запоминаем координаты кнопки для проверки клика
        self.level2_rect = {
            "left": level2_x - level2_width // 2,
            "right": level2_x + level2_width // 2,
            "top": level2_y + level2_height // 2,
            "bottom": level2_y - level2_height // 2
        }

        # Текст на кнопке
        arcade.draw_text(
            "УРОВЕНЬ 2",
            level2_x,
            level2_y,
            arcade.color.GOLD,
            24,
            anchor_x="center",
            anchor_y="center"
        )

        # Инструкция внизу
        arcade.draw_text(
            "Клик по уровню — начать",
            w // 2,
            40,
            arcade.color.WHITE,
            14,
            anchor_x="center"
        )

    def on_mouse_press(self, x, y, button, modifiers):
        """Проверяет, по какой кнопке кликнули."""
        if self.level1_rect:
            if (self.level1_rect["left"] <= x <= self.level1_rect["right"] and
                self.level1_rect["bottom"] <= y <= self.level1_rect["top"]):
                # Запускаем уровень 1
                game = GameView(self.character)
                game.setup()
                self.window.show_view(game)
                return
                
        if self.level2_rect:
            if (self.level2_rect["left"] <= x <= self.level2_rect["right"] and
                self.level2_rect["bottom"] <= y <= self.level2_rect["top"]):
                # Запускаем уровень 2
                game = GameView2(self.character)
                game.setup()
                self.window.show_view(game)
                return

# =====================================================
# ЭКРАН ПОБЕДЫ (УРОВЕНЬ 1)
# =====================================================
class WinView(arcade.View):
    """
    Экран победы после прохождения уровня 1.
    Показывает результаты и рекорды.
    """
    def __init__(self, score, elapsed, record=None, is_new=False):
        super().__init__()
        self.score = score        # Счет игрока
        self.elapsed = elapsed    # Затраченное время
        self.record = record      # Рекорд уровня
        self.is_new = is_new      # Новый ли это рекорд
        self.particle_system = ParticleSystem()  # Для эффектов

    def on_show(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        arcade.start_render()
        w, h = self.window.width, self.window.height

        # Большая надпись ПОБЕДА
        arcade.draw_text("ПОБЕДА!",
                         w // 2, h // 2 + 120,
                         arcade.color.GOLD, 32, anchor_x="center")

        # Показываем результаты
        arcade.draw_text(f"Монеты: {self.score}",
                         w // 2, h // 2 + 70,
                         arcade.color.WHITE, 18, anchor_x="center")

        arcade.draw_text("Ключ получен",
                         w // 2, h // 2 + 40,
                         arcade.color.WHITE, 18, anchor_x="center")

        arcade.draw_text(
            f"Время: {self.elapsed // 60} м. {self.elapsed % 60} с.",
            w // 2, h // 2 + 10,
            arcade.color.WHITE, 18, anchor_x="center"
        )
        
        # Показываем рекорд, если есть
        if self.record:
            arcade.draw_text("РЕКОРД УРОВНЯ:",
                             w // 2, h // 2 - 30,
                             arcade.color.GOLD, 20, anchor_x="center")
            
            arcade.draw_text(
                f"{self.record.get('coins', 0)} монет | "
                f"{self.record.get('time', 0) // 60} м. {self.record.get('time', 0) % 60} с.",
                w // 2, h // 2 - 60,
                arcade.color.WHITE, 16, anchor_x="center"
            )
            
            # Если это новый рекорд
            if self.is_new:
                arcade.draw_text("НОВЫЙ РЕКОРД!",
                                 w // 2, h // 2 - 90,
                                 arcade.color.GOLD, 20, anchor_x="center")

        # Инструкция
        arcade.draw_text("Клик — в главное меню",
                         w // 2, 40,
                         arcade.color.WHITE, 14, anchor_x="center")
        
        # Рисуем частицы (эффекты)
        self.particle_system.draw()

    def on_update(self, delta_time):
        """Обновляет частицы для эффектов."""
        self.particle_system.update(delta_time)
        
        # Создаем случайные искры
        if random.random() < 0.3:
            x = random.uniform(100, self.window.width - 100)
            y = random.uniform(100, self.window.height - 100)
            color = random.choice([arcade.color.GOLD, arcade.color.YELLOW, arcade.color.ORANGE])
            self.particle_system.create_sparkle(x, y, color, count=random.randint(3, 8))

    def on_mouse_press(self, x, y, button, modifiers):
        """При клике перезапускает игру."""
        self.window.close()
        main()

# =====================================================
# ИГРА - УРОВЕНЬ 1 (ЛЕГКИЙ)
# =====================================================
class GameView(arcade.View):
    """
    Основной класс для уровня 1.
    Управляет всем игровым процессом.
    """
    def __init__(self, character):
        super().__init__()
        self.character = character      # Запоминаем персонажа
        self.window_size_changed = False  # Для изменения размера окна

    def setup(self):
        """Настраивает уровень 1."""
        arcade.set_background_color(BG_COLOR)
        self.start_time = time.time()   # Время начала
        self.score = 0                  # Начинаем с нуля очков
        self.has_key = False            # Ключ еще не найден

        # Загружаем звуки
        self.sound_coin = arcade.load_sound(":resources:/sounds/coin1.wav")
        self.sound_key = arcade.load_sound(":resources:/sounds/coin5.wav")
        self.sound_jump = arcade.load_sound(":resources:/sounds/phaseJump1.wav")
        self.sound_win = arcade.load_sound(":resources:/sounds/secret4.wav")

        # Создаем списки для разных типов объектов
        self.walls = arcade.SpriteList(use_spatial_hash=True)  # Стены
        self.coins = arcade.SpriteList()                       # Монеты
        self.keys = arcade.SpriteList()                        # Ключи
        self.doors = arcade.SpriteList()                       # Двери
        self.player_list = arcade.SpriteList()                 # Игрок

        # Загружаем картинки персонажа
        if self.character == "male":
            base = ":resources:/images/animated_characters/male_adventurer/"
            self.idle = arcade.load_texture(base + "maleAdventurer_idle.png")
            self.jump = arcade.load_texture(base + "maleAdventurer_jump.png")
            self.walk = [
                arcade.load_texture(base + f"maleAdventurer_walk{i}.png")
                for i in range(8)
            ]
        else:  # female
            base = ":resources:/images/animated_characters/female_adventurer/"
            self.idle = arcade.load_texture(base + "femaleAdventurer_idle.png")
            self.jump = arcade.load_texture(base + "femaleAdventurer_jump.png")
            self.walk = [
                arcade.load_texture(base + f"femaleAdventurer_walk{i}.png")
                for i in range(8)
            ]

        # Создаем мир по карте LEVEL_1
        for row, line in enumerate(LEVEL_1):
            for col, ch in enumerate(line):
                x = col * TILE + TILE // 2
                y = (len(LEVEL_1) - row) * TILE

                if ch == "1":  # Стена
                    wall = arcade.Sprite(":resources:/images/tiles/grassCenter.png", 0.5)
                    wall.center_x, wall.center_y = x, y
                    self.walls.append(wall)

                elif ch == "d":  # Верх двери
                    wall = arcade.Sprite(":resources:/images/tiles/grassCenter.png", 0.5)
                    wall.center_x, wall.center_y = x, y
                    self.walls.append(wall)

                    door = arcade.Sprite(":resources:/images/tiles/doorClosed_top.png", 0.5)
                    door.center_x, door.center_y = x, y - TILE // 6
                    self.doors.append(door)

                elif ch == "E":  # Середина двери
                    door = arcade.Sprite(":resources:/images/tiles/doorClosed_mid.png", 0.5)
                    door.center_x, door.center_y = x, y
                    self.doors.append(door)

                elif ch == "P":  # Игрок
                    self.player = arcade.Sprite(scale=0.45)
                    self.player.texture = self.idle
                    self.player.center_x, self.player.center_y = x, y + 20
                    self.player_list.append(self.player)

                elif ch == "C":  # Монета
                    coin = AnimatedCoin(x, y)
                    self.coins.append(coin)

                elif ch == "K":  # Ключ
                    key = arcade.Sprite(":resources:/images/items/keyYellow.png", 0.5)
                    key.center_x, key.center_y = x, y
                    self.keys.append(key)

        # Создаем физический движок для игрока
        self.physics = arcade.PhysicsEnginePlatformer(self.player, self.walls, GRAVITY)
        self.walk_index = 0  # Для анимации ходьбы

    def on_draw(self):
        """Рисует все на экране."""
        arcade.start_render()
        w, h = self.window.width, self.window.height

        # Рисуем все объекты
        self.walls.draw()
        self.coins.draw()
        self.keys.draw()
        self.doors.draw()
        self.player_list.draw()

        # Считаем прошедшее время
        elapsed = int(time.time() - self.start_time)

        # Рисуем информацию вверху
        left_margin = w * 0.05  # 5% от ширины окна
        
        arcade.draw_text(f"Монеты: {self.score}", 
                         left_margin, h - 30,
                         arcade.color.GOLD, int(14 * w / 800), anchor_x="left")

        arcade.draw_text(f"Ключ: {'есть' if self.has_key else 'нет'}",
                         left_margin, h - 60,
                         arcade.color.WHITE, int(14 * w / 800), anchor_x="left")

        arcade.draw_text(f"Время: {elapsed // 60} м. {elapsed % 60} с.",
                         w - left_margin, h - 30,
                         arcade.color.WHITE, int(14 * w / 800), anchor_x="right")

    def on_update(self, delta_time):
        """Обновляет игру каждый кадр."""
        self.physics.update()

        # Обновляем анимацию монет
        for coin in self.coins:
            coin.update_animation(delta_time)

        # Анимация игрока
        if not self.physics.can_jump():  # Если в прыжке
            self.player.texture = self.jump
        elif abs(self.player.change_x) > 0:  # Если идет
            self.walk_index = (self.walk_index + 0.2) % len(self.walk)
            self.player.texture = self.walk[int(self.walk_index)]
        else:  # Если стоит
            self.player.texture = self.idle

        # Проверяем сбор монет
        for coin in arcade.check_for_collision_with_list(self.player, self.coins):
            if not coin.collected:
                arcade.play_sound(self.sound_coin)
                coin.collected = True
                coin.remove_from_sprite_lists()
                self.score += 1

        # Проверяем сбор ключа
        if arcade.check_for_collision_with_list(self.player, self.keys):
            arcade.play_sound(self.sound_key)
            self.keys[0].remove_from_sprite_lists()
            self.has_key = True

        # Проверяем выход через дверь
        if self.has_key and arcade.check_for_collision_with_list(self.player, self.doors):
            arcade.play_sound(self.sound_win)
            elapsed = int(time.time() - self.start_time)
            
            # Сохраняем рекорд
            record, is_new = save_record(1, self.score, 0, False, False, elapsed)
            self.window.show_view(WinView(self.score, elapsed, record, is_new))

    def on_key_press(self, key, modifiers):
        """Обрабатывает нажатие клавиш."""
        if key == arcade.key.RIGHT:
            self.player.change_x = PLAYER_SPEED
        elif key == arcade.key.LEFT:
            self.player.change_x = -PLAYER_SPEED
        elif key == arcade.key.UP and self.physics.can_jump():
            arcade.play_sound(self.sound_jump)
            self.player.change_y = JUMP_SPEED

    def on_key_release(self, key, modifiers):
        """Обрабатывает отпускание клавиш."""
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.player.change_x = 0

# =====================================================
# ИГРА - УРОВЕНЬ 2 (СЛОЖНЫЙ)
# =====================================================
class GameView2(arcade.View):
    """
    Класс для уровня 2.
    Более сложный, с камерой, врагами и опасностями.
    """
    def __init__(self, character):
        super().__init__()
        self.character = character
        self.spike_hit_timer = 0        # Для урона от шипов
        self.window_size_changed = False

    def setup(self):
        """Настраивает уровень 2."""
        arcade.set_background_color(BG_COLOR)

        # Создаем камеры
        self.camera = arcade.Camera(self.window.width, self.window.height)  # Для мира
        self.gui_camera = arcade.Camera(self.window.width, self.window.height)  # Для интерфейса

        # Переменные игры
        self.start_time = time.time()   # Время начала
        self.hp = 100                   # Здоровье
        self.coins = 0                  # Монеты
        self.diamonds = 0               # Алмазы
        self.has_key = False            # Ключ
        self.saved_mouse = False        # Мышь спасена
        self.saved_frog = False         # Лягушка спасена
        self.spike_hit_timer = 0        # Таймер для шипов

        # Загружаем звуки
        self.s_coin = arcade.load_sound(":resources:/sounds/coin1.wav")
        self.s_diamond = arcade.load_sound(":resources:/sounds/coin3.wav")
        self.s_key = arcade.load_sound(":resources:/sounds/coin5.wav")
        self.s_bomb = arcade.load_sound(":resources:/sounds/explosion1.wav")
        self.s_spike = arcade.load_sound(":resources:/sounds/hit3.wav")
        self.s_ladder = arcade.load_sound(":resources:/sounds/rockHit2.ogg")
        self.s_save = arcade.load_sound(":resources:/sounds/upgrade3.wav")
        self.s_gameover = arcade.load_sound(":resources:/sounds/gameover2.wav")
        self.s_win = arcade.load_sound(":resources:/sounds/secret4.wav")

        # Списки объектов
        self.walls = arcade.SpriteList(use_spatial_hash=True)  # Стены
        self.ladders = arcade.SpriteList(use_spatial_hash=True)  # Лестницы
        self.spikes = arcade.SpriteList()  # Шипы
        self.bombs = arcade.SpriteList()   # Бомбы
        self.coins_list = arcade.SpriteList()  # Монеты
        self.diamonds_list = arcade.SpriteList()  # Алмазы
        self.keys = arcade.SpriteList()  # Ключи
        self.doors = arcade.SpriteList()  # Двери
        self.mushrooms = arcade.SpriteList()  # Грибы
        self.mice = arcade.SpriteList()  # Мыши
        self.frogs = arcade.SpriteList()  # Лягушки

        # Загружаем картинки персонажа
        if self.character == "male":
            base = ":resources:/images/animated_characters/male_adventurer/"
            self.tex_idle = arcade.load_texture(base + "maleAdventurer_idle.png")
            self.tex_jump = arcade.load_texture(base + "maleAdventurer_jump.png")
            self.tex_walk = [
                arcade.load_texture(base + f"maleAdventurer_walk{i}.png")
                for i in range(8)
            ]
            self.tex_climb = [
                arcade.load_texture(base + "maleAdventurer_climb0.png"),
                arcade.load_texture(base + "maleAdventurer_climb1.png"),
            ]
        else:  # female
            base = ":resources:/images/animated_characters/female_adventurer/"
            self.tex_idle = arcade.load_texture(base + "femaleAdventurer_idle.png")
            self.tex_jump = arcade.load_texture(base + "femaleAdventurer_jump.png")
            self.tex_walk = [
                arcade.load_texture(base + f"femaleAdventurer_walk{i}.png")
                for i in range(8)
            ]
            self.tex_climb = [
                arcade.load_texture(base + "femaleAdventurer_climb0.png"),
                arcade.load_texture(base + "femaleAdventurer_climb1.png"),
            ]

        self.player = arcade.Sprite(scale=0.45)
        self.player.texture = self.tex_idle
        self.walk_index = 0
        self.climb_index = 0

        # Создаем мир по карте LEVEL_2
        for row, line in enumerate(LEVEL_2):
            for col, ch in enumerate(line):
                x = col * TILE + TILE // 2
                y = (len(LEVEL_2) - row) * TILE

                if ch == "1":
                    self._wall(":resources:/images/tiles/grassCenter.png", x, y)
                elif ch == "2":
                    self._wall(":resources:/images/tiles/grassMid.png", x, y)
                elif ch == "s":
                    self._wall(":resources:/images/tiles/rock.png", x, y)
                elif ch == "g":
                    self._wall(":resources:/images/tiles/grass_sprout.png", x, y)
                elif ch == "L":
                    self._ladder(":resources:/images/items/ladderMid.png", x, y)
                elif ch == "T":
                    self._ladder(":resources:/images/items/ladderTop.png", x, y)
                elif ch == "S":
                    self._simple(":resources:/images/tiles/spikes.png", x, y, self.spikes)
                elif ch == "B":
                    bomb = Bomb(x, y)
                    self.bombs.append(bomb)
                elif ch == "C":
                    coin = AnimatedCoin(x, y)
                    self.coins_list.append(coin)
                elif ch == "D":
                    diamond = arcade.Sprite(":resources:/images/items/gemBlue.png", 0.5)
                    diamond.center_x, diamond.center_y = x, y
                    self.diamonds_list.append(diamond)
                elif ch == "K":
                    key = arcade.Sprite(":resources:/images/items/keyYellow.png", 0.5)
                    key.center_x, key.center_y = x, y
                    self.keys.append(key)
                elif ch == "M":  # Мышь
                    mouse = Enemy(":resources:/images/enemies/mouse.png", 0.5, move_speed=0.8)
                    mouse.center_x, mouse.center_y = x, y
                    self.mice.append(mouse)
                elif ch == "F":  # Лягушка
                    frog = Enemy(":resources:/images/enemies/frog.png", 0.5, move_speed=1.2)
                    frog.center_x, frog.center_y = x, y
                    self.frogs.append(frog)
                elif ch == "m":  # Гриб
                    mushroom = arcade.Sprite(":resources:/images/tiles/mushroomRed.png", 0.5)
                    mushroom.center_x, mushroom.center_y = x, y
                    self.mushrooms.append(mushroom)
                elif ch == "d":  # Верх двери
                    door = arcade.Sprite(":resources:/images/tiles/doorClosed_top.png", 0.5)
                    door.center_x, door.center_y = x, y
                    self.doors.append(door)
                elif ch == "E":  # Середина двери
                    door = arcade.Sprite(":resources:/images/tiles/doorClosed_mid.png", 0.5)
                    door.center_x, door.center_y = x, y
                    self.doors.append(door)
                elif ch == "P":  # Игрок
                    self.player.center_x = x
                    self.player.center_y = y + 20

        # Физический движок с лестницами
        self.physics = arcade.PhysicsEnginePlatformer(
            self.player,
            self.walls,
            gravity_constant=GRAVITY,
            ladders=self.ladders
        )

    def _wall(self, tex, x, y):
        """Создает стену."""
        s = arcade.Sprite(tex, 0.5)
        s.center_x, s.center_y = x, y
        self.walls.append(s)

    def _ladder(self, tex, x, y):
        """Создает лестницу."""
        s = arcade.Sprite(tex, 0.5)
        s.center_x, s.center_y = x, y
        self.ladders.append(s)

    def _simple(self, tex, x, y, lst):
        """Создает простой объект."""
        s = arcade.Sprite(tex, 0.5)
        s.center_x, s.center_y = x, y
        lst.append(s)

    def on_resize(self, width, height):
        """Обрабатывает изменение размера окна."""
        self.camera.resize(width, height)
        self.gui_camera.resize(width, height)
        self.window_size_changed = True

    def on_update(self, delta_time):
        """Обновляет игру каждый кадр."""
        # Уменьшаем таймер шипов
        if self.spike_hit_timer > 0:
            self.spike_hit_timer -= delta_time
        
        # Обновляем физику
        self.physics.update()
        
        # Обновляем анимацию монет
        for coin in self.coins_list:
            coin.update_animation(delta_time)
        
        # Обновляем врагов
        for mouse in self.mice:
            mouse.update_ai(delta_time, self.walls)
        
        for frog in self.frogs:
            frog.update_ai(delta_time, self.walls)

        # Двигаем камеру за игроком
        target_x = self.player.center_x - self.window.width // 2
        target_y = self.player.center_y - self.window.height // 2
        
        # Не даем камере выйти за границы уровня
        max_x = len(LEVEL_2[0]) * TILE - self.window.width
        max_y = len(LEVEL_2) * TILE - self.window.height
        
        target_x = max(0, min(target_x, max_x))
        target_y = max(0, min(target_y, max_y))
        
        # Плавное движение камеры
        current_x, current_y = self.camera.position
        new_x = current_x + (target_x - current_x) * CAMERA_SPEED
        new_y = current_y + (target_y - current_y) * CAMERA_SPEED
        
        self.camera.move_to((new_x, new_y))

        # Анимация персонажа
        if self.physics.is_on_ladder():  # На лестнице
            self.climb_index = (self.climb_index + 0.1) % 2
            self.player.texture = self.tex_climb[int(self.climb_index)]
        elif not self.physics.can_jump():  # В прыжке
            self.player.texture = self.tex_jump
        elif abs(self.player.change_x) > 0:  # Идет
            self.walk_index = (self.walk_index + 0.2) % len(self.tex_walk)
            self.player.texture = self.tex_walk[int(self.walk_index)]
        else:  # Стоит
            self.player.texture = self.tex_idle

        # Сбор монет
        for c in arcade.check_for_collision_with_list(self.player, self.coins_list):
            if not c.collected:
                arcade.play_sound(self.s_coin)
                c.collected = True
                c.remove_from_sprite_lists()
                self.coins += 1

        # Сбор алмазов
        for d in arcade.check_for_collision_with_list(self.player, self.diamonds_list):
            arcade.play_sound(self.s_diamond)
            d.remove_from_sprite_lists()
            self.diamonds += 1

        # Сбор ключа
        if arcade.check_for_collision_with_list(self.player, self.keys):
            arcade.play_sound(self.s_key)
            self.keys.clear()
            self.has_key = True

        # Шипы наносят урон
        if arcade.check_for_collision_with_list(self.player, self.spikes):
            if self.spike_hit_timer <= 0:  # Если можно получить урон
                arcade.play_sound(self.s_spike)
                self.hp -= SPIKE_DAMAGE
                self.spike_hit_timer = SPIKE_COOLDOWN
                
                if self.hp < 0:
                    self.hp = 0

        # Спасение мыши
        for mouse in arcade.check_for_collision_with_list(self.player, self.mice):
            if not self.saved_mouse:
                arcade.play_sound(self.s_save)
                self.saved_mouse = True
            mouse.remove_from_sprite_lists()

        # Спасение лягушки
        for frog in arcade.check_for_collision_with_list(self.player, self.frogs):
            if not self.saved_frog:
                arcade.play_sound(self.s_save)
                self.saved_frog = True
            frog.remove_from_sprite_lists()

        # Взрыв бомбы
        for bomb in arcade.check_for_collision_with_list(self.player, self.bombs):
            if bomb.active:
                arcade.play_sound(self.s_bomb)
                self.hp //= 2  # Здоровье уменьшается вдвое
                bomb.active = False
                bomb.remove_from_sprite_lists()

        # Проверяем смерть
        if self.hp <= 0:
            arcade.play_sound(self.s_gameover)
            self.window.show_view(GameOverView())

        # Выход через дверь
        if self.has_key and arcade.check_for_collision_with_list(self.player, self.doors):
            arcade.play_sound(self.s_win)
            elapsed = int(time.time() - self.start_time)
            
            # Сохраняем рекорд
            record, is_new = save_record(2, self.coins, self.diamonds, 
                                       self.saved_mouse, self.saved_frog, elapsed)
            
            self.window.show_view(
                WinLevel2View({
                    "coins": self.coins,
                    "diamonds": self.diamonds,
                    "saved_mouse": self.saved_mouse,
                    "saved_frog": self.saved_frog,
                    "time": elapsed
                }, record, is_new)
            )

    def on_draw(self):
        """Рисует игру."""
        arcade.start_render()
        
        # Используем камеру для мира
        self.camera.use()
        
        # Рисуем все объекты мира
        self.walls.draw()
        self.ladders.draw()
        self.spikes.draw()
        self.bombs.draw()
        self.coins_list.draw()
        self.diamonds_list.draw()
        self.keys.draw()
        self.mushrooms.draw()
        self.mice.draw()
        self.frogs.draw()
        self.doors.draw()
        self.player.draw()
        
        # Используем камеру для интерфейса
        self.gui_camera.use()
        
        w, h = self.window.width, self.window.height
        elapsed = int(time.time() - self.start_time)
        
        # Адаптивный интерфейс
        left_margin = w * 0.05
        font_size = int(14 * w / 800)
        
        # Полупрозрачный фон для информации
        arcade.draw_rectangle_filled(w // 2, h - 100, w, 200, (0, 0, 0, 150))
        
        # Здоровье (красное если мало)
        arcade.draw_text(f"HP: {self.hp}", 
                         left_margin, h - 30, 
                         arcade.color.RED if self.hp < 30 else arcade.color.GREEN, 
                         font_size, anchor_x="left")
        
        # Монеты
        arcade.draw_text(f"Монеты: {self.coins}", 
                         left_margin, h - 60, 
                         arcade.color.GOLD, 
                         font_size, anchor_x="left")
        
        # Алмазы
        arcade.draw_text(f"Алмазы: {self.diamonds}", 
                         left_margin, h - 90, 
                         arcade.color.CYAN, 
                         font_size, anchor_x="left")
        
        # Ключ
        arcade.draw_text(f"Ключ: {'есть' if self.has_key else 'нет'}",
                         left_margin, h - 120,
                         arcade.color.WHITE,
                         font_size, anchor_x="left")
        
        # Мышь
        arcade.draw_text(f"Мышь: {'спасена' if self.saved_mouse else 'нет'}",
                         left_margin, h - 150,
                         arcade.color.LIGHT_GRAY if not self.saved_mouse else arcade.color.GREEN,
                         font_size, anchor_x="left")
        
        # Лягушка
        arcade.draw_text(f"Лягушка: {'спасена' if self.saved_frog else 'нет'}",
                         left_margin, h - 180,
                         arcade.color.LIGHT_GRAY if not self.saved_frog else arcade.color.GREEN,
                         font_size, anchor_x="left")
        
        # Время (справа)
        arcade.draw_text(f"Время: {elapsed // 60}:{elapsed % 60:02}",
                         w - left_margin, h - 30,
                         arcade.color.WHITE, font_size,
                         anchor_x="right")

    def on_key_press(self, key, modifiers):
        """Обрабатывает нажатие клавиш."""
        if key == arcade.key.RIGHT:
            self.player.change_x = PLAYER_SPEED
        elif key == arcade.key.LEFT:
            self.player.change_x = -PLAYER_SPEED
        elif key == arcade.key.UP:
            if self.physics.is_on_ladder():  # На лестнице
                arcade.play_sound(self.s_ladder)
                self.player.change_y = PLAYER_SPEED
            elif self.physics.can_jump():  # Прыжок
                self.player.change_y = JUMP_SPEED

    def on_key_release(self, key, modifiers):
        """Обрабатывает отпускание клавиш."""
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.player.change_x = 0

# =====================================================
# ЭКРАН ПРОИГРЫША
# =====================================================
class GameOverView(arcade.View):
    """
    Экран проигрыша.
    Показывается, когда здоровье игрока заканчивается.
    """
    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        arcade.start_render()
        w, h = self.window.width, self.window.height

        arcade.draw_text(
            "ВЫ ПРОИГРАЛИ",
            w // 2, h // 2 + 30,
            arcade.color.RED, 36,
            anchor_x="center"
        )

        arcade.draw_text(
            "Клик мышью — в главное меню",
            w // 2, h // 2 - 20,
            arcade.color.WHITE, 16,
            anchor_x="center"
        )

    def on_mouse_press(self, x, y, button, modifiers):
        """При клике перезапускает игру."""
        self.window.close()
        main()

# =====================================================
# ЭКРАН ПОБЕДЫ (УРОВЕНЬ 2)
# =====================================================
class WinLevel2View(arcade.View):
    """
    Экран победы для уровня 2.
    Показывает больше информации, чем для уровня 1.
    """
    def __init__(self, stats, record=None, is_new=False):
        super().__init__()
        self.stats = stats        # Статистика игрока
        self.record = record      # Рекорд
        self.is_new = is_new      # Новый ли рекорд
        self.particle_system = ParticleSystem()  # Для эффектов

    def on_show(self):
        arcade.set_background_color(BG_COLOR)

    def on_draw(self):
        arcade.start_render()
        w, h = self.window.width, self.window.height

        arcade.draw_text(
            "УРОВЕНЬ ПРОЙДЕН!",
            w // 2, h // 2 + 120,
            arcade.color.GOLD, 32,
            anchor_x="center"
        )

        # Детальная статистика
        arcade.draw_text(
            f"Монеты: {self.stats['coins']}",
            w // 2, h // 2 + 70,
            arcade.color.GOLD, 18,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Алмазы: {self.stats['diamonds']}",
            w // 2, h // 2 + 40,
            arcade.color.CYAN, 18,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Мышь: {'спасена' if self.stats['saved_mouse'] else 'не спасена'}",
            w // 2, h // 2 + 10,
            arcade.color.GREEN if self.stats['saved_mouse'] else arcade.color.RED, 18,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Лягушка: {'спасена' if self.stats['saved_frog'] else 'не спасена'}",
            w // 2, h // 2 - 20,
            arcade.color.GREEN if self.stats['saved_frog'] else arcade.color.RED, 18,
            anchor_x="center"
        )

        arcade.draw_text(
            f"Время: {self.stats['time'] // 60} м. {self.stats['time'] % 60} с.",
            w // 2, h // 2 - 50,
            arcade.color.WHITE, 18,
            anchor_x="center"
        )
        
        # Рекорд уровня
        if self.record:
            arcade.draw_text("РЕКОРД УРОВНЯ:",
                             w // 2, h // 2 - 90,
                             arcade.color.GOLD, 20, anchor_x="center")
            
            arcade.draw_text(
                f"Счёт: {self.record.get('score', 0)} | "
                f"Время: {self.record.get('time', 0) // 60} м. {self.record.get('time', 0) % 60} с.",
                w // 2, h // 2 - 120,
                arcade.color.WHITE, 16, anchor_x="center"
            )
            
            # Если побили рекорд
            if self.is_new:
                arcade.draw_text("НОВЫЙ РЕКОРД!",
                                 w // 2, h // 2 - 150,
                                 arcade.color.GOLD, 20, anchor_x="center")

        # Инструкция
        arcade.draw_text(
            "Клик — в главное меню",
            w // 2, 40,
            arcade.color.WHITE, 16,
            anchor_x="center"
        )
        
        # Эффекты
        self.particle_system.draw()

    def on_update(self, delta_time):
        """Обновляет частицы."""
        self.particle_system.update(delta_time)
        
        # Создаем искры
        if random.random() < 0.3:
            x = random.uniform(100, self.window.width - 100)
            y = random.uniform(100, self.window.height - 100)
            color = random.choice([arcade.color.GOLD, arcade.color.YELLOW, 
                                  arcade.color.ORANGE, arcade.color.CYAN])
            self.particle_system.create_sparkle(x, y, color, 
                                               count=random.randint(5, 15))

    def on_mouse_press(self, x, y, button, modifiers):
        """При клике перезапускает игру."""
        self.window.close()
        main()

# =====================================================
# ЗАПУСК ИГРЫ
# =====================================================
def main():
    """
    Главная функция, которая запускает игру.
    Создает окно и показывает стартовый экран.
    """
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
        resizable=True  # Окно можно менять размер
    )

    start_view = StartView()
    window.show_view(start_view)

    arcade.run()

if __name__ == "__main__":
    main()
