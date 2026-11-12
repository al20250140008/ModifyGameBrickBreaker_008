def glow(color, radius):
    key = (color, radius)
    if key not in glow_cache:
        s = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        for i in range(8, 0, -1):
            pygame.draw.circle(s, (*color, 12), (radius * 2, radius * 2), radius + i * radius // 3)
        glow_cache[key] = s
    return glow_cache[key]


def draw_text(surf, text, font, color, center):
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(center=(int(center[0]), int(center[1]))))


# ------------------------------------------------------------- Suara
class SoundBank:
    """Membuat dan memutar efek suara. Kalau audio tidak tersedia, game tetap jalan."""

    def __init__(self):
        self.on = False
        self.muted = False
        self.last_animal = 0.0
        self.sounds = {}
        self.animals = []  # (nama_file, label)
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.sr, fmt, self.ch = pygame.mixer.get_init()
            if fmt != -16:
                return
            pygame.mixer.set_num_channels(24)
            self.build()
            self.on = True
        except Exception as err:
            print("Audio dimatikan:", err)

    def make(self, duration, freq_fn, harmonics=((1, 1.0),), vib=(0, 0), noise=0.0,
             pulse=0, decay=None, vol=0.5):
        n = int(self.sr * duration)
        buf = array("h")
        phase = 0.0
        total = sum(a for _, a in harmonics)
        for i in range(n):
            t = i / self.sr
            p = i / n
            f = freq_fn(p)
            if vib[1]:
                f *= 1 + vib[1] * math.sin(math.tau * vib[0] * t)
            phase += math.tau * f / self.sr
            v = sum(a * math.sin(h * phase) for h, a in harmonics) / total
            if noise:
                v = v * (1 - noise) + random.uniform(-1, 1) * noise
            if pulse:
                v *= 0.55 + 0.45 * math.sin(math.tau * pulse * t)
            if decay is None:
                env = min(1.0, p / 0.05) * min(1.0, (1 - p) / 0.2)
            else:
                env = min(1.0, p / 0.02) * (1 - p) ** decay
            s = int(max(-1.0, min(1.0, v * env * vol)) * 32767)
            for _ in range(self.ch):
                buf.append(s)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def add(self, name, builder):
        path = os.path.join(BASE_DIR, "sounds", name + ".wav")
        try:
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
            else:
                self.sounds[name] = builder()
        except Exception as err:
            print("Gagal memuat suara", name, err)

    def build(self):
        rich = ((1, 1.0), (2, 0.8), (3, 0.7), (4, 0.55), (5, 0.45), (6, 0.35), (7, 0.25))
        add = self.add
        # ----- hewan
        add("meong", lambda: self.make(0.45, lambda p: 450 + 520 * math.sin(math.pi * p) ** 0.8,
                                       ((1, 1.0), (2, 0.6), (3, 0.4), (4, 0.25)), vib=(7, 0.02)))
        add("guk", lambda: self.make(0.22, lambda p: 430 - 230 * p, rich, noise=0.25, decay=1.6, vol=0.6))
        add("kwek", lambda: self.make(0.28, lambda p: 340 - 40 * p, rich, vib=(38, 0.07), noise=0.1))
        add("ngoek", lambda: self.make(0.36, lambda p: 170 - 80 * p, rich, vib=(18, 0.12), noise=0.15))
        add("muu", lambda: self.make(0.75, lambda p: 130 + 35 * math.sin(math.pi * p) - 25 * p,
                                     ((1, 1.0), (2, 0.7), (3, 0.5), (4, 0.3)), vib=(5, 0.03)))

        def rooster(p):
            if p < 0.2:
                return 600 + 200 * (p / 0.2)
            if p < 0.4:
                return 750 + 200 * ((p - 0.2) / 0.2)
            if p < 0.6:
                return 900 + 200 * ((p - 0.4) / 0.2)
            return 1100 - 500 * ((p - 0.6) / 0.4)
        add("kukuruyuk", lambda: self.make(0.7, rooster, ((1, 1.0), (2, 0.5), (3, 0.3)), vib=(9, 0.02)))
        add("kroak", lambda: self.make(0.3, lambda p: 220 + 30 * p, rich, pulse=28, noise=0.08))
        add("cip", lambda: self.make(0.12, lambda p: 2200 + 700 * p, ((1, 1.0), (2, 0.2)), vol=0.4))
        add("mbek", lambda: self.make(0.5, lambda p: 330 - 40 * p, rich, vib=(30, 0.1)))
        # ----- efek lain
        add("tick", lambda: self.make(0.05, lambda p: 700, ((1, 1.0),), decay=1.0, vol=0.25))
        add("paddle", lambda: self.make(0.1, lambda p: 220 - 110 * p, ((1, 1.0), (2, 0.4)), decay=1.2, vol=0.5))
        add("boom", lambda: self.make(0.55, lambda p: 90 - 55 * p, ((1, 1.0), (2, 0.5)), noise=0.6,
                                      decay=1.4, vol=0.7))
        add("powerup", lambda: self.make(0.28, lambda p: 600 + 700 * p, ((1, 1.0), (2, 0.4), (3, 0.2)), vol=0.4))
        add("lose", lambda: self.make(0.5, lambda p: 420 - 250 * p, ((1, 1.0), (2, 0.5)), vol=0.45))
        add("gameover", lambda: self.make(1.0, lambda p: 400 - 300 * p, ((1, 1.0), (2, 0.6), (3, 0.3)),
                                          vib=(6, 0.03), vol=0.5))
        add("levelup", lambda: self.make(0.5, lambda p: 500 if p < 0.33 else (650 if p < 0.66 else 800),
                                         ((1, 1.0), (2, 0.4)), vol=0.4))
        self.animals = [
            ("meong", "MEONG!"), ("guk", "GUK!"), ("kwek", "KWEK!"), ("ngoek", "NGOEK!"),
            ("muu", "MUUU!"), ("kukuruyuk", "KOKOKOK!"), ("kroak", "KROAK!"),
            ("cip", "CIP!"), ("mbek", "MBEEK!"),
        ]
        self.animals = [a for a in self.animals if a[0] in self.sounds]

    def play(self, name):
        if self.on and not self.muted and name in self.sounds:
            self.sounds[name].play()

    def play_animal(self):
        """Putar suara hewan acak, kembalikan teks label (atau None)."""
        if not (self.on and self.animals):
            return None
        name, label = random.choice(self.animals)
        now = time.time()
        if now - self.last_animal < 0.06:  # cegah terlalu ramai
            return label
        self.last_animal = now
        self.play(name)
        return label


# ---------------------------------------------------------------- Ball
class Ball:
    def __init__(self, posx, posy, radius, speed, color):
        self.posx, self.posy = posx, posy
        self.radius = radius
        self.speed = speed
        self.color = color
        self.vx, self.vy = 0.0, 0.0
        self.stuck = True
        self.trail = []
        self.wall_hit = False

    def launch(self):
        ang = math.radians(random.uniform(-25, 25))
        self.vx, self.vy = math.sin(ang), -math.cos(ang)
        self.stuck = False

    def display(self, canvas, fire=False):
        col = ORANGE if fire else self.color
        for i, (tx, ty) in enumerate(self.trail):
            r = max(1, int(self.radius * i / len(self.trail)))
            pygame.draw.circle(canvas, col, (int(tx), int(ty)), r)
        g = glow(col, self.radius)
        canvas.blit(g, (int(self.posx - self.radius * 2), int(self.posy - self.radius * 2)))
        pygame.draw.circle(canvas, WHITE, (int(self.posx), int(self.posy)), self.radius)

    def update(self, dt):
        """Return True kalau bola jatuh ke bawah."""
        self.trail.append((self.posx, self.posy))
        if len(self.trail) > 14:
            self.trail.pop(0)
        self.posx += self.vx * self.speed * dt
        self.posy += self.vy * self.speed * dt
        if self.posx <= self.radius:
            self.posx, self.vx = self.radius, abs(self.vx)
            self.wall_hit = True
        elif self.posx >= WIDTH - self.radius:
            self.posx, self.vx = WIDTH - self.radius, -abs(self.vx)
            self.wall_hit = True
        if self.posy <= self.radius:
            self.posy, self.vy = self.radius, abs(self.vy)
            self.wall_hit = True
        return self.posy >= HEIGHT + self.radius

    def hit(self):
        self.vy *= -1

    def getRect(self):
        r = self.radius
        return pygame.Rect(int(self.posx - r), int(self.posy - r), r * 2, r * 2)


# ------------------------------------------------------------- Objects
class Brick:
    def __init__(self, rect, hp, bomb=False):
        self.rect, self.hp, self.bomb = rect, hp, bomb

    @property
    def color(self):
        return ORANGE if self.bomb else HP_COLORS[max(1, min(3, self.hp))]

    def draw(self, canvas):
        c = self.color
        pygame.draw.rect(canvas, tuple(v // 3 for v in c), self.rect, border_radius=5)
        pygame.draw.rect(canvas, c, self.rect, 2, border_radius=5)
        if self.bomb:
            draw_text(canvas, "*", FONT, WHITE, self.rect.center)


class Particle:
    def __init__(self, x, y, color, speed=260):
        a, s = random.uniform(0, math.tau), random.uniform(40, speed)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * s, math.sin(a) * s
        self.life = self.max = random.uniform(0.3, 0.8)
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 300 * dt
        self.life -= dt

    def draw(self, canvas):
        r = max(1, int(4 * self.life / self.max))
        pygame.draw.circle(canvas, self.color, (int(self.x), int(self.y)), r)


class FloatText:
    """Teks melayang (MEONG!, GUK!, dst)."""

    def __init__(self, text, x, y, color):
        self.text, self.x, self.y, self.color = text, x, y, color
        self.life = 0.8

    def update(self, dt):
        self.y -= 50 * dt
        self.life -= dt

    def draw(self, canvas):
        draw_text(canvas, self.text, FONT, self.color, (self.x, self.y))


class Capsule:
    COLORS = {"M": CYAN, "W": GREEN, "S": MAGENTA, "F": ORANGE, "L": YELLOW}

    def __init__(self, x, y, kind):
        self.fy = float(y)
        self.rect = pygame.Rect(0, 0, 38, 20)
        self.rect.center = (int(x), int(y))
        self.kind = kind

    def fall(self, dt):
        self.fy += 170 * dt
        self.rect.y = int(self.fy)

    def draw(self, canvas):
        c = self.COLORS[self.kind]
        canvas.blit(glow(c, 12), (self.rect.centerx - 24, self.rect.centery - 24))
        pygame.draw.rect(canvas, c, self.rect, border_radius=10)
        draw_text(canvas, self.kind, SMALL, BG, self.rect.center)


# ---------------------------------------------------------------- Game
class Game:
    def __init__(self):
        self.sfx = SoundBank()
        self.stars = [[random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1), random.uniform(0.2, 1)]
                      for _ in range(90)]
        self.best = 0
        self.state = "menu"
        self.shake = 0.0
        self.warp = False
        self.balls = []
        self.bricks = []
        self.capsules = []
        self.particles = []
        self.texts = []
        self.effects = {"W": 0, "S": 0, "F": 0}
        self.level, self.score, self.lives = 1, 0, 3
        self.energy, self.combo = 100.0, 0
        self.descent_timer, self.interval = 10, 10
        self.paddle = pygame.Rect(0, PADDLE_Y, 130, 14)
        self.paddle.centerx = WIDTH // 2
        self.paddle_w = 130.0
        self.last_mouse_x = pygame.mouse.get_pos()[0]

    def new_game(self):
        self.level, self.score, self.lives = 1, 0, 3
        self.energy, self.combo = 100.0, 0
        self.start_level()
        self.state = "play"

    def start_level(self):
        self.paddle_w = 130.0
        self.paddle = pygame.Rect(0, PADDLE_Y, 130, 14)
        self.paddle.centerx = WIDTH // 2
        self.effects = {"W": 0, "S": 0, "F": 0}
        self.bricks = self.build_level(self.level)
        self.capsules, self.particles, self.texts = [], [], []
        self.interval = max(6.0, 15 - self.level)
        self.descent_timer = self.interval
        self.shake = 0.0
        self.reset_ball()

    def reset_ball(self):
        self.balls = [Ball(self.paddle.centerx, PADDLE_Y - 10, 8, self.base_speed(), WHITE)]
        self.combo = 0

    def base_speed(self):
        return 420 + self.level * 25

    def build_level(self, level):
        rows, cols, bw, bh, gap = min(4 + level, 9), 10, 76, 26, 6
        left = (WIDTH - (cols * bw + (cols - 1) * gap)) // 2
        pattern = level % 4
        bricks = []
        for r in range(rows):
            for c in range(cols):
                if pattern == 1 and (r + c) % 2:
                    continue
                if pattern == 2 and abs(c - 4.5) > r + 1.5:
                    continue
                if pattern == 3 and r > 2 + 2 * math.sin(c * 0.9) + 2:
                    continue
                hp = 1
                if level > 1 and r < rows // 3:
                    hp = random.choice([2, 3])
                elif level > 0 and r < 2 * rows // 3:
                    hp = random.choice([1, 2])
                rect = pygame.Rect(left + c * (bw + gap), 70 + r * (bh + gap), bw, bh)
                bricks.append(Brick(rect, hp, bomb=random.random() < 0.07))
        if not bricks:
            bricks.append(Brick(pygame.Rect(WIDTH // 2 - 38, 100, bw, bh), 1))
        return bricks

    # --------------------------------------------------- game mechanics
    def damage(self, brick, amount=1):
        if brick not in self.bricks:
            return
        brick.hp -= amount
        if brick.hp > 0:
            self.score += 5
            self.burst(brick.rect.center, brick.color, 5)
            self.sfx.play("tick")
            return
        self.bricks.remove(brick)
        self.combo += 1
        self.score += 10 * max(1, self.combo)
        self.energy = min(100, self.energy + 4)
        self.burst(brick.rect.center, brick.color, 22)
        # suara hewan!
        label = self.sfx.play_animal()
        if label:
            self.texts.append(FloatText(label, brick.rect.centerx, brick.rect.centery, brick.color))
        if random.random() < 0.13:
            self.capsules.append(Capsule(brick.rect.centerx, brick.rect.centery, random.choice("MWSFLMWSF")))
        if brick.bomb:
            self.shake = 14
            self.sfx.play("boom")
            cx, cy = brick.rect.center
            for other in self.bricks[:]:
                ox, oy = other.rect.center
                if math.hypot(ox - cx, oy - cy) < 115:
                    self.damage(other, 2)

    def burst(self, pos, color, n):
        self.particles += [Particle(pos[0], pos[1], color) for _ in range(n)]

    def apply_powerup(self, kind):
        self.sfx.play("powerup")
        if kind == "M":
            for b in self.balls[:2]:
                if b.stuck:
                    continue
                for off in (-0.5, 0.5):
                    nb = Ball(b.posx, b.posy, b.radius, b.speed, b.color)
                    ang = math.atan2(b.vx, -b.vy) + off
                    nb.vx, nb.vy, nb.stuck = math.sin(ang), -math.cos(ang), False
                    self.balls.append(nb)
        elif kind == "W":
            self.effects["W"] = 10
        elif kind == "S":
            self.effects["S"] = 8
        elif kind == "F":
            self.effects["F"] = 6
        elif kind == "L":
            self.lives = min(5, self.lives + 1)
        self.score += 50

    def ball_vs_brick(self, ball):
        fire = self.effects["F"] > 0
        for b in self.bricks[:]:
            cx = max(b.rect.left, min(ball.posx, b.rect.right))
            cy = max(b.rect.top, min(ball.posy, b.rect.bottom))
            if math.hypot(ball.posx - cx, ball.posy - cy) > ball.radius:
                continue
            self.damage(b, 3 if fire else 1)
            if not fire:
                r = ball.radius
                overlaps = {
                    "l": ball.posx + r - b.rect.left, "r": b.rect.right - (ball.posx - r),
                    "t": ball.posy + r - b.rect.top, "b": b.rect.bottom - (ball.posy - r),
                }
                side = min(overlaps, key=overlaps.get)
                if side == "l":
                    ball.vx = -abs(ball.vx)
                elif side == "r":
                    ball.vx = abs(ball.vx)
                elif side == "t":
                    ball.vy = -abs(ball.vy)
                else:
                    ball.vy = abs(ball.vy)
                return

    def ball_vs_paddle(self, ball):
        if ball.vy <= 0 or not ball.getRect().colliderect(self.paddle):
            return
        off = max(-1, min(1, (ball.posx - self.paddle.centerx) / (self.paddle.w / 2)))
        ang = math.radians(off * 62)
        ball.vx, ball.vy = math.sin(ang), -math.cos(ang)
        ball.posy = self.paddle.top - ball.radius
        self.combo = 0
        self.burst((ball.posx, self.paddle.top), CYAN, 6)
        self.sfx.play("paddle")

    # ------------------------------------------------------------ update
    def update(self, dt, keys):
        warp = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.energy > 0
        if warp:
            self.energy = max(0, self.energy - 35 * dt)
            dt *= 0.35
        else:
            self.energy = min(100, self.energy + 4 * dt)
        self.warp = bool(warp)

        target_w = 210 if self.effects["W"] > 0 else 130
        self.paddle_w += (target_w - self.paddle_w) * min(1, dt * 12)
        cx = self.paddle.centerx
        self.paddle.w = int(self.paddle_w)
        self.paddle.centerx = cx

        mx = pygame.mouse.get_pos()[0]
        if mx != self.last_mouse_x:
            self.paddle.centerx = mx
            self.last_mouse_x = mx
        move = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.paddle.x += int(move * 800 * dt)
        self.paddle.clamp_ip(screen.get_rect())

        for k in self.effects:
            self.effects[k] = max(0, self.effects[k] - dt)

        slow = 0.6 if self.effects["S"] > 0 else 1
        for ball in self.balls[:]:
            if ball.stuck:
                ball.posx, ball.posy = self.paddle.centerx, PADDLE_Y - ball.radius - 2
                continue
            ball.speed = self.base_speed() * slow
            if ball.update(dt):
                self.balls.remove(ball)
                continue
            if ball.wall_hit:
                ball.wall_hit = False
                self.sfx.play("tick")
            self.ball_vs_paddle(ball)
            self.ball_vs_brick(ball)

        if not self.balls:
            self.lives -= 1
            self.shake = 10
            if self.lives <= 0:
                self.game_over()
                return
            self.sfx.play("lose")
            self.reset_ball()

        for c in self.capsules[:]:
            c.fall(dt)
            if c.rect.colliderect(self.paddle):
                self.apply_powerup(c.kind)
                self.capsules.remove(c)
            elif c.rect.top > HEIGHT:
                self.capsules.remove(c)

        self.descent_timer -= dt
        if self.descent_timer <= 0:
            self.descent_timer = self.interval
            self.shake = 6
            for b in self.bricks:
                b.rect.y += 24
            if any(b.rect.bottom >= PADDLE_Y - 20 for b in self.bricks):
                self.game_over()
                return

        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0:
                self.particles.remove(p)
        for t in self.texts[:]:
            t.update(dt)
            if t.life <= 0:
                self.texts.remove(t)
        self.shake = max(0.0, self.shake - 40 * dt)

        if not self.bricks:
            self.level += 1
            self.score += 200
            self.sfx.play("levelup")
            self.start_level()

    def game_over(self):
        self.best = max(self.best, self.score)
        self.state = "over"
        self.sfx.play("gameover")

    # -------------------------------------------------------------- draw
    def draw_background(self, canvas):
        canvas.fill(BG)
        for s in self.stars:
            s[1] = (s[1] + s[2] * 0.6) % HEIGHT
            v = int(60 + 120 * s[2])
            canvas.set_at((int(s[0]), int(s[1])), (v, v, 255))

    def draw(self):
        canvas = pygame.Surface((WIDTH, HEIGHT))
        self.draw_background(canvas)

        if self.state == "menu":
            draw_text(canvas, "NEON BREAKER", BIG, CYAN, (WIDTH // 2, 240))
            draw_text(canvas, "D E S C E N T", FONT, MAGENTA, (WIDTH // 2, 295))
            draw_text(canvas, "Hancurkan brick sebelum mereka turun menimpamu!", SMALL, WHITE, (WIDTH // 2, 370))
            draw_text(canvas, "SHIFT = Time Warp   |   M W S F L = power-up   |   * = bom", SMALL, WHITE, (WIDTH // 2, 400))
            snd = "suara hewan aktif  (N = bisu)" if self.sfx.on else "audio tidak tersedia"
            draw_text(canvas, snd, SMALL, GREEN, (WIDTH // 2, 430))
            draw_text(canvas, "Tekan SPASI / klik untuk mulai", FONT, YELLOW, (WIDTH // 2, 490))
        else:
            for b in self.bricks:
                b.draw(canvas)
            for c in self.capsules:
                c.draw(canvas)
            for p in self.particles:
                p.draw(canvas)
            for ball in self.balls:
                ball.display(canvas, fire=self.effects["F"] > 0)
            for t in self.texts:
                t.draw(canvas)

            gl = pygame.Surface((self.paddle.w + 40, 50), pygame.SRCALPHA)
            for i in range(5, 0, -1):
                pygame.draw.rect(gl, (*CYAN, 25),
                                 (20 - i * 3, 18 - i * 2, self.paddle.w + i * 6, 14 + i * 4), border_radius=12)
            canvas.blit(gl, (self.paddle.x - 20, self.paddle.y - 18))
            pygame.draw.rect(canvas, CYAN, self.paddle, border_radius=7)

            warn = self.descent_timer < 2 and int(self.descent_timer * 6) % 2 == 0
            pygame.draw.line(canvas, (255, 40, 80) if warn else (60, 20, 40),
                             (0, PADDLE_Y - 20), (WIDTH, PADDLE_Y - 20), 1)

            draw_text(canvas, f"SKOR {self.score}", FONT, WHITE, (90, 25))
            draw_text(canvas, f"LEVEL {self.level}", FONT, YELLOW, (WIDTH // 2, 25))
            draw_text(canvas, "<3 " * self.lives, FONT, MAGENTA, (WIDTH - 80, 25))
            if self.combo > 1:
                draw_text(canvas, f"COMBO x{self.combo}", FONT, ORANGE, (WIDTH // 2, 50))
            pygame.draw.rect(canvas, (40, 40, 70), (20, HEIGHT - 20, 200, 8), border_radius=4)
            bar_w = int(2 * self.energy)
            if bar_w > 0:
                pygame.draw.rect(canvas, MAGENTA if self.warp else CYAN,
                                 (20, HEIGHT - 20, bar_w, 8), border_radius=4)
            draw_text(canvas, "TIME WARP", SMALL, WHITE, (270, HEIGHT - 16))
            if self.sfx.muted:
                draw_text(canvas, "BISU (N)", SMALL, (150, 150, 170), (WIDTH - 60, 55))
            y = HEIGHT - 20
            for k, t in self.effects.items():
                if t > 0:
                    draw_text(canvas, f"{k} {t:.0f}s", SMALL, Capsule.COLORS[k], (WIDTH - 60, y))
                    y -= 20
            if any(b.stuck for b in self.balls):
                draw_text(canvas, "SPASI / klik untuk luncurkan", SMALL, WHITE, (WIDTH // 2, PADDLE_Y - 50))
            if self.warp:
                tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                tint.fill((120, 0, 200, 40))
                canvas.blit(tint, (0, 0))

            if self.state == "over":
                shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                shade.fill((0, 0, 0, 170))
                canvas.blit(shade, (0, 0))
                draw_text(canvas, "GAME OVER", BIG, MAGENTA, (WIDTH // 2, 270))
                draw_text(canvas, f"Skor {self.score}   |   Terbaik {self.best}", FONT, WHITE, (WIDTH // 2, 345))
                draw_text(canvas, "Tekan SPASI untuk main lagi", FONT, YELLOW, (WIDTH // 2, 420))

        sh = int(self.shake)
        off = (random.randint(-sh, sh), random.randint(-sh, sh)) if sh > 0 else (0, 0)
        screen.fill((0, 0, 0))
        screen.blit(canvas, off)
        pygame.display.flip()


def main():
    game = Game()
    while True:
        dt = min(clock.tick(60) / 1000, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_n:
                game.sfx.muted = not game.sfx.muted
            go = (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE) or \
                 (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)
            if go:
                if game.state in ("menu", "over"):
                    game.new_game()
                else:
                    for b in game.balls:
                        if b.stuck:
                            b.launch()
        if game.state == "play":
            game.update(dt, pygame.key.get_pressed())
        game.draw()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        input("Error! Tekan Enter untuk menutup...")