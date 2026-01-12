import arcade

# ============================================================
#                     ОБЩИЕ НАСТРОЙКИ
# ============================================================

# Размер окна приложения
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Подземелье авантюристов"

# Размер одного тайла (клетки карты)
TILE_SIZE = 64

# Параметры движения игрока
PLAYER_SPEED = 4          # скорость движения влево/вправо
GRAVITY = 0.8             # сила гравитации
JUMP_SPEED = 15           # сила прыжка (достаточно для прыжка на один блок)

# Цвет фона игрового уровня
BACKGROUND_COLOR = arcade.color.DARK_BROWN


# ============================================================
#                     КАРТА УРОВНЯ
# ============================================================
# Используется символьная карта:
# 1 — стена
# 0 — пустое пространство
# P — стартовая позиция игрока
# C — монета
# E — выход из уровня

LEVEL_MAP = [
    "111111111111111",
    "1P000000000E001",
    "101110111011101",
    "100000100000001",
    "101111101111101",
    "1C00000000000C1",
    "111111111111111",
]


# ============================================================
#                     ГЛАВНОЕ МЕНЮ
# ============================================================

class MenuView(arcade.View):
    """Экран главного меню"""

    def on_show(self):
        # Устанавливаем цвет фона меню
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        # Отрисовка элементов меню
        arcade.start_render()

        arcade.draw_text(
            "ПОДЗЕМЕЛЬЕ АВАНТЮРИСТОВ",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 40,
            arcade.color.GOLD,
            30,
            anchor_x="center",
        )

        arcade.draw_text(
            "ENTER — начать игру",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            arcade.color.WHITE,
            18,
            anchor_x="center",
        )

        arcade.draw_text(
            "← → движение   ↑ прыжок",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 40,
            arcade.color.LIGHT_GRAY,
            14,
            anchor_x="center",
        )

    def on_key_press(self, key, modifiers):
        # При нажатии ENTER переходим в игровой режим
        if key == arcade.key.ENTER:
            game = GameView()
            game.setup()
            self.window.show_view(game)


# ============================================================
#                     ОСНОВНОЙ ИГРОВОЙ КЛАСС
# ============================================================

class GameView(arcade.View):
    """Основной игровой экран"""

    def __init__(self):
        super().__init__()

        # Игрок
        self.player = None

        # Текстуры для анимации игрока
        self.player_textures = []
        self.current_texture = 0
        self.texture_timer = 0

        # Списки объектов
        self.walls = arcade.SpriteList()
        self.coins = arcade.SpriteList()
        self.exit_list = arcade.SpriteList()

        # Физический движок
        self.physics_engine = None

        # Камера
        self.camera = None

        # Игровые параметры
        self.score = 0
        self.map_width = 0
        self.map_height = 0

    def setup(self):
        """Инициализация уровня"""

        arcade.set_background_color(BACKGROUND_COLOR)
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ---------- ЗАГРУЗКА АНИМАЦИИ ПЕРСОНАЖА ----------
        for i in range(8):
            texture = arcade.load_texture(
                f":resources:images/animated_characters/male_adventurer/maleAdventurer_walk{i}.png"
            )
            self.player_textures.append(texture)

        # ---------- СОЗДАНИЕ КАРТЫ ПО LEVEL_MAP ----------
        for row, line in enumerate(LEVEL_MAP):
            for col, char in enumerate(line):
                x = col * TILE_SIZE + TILE_SIZE // 2
                y = (len(LEVEL_MAP) - row) * TILE_SIZE

                # Стены
                if char == "1":
                    wall = arcade.Sprite(
                        ":resources:images/tiles/grassCenter.png",
                        0.5,
                    )
                    wall.center_x = x
                    wall.center_y = y
                    self.walls.append(wall)

                # Игрок
                elif char == "P":
                    self.player = arcade.Sprite()
                    self.player.textures = self.player_textures
                    self.player.texture = self.player_textures[0]
                    self.player.scale = 0.6
                    self.player.center_x = x
                    self.player.center_y = y

                # Монеты
                elif char == "C":
                    coin = arcade.Sprite(
                        ":resources:images/items/coinGold.png",
                        0.4,
                    )
                    coin.center_x = x
                    coin.center_y = y
                    self.coins.append(coin)

                # Выход из уровня
                elif char == "E":
                    exit_sprite = arcade.Sprite(
                        ":resources:images/tiles/signExit.png",
                        0.5,
                    )
                    exit_sprite.center_x = x
                    exit_sprite.center_y = y

                    # Уменьшенный хитбокс для удобного касания
                    exit_sprite.set_hit_box([
                        (-20, -20),
                        (20, -20),
                        (20, 20),
                        (-20, 20),
                    ])

                    self.exit_list.append(exit_sprite)

        # Размер всей карты
        self.map_width = len(LEVEL_MAP[0]) * TILE_SIZE
        self.map_height = len(LEVEL_MAP) * TILE_SIZE

        # Инициализация физики платформера
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player,
            self.walls,
            gravity_constant=GRAVITY,
        )

    def on_draw(self):
        """Отрисовка игрового кадра"""

        arcade.start_render()
        self.camera.use()

        # Отрисовка игровых объектов
        self.walls.draw()
        self.coins.draw()
        self.exit_list.draw()
        self.player.draw()

        # Отображение HUD (счёт)
        arcade.draw_text(
            f"Монеты: {self.score}",
            self.camera.position[0] + 10,
            self.camera.position[1] + SCREEN_HEIGHT - 30,
            arcade.color.WHITE,
            14,
        )

    def on_update(self, delta_time):
        """Обновление логики игры"""

        self.physics_engine.update()
        self.update_camera()
        self.update_animation()

        # Проверка сбора монет
        for coin in arcade.check_for_collision_with_list(self.player, self.coins):
            coin.remove_from_sprite_lists()
            self.score += 1

        # Проверка достижения выхода
        if arcade.check_for_collision_with_list(self.player, self.exit_list):
            self.window.show_view(FinishView(self.score))

    def update_animation(self):
        """Анимация ходьбы персонажа"""
        if self.player.change_x != 0:
            self.texture_timer += 1
            if self.texture_timer > 5:
                self.texture_timer = 0
                self.current_texture = (self.current_texture + 1) % len(self.player_textures)
                self.player.texture = self.player_textures[self.current_texture]

    def update_camera(self):
        """Следование камеры за игроком"""

        x = self.player.center_x - SCREEN_WIDTH // 2
        y = self.player.center_y - SCREEN_HEIGHT // 2

        x = max(0, min(x, self.map_width - SCREEN_WIDTH))
        y = max(0, min(y, self.map_height - SCREEN_HEIGHT))

        self.camera.move_to((x, y))

    # ---------- УПРАВЛЕНИЕ ----------
    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.player.change_x = -PLAYER_SPEED
        elif key == arcade.key.RIGHT:
            self.player.change_x = PLAYER_SPEED
        elif key == arcade.key.UP:
            if self.physics_engine.can_jump():
                self.player.change_y = JUMP_SPEED

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT):
            self.player.change_x = 0


# ============================================================
#                     ЭКРАН ЗАВЕРШЕНИЯ
# ============================================================

class FinishView(arcade.View):
    """Экран окончания игры"""

    def __init__(self, score):
        super().__init__()
        self.score = score

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        arcade.start_render()
        arcade.draw_text(
            "ВЫ ВЫШЛИ ИЗ ПОДЗЕМЕЛЬЯ!",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 + 40,
            arcade.color.LIGHT_GREEN,
            26,
            anchor_x="center",
        )
        arcade.draw_text(
            f"Собрано монет: {self.score}",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
            arcade.color.WHITE,
            18,
            anchor_x="center",
        )
        arcade.draw_text(
            "ESC — выход",
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - 40,
            arcade.color.GRAY,
            14,
            anchor_x="center",
        )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            arcade.close_window()


# ============================================================
#                     ЗАПУСК ПРОГРАММЫ
# ============================================================

def main():
    window = arcade.Window(
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        SCREEN_TITLE,
    )
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
