"""
UI/AdminUI.py
Modal quản trị dành cho tài khoản có role='admin'.
Tabs:
  - Quan ly tai khoan: xem danh sách user, đổi role, xóa user
  - Quan ly tin nhan: xem tất cả tin nhắn, xóa tin nhắn
"""

import pygame
import os
import sys
import threading

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_TEXT, C_TEXT_DIM,
    C_ERROR, C_SUCCESS, C_OVERLAY, Button,
)

C_ADMIN_GOLD  = (255, 200, 50)
C_BAN_RED     = (200, 60,  60)
C_BAN_HOV     = (230, 80,  80)
C_ROLE_ADMIN  = (255, 180, 50)
C_ROLE_USER   = (100, 200, 140)
C_ROLE_BANNED = (200, 80,  80)
C_DEL_BG      = (160, 50,  50)
C_DEL_HOV     = (200, 70,  70)
C_ROW_ALT     = (30,  30,  50)


def _role_color(role):
    if role == 'admin':  return C_ROLE_ADMIN
    if role == 'banned': return C_ROLE_BANNED
    return C_ROLE_USER


class AdminModal:
    W, H = 700, 540

    def __init__(self, screen_w: int, screen_h: int, admin_username: str):
        self.screen_w       = screen_w
        self.screen_h       = screen_h
        self.admin_username = admin_username
        self._result        = ...
        self._open_t        = 0
        self._tab           = 'users'   # 'users' | 'messages'

        # data
        self._users    = []
        self._messages = []
        self._loading  = False
        self._msg      = ''
        self._msg_ok   = False
        self._msg_t    = 0

        # scroll
        self._scroll_u = 0
        self._scroll_m = 0

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        self._load_data()

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 20, bold=True)
        self.f_tab    = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_hdr    = pygame.font.SysFont('segoeui', 12, bold=True)
        self.f_row    = pygame.font.SysFont('segoeui', 13)
        self.f_small  = pygame.font.SysFont('segoeui', 11)
        self.f_btn    = pygame.font.SysFont('segoeui', 12, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 13)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        self.btn_close  = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        pad   = 20
        tab_w = (self.W - pad * 2 - 8) // 2
        self.tab_users_rect = pygame.Rect(mx + pad,           my + 46, tab_w, 32)
        self.tab_msgs_rect  = pygame.Rect(mx + pad + tab_w + 8, my + 46, tab_w, 32)

        # list area
        self.list_rect = pygame.Rect(mx + pad, my + 88, self.W - pad * 2, self.H - 88 - pad)

        # nút reload
        self.btn_reload = pygame.Rect(mx + self.W - 36 - 36, my + 10, 26, 26)

    # ── data loading ──────────────────────────────────────────────────────────

    def _load_data(self):
        self._loading = True
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            import DataSeverConfig as db
            self._users    = db.admin_get_users()
            self._messages = db.admin_get_messages(100)
        except Exception as e:
            self._users    = []
            self._messages = []
        self._loading = False

    # ── run ───────────────────────────────────────────────────────────────────

    def run(self, surface):
        self._result = ...
        self._open_t = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        while self._result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._result = None
                    break
                self._handle(event)
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)
        return self._result

    # ── events ────────────────────────────────────────────────────────────────

    def _handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._result = None
            return

        if event.type == pygame.MOUSEWHEEL:
            if self._tab == 'users':
                self._scroll_u = max(0, self._scroll_u - event.y * 3)
            else:
                self._scroll_m = max(0, self._scroll_m - event.y * 3)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._result = None
                return
            if self.btn_reload.collidepoint(pos):
                self._load_data()
                return
            if not self.panel_rect.collidepoint(pos):
                self._result = None
                return
            if self.tab_users_rect.collidepoint(pos):
                self._tab = 'users'; return
            if self.tab_msgs_rect.collidepoint(pos):
                self._tab = 'messages'; return

            # click trong list
            if self.list_rect.collidepoint(pos):
                if self._tab == 'users':
                    self._handle_user_click(pos)
                else:
                    self._handle_msg_click(pos)

    def _handle_user_click(self, pos):
        ROW_H = 38
        y0    = self.list_rect.y + 28 - self._scroll_u
        for i, u in enumerate(self._users):
            ry = y0 + i * ROW_H
            if ry + ROW_H < self.list_rect.y or ry > self.list_rect.bottom:
                continue
            row = pygame.Rect(self.list_rect.x, ry, self.list_rect.w, ROW_H - 2)
            if not row.collidepoint(pos):
                continue
            # nút role toggle
            role_btn = pygame.Rect(row.right - 160, row.y + 6, 70, 26)
            del_btn  = pygame.Rect(row.right - 80,  row.y + 6, 70, 26)
            if role_btn.collidepoint(pos):
                self._toggle_role(u)
            elif del_btn.collidepoint(pos):
                self._delete_user(u)
            break

    def _handle_msg_click(self, pos):
        ROW_H = 52
        y0    = self.list_rect.y + 28 - self._scroll_m
        for i, m in enumerate(self._messages):
            ry = y0 + i * ROW_H
            if ry + ROW_H < self.list_rect.y or ry > self.list_rect.bottom:
                continue
            row = pygame.Rect(self.list_rect.x, ry, self.list_rect.w, ROW_H - 2)
            if not row.collidepoint(pos):
                continue
            del_btn = pygame.Rect(row.right - 80, row.y + (ROW_H - 26) // 2, 70, 26)
            if del_btn.collidepoint(pos):
                self._delete_message(m)
            break

    def _toggle_role(self, u):
        uname = u.get('username', '')
        if uname == self.admin_username:
            self._show_msg('Khong the doi role cua chinh minh', False); return
        cur_role = u.get('role', 'user')
        new_role = 'user' if cur_role == 'admin' else ('admin' if cur_role == 'banned' else 'banned')
        def _do():
            import DataSeverConfig as db
            res = db.admin_set_role(uname, new_role)
            if res.get('ok'):
                u['role'] = new_role
                self._show_msg(f'Da doi {uname} → {new_role}', True)
            else:
                self._show_msg(res.get('error', 'Loi'), False)
        threading.Thread(target=_do, daemon=True).start()

    def _delete_user(self, u):
        uname = u.get('username', '')
        if uname == self.admin_username:
            self._show_msg('Khong the xoa chinh minh', False); return
        def _do():
            import DataSeverConfig as db
            res = db.admin_delete_user(uname)
            if res.get('ok'):
                self._users = [x for x in self._users if x.get('username') != uname]
                self._show_msg(f'Da xoa {uname}', True)
            else:
                self._show_msg(res.get('error', 'Loi'), False)
        threading.Thread(target=_do, daemon=True).start()

    def _delete_message(self, m):
        mid = m.get('id', 0)
        def _do():
            import DataSeverConfig as db
            res = db.admin_delete_message(mid)
            if res.get('ok'):
                self._messages = [x for x in self._messages if x.get('id') != mid]
                self._show_msg('Da xoa tin nhan', True)
            else:
                self._show_msg(res.get('error', 'Loi'), False)
        threading.Thread(target=_do, daemon=True).start()

    def _show_msg(self, text, ok):
        self._msg    = text
        self._msg_ok = ok
        self._msg_t  = pygame.time.get_ticks() + 3000

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        elapsed = (pygame.time.get_ticks() - self._open_t) / 200.0
        ease    = 1 - (1 - min(1.0, elapsed)) ** 3
        ox, oy  = self.panel_rect.x, self.panel_rect.y

        if ease < 1.0:
            sw = max(1, int(self.W * ease))
            sh = max(1, int(self.H * ease))
            old = surface.get_clip()
            surface.set_clip(pygame.Rect(
                ox + (self.W - sw) // 2, oy + (self.H - sh) // 2, sw, sh))
        else:
            old = None

        self._draw_panel(surface, ox, oy)

        if old is not None:
            surface.set_clip(old)

    def _draw_panel(self, surface, ox, oy):
        pr = pygame.Rect(ox, oy, self.W, self.H)
        dx = ox - self.panel_rect.x
        dy = oy - self.panel_rect.y

        # shadow
        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 80))
        surface.blit(sh, (ox - 10, oy + 10))

        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ADMIN_GOLD,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        # tiêu đề
        title = self.f_title.render('⚙  Quan tri he thong', True, C_ADMIN_GOLD)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 12))

        # nút đóng
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # nút reload
        rr = self.btn_reload.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, rr.center, 13)
        pygame.draw.circle(surface, C_BORDER, rr.center, 13, 1)
        rl = self.f_label.render('↺', True, C_ACCENT)
        surface.blit(rl, rl.get_rect(center=rr.center))

        # tabs
        for tab_id, rect, label in [
            ('users',    self.tab_users_rect, '👤  Tai khoan'),
            ('messages', self.tab_msgs_rect,  '💬  Tin nhan'),
        ]:
            r   = rect.move(dx, dy)
            act = (self._tab == tab_id)
            bg  = C_ADMIN_GOLD if act else C_PANEL2
            tc  = (10, 10, 20) if act else C_TEXT_DIM
            pygame.draw.rect(surface, bg, r, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=8)
            lbl = self.f_tab.render(label, True, tc)
            surface.blit(lbl, lbl.get_rect(center=r.center))

        # list area clip
        lr = self.list_rect.move(dx, dy)
        old_clip = surface.get_clip()
        surface.set_clip(lr)

        if self._loading:
            t = pygame.time.get_ticks() / 500.0
            dots = '.' * (int(t) % 4)
            lbl = self.f_row.render(f'Dang tai{dots}', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(center=lr.center))
        elif self._tab == 'users':
            self._draw_users(surface, lr, dx, dy)
        else:
            self._draw_messages(surface, lr, dx, dy)

        surface.set_clip(old_clip)

        # thông báo
        if self._msg and pygame.time.get_ticks() < self._msg_t:
            c   = C_SUCCESS if self._msg_ok else C_ERROR
            ml  = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(
                centerx=ox + self.W // 2,
                y=oy + self.H - 18))

    def _draw_users(self, surface, lr, dx, dy):
        ROW_H = 38
        # header
        hdr_y = lr.y + 4
        for text, x in [('Username', lr.x + 8), ('Email', lr.x + 160),
                         ('W/L/D', lr.x + 360), ('Role', lr.x + 450), ('', lr.x + 530)]:
            lbl = self.f_hdr.render(text, True, C_TEXT_DIM)
            surface.blit(lbl, (x, hdr_y))
        pygame.draw.line(surface, C_BORDER, (lr.x, hdr_y + 16), (lr.right, hdr_y + 16), 1)

        y0    = lr.y + 28 - self._scroll_u
        mouse = pygame.mouse.get_pos()

        for i, u in enumerate(self._users):
            ry = y0 + i * ROW_H
            if ry + ROW_H < lr.y or ry > lr.bottom:
                continue

            row = pygame.Rect(lr.x, ry, lr.w, ROW_H - 2)
            bg  = C_ROW_ALT if i % 2 == 0 else C_PANEL
            pygame.draw.rect(surface, bg, row, border_radius=4)

            cy = ry + ROW_H // 2

            # username
            uname = u.get('username', '')
            un_lbl = self.f_row.render(uname[:18], True, C_TEXT)
            surface.blit(un_lbl, (lr.x + 8, cy - un_lbl.get_height() // 2))

            # email
            em = (u.get('email') or '')[:22]
            em_lbl = self.f_small.render(em, True, C_TEXT_DIM)
            surface.blit(em_lbl, (lr.x + 160, cy - em_lbl.get_height() // 2))

            # stats
            wld = f"{u.get('wins',0)}/{u.get('losses',0)}/{u.get('draws',0)}"
            wld_lbl = self.f_small.render(wld, True, C_TEXT_DIM)
            surface.blit(wld_lbl, (lr.x + 360, cy - wld_lbl.get_height() // 2))

            # role badge
            role = u.get('role', 'user')
            rc   = _role_color(role)
            rl   = self.f_small.render(role.upper(), True, rc)
            surface.blit(rl, (lr.x + 450, cy - rl.get_height() // 2))

            # nút đổi role (cycle: user→banned→admin→user)
            role_btn = pygame.Rect(row.right - 160, ry + 6, 70, 26)
            next_role = 'banned' if role == 'user' else ('admin' if role == 'banned' else 'user')
            rb_hov = role_btn.collidepoint(mouse)
            rb_bg  = (80, 80, 120) if rb_hov else (50, 50, 80)
            pygame.draw.rect(surface, rb_bg, role_btn, border_radius=6)
            rb_lbl = self.f_btn.render(f'→{next_role}', True, _role_color(next_role))
            surface.blit(rb_lbl, rb_lbl.get_rect(center=role_btn.center))

            # nút xóa
            del_btn = pygame.Rect(row.right - 80, ry + 6, 70, 26)
            db_hov  = del_btn.collidepoint(mouse)
            db_bg   = C_DEL_HOV if db_hov else C_DEL_BG
            pygame.draw.rect(surface, db_bg, del_btn, border_radius=6)
            dl_lbl = self.f_btn.render('Xoa', True, (255, 255, 255))
            surface.blit(dl_lbl, dl_lbl.get_rect(center=del_btn.center))

        # max scroll
        total_h = len(self._users) * ROW_H
        max_scroll = max(0, total_h - (lr.h - 28))
        self._scroll_u = min(self._scroll_u, max_scroll)

        # count
        cnt = self.f_small.render(f'Tong: {len(self._users)} tai khoan', True, C_TEXT_DIM)
        surface.blit(cnt, (lr.x + 4, lr.bottom - 14))

    def _draw_messages(self, surface, lr, dx, dy):
        ROW_H = 52
        # header
        hdr_y = lr.y + 4
        for text, x in [('Tu', lr.x + 8), ('Den', lr.x + 140),
                         ('Noi dung', lr.x + 280), ('Thoi gian', lr.x + 500)]:
            lbl = self.f_hdr.render(text, True, C_TEXT_DIM)
            surface.blit(lbl, (x, hdr_y))
        pygame.draw.line(surface, C_BORDER, (lr.x, hdr_y + 16), (lr.right, hdr_y + 16), 1)

        y0    = lr.y + 28 - self._scroll_m
        mouse = pygame.mouse.get_pos()

        for i, m in enumerate(self._messages):
            ry = y0 + i * ROW_H
            if ry + ROW_H < lr.y or ry > lr.bottom:
                continue

            row = pygame.Rect(lr.x, ry, lr.w, ROW_H - 2)
            bg  = C_ROW_ALT if i % 2 == 0 else C_PANEL
            pygame.draw.rect(surface, bg, row, border_radius=4)

            cy = ry + ROW_H // 2

            # from
            from_lbl = self.f_row.render((m.get('from_user') or '')[:14], True, C_ACCENT)
            surface.blit(from_lbl, (lr.x + 8, cy - from_lbl.get_height() // 2))

            # to
            to_lbl = self.f_row.render((m.get('to_user') or '')[:14], True, C_TEXT_DIM)
            surface.blit(to_lbl, (lr.x + 140, cy - to_lbl.get_height() // 2))

            # content — 2 dòng nếu dài
            content = m.get('content', '')
            if len(content) > 30:
                line1 = content[:30]
                line2 = content[30:58] + ('...' if len(content) > 58 else '')
                l1 = self.f_small.render(line1, True, C_TEXT)
                l2 = self.f_small.render(line2, True, C_TEXT_DIM)
                surface.blit(l1, (lr.x + 280, ry + 8))
                surface.blit(l2, (lr.x + 280, ry + 24))
            else:
                cl = self.f_small.render(content, True, C_TEXT)
                surface.blit(cl, (lr.x + 280, cy - cl.get_height() // 2))

            # thời gian
            sent = str(m.get('sent_at', ''))[:16]
            tl   = self.f_small.render(sent, True, C_TEXT_DIM)
            surface.blit(tl, (lr.x + 500, cy - tl.get_height() // 2))

            # nút xóa
            del_btn = pygame.Rect(row.right - 80, ry + (ROW_H - 26) // 2, 70, 26)
            db_hov  = del_btn.collidepoint(mouse)
            db_bg   = C_DEL_HOV if db_hov else C_DEL_BG
            pygame.draw.rect(surface, db_bg, del_btn, border_radius=6)
            dl_lbl = self.f_btn.render('Xoa', True, (255, 255, 255))
            surface.blit(dl_lbl, dl_lbl.get_rect(center=del_btn.center))

        # max scroll
        total_h = len(self._messages) * ROW_H
        max_scroll = max(0, total_h - (lr.h - 28))
        self._scroll_m = min(self._scroll_m, max_scroll)

        cnt = self.f_small.render(f'Tong: {len(self._messages)} tin nhan', True, C_TEXT_DIM)
        surface.blit(cnt, (lr.x + 4, lr.bottom - 14))
