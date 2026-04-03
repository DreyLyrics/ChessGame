"""
UI/AdminUI.py
Modal quản trị dành cho tài khoản có role='admin'.
Tabs:
  - Quan ly tai khoan: tìm kiếm, xem danh sách user, ban (vĩnh viễn/có hạn), xóa
  - Quan ly tin nhan: xem tất cả tin nhắn, xóa tin nhắn
"""

import pygame
import os
import sys
import threading
from datetime import datetime, timedelta, timezone

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
C_INPUT_BG    = (25,  25,  45)
C_INPUT_FOCUS = (60,  60, 100)


def _role_color(role):
    if role == 'admin':  return C_ROLE_ADMIN
    if role == 'banned': return C_ROLE_BANNED
    return C_ROLE_USER


def _fmt_date(val):
    """Rút gọn timestamp thành dd/mm/yyyy."""
    if not val:
        return ''
    s = str(val)[:10]
    try:
        dt = datetime.strptime(s, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return s


# ── Ban Dialog ────────────────────────────────────────────────────────────────

class BanDialog:
    """Dialog nhỏ để chọn loại ban và thời gian."""
    W, H = 360, 260

    def __init__(self, screen_w, screen_h, username):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.username = username
        self.result   = ...   # None=cancel, dict=confirm

        ox = screen_w // 2 - self.W // 2
        oy = screen_h // 2 - self.H // 2
        self.rect = pygame.Rect(ox, oy, self.W, self.H)

        # loại ban
        self.ban_type = 'permanent'   # 'permanent' | 'timed'

        # input số ngày/giờ
        self.days_str  = '1'
        self.hours_str = '0'
        self._focus    = None   # 'days' | 'hours'

        self._init_fonts()
        self._build_rects(ox, oy)

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill((0, 0, 0, 160))

    def _init_fonts(self):
        self.f_title = pygame.font.SysFont('segoeui', 16, bold=True)
        self.f_lbl   = pygame.font.SysFont('segoeui', 13)
        self.f_btn   = pygame.font.SysFont('segoeui', 13, bold=True)
        self.f_small = pygame.font.SysFont('segoeui', 11)

    def _build_rects(self, ox, oy):
        self.rb_perm  = pygame.Rect(ox + 20, oy + 60, 14, 14)
        self.rb_timed = pygame.Rect(ox + 20, oy + 90, 14, 14)

        self.inp_days  = pygame.Rect(ox + 100, oy + 130, 70, 28)
        self.inp_hours = pygame.Rect(ox + 220, oy + 130, 70, 28)

        self.btn_ok     = pygame.Rect(ox + 20,        oy + self.H - 50, 150, 34)
        self.btn_cancel = pygame.Rect(ox + self.W - 170, oy + self.H - 50, 150, 34)

    def run(self, surface):
        clock = pygame.time.Clock()
        while self.result is ...:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.result = None
                    break
                self._handle(event)
            self._draw(surface)
            pygame.display.flip()
            clock.tick(60)
        return self.result

    def _handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.result = None
                return
            if event.key == pygame.K_TAB:
                self._focus = 'hours' if self._focus == 'days' else 'days'
                return
            if self._focus == 'days':
                self.days_str = self._edit_num(self.days_str, event)
            elif self._focus == 'hours':
                self.hours_str = self._edit_num(self.hours_str, event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.rb_perm.collidepoint(pos):
                self.ban_type = 'permanent'
            elif self.rb_timed.collidepoint(pos):
                self.ban_type = 'timed'
            elif self.inp_days.collidepoint(pos):
                self._focus = 'days'
            elif self.inp_hours.collidepoint(pos):
                self._focus = 'hours'
            elif self.btn_ok.collidepoint(pos):
                self._confirm()
            elif self.btn_cancel.collidepoint(pos):
                self.result = None
            else:
                self._focus = None

    def _edit_num(self, s, event):
        if event.key == pygame.K_BACKSPACE:
            return s[:-1] or '0'
        if event.unicode.isdigit():
            new = (s if s != '0' else '') + event.unicode
            return new[:4]
        return s

    def _confirm(self):
        if self.ban_type == 'permanent':
            self.result = {'ban_until': None}
        else:
            try:
                days  = int(self.days_str  or 0)
                hours = int(self.hours_str or 0)
            except ValueError:
                days, hours = 1, 0
            delta = timedelta(days=days, hours=hours)
            if delta.total_seconds() <= 0:
                delta = timedelta(hours=1)
            until = datetime.now(timezone.utc) + delta
            self.result = {'ban_until': until.isoformat()}

    def _draw(self, surface):
        surface.blit(self._overlay, (0, 0))
        ox, oy = self.rect.x, self.rect.y

        pygame.draw.rect(surface, C_PANEL, self.rect, border_radius=12)
        pygame.draw.rect(surface, C_BAN_RED, self.rect, 2, border_radius=12)

        # tiêu đề
        t = self.f_title.render(f'Ban: {self.username}', True, C_BAN_RED)
        surface.blit(t, t.get_rect(centerx=ox + self.W // 2, y=oy + 16))

        # radio permanent
        pygame.draw.circle(surface, C_BORDER, self.rb_perm.center, 7, 1)
        if self.ban_type == 'permanent':
            pygame.draw.circle(surface, C_BAN_RED, self.rb_perm.center, 4)
        lbl = self.f_lbl.render('Ban vinh vien', True, C_TEXT)
        surface.blit(lbl, (ox + 40, oy + 55))

        # radio timed
        pygame.draw.circle(surface, C_BORDER, self.rb_timed.center, 7, 1)
        if self.ban_type == 'timed':
            pygame.draw.circle(surface, C_ACCENT, self.rb_timed.center, 4)
        lbl2 = self.f_lbl.render('Ban co thoi han', True, C_TEXT)
        surface.blit(lbl2, (ox + 40, oy + 85))

        # inputs (chỉ hiện khi timed)
        if self.ban_type == 'timed':
            # label
            dl = self.f_small.render('Ngay:', True, C_TEXT_DIM)
            surface.blit(dl, (ox + 20, oy + 118))
            hl = self.f_small.render('Gio:', True, C_TEXT_DIM)
            surface.blit(hl, (ox + 140, oy + 118))

            for inp, val, key in [
                (self.inp_days,  self.days_str,  'days'),
                (self.inp_hours, self.hours_str, 'hours'),
            ]:
                bg = C_INPUT_FOCUS if self._focus == key else C_INPUT_BG
                pygame.draw.rect(surface, bg, inp, border_radius=6)
                pygame.draw.rect(surface, C_BORDER, inp, 1, border_radius=6)
                vl = self.f_lbl.render(val, True, C_TEXT)
                surface.blit(vl, vl.get_rect(center=inp.center))

            # preview
            try:
                days  = int(self.days_str  or 0)
                hours = int(self.hours_str or 0)
                until = datetime.now(timezone.utc) + timedelta(days=days, hours=hours)
                prev  = self.f_small.render(
                    f'Het han: {until.strftime("%d/%m/%Y %H:%M")} UTC', True, C_TEXT_DIM)
                surface.blit(prev, (ox + 20, oy + 168))
            except Exception:
                pass
        else:
            note = self.f_small.render('Tai khoan se bi khoa vinh vien.', True, C_TEXT_DIM)
            surface.blit(note, (ox + 20, oy + 130))

        # buttons
        mouse = pygame.mouse.get_pos()
        for btn, label, base, hov in [
            (self.btn_ok,     'Xac nhan Ban', C_BAN_RED,  C_BAN_HOV),
            (self.btn_cancel, 'Huy',          C_PANEL2,   (70, 70, 100)),
        ]:
            bg = hov if btn.collidepoint(mouse) else base
            pygame.draw.rect(surface, bg, btn, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, btn, 1, border_radius=8)
            bl = self.f_btn.render(label, True, C_TEXT)
            surface.blit(bl, bl.get_rect(center=btn.center))


# ── AdminModal ────────────────────────────────────────────────────────────────

class AdminModal:
    W, H = 760, 560

    def __init__(self, screen_w: int, screen_h: int, admin_username: str):
        self.screen_w       = screen_w
        self.screen_h       = screen_h
        self.admin_username = admin_username
        self._result        = ...
        self._open_t        = 0
        self._tab           = 'users'

        self._users         = []
        self._users_all     = []   # bản gốc để filter
        self._messages      = []
        self._loading       = False
        self._msg           = ''
        self._msg_ok        = False
        self._msg_t         = 0

        self._scroll_u      = 0
        self._scroll_m      = 0

        # search
        self._search_text   = ''
        self._search_focus  = False

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        self._load_data()

    # ── fonts ──────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 20, bold=True)
        self.f_tab    = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_hdr    = pygame.font.SysFont('segoeui', 12, bold=True)
        self.f_row    = pygame.font.SysFont('segoeui', 13)
        self.f_small  = pygame.font.SysFont('segoeui', 11)
        self.f_btn    = pygame.font.SysFont('segoeui', 12, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 13)

    # ── layout ─────────────────────────────────────────────────────────────────

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)
        self.btn_close  = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)
        self.btn_reload = pygame.Rect(mx + self.W - 68, my + 10, 26, 26)

        pad   = 20
        tab_w = (self.W - pad * 2 - 8) // 2
        self.tab_users_rect = pygame.Rect(mx + pad,             my + 46, tab_w, 32)
        self.tab_msgs_rect  = pygame.Rect(mx + pad + tab_w + 8, my + 46, tab_w, 32)

        # search bar (chỉ hiện ở tab users)
        self.search_rect = pygame.Rect(mx + pad, my + 86, self.W - pad * 2, 28)

        # list area (bắt đầu sau search bar)
        self.list_rect = pygame.Rect(mx + pad, my + 122, self.W - pad * 2, self.H - 122 - pad)

    # ── data ───────────────────────────────────────────────────────────────────

    def _load_data(self):
        self._loading = True
        threading.Thread(target=self._fetch_data, daemon=True).start()

    def _fetch_data(self):
        try:
            import DataSeverConfig as db
            self._users_all = db.admin_get_users()
            self._messages  = db.admin_get_messages(100)
        except Exception:
            self._users_all = []
            self._messages  = []
        self._apply_search()
        self._loading = False

    def _apply_search(self):
        q = self._search_text.strip().lower()
        if not q:
            self._users = list(self._users_all)
        else:
            self._users = [
                u for u in self._users_all
                if q in u.get('username', '').lower()
                or q in (u.get('email') or '').lower()
            ]
        self._scroll_u = 0

    # ── run ────────────────────────────────────────────────────────────────────

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

    # ── events ─────────────────────────────────────────────────────────────────

    def _handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._result = None
                return
            if self._search_focus and self._tab == 'users':
                if event.key == pygame.K_BACKSPACE:
                    self._search_text = self._search_text[:-1]
                elif event.unicode and len(self._search_text) < 40:
                    self._search_text += event.unicode
                self._apply_search()
                return

        if event.type == pygame.MOUSEWHEEL:
            if self._tab == 'users':
                self._scroll_u = max(0, self._scroll_u - event.y * 3)
            else:
                self._scroll_m = max(0, self._scroll_m - event.y * 3)

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._result = None; return
            if self.btn_reload.collidepoint(pos):
                self._load_data(); return
            if not self.panel_rect.collidepoint(pos):
                self._result = None; return
            if self.tab_users_rect.collidepoint(pos):
                self._tab = 'users'; return
            if self.tab_msgs_rect.collidepoint(pos):
                self._tab = 'messages'; return

            # search bar focus
            if self._tab == 'users' and self.search_rect.collidepoint(pos):
                self._search_focus = True
                return
            else:
                self._search_focus = False

            if self.list_rect.collidepoint(pos):
                if self._tab == 'users':
                    self._handle_user_click(pos)
                else:
                    self._handle_msg_click(pos)

    def _handle_user_click(self, pos):
        ROW_H = 40
        y0    = self.list_rect.y + 28 - self._scroll_u
        for i, u in enumerate(self._users):
            ry = y0 + i * ROW_H
            if ry + ROW_H < self.list_rect.y or ry > self.list_rect.bottom:
                continue
            row = pygame.Rect(self.list_rect.x, ry, self.list_rect.w, ROW_H - 2)
            if not row.collidepoint(pos):
                continue
            ban_btn  = pygame.Rect(row.right - 170, row.y + 7, 76, 26)
            del_btn  = pygame.Rect(row.right - 86,  row.y + 7, 76, 26)
            if ban_btn.collidepoint(pos):
                self._open_ban_dialog(u)
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

    # ── actions ────────────────────────────────────────────────────────────────

    def _open_ban_dialog(self, u):
        uname = u.get('username', '')
        if uname == self.admin_username:
            self._show_msg('Khong the ban chinh minh', False); return

        # lấy surface hiện tại
        surface = pygame.display.get_surface()
        dialog  = BanDialog(self.screen_w, self.screen_h, uname)
        res     = dialog.run(surface)
        if res is None:
            return

        ban_until = res.get('ban_until', None)

        def _do():
            import DataSeverConfig as db
            r = db.admin_ban_user(uname, ban_until)
            if r.get('ok'):
                u['role'] = 'banned'
                u['ban_until'] = ban_until
                if ban_until:
                    try:
                        dt = datetime.fromisoformat(ban_until)
                        label = dt.strftime('%d/%m/%Y %H:%M')
                    except Exception:
                        label = str(ban_until)
                    self._show_msg(f'Da ban {uname} den {label}', True)
                else:
                    self._show_msg(f'Da ban {uname} vinh vien', True)
            else:
                self._show_msg(r.get('error', 'Loi'), False)
        threading.Thread(target=_do, daemon=True).start()

    def _delete_user(self, u):
        uname = u.get('username', '')
        if uname == self.admin_username:
            self._show_msg('Khong the xoa chinh minh', False); return
        def _do():
            import DataSeverConfig as db
            res = db.admin_delete_user(uname)
            if res.get('ok'):
                self._users_all = [x for x in self._users_all if x.get('username') != uname]
                self._apply_search()
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
        self._msg_t  = pygame.time.get_ticks() + 3500

    # ── draw ───────────────────────────────────────────────────────────────────

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

        sh = pygame.Surface((self.W + 20, self.H + 20), pygame.SRCALPHA)
        sh.fill((0, 0, 0, 80))
        surface.blit(sh, (ox - 10, oy + 10))

        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ADMIN_GOLD,
                         pygame.Rect(ox, oy, self.W, 4), border_radius=16)

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

        # search bar (tab users)
        if self._tab == 'users':
            sr = self.search_rect.move(dx, dy)
            bg = C_INPUT_FOCUS if self._search_focus else C_INPUT_BG
            pygame.draw.rect(surface, bg, sr, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, sr, 1, border_radius=8)
            placeholder = self._search_text or '🔍  Tim kiem username, email...'
            tc = C_TEXT if self._search_text else C_TEXT_DIM
            sl = self.f_row.render(placeholder[:50], True, tc)
            surface.blit(sl, (sr.x + 8, sr.y + (sr.h - sl.get_height()) // 2))

        # list area clip
        lr = self.list_rect.move(dx, dy)
        old_clip = surface.get_clip()
        surface.set_clip(lr)

        if self._loading:
            t    = pygame.time.get_ticks() / 500.0
            dots = '.' * (int(t) % 4)
            lbl  = self.f_row.render(f'Dang tai{dots}', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(center=lr.center))
        elif self._tab == 'users':
            self._draw_users(surface, lr)
        else:
            self._draw_messages(surface, lr)

        surface.set_clip(old_clip)

        # thông báo
        if self._msg and pygame.time.get_ticks() < self._msg_t:
            c  = C_SUCCESS if self._msg_ok else C_ERROR
            ml = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(centerx=ox + self.W // 2, y=oy + self.H - 18))

    def _draw_users(self, surface, lr):
        ROW_H = 40
        # header — Username | Email | W/L/D | Role | Ngay tao | (buttons)
        hdr_y = lr.y + 4
        cols_hdr = [
            ('Username',  lr.x + 8),
            ('Email',     lr.x + 148),
            ('W/L/D',     lr.x + 318),
            ('Role',      lr.x + 390),
            ('Ngay tao',  lr.x + 460),
        ]
        for text, x in cols_hdr:
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
            un_lbl = self.f_row.render(u.get('username', '')[:16], True, C_TEXT)
            surface.blit(un_lbl, (lr.x + 8, cy - un_lbl.get_height() // 2))

            # email
            em_lbl = self.f_small.render((u.get('email') or '')[:20], True, C_TEXT_DIM)
            surface.blit(em_lbl, (lr.x + 148, cy - em_lbl.get_height() // 2))

            # W/L/D
            wld = f"{u.get('wins',0)}/{u.get('losses',0)}/{u.get('draws',0)}"
            wld_lbl = self.f_small.render(wld, True, C_TEXT_DIM)
            surface.blit(wld_lbl, (lr.x + 318, cy - wld_lbl.get_height() // 2))

            # role badge
            role = u.get('role', 'user')
            rc   = _role_color(role)
            rl   = self.f_small.render(role.upper(), True, rc)
            surface.blit(rl, (lr.x + 390, cy - rl.get_height() // 2))

            # ngày tạo
            created = _fmt_date(u.get('created_at', ''))
            cl = self.f_small.render(created, True, C_TEXT_DIM)
            surface.blit(cl, (lr.x + 460, cy - cl.get_height() // 2))

            # nút ban
            ban_btn = pygame.Rect(row.right - 170, ry + 7, 76, 26)
            ban_hov = ban_btn.collidepoint(mouse)
            ban_bg  = C_BAN_HOV if ban_hov else C_BAN_RED
            pygame.draw.rect(surface, ban_bg, ban_btn, border_radius=6)
            ban_lbl = self.f_btn.render('--banned', True, (255, 255, 255))
            surface.blit(ban_lbl, ban_lbl.get_rect(center=ban_btn.center))

            # nút xóa
            del_btn = pygame.Rect(row.right - 86, ry + 7, 76, 26)
            db_hov  = del_btn.collidepoint(mouse)
            db_bg   = C_DEL_HOV if db_hov else C_DEL_BG
            pygame.draw.rect(surface, db_bg, del_btn, border_radius=6)
            dl_lbl = self.f_btn.render('Xoa', True, (255, 255, 255))
            surface.blit(dl_lbl, dl_lbl.get_rect(center=del_btn.center))

        # max scroll
        total_h = len(self._users) * ROW_H
        self._scroll_u = min(self._scroll_u, max(0, total_h - (lr.h - 28)))

        cnt = self.f_small.render(
            f'Tong: {len(self._users)}/{len(self._users_all)} tai khoan', True, C_TEXT_DIM)
        surface.blit(cnt, (lr.x + 4, lr.bottom - 14))

    def _draw_messages(self, surface, lr):
        ROW_H = 52
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

            from_lbl = self.f_row.render((m.get('from_user') or '')[:14], True, C_ACCENT)
            surface.blit(from_lbl, (lr.x + 8, cy - from_lbl.get_height() // 2))

            to_lbl = self.f_row.render((m.get('to_user') or '')[:14], True, C_TEXT_DIM)
            surface.blit(to_lbl, (lr.x + 140, cy - to_lbl.get_height() // 2))

            content = m.get('content', '')
            if len(content) > 30:
                l1 = self.f_small.render(content[:30], True, C_TEXT)
                l2 = self.f_small.render(content[30:58] + ('...' if len(content) > 58 else ''), True, C_TEXT_DIM)
                surface.blit(l1, (lr.x + 280, ry + 8))
                surface.blit(l2, (lr.x + 280, ry + 24))
            else:
                cl = self.f_small.render(content, True, C_TEXT)
                surface.blit(cl, (lr.x + 280, cy - cl.get_height() // 2))

            sent = str(m.get('sent_at', ''))[:16]
            tl   = self.f_small.render(sent, True, C_TEXT_DIM)
            surface.blit(tl, (lr.x + 500, cy - tl.get_height() // 2))

            del_btn = pygame.Rect(row.right - 80, ry + (ROW_H - 26) // 2, 70, 26)
            db_hov  = del_btn.collidepoint(mouse)
            db_bg   = C_DEL_HOV if db_hov else C_DEL_BG
            pygame.draw.rect(surface, db_bg, del_btn, border_radius=6)
            dl_lbl = self.f_btn.render('Xoa', True, (255, 255, 255))
            surface.blit(dl_lbl, dl_lbl.get_rect(center=del_btn.center))

        total_h = len(self._messages) * ROW_H
        self._scroll_m = min(self._scroll_m, max(0, total_h - (lr.h - 28)))

        cnt = self.f_small.render(f'Tong: {len(self._messages)} tin nhan', True, C_TEXT_DIM)
        surface.blit(cnt, (lr.x + 4, lr.bottom - 14))
