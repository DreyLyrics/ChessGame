"""
UI/LoginAndResgister.py
Components:
  - AvatarButton  : icon avatar góc trên phải, click → dropdown
  - DropdownMenu  : menu thả xuống — Đăng nhập / Đăng ký
  - Modal         : overlay modal form đăng nhập hoặc đăng ký
  - InputField    : ô nhập liệu
  - Button        : nút bấm
"""

import pygame
import math

# ------------------------------------------------------------------ #
#  PALETTE                                                             #
# ------------------------------------------------------------------ #
C_BG          = (18,  18,  30)
C_PANEL       = (24,  24,  42)
C_PANEL2      = (32,  32,  52)
C_BORDER      = (55,  55,  85)
C_ACCENT      = (100, 160, 255)   # xanh dương — Đăng nhập
C_ACCENT_HOV  = (130, 185, 255)
C_REG         = ( 72, 199, 142)   # xanh lá tươi — Đăng ký
C_REG_HOV     = (100, 220, 165)
C_TEXT        = (220, 220, 240)
C_TEXT_DIM    = (120, 120, 155)
C_INPUT_BG    = (20,  20,  36)
C_INPUT_ACT   = (30,  30,  50)
C_ERROR       = (255,  85,  85)
C_SUCCESS     = ( 72, 199, 142)
C_BTN_BG      = (100, 160, 255)
C_BTN_HOV     = (130, 185, 255)
C_BTN_TEXT    = (255, 255, 255)
C_OVERLAY     = (  0,   0,   0, 155)


# ------------------------------------------------------------------ #
#  HELPERS                                                             #
# ------------------------------------------------------------------ #

def _draw_rounded_rect(surface, color, rect, radius=10, border=0, border_color=None):
    if not (len(color) == 4 and color[3] == 0):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def _draw_avatar_icon(surface, cx, cy, radius, color, border_color,
                      logged_in=False, username=''):
    pygame.draw.circle(surface, color, (cx, cy), radius)
    pygame.draw.circle(surface, border_color, (cx, cy), radius, 2)
    if logged_in and username:
        font = pygame.font.SysFont('segoeui', radius, bold=True)
        lbl  = font.render(username[0].upper(), True, C_TEXT)
        surface.blit(lbl, lbl.get_rect(center=(cx, cy)))
    else:
        head_r = radius // 3
        pygame.draw.circle(surface, C_TEXT, (cx, cy - radius // 5), head_r)
        body_rect = pygame.Rect(cx - radius // 2, cy + radius // 8,
                                radius, radius // 2)
        pygame.draw.ellipse(surface, C_TEXT, body_rect)


# ------------------------------------------------------------------ #
#  INPUT FIELD                                                         #
# ------------------------------------------------------------------ #

class InputField:
    _BACKSPACE_DELAY = 400   # ms trước khi repeat
    _BACKSPACE_RATE  = 40    # ms mỗi lần repeat

    def __init__(self, x, y, w, h, label='', placeholder='', password=False):
        self.rect        = pygame.Rect(x, y, w, h)
        self.label       = label
        self.placeholder = placeholder
        self.password    = password
        self.text        = ''
        self.active      = False
        self.error       = ''
        self._selected   = False          # Ctrl+A select all
        self._bs_held    = False          # backspace đang giữ
        self._bs_next    = 0              # thời điểm xóa tiếp theo

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            if not self.active:
                self._selected = False

        if event.type == pygame.KEYDOWN and self.active:
            mods = pygame.key.get_mods()

            # Ctrl+A — select all
            if event.key == pygame.K_a and (mods & pygame.KMOD_CTRL):
                self._selected = bool(self.text)
                return

            if event.key == pygame.K_BACKSPACE:
                if self._selected:
                    self.text = ''
                    self._selected = False
                else:
                    self.text = self.text[:-1]
                self._bs_held = True
                self._bs_next = pygame.time.get_ticks() + self._BACKSPACE_DELAY
            elif event.key not in (pygame.K_RETURN, pygame.K_TAB, pygame.K_ESCAPE):
                if self._selected:
                    self.text = ''
                    self._selected = False
                if len(self.text) < 64:
                    self.text += event.unicode
            else:
                self._selected = False
            self.error = ''

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_BACKSPACE:
                self._bs_held = False

    def update(self):
        """Gọi mỗi frame để xử lý giữ backspace."""
        if self._bs_held and self.active and self.text:
            now = pygame.time.get_ticks()
            if now >= self._bs_next:
                if self._selected:
                    self.text = ''
                    self._selected = False
                else:
                    self.text = self.text[:-1]
                self._bs_next = now + self._BACKSPACE_RATE

    def clear(self):
        self.text = self.error = ''
        self.active    = False
        self._selected = False
        self._bs_held  = False

    def draw(self, surface, font_label, font_input):
        if self.label:
            lbl = font_label.render(self.label, True, C_TEXT_DIM)
            surface.blit(lbl, (self.rect.x, self.rect.y - lbl.get_height() - 5))

        bg = C_INPUT_ACT if self.active else C_INPUT_BG
        pygame.draw.rect(surface, bg, self.rect, border_radius=10)
        bc = C_ACCENT if self.active else (C_ERROR if self.error else C_BORDER)
        pygame.draw.rect(surface, bc, self.rect, 2, border_radius=10)

        display = ('•' * len(self.text)) if self.password else self.text

        # highlight khi select all
        if self._selected and display:
            sel_w = min(font_input.size(display)[0], self.rect.w - 28)
            sel_r = pygame.Rect(self.rect.x + 12, self.rect.centery - 12,
                                sel_w + 4, 24)
            sel_surf = pygame.Surface((sel_r.w, sel_r.h), pygame.SRCALPHA)
            sel_surf.fill((100, 160, 255, 80))
            surface.blit(sel_surf, sel_r.topleft)

        t = font_input.render(display or self.placeholder, True,
                              C_TEXT if display else C_TEXT_DIM)
        clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-8, -4))
        surface.blit(t, (self.rect.x + 14,
                         self.rect.centery - t.get_height() // 2))
        surface.set_clip(clip)

        # cursor (ẩn khi đang select all)
        if self.active and not self._selected and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = self.rect.x + 14 + font_input.size(display)[0] + 1
            pygame.draw.line(surface, C_ACCENT,
                             (cx, self.rect.centery - 11),
                             (cx, self.rect.centery + 11), 2)

        if self.error:
            e = font_label.render(self.error, True, C_ERROR)
            surface.blit(e, (self.rect.x, self.rect.bottom + 4))


# ------------------------------------------------------------------ #
#  BUTTON                                                              #
# ------------------------------------------------------------------ #

class Button:
    def __init__(self, x, y, w, h, text,
                 bg=C_BTN_BG, bg_hover=C_BTN_HOV, text_color=C_BTN_TEXT,
                 outline=False, radius=10):
        self.rect       = pygame.Rect(x, y, w, h)
        self.text       = text
        self.bg         = bg
        self.bg_hover   = bg_hover
        self.text_color = text_color
        self.outline    = outline
        self.radius     = radius
        self._hovered   = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface, font):
        col = self.bg_hover if self._hovered else self.bg
        if self.outline:
            # nền trong suốt + viền màu + text màu
            pygame.draw.rect(surface, self.bg, self.rect, border_radius=self.radius)
            pygame.draw.rect(surface, col, self.rect, 2, border_radius=self.radius)
            lbl = font.render(self.text, True, col)
        else:
            pygame.draw.rect(surface, col, self.rect, border_radius=self.radius)
            lbl = font.render(self.text, True, self.text_color)
        surface.blit(lbl, lbl.get_rect(center=self.rect.center))


# ------------------------------------------------------------------ #
#  DROPDOWN MENU                                                       #
# ------------------------------------------------------------------ #

class DropdownMenu:
    ITEM_W  = 200
    ITEM_H  = 44
    PADDING = 10

    def __init__(self, anchor_x, anchor_y, logged_in=False, username='', email='',
                 display_name='', avatar_surf=None):
        self.x            = anchor_x - self.ITEM_W
        self.y            = anchor_y
        self.logged_in    = logged_in
        self.username     = username
        self.email        = email
        self.display_name = display_name or username
        self.avatar_surf  = avatar_surf   # pygame.Surface tròn hoặc None
        self._open_t   = pygame.time.get_ticks()
        self._hovered  = -1

        self._font      = pygame.font.SysFont('segoeui', 15, bold=True)
        self._font_info = pygame.font.SysFont('segoeui', 13)
        self._font_dim  = pygame.font.SysFont('segoeui', 12)

        if logged_in:
            # Thong tin + Tuy chinh + Dang xuat
            self._items  = ['Thong tin', 'Tuy chinh', 'Dang xuat']
            self._colors = [
                ((100, 200, 255), (130, 220, 255)),   # Thong tin — xanh nhạt
                (C_ACCENT, C_ACCENT_HOV),              # Tuy chinh — xanh dương
                ((200, 80, 80), (230, 100, 100)),      # Dang xuat — đỏ
            ]
            info_h = 70   # chiều cao phần thông tin user
        else:
            self._items  = ['Dang nhap']
            self._colors = [(C_ACCENT, C_ACCENT_HOV)]
            info_h       = 0

        self._info_h = info_h
        total_h = (self.PADDING * 2 + info_h
                   + len(self._items) * self.ITEM_H
                   + (len(self._items) - 1) * 4)
        self.rect = pygame.Rect(self.x - self.PADDING, self.y,
                                self.ITEM_W + self.PADDING * 2, total_h)

    def _item_rect(self, idx):
        iy = self.y + self.PADDING + self._info_h + idx * (self.ITEM_H + 4)
        return pygame.Rect(self.x, iy, self.ITEM_W, self.ITEM_H)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hovered = -1
            for i in range(len(self._items)):
                if self._item_rect(i).collidepoint(event.pos):
                    self._hovered = i
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, name in enumerate(self._items):
                if self._item_rect(i).collidepoint(event.pos):
                    return name
        return None

    def draw(self, surface):
        elapsed  = (pygame.time.get_ticks() - self._open_t) / 140.0
        ease     = 1 - (1 - min(1.0, elapsed)) ** 3
        clip_h   = int(self.rect.height * ease)
        old_clip = surface.get_clip()
        surface.set_clip(pygame.Rect(self.rect.x - 4, self.rect.y,
                                     self.rect.width + 8, clip_h))

        # shadow
        sh = pygame.Surface((self.rect.width + 8, self.rect.height + 8), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 55))
        surface.blit(sh, (self.rect.x - 4, self.rect.y + 4))

        pygame.draw.rect(surface, C_PANEL2, self.rect, border_radius=12)
        pygame.draw.rect(surface, C_BORDER, self.rect, 1, border_radius=12)

        # ── phần thông tin user (nếu đã đăng nhập) ──
        if self.logged_in and self._info_h > 0:
            info_rect = pygame.Rect(self.x - self.PADDING, self.y,
                                    self.ITEM_W + self.PADDING * 2,
                                    self._info_h + self.PADDING)
            pygame.draw.rect(surface, (40, 40, 65), info_rect, border_radius=12)

            # avatar nhỏ — căn giữa dọc trong info_h
            av_r  = 20
            av_cx = self.x + self.PADDING + av_r
            av_cy = self.y + self.PADDING + self._info_h // 2

            if self.avatar_surf:
                d = av_r * 2
                scaled = pygame.transform.smoothscale(self.avatar_surf, (d, d))
                surface.blit(scaled, (av_cx - av_r, av_cy - av_r))
                pygame.draw.circle(surface, C_ACCENT, (av_cx, av_cy), av_r, 2)
            else:
                pygame.draw.circle(surface, (60, 170, 100), (av_cx, av_cy), av_r)
                pygame.draw.circle(surface, C_ACCENT,       (av_cx, av_cy), av_r, 2)
                af = pygame.font.SysFont('segoeui', av_r, bold=True)
                al = af.render(self.username[0].upper() if self.username else '?', True, C_TEXT)
                surface.blit(al, al.get_rect(center=(av_cx, av_cy)))

            # tên hiển thị — dùng display_name thay vì username
            tx = av_cx + av_r + 10
            name_lbl  = self._font.render(self.display_name, True, C_TEXT)
            email_lbl = self._font_dim.render(self.email or '', True, C_TEXT_DIM)

            if self.email:
                # có email → tên + email xếp dọc, cả 2 căn giữa cùng nhau
                total_text_h = name_lbl.get_height() + 4 + email_lbl.get_height()
                ty = av_cy - total_text_h // 2
                surface.blit(name_lbl,  (tx, ty))
                surface.blit(email_lbl, (tx, ty + name_lbl.get_height() + 4))
            else:
                # chỉ có tên → căn giữa dọc
                surface.blit(name_lbl, (tx, av_cy - name_lbl.get_height() // 2))

            # đường kẻ phân cách
            sep_y = self.y + self.PADDING + self._info_h + 2
            pygame.draw.line(surface, C_BORDER,
                             (self.x, sep_y), (self.x + self.ITEM_W, sep_y), 1)

        # ── các item ──
        for i, name in enumerate(self._items):
            ir            = self._item_rect(i)
            c_norm, c_hov = self._colors[i]
            if i == self._hovered:
                pygame.draw.rect(surface, c_norm, ir, border_radius=8)
                lbl = self._font.render(name, True, (10, 10, 20))
            else:
                lbl = self._font.render(name, True, c_norm)
            surface.blit(lbl, lbl.get_rect(center=ir.center))

        surface.set_clip(old_clip)


# ------------------------------------------------------------------ #
#  MODAL                                                               #
# ------------------------------------------------------------------ #

class Modal:
    """
    mode = 'login' | 'register'
    Layout: tất cả elements được căn đều theo chiều dọc trong panel.
    """
    W = 420

    # kích thước cố định theo mode
    _H = {'login': 360, 'register': 460}

    def __init__(self, screen_w, screen_h, mode='login'):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.mode     = mode
        self.msg      = ''
        self.msg_ok   = False
        self._open_t  = pygame.time.get_ticks()
        self._init_fonts()
        self._build()

    def _init_fonts(self):
        self.font_title = pygame.font.SysFont('segoeui', 22, bold=True)
        self.font_label = pygame.font.SysFont('segoeui', 13)
        self.font_input = pygame.font.SysFont('segoeui', 15)
        self.font_btn   = pygame.font.SysFont('segoeui', 16, bold=True)
        self.font_close = pygame.font.SysFont('segoeui', 15, bold=True)  # cache

    def _build(self):
        self.H  = self._H[self.mode]
        pad     = 32
        iw      = self.W - pad * 2
        ih      = 44          # chiều cao input
        btn_h   = 46
        gap     = 18          # khoảng cách giữa các field

        # --- tính tổng chiều cao nội dung để căn giữa ---
        title_h  = 30
        n_fields = 3 if self.mode == 'register' else 2
        # login:    title + user + pass + btn_submit + btn_switch
        # register: title + user + email + pass + btn_submit + btn_back
        n_btns   = 2   # submit + switch/back
        content_h = (title_h + gap
                     + n_fields * ih + (n_fields - 1) * (gap + 18)  # 18 = label height
                     + gap * 2
                     + n_btns * btn_h + gap)

        # vị trí panel
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        # điểm bắt đầu nội dung — căn giữa dọc
        start_y = my + (self.H - content_h) // 2

        cy = start_y

        # tiêu đề (lưu y để vẽ)
        self._title_y = cy
        cy += title_h + gap

        # fields
        field_step = ih + gap + 18   # ih + gap + label

        self.field_user = InputField(
            mx + pad, cy, iw, ih,
            label='Tên đăng nhập', placeholder='Nhập username...')
        cy += field_step

        if self.mode == 'register':
            self.field_email = InputField(
                mx + pad, cy, iw, ih,
                label='Email', placeholder='example@email.com')
            cy += field_step
        else:
            self.field_email = None

        self.field_pass = InputField(
            mx + pad, cy, iw, ih,
            label='Mật khẩu',
            placeholder='Tối thiểu 4 ký tự' if self.mode == 'register' else '••••••••',
            password=True)
        cy += ih + gap * 2

        # nút submit
        submit_color = (C_ACCENT, C_ACCENT_HOV) if self.mode == 'login' else (C_REG, C_REG_HOV)
        self.btn_submit = Button(
            mx + pad, cy, iw, btn_h,
            text='Đăng nhập' if self.mode == 'login' else 'Đăng ký',
            bg=submit_color[0], bg_hover=submit_color[1],
            text_color=(10, 10, 20), radius=12)
        cy += btn_h + gap

        # nút chuyển mode
        if self.mode == 'login':
            self.btn_switch = Button(
                mx + pad, cy, iw, btn_h,
                text='Chua co tai khoan? Dang ky',
                bg=(38, 38, 62), bg_hover=(50, 50, 80),
                text_color=C_REG, outline=False, radius=12)
        else:
            self.btn_switch = Button(
                mx + pad, cy, iw, btn_h,
                text='<  Quay lai dang nhap',
                bg=(38, 38, 62), bg_hover=(50, 50, 80),
                text_color=C_ACCENT, outline=False, radius=12)

        # nút đóng X (góc trên phải panel)
        self.btn_close = pygame.Rect(mx + self.W - 40, my + 14, 26, 26)

        # danh sách fields theo thứ tự Tab
        if self.mode == 'register':
            self._fields = [self.field_user, self.field_email, self.field_pass]
        else:
            self._fields = [self.field_user, self.field_pass]

        # focus field đầu tiên mặc định
        self._fields[0].active = True

        # timer hiển thị thông báo thành công trước khi chuyển modal
        self._success_timer = 0   # ms, đếm ngược

    # ---------------------------------------------------------------- #

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_close.collidepoint(event.pos):
                return 'close'
            if not self.panel_rect.collidepoint(event.pos):
                return 'close'
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return 'close'

        # Tab: chuyển focus giữa các field
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self._tab_focus()
            return None

        # Enter: submit nếu có field đang active
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if any(f.active for f in self._fields):
                return self._submit()

        for f in self._fields:
            f.handle_event(event)

        if self.btn_submit.handle_event(event):
            return self._submit()

        if self.btn_switch.handle_event(event):
            return 'switch_register' if self.mode == 'login' else 'switch_login'

        return None

    def _tab_focus(self):
        """Chuyển focus sang field tiếp theo theo vòng."""
        active_idx = -1
        for i, f in enumerate(self._fields):
            if f.active:
                active_idx = i
                break
        # tắt tất cả
        for f in self._fields:
            f.active = False
        # bật field tiếp theo
        next_idx = (active_idx + 1) % len(self._fields)
        self._fields[next_idx].active = True

    def _submit(self):
        import os, sys
        _ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
        if _ROOT not in sys.path:
            sys.path.insert(0, _ROOT)
        import DataSeverConfig as db

        u = self.field_user.text.strip()
        p = self.field_pass.text
        if not u:
            self.field_user.error = 'Vui long nhap ten dang nhap'
            return None
        if len(p) < 4:
            self.field_pass.error = 'Mat khau toi thieu 4 ky tu'
            return None

        if self.mode == 'register' and self.field_email:
            e = self.field_email.text.strip()
            if '@' not in e:
                self.field_email.error = 'Email khong hop le'
                return None
            res = db.register(u, e, p)
            if not res['ok']:
                self.msg    = res.get('error', 'Loi dang ky')
                self.msg_ok = False
                return None
            self.msg         = 'Dang ky thanh cong! Chuyen sang dang nhap...'
            self.msg_ok      = True
            self._success_timer = pygame.time.get_ticks() + 1800
            return None

        # login
        res = db.login(u, p)
        if not res['ok']:
            self.msg    = res.get('error', 'Sai ten dang nhap hoac mat khau')
            self.msg_ok = False
            return None
        self.msg    = 'Dang nhap thanh cong!'
        self.msg_ok = True
        return ('login', u, p)

    def tick(self):
        """
        Gọi mỗi frame. Trả về 'switch_login' khi timer đăng ký hết.
        """
        if self._success_timer and pygame.time.get_ticks() >= self._success_timer:
            self._success_timer = 0
            return 'switch_login'
        return None

    # ---------------------------------------------------------------- #

    def draw(self, surface):
        # update giữ backspace cho tất cả fields
        for f in self._fields:
            f.update()

        # overlay — chặn click ngoài
        ov = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        ov.fill(C_OVERLAY)
        surface.blit(ov, (0, 0))

        # scale-in animation
        elapsed = (pygame.time.get_ticks() - self._open_t) / 180.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3

        # luôn vẽ trực tiếp lên surface (không dùng tmp) để tránh crash set_clip
        self._draw_panel(surface, self.panel_rect.x, self.panel_rect.y, ease)

    def _draw_panel(self, surface, ox, oy, ease=1.0):
        # scale-in: thu nhỏ panel quanh tâm khi ease < 1
        if ease < 1.0:
            # clip vùng panel để tạo hiệu ứng scale mà không crash set_clip
            sw = max(1, int(self.W * ease))
            sh = max(1, int(self.H * ease))
            clip_x = ox + (self.W - sw) // 2
            clip_y = oy + (self.H - sh) // 2
            old_clip = surface.get_clip()
            surface.set_clip(pygame.Rect(clip_x, clip_y, sw, sh))
        else:
            old_clip = None

        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x
        dy = oy - self.panel_rect.y

        # shadow
        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 70))
        surface.blit(sh, (ox - 10, oy + 10))

        # nền
        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)

        # thanh accent trên cùng (màu theo mode)
        bar_color = C_ACCENT if self.mode == 'login' else C_REG
        pygame.draw.rect(surface, bar_color,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        # tiêu đề
        title_text = 'Đăng nhập' if self.mode == 'login' else 'Đăng ký tài khoản'
        title = self.font_title.render(title_text, True, bar_color)
        surface.blit(title, title.get_rect(
            centerx=ox + self.W // 2,
            y=oy + self._title_y - self.panel_rect.y + dy))

        # fields
        def draw_field(f):
            orig = f.rect.copy()
            f.rect = f.rect.move(dx, dy)
            f.draw(surface, self.font_label, self.font_input)
            f.rect = orig

        draw_field(self.field_user)
        draw_field(self.field_pass)
        if self.field_email:
            draw_field(self.field_email)

        # nút submit
        def draw_btn(b):
            orig = b.rect.copy()
            b.rect = b.rect.move(dx, dy)
            b.draw(surface, self.font_btn)
            b.rect = orig

        draw_btn(self.btn_submit)

        # đường kẻ phân cách
        sep_y = self.btn_submit.rect.move(dx, dy).bottom + 10
        pygame.draw.line(surface, C_BORDER,
                         (ox + 32, sep_y), (ox + self.W - 32, sep_y), 1)

        draw_btn(self.btn_switch)

        # nút đóng X — dùng font đã cache
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.font_close.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # thông báo
        if self.msg:
            c  = C_SUCCESS if self.msg_ok else C_ERROR
            ml = self.font_label.render(self.msg, True, c)
            surface.blit(ml, ml.get_rect(
                centerx=ox + self.W // 2,
                y=self.btn_switch.rect.move(dx, dy).bottom + 8))

        # restore clip sau scale-in
        if old_clip is not None:
            surface.set_clip(old_clip)


# ------------------------------------------------------------------ #
#  AVATAR BUTTON                                                       #
# ------------------------------------------------------------------ #

class AvatarButton:
    RADIUS = 22

    def __init__(self, screen_w, screen_h, margin=16):
        self.screen_w    = screen_w
        self.screen_h    = screen_h
        self.cx          = screen_w - margin - self.RADIUS
        self.cy          = margin + self.RADIUS
        self.logged_in   = False
        self.username    = ''
        self.email       = ''
        self.display_name = ''
        self.avatar_path  = ''
        self._avatar_surf = None   # ảnh tròn đã scale
        self._state      = 'idle'
        self._dropdown   = None
        self._modal      = None
        self._font_user  = pygame.font.SysFont('segoeui', 13)

    def update_from_user(self, user: dict):
        """Cập nhật thông tin từ user dict sau khi lưu."""
        self.username     = user.get('username', self.username)
        self.display_name = user.get('display_name', '') or self.username
        new_path = user.get('avatar_path', '')
        if new_path and new_path != self.avatar_path:
            self.avatar_path = new_path
            self._load_avatar(new_path)
        elif not new_path:
            self.avatar_path  = ''
            self._avatar_surf = None

    def _load_avatar(self, path):
        try:
            import os
            if not os.path.isfile(path):
                self._avatar_surf = None
                return
            raw  = pygame.image.load(path).convert_alpha()
            d    = self.RADIUS * 2
            scaled = pygame.transform.smoothscale(raw, (d, d))
            result = pygame.Surface((d, d), pygame.SRCALPHA)
            result.blit(scaled, (0, 0))
            mask = pygame.Surface((d, d), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 0))
            pygame.draw.circle(mask, (255, 255, 255, 255), (self.RADIUS, self.RADIUS), self.RADIUS)
            result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            self._avatar_surf = result
        except Exception:
            self._avatar_surf = None

    def handle_event(self, event):
        """
        Trả về:
          - ('login'|'register', u, p) khi xác thực xong
          - 'modal_active' khi modal đang mở (menu nên bỏ qua event này)
          - None trong các trường hợp khác
        """
        if self._state == 'idle':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if math.hypot(event.pos[0] - self.cx,
                              event.pos[1] - self.cy) <= self.RADIUS + 4:
                    self._open_dropdown()
            return None

        if self._state == 'dropdown':
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not self._dropdown.rect.collidepoint(event.pos):
                    if math.hypot(event.pos[0] - self.cx,
                                  event.pos[1] - self.cy) > self.RADIUS + 4:
                        self._state = 'idle'
                        self._dropdown = None
                        return None
            chosen = self._dropdown.handle_event(event)
            if chosen == 'Dang nhap':
                self._open_modal('login')
            elif chosen == 'Dang xuat':
                self.logged_in = False
                self.username  = ''
                self.email     = ''
                self._state    = 'idle'
                self._dropdown = None
                return 'logout'
            elif chosen == 'Thong tin':
                self._state    = 'idle'
                self._dropdown = None
                return 'user_info'
            elif chosen == 'Tuy chinh':
                self._state    = 'idle'
                self._dropdown = None
                return 'settings'
            return 'modal_active'

        if self._state == 'modal':
            # tick timer (đăng ký thành công → chuyển login)
            tick_result = self._modal.tick()
            if tick_result == 'switch_login':
                self._open_modal('login')
                return 'modal_active'

            result = self._modal.handle_event(event)
            if result == 'close':
                self._state = 'idle'
                self._modal = None
            elif result == 'switch_register':
                self._open_modal('register')
            elif result == 'switch_login':
                self._open_modal('login')
            elif isinstance(result, tuple):
                _, u, _ = result
                self.logged_in = True
                self.username  = u
                # lấy đầy đủ thông tin từ DB
                import os as _os, sys as _sys
                _root = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..')
                if _root not in _sys.path:
                    _sys.path.insert(0, _root)
                import DataSeverConfig as _db
                full = _db.get_user(u) or {}
                self.email        = full.get('email', '')
                self.display_name = full.get('display_name', '') or u
                ap = full.get('avatar_path', '')
                if ap:
                    self.avatar_path = ap
                    self._load_avatar(ap)
                self._state    = 'idle'
                self._modal    = None
                return result
            return 'modal_active'   # modal đang mở → chặn nút ngoài

        return None

    def draw(self, surface):
        if self._avatar_surf and self.logged_in:
            # vẽ ảnh tròn
            surface.blit(self._avatar_surf, (self.cx - self.RADIUS, self.cy - self.RADIUS))
            pygame.draw.circle(surface, C_ACCENT_HOV, (self.cx, self.cy), self.RADIUS, 2)
        else:
            bg = C_ACCENT if not self.logged_in else (60, 170, 100)
            _draw_avatar_icon(surface, self.cx, self.cy, self.RADIUS,
                              bg, C_ACCENT_HOV, self.logged_in, self.username)

        if self.logged_in:
            label = self.display_name or self.username
            lbl = self._font_user.render(label, True, C_TEXT_DIM)
            surface.blit(lbl, (self.cx - lbl.get_width() - self.RADIUS - 6,
                               self.cy - lbl.get_height() // 2))

        if self._state == 'dropdown' and self._dropdown:
            self._dropdown.draw(surface)

        if self._state == 'modal' and self._modal:
            self._modal.draw(surface)

    def _open_dropdown(self):
        self._dropdown = DropdownMenu(
            self.cx + self.RADIUS + 4,
            self.cy + self.RADIUS + 6,
            logged_in=self.logged_in,
            username=self.username,
            email=self.email,
            display_name=self.display_name,
            avatar_surf=self._avatar_surf,
        )
        self._state = 'dropdown'

    def _open_modal(self, mode):
        self._modal    = Modal(self.screen_w, self.screen_h, mode=mode)
        self._state    = 'modal'
        self._dropdown = None
