"""
UI/AlarmMess.py
Hệ thống thông báo tin nhắn mới — góc dưới phải màn hình.

Dùng:
    from AlarmMess import MessageNotifier
    notifier = MessageNotifier(screen_w, screen_h, user_id)
    notifier.start_polling()          # bắt đầu poll tin nhắn mới trong background

    # Trong game loop mỗi frame:
    notifier.update()                 # cập nhật animation
    notifier.draw(surface)            # vẽ thông báo
    notifier.handle_event(event)      # xử lý click (đóng thông báo)
"""

import pygame
import os, sys, threading, time

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
_ASSETS = os.path.join(os.path.dirname(_HERE), 'assets', 'sounds')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Sound ─────────────────────────────────────────────────────────────────────
_SOUND_PATH = os.path.join(_ASSETS, 'MessSound.mp3')
_sound      = None

def _play_sound():
    global _sound
    try:
        if _sound is None:
            pygame.mixer.init()
            _sound = pygame.mixer.Sound(_SOUND_PATH)
        _sound.play()
    except Exception:
        pass


# ── Toast notification ────────────────────────────────────────────────────────

class _Toast:
    """1 thông báo nhỏ."""
    DURATION = 4000   # ms hiển thị
    W, H     = 280, 64
    SLIDE_MS = 300    # ms animation trượt vào

    def __init__(self, sender: str, preview: str, screen_w: int, screen_h: int,
                 idx: int = 0, friend_data: dict = None):
        self.sender      = sender
        self.preview     = preview[:40] + ('...' if len(preview) > 40 else '')
        self.screen_w    = screen_w
        self.screen_h    = screen_h
        self.idx         = idx
        self.friend_data = friend_data or {}   # {'id', 'username', 'display_name'}
        self._born       = pygame.time.get_ticks()
        self._closed     = False
        self._clicked    = False   # True khi người dùng click vào body toast

        self._font_name    = pygame.font.SysFont('segoeui', 13, bold=True)
        self._font_preview = pygame.font.SysFont('segoeui', 12)
        self._font_close   = pygame.font.SysFont('segoeui', 12, bold=True)
        self._font_bell    = pygame.font.SysFont('segoeui', 18, bold=True)

    @property
    def alive(self):
        return not self._closed and (pygame.time.get_ticks() - self._born) < self.DURATION

    def close(self):
        self._closed = True

    def _progress(self):
        """0.0 → 1.0 trong DURATION ms."""
        return min(1.0, (pygame.time.get_ticks() - self._born) / self.DURATION)

    def _ease_in(self):
        t = min(1.0, (pygame.time.get_ticks() - self._born) / self.SLIDE_MS)
        return 1 - (1 - t) ** 3   # ease-out cubic

    def get_rect(self) -> pygame.Rect:
        margin = 12
        ease   = self._ease_in()
        # trượt từ phải vào
        x_off  = int((1 - ease) * (self.W + margin))
        x = self.screen_w - self.W - margin + x_off
        y = self.screen_h - margin - (self.H + 8) * (self.idx + 1)
        return pygame.Rect(x, y, self.W, self.H)

    def draw(self, surface):
        rect = self.get_rect()
        progress = self._progress()

        # fade out ở cuối
        alpha = 255
        if progress > 0.75:
            alpha = int(255 * (1 - (progress - 0.75) / 0.25))

        # nền
        bg = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(bg, (28, 28, 50, min(230, alpha)), bg.get_rect(), border_radius=12)
        pygame.draw.rect(bg, (80, 130, 255, min(200, alpha)), bg.get_rect(), 2, border_radius=12)

        # thanh màu trái
        bar = pygame.Surface((4, self.H - 16), pygame.SRCALPHA)
        bar.fill((100, 160, 255, alpha))
        bg.blit(bar, (8, 8))

        # icon chuông dùng emoji với font hỗ trợ
        for fname in ('Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', 'segoeui'):
            try:
                f_icon = pygame.font.SysFont(fname, 20)
                icon   = f_icon.render('🔔', True, (100, 160, 255))
                if icon.get_width() > 4:   # font hỗ trợ emoji
                    icon.set_alpha(alpha)
                    bg.blit(icon, (14, self.H // 2 - icon.get_height() // 2))
                    break
            except Exception:
                continue

        # tên người gửi
        name_lbl = self._font_name.render(self.sender, True, (220, 220, 255))
        name_lbl.set_alpha(alpha)
        bg.blit(name_lbl, (44, 12))

        # preview
        prev_lbl = self._font_preview.render(self.preview, True, (160, 160, 200))
        prev_lbl.set_alpha(alpha)
        bg.blit(prev_lbl, (44, 32))

        # nút X
        x_lbl = self._font_close.render('×', True, (150, 150, 180))
        x_lbl.set_alpha(alpha)
        bg.blit(x_lbl, (self.W - 18, 6))

        # progress bar dưới cùng
        bar_w = int(self.W * (1 - progress))
        if bar_w > 0:
            pb = pygame.Surface((bar_w, 3), pygame.SRCALPHA)
            pb.fill((100, 160, 255, alpha // 2))
            bg.blit(pb, (0, self.H - 3))

        surface.blit(bg, rect.topleft)

    def handle_click(self, pos) -> str | None:
        """
        Trả về:
          'close'     — click nút X
          'open_chat' — click vào body toast
          None        — không click vào toast
        """
        rect = self.get_rect()
        if not rect.collidepoint(pos):
            return None
        x_rect = pygame.Rect(rect.right - 22, rect.top + 2, 20, 20)
        if x_rect.collidepoint(pos):
            self.close()
            return 'close'
        # click vào body → mở chat
        self.close()
        return 'open_chat'


# ── MessageNotifier ───────────────────────────────────────────────────────────

class MessageNotifier:
    POLL_INTERVAL = 5   # giây poll 1 lần

    def __init__(self, screen_w: int, screen_h: int, user_id: int, friends: list = None):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.user_id   = user_id
        self.friends   = friends or []   # list of {'id', 'username', 'display_name'}
        self._toasts   = []
        self._lock     = threading.Lock()
        self._running  = False
        self._thread   = None
        # lưu id tin nhắn cuối đã biết cho mỗi friend
        self._last_msg_id: dict = {}

    def set_friends(self, friends: list):
        self.friends = friends

    def start_polling(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self):
        self._running = False

    def _poll_loop(self):
        # lần đầu: lấy id tin nhắn mới nhất để làm baseline (không thông báo)
        self._init_baseline()
        while self._running:
            time.sleep(self.POLL_INTERVAL)
            if not self._running:
                break
            self._check_new_messages()

    def _init_baseline(self):
        try:
            import DataSeverConfig as db
            for f in self.friends:
                msgs = db.get_messages(self.user_id, f['id'], limit=1)
                if msgs:
                    self._last_msg_id[f['id']] = msgs[-1]['id']
        except Exception:
            pass

    def _check_new_messages(self):
        try:
            import DataSeverConfig as db
            for f in self.friends:
                msgs = db.get_messages(self.user_id, f['id'], limit=5)
                if not msgs:
                    continue
                last_known = self._last_msg_id.get(f['id'], 0)
                new_msgs = [m for m in msgs
                            if m['id'] > last_known and m['from_id'] == f['id']]
                if new_msgs:
                    self._last_msg_id[f['id']] = msgs[-1]['id']
                    sender = f.get('display_name') or f.get('username', '?')
                    preview = new_msgs[-1].get('content', '')
                    self._add_toast(sender, preview, friend_data=f)
        except Exception:
            pass

    def _add_toast(self, sender: str, preview: str, friend_data: dict = None):
        _play_sound()
        with self._lock:
            if len(self._toasts) >= 3:
                self._toasts.pop(0)
            idx = len(self._toasts)
            self._toasts.append(_Toast(sender, preview, self.screen_w, self.screen_h,
                                       idx, friend_data=friend_data))

    def update(self):
        """Gọi mỗi frame — dọn toast đã hết hạn và cập nhật idx."""
        with self._lock:
            self._toasts = [t for t in self._toasts if t.alive]
            for i, t in enumerate(self._toasts):
                t.idx = i

    def draw(self, surface):
        with self._lock:
            for toast in self._toasts:
                toast.draw(surface)

    def handle_event(self, event, me: dict = None, surface=None):
        """
        me: {'id', 'username', 'display_name'} — thông tin người dùng hiện tại
        surface: pygame surface để vẽ ChatModal
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            with self._lock:
                toasts = list(self._toasts)
            for toast in toasts:
                action = toast.handle_click(event.pos)
                if action == 'open_chat' and me and surface and toast.friend_data:
                    try:
                        import sys, os
                        _ui = os.path.join(os.path.dirname(os.path.abspath(__file__)))
                        if _ui not in sys.path:
                            sys.path.insert(0, _ui)
                        from ChatModal import ChatModal
                        ChatModal(self.screen_w, self.screen_h, me, toast.friend_data).run(surface)
                    except Exception as e:
                        print(f'[AlarmMess] open chat error: {e}')
                    break

    def notify(self, sender: str, preview: str, friend_data: dict = None):
        """Gọi thủ công để test hoặc thêm thông báo từ ngoài."""
        self._add_toast(sender, preview, friend_data=friend_data)
