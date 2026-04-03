"""
UI/FriendModal.py
Modal quản lý bạn bè:
  - Tab "Ban be": danh sách bạn bè đã accepted
  - Tab "Loi moi": lời mời đang chờ (chấp nhận / từ chối)
  - Tab "Tim kiem": tìm user theo username và gửi lời mời
"""

import pygame
import os, sys

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR,
    InputField, Button,
)

C_ACCEPT = ( 50, 160, 100)
C_REJECT = (160,  50,  50)
C_REMOVE = ( 80,  80, 110)


class FriendModal:
    W, H = 500, 480

    def __init__(self, screen_w, screen_h, user: dict):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.user     = user          # {'id', 'username', 'display_name', ...}
        self._result  = ...
        self._open_t  = 0
        self._tab     = 'friends'     # 'friends' | 'requests' | 'search'
        self._msg     = ''
        self._msg_ok  = False

        self._friends  = []
        self._requests = []
        self._search_results = []

        self._init_fonts()
        self._build()
        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)
        self._load_data()

    def _load_data(self):
        try:
            import DataSeverConfig as db
            uid = self.user.get('id', 0)
            self._friends  = db.get_friends(uid)
            self._requests = db.get_pending_requests(uid)
        except Exception:
            pass

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 18, bold=True)
        self.f_tab   = pygame.font.SysFont('segoeui', 13, bold=True)
        self.f_name  = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_sub   = pygame.font.SysFont('segoeui', 12)
        self.f_btn   = pygame.font.SysFont('segoeui', 12, bold=True)
        self.f_label = pygame.font.SysFont('segoeui', 12)
        self.f_input = pygame.font.SysFont('segoeui', 14)

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        pad = 20; iw = self.W - pad * 2

        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        # tabs
        tab_w = iw // 3
        self.tab_rects = {
            'friends':  pygame.Rect(mx + pad,              my + 46, tab_w - 4, 30),
            'requests': pygame.Rect(mx + pad + tab_w,      my + 46, tab_w - 4, 30),
            'search':   pygame.Rect(mx + pad + tab_w * 2,  my + 46, tab_w - 4, 30),
        }

        # search field
        self.field_search = InputField(
            mx + pad, my + 90, iw - 90, 36,
            placeholder='Nhap username...')
        self.btn_search = Button(
            mx + pad + iw - 82, my + 90, 82, 36,
            text='Tim kiem', bg=C_ACCENT, bg_hover=C_ACCENT_HOV,
            text_color=(10,10,20), radius=8)

        self._list_rect = pygame.Rect(mx + pad, my + 140, iw, self.H - 160)

    def run(self, surface) -> None:
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._result = None
                self._handle(event)
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)

    def _handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._result = None; return
            if not self.panel_rect.collidepoint(pos):
                self._result = None; return
            for tab_id, rect in self.tab_rects.items():
                if rect.collidepoint(pos):
                    self._tab = tab_id
                    self._msg = ''
                    return
            # click nút trong danh sách
            self._handle_list_click(pos)

        if self._tab == 'search':
            self.field_search.handle_event(event)
            if self.btn_search.handle_event(event):
                self._do_search()

    def _handle_list_click(self, pos):
        import DataSeverConfig as db
        uid  = self.user.get('id', 0)
        lr   = self._list_rect
        row_h = 52

        if self._tab == 'friends':
            for i, f in enumerate(self._friends):
                ry = lr.y + i * row_h
                btn_chat = pygame.Rect(lr.right - 162, ry + 12, 72, 28)
                btn_r    = pygame.Rect(lr.right - 82,  ry + 12, 72, 28)
                if btn_chat.collidepoint(pos):
                    # mở ChatModal
                    from ChatModal import ChatModal
                    ChatModal(self.screen_w, self.screen_h, self.user, f).run(
                        pygame.display.get_surface())
                    return
                if btn_r.collidepoint(pos):
                    res = db.remove_friend(uid, f['id'])
                    if res.get('ok'):
                        self._msg = f'Da xoa {f["display_name"] or f["username"]}'; self._msg_ok = True
                        self._load_data()
                    return

        elif self._tab == 'requests':
            for i, r in enumerate(self._requests):
                ry = lr.y + i * row_h
                btn_acc = pygame.Rect(lr.right - 160, ry + 12, 70, 28)
                btn_rej = pygame.Rect(lr.right - 82,  ry + 12, 70, 28)
                if btn_acc.collidepoint(pos):
                    res = db.accept_friend_request(uid, r['id'])
                    if res.get('ok'):
                        self._msg = f'Da chap nhan {r["display_name"] or r["username"]}'; self._msg_ok = True
                        self._load_data()
                    return
                if btn_rej.collidepoint(pos):
                    res = db.reject_friend_request(uid, r['id'])
                    if res.get('ok'):
                        self._msg = 'Da tu choi'; self._msg_ok = True
                        self._load_data()
                    return

        elif self._tab == 'search':
            for i, u in enumerate(self._search_results):
                ry = lr.y + i * row_h
                btn_add = pygame.Rect(lr.right - 90, ry + 12, 82, 28)
                if btn_add.collidepoint(pos):
                    res = db.send_friend_request(uid, u['username'])
                    self._msg    = res.get('error', 'Da gui loi moi!') if not res.get('ok') else 'Da gui loi moi!'
                    self._msg_ok = res.get('ok', False)
                    return

    def _do_search(self):
        q = self.field_search.text.strip()
        if not q:
            return
        try:
            import DataSeverConfig as db
            user = db.get_user(q)
            if user and user.get('id') != self.user.get('id'):
                self._search_results = [user]
                self._msg = ''
            else:
                self._search_results = []
                self._msg = 'Khong tim thay nguoi dung'; self._msg_ok = False
        except Exception:
            self._search_results = []

    # ── draw ──────────────────────────────────────────────────────────────────

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

        title = self.f_title.render('Ket ban', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox+self.W//2, y=oy+14))

        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # tabs
        tab_labels = {'friends': f'Ban be ({len(self._friends)})',
                      'requests': f'Loi moi ({len(self._requests)})',
                      'search': 'Tim kiem'}
        for tab_id, rect in self.tab_rects.items():
            r   = rect.move(dx, dy)
            act = (self._tab == tab_id)
            bg  = C_ACCENT if act else C_PANEL2
            tc  = (10,10,20) if act else C_TEXT_DIM
            pygame.draw.rect(surface, bg, r, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=8)
            lbl = self.f_tab.render(tab_labels[tab_id], True, tc)
            surface.blit(lbl, lbl.get_rect(center=r.center))

        # search field (chỉ hiện ở tab search)
        if self._tab == 'search':
            orig = self.field_search.rect.copy()
            self.field_search.rect = self.field_search.rect.move(dx, dy)
            self.field_search.draw(surface, self.f_label, self.f_input)
            self.field_search.rect = orig
            orig = self.btn_search.rect.copy()
            self.btn_search.rect = self.btn_search.rect.move(dx, dy)
            self.btn_search.draw(surface, self.f_btn)
            self.btn_search.rect = orig

        # thông báo
        if self._msg:
            c = C_SUCCESS if self._msg_ok else C_ERROR
            ml = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(centerx=ox+self.W//2, y=oy+self._list_rect.y-self.panel_rect.y-16))

        # danh sách
        lr  = self._list_rect.move(dx, dy)
        old_clip = surface.get_clip()
        surface.set_clip(lr)
        self._draw_list(surface, lr)
        surface.set_clip(old_clip)

    def _draw_list(self, surface, lr):
        row_h = 52
        mouse = pygame.mouse.get_pos()

        if self._tab == 'friends':
            items = self._friends
        elif self._tab == 'requests':
            items = self._requests
        else:
            items = self._search_results

        if not items:
            lbl = self.f_sub.render('Chua co du lieu.', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(centerx=lr.centerx, y=lr.y+20))
            return

        for i, item in enumerate(items[:8]):
            ry  = lr.y + i * row_h
            bg  = (28,28,44) if i%2==0 else (32,32,52)
            row = pygame.Rect(lr.x, ry, lr.w, row_h-2)
            pygame.draw.rect(surface, bg, row, border_radius=6)

            name = item.get('display_name') or item.get('username', '?')
            uname = item.get('username', '')
            nl = self.f_name.render(name, True, C_TEXT)
            ul = self.f_sub.render(f'@{uname}', True, C_TEXT_DIM)
            surface.blit(nl, (row.x+12, ry+8))
            surface.blit(ul, (row.x+12, ry+26))

            if self._tab == 'friends':
                btn_chat = pygame.Rect(row.right-162, ry+12, 72, 28)
                btn_r    = pygame.Rect(row.right-82,  ry+12, 72, 28)
                for btn, label, color in [
                    (btn_chat, 'Chat', (50,100,200)),
                    (btn_r,    'Xoa ban', C_REMOVE),
                ]:
                    bc = tuple(min(255,c+30) for c in color) if btn.collidepoint(mouse) else color
                    pygame.draw.rect(surface, bc, btn, border_radius=6)
                    bl = self.f_btn.render(label, True, C_TEXT)
                    surface.blit(bl, bl.get_rect(center=btn.center))

            elif self._tab == 'requests':
                btn_acc = pygame.Rect(row.right-160, ry+12, 70, 28)
                btn_rej = pygame.Rect(row.right-82,  ry+12, 70, 28)
                for btn, label, color in [(btn_acc,'Chap nhan',C_ACCEPT),(btn_rej,'Tu choi',C_REJECT)]:
                    bc = tuple(min(255,c+30) for c in color) if btn.collidepoint(mouse) else color
                    pygame.draw.rect(surface, bc, btn, border_radius=6)
                    bl = self.f_btn.render(label, True, (255,255,255))
                    surface.blit(bl, bl.get_rect(center=btn.center))

            elif self._tab == 'search':
                btn_add = pygame.Rect(row.right-90, ry+12, 82, 28)
                bc = (60,160,100) if btn_add.collidepoint(mouse) else (40,120,75)
                pygame.draw.rect(surface, bc, btn_add, border_radius=6)
                bl = self.f_btn.render('+ Ket ban', True, (255,255,255))
                surface.blit(bl, bl.get_rect(center=btn_add.center))
