"""
UI/ChatModal.py
Modal chat giữa 2 người dùng.
"""

import pygame
import os, sys, time, threading

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS,
    InputField,
)

C_MY_MSG    = ( 50, 100, 200)
C_THEIR_MSG = ( 35,  35,  55)
C_SEND_BG   = ( 50, 130, 220)
C_SEND_HOV  = ( 80, 160, 255)


class ChatModal:
    W, H = 480, 520

    def __init__(self, screen_w, screen_h, me: dict, friend: dict):
        """
        me, friend: {'id', 'username', 'display_name'}
        """
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.me       = me
        self.friend   = friend
        self._result  = ...
        self._open_t  = 0
        self._messages = []
        self._scroll   = 0
        self._loading  = True

        self._init_fonts()
        self._build()
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        # load tin nhắn trong thread
        threading.Thread(target=self._load_messages, daemon=True).start()
        # auto-refresh mỗi 3 giây
        self._last_refresh = 0

    def _load_messages(self):
        try:
            import DataSeverConfig as db
            self._messages = db.get_messages(
                self.me['id'], self.friend['id'], limit=100)
        except Exception:
            self._messages = []
        self._loading = False
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self._scroll = max(0, len(self._messages) * 60 - (self.H - 160))

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 16, bold=True)
        self.f_msg    = pygame.font.SysFont('segoeui', 13)
        self.f_name   = pygame.font.SysFont('segoeui', 11)
        self.f_time   = pygame.font.SysFont('segoeui', 10)
        self.f_btn    = pygame.font.SysFont('segoeui', 13, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 12)
        self.f_input  = pygame.font.SysFont('segoeui', 13)

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        pad = 12

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)
        self._msg_area = pygame.Rect(mx + pad, my + 50, self.W - pad*2, self.H - 110)

        # input + nút gửi
        self.field_input = InputField(
            mx + pad, my + self.H - 52, self.W - pad*2 - 72, 40,
            placeholder='Nhap tin nhan...')
        self.field_input.active = True   # focus mặc định
        from LoginAndResgister import Button
        self.btn_send = Button(
            mx + self.W - pad - 64, my + self.H - 52, 64, 40,
            text='Gui', bg=C_SEND_BG, bg_hover=C_SEND_HOV,
            text_color=(255,255,255), radius=8)

    def run(self, surface):
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            now = time.time()
            if now - self._last_refresh > 3 and not self._loading:
                self._last_refresh = now
                threading.Thread(target=self._load_messages, daemon=True).start()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = None; break

                # đóng modal
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._result = None; break

                # Enter gửi
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._send()
                    continue   # không truyền Enter xuống field

                # scroll
                if event.type == pygame.MOUSEWHEEL:
                    if self._msg_area.collidepoint(pygame.mouse.get_pos()):
                        self._scroll = max(0, self._scroll - event.y * 20)

                # click đóng / ngoài panel
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_close.collidepoint(event.pos):
                        self._result = None; break
                    if not self.panel_rect.collidepoint(event.pos):
                        self._result = None; break

                # nút gửi
                if self.btn_send.handle_event(event):
                    self._send()
                    self.field_input.active = True   # giữ focus
                    continue

                # field input
                self.field_input.handle_event(event)

            self.field_input.update()
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

    def _send(self):
        text = self.field_input.text.strip()
        if not text:
            return
        try:
            import DataSeverConfig as db
            res = db.send_message(self.me['id'], self.friend['id'], text)
            if res.get('ok'):
                self.field_input.clear()
                self.field_input.active = True
                self._loading = False
                threading.Thread(target=self._load_messages, daemon=True).start()
            else:
                print(f'[Chat] send error: {res}')
        except Exception as e:
            print(f'[Chat] exception: {e}')

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        elapsed = (pygame.time.get_ticks() - self._open_t) / 180.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3
        ox, oy  = self.panel_rect.x, self.panel_rect.y
        if ease < 1.0:
            old = surface.get_clip()
            sw = max(1, int(self.W * ease)); sh = max(1, int(self.H * ease))
            surface.set_clip(pygame.Rect(ox+(self.W-sw)//2, oy+(self.H-sh)//2, sw, sh))
        else:
            old = None
        self._draw_panel(surface, ox, oy)
        if old is not None:
            surface.set_clip(old)

    def _draw_panel(self, surface, ox, oy):
        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x; dy = oy - self.panel_rect.y
        sh = pygame.Surface((self.W+20, self.H+20), pygame.SRCALPHA)
        sh.fill((0,0,0,80)); surface.blit(sh, (ox-10, oy+10))
        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ACCENT, pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        fname = self.friend.get('display_name') or self.friend.get('username', '?')
        title = self.f_title.render(f'Chat voi {fname}', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox+self.W//2, y=oy+14))

        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # vùng tin nhắn
        ma = self._msg_area.move(dx, dy)
        pygame.draw.rect(surface, (20, 20, 34), ma, border_radius=8)
        pygame.draw.rect(surface, C_BORDER, ma, 1, border_radius=8)

        old_clip = surface.get_clip()
        surface.set_clip(ma)
        self._draw_messages(surface, ma)
        surface.set_clip(old_clip)

        # input
        orig = self.field_input.rect.copy()
        self.field_input.rect = self.field_input.rect.move(dx, dy)
        self.field_input.draw(surface, self.f_label, self.f_input)
        self.field_input.rect = orig

        # nút gửi
        orig = self.btn_send.rect.copy()
        self.btn_send.rect = self.btn_send.rect.move(dx, dy)
        self.btn_send.draw(surface, self.f_btn)
        self.btn_send.rect = orig

    def _draw_messages(self, surface, ma):
        if self._loading:
            lbl = self.f_msg.render('Dang tai...', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(center=ma.center))
            return
        if not self._messages:
            lbl = self.f_msg.render('Chua co tin nhan nao.', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(center=ma.center))
            return

        pad   = 8
        row_h = 52
        total = len(self._messages) * row_h
        max_s = max(0, total - ma.h + pad)
        self._scroll = min(self._scroll, max_s)

        my_id = self.me['id']
        for i, msg in enumerate(self._messages):
            ry = ma.y + pad + i * row_h - self._scroll
            if ry + row_h < ma.y or ry > ma.bottom:
                continue

            is_me   = (msg['from_id'] == my_id)
            content = msg.get('content', '')
            sent_at = str(msg.get('sent_at', ''))[:16]

            # bubble
            max_w = ma.w - 80
            words = content.split()
            lines = []; line = ''
            for w in words:
                test = (line + ' ' + w).strip()
                if self.f_msg.size(test)[0] > max_w:
                    if line: lines.append(line)
                    line = w
                else:
                    line = test
            if line: lines.append(line)

            bub_w = min(max_w, max(self.f_msg.size(l)[0] for l in lines) + 20)
            bub_h = len(lines) * 18 + 14
            bub_x = ma.right - bub_w - pad if is_me else ma.x + pad
            bub_y = ry + 4
            bub_c = C_MY_MSG if is_me else C_THEIR_MSG

            pygame.draw.rect(surface, bub_c,
                             pygame.Rect(bub_x, bub_y, bub_w, bub_h), border_radius=10)
            for j, ln in enumerate(lines):
                lbl = self.f_msg.render(ln, True, C_TEXT)
                surface.blit(lbl, (bub_x + 10, bub_y + 7 + j * 18))

            # thời gian
            tl = self.f_time.render(sent_at[11:], True, C_TEXT_DIM)
            if is_me:
                surface.blit(tl, (bub_x - tl.get_width() - 4, bub_y + bub_h - tl.get_height()))
            else:
                surface.blit(tl, (bub_x + bub_w + 4, bub_y + bub_h - tl.get_height()))
