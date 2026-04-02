"""
UI/UserModal.py
Modal thông tin người dùng:
  - Avatar tuỳ chỉnh hình ảnh (chọn file từ ổ cứng)
  - Đổi tên hiển thị (display_name)
  - Thống kê: thắng / thua / hoà
  - Lịch sử ván đấu gần nhất
"""

import pygame
import os
import sys
import tkinter as tk
from tkinter import filedialog

_HERE = os.path.dirname(os.path.abspath(__file__))
_DB   = os.path.join(os.path.dirname(_HERE), 'DataBase')
for _p in (_HERE, _DB):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    C_PANEL, C_PANEL2, C_BORDER, C_ACCENT, C_REG,
    C_TEXT, C_TEXT_DIM, C_ERROR, C_SUCCESS, C_OVERLAY,
    InputField, Button,
)
import os, sys
_ONLINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Online')
if _ONLINE not in sys.path:
    sys.path.insert(0, _ONLINE)
import DataSeverConfig as db

C_HISTORY_WIN  = ( 72, 199, 142)
C_HISTORY_LOSS = (220,  80,  80)
C_HISTORY_DRAW = (150, 150, 200)

SUPPORTED_EXTS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')


def _open_file_dialog():
    """Mở hộp thoại chọn file ảnh, trả về đường dẫn hoặc None."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        title='Chon anh dai dien',
        filetypes=[
            ('Anh', '*.png *.jpg *.jpeg *.bmp *.gif *.webp'),
            ('Tat ca file', '*.*'),
        ]
    )
    root.destroy()
    return path if path else None


def _make_circle_surface(img_surface, diameter):
    """Cắt ảnh thành hình tròn."""
    size = (diameter, diameter)
    scaled = pygame.transform.smoothscale(img_surface, size)
    circle_surf = pygame.Surface(size, pygame.SRCALPHA)
    circle_surf.fill((0, 0, 0, 0))
    pygame.draw.circle(circle_surf, (255, 255, 255, 255),
                       (diameter // 2, diameter // 2), diameter // 2)
    # dùng circle_surf làm mask
    result = pygame.Surface(size, pygame.SRCALPHA)
    result.blit(scaled, (0, 0))
    # áp mask
    mask_surf = pygame.Surface(size, pygame.SRCALPHA)
    mask_surf.fill((0, 0, 0, 0))
    pygame.draw.circle(mask_surf, (255, 255, 255, 255),
                       (diameter // 2, diameter // 2), diameter // 2)
    result.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return result


class UserModal:
    W, H = 520, 460

    def __init__(self, screen_w, screen_h, user: dict):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.user     = dict(user)
        self._result  = ...
        self._open_t  = 0
        self._tab     = 'profile'
        self._msg     = ''
        self._msg_ok  = False

        self._init_fonts()
        self._build()

        self._overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)

        self._history     = db.get_match_history(user.get('id', 0), limit=15)
        self._saved_user  = None   # sẽ được set sau khi lưu thành công

        # load ảnh avatar nếu có
        self._avatar_surf = None
        saved_path = self.user.get('avatar_path', '')
        if saved_path and os.path.isfile(saved_path):
            self._load_avatar(saved_path)

    # ── fonts ─────────────────────────────────────────────────────────────────

    def _init_fonts(self):
        self.f_title  = pygame.font.SysFont('segoeui', 20, bold=True)
        self.f_label  = pygame.font.SysFont('segoeui', 13)
        self.f_input  = pygame.font.SysFont('segoeui', 15)
        self.f_btn    = pygame.font.SysFont('segoeui', 15, bold=True)
        self.f_stat   = pygame.font.SysFont('segoeui', 22, bold=True)
        self.f_stat_l = pygame.font.SysFont('segoeui', 12)
        self.f_hist   = pygame.font.SysFont('segoeui', 13)
        self.f_tab    = pygame.font.SysFont('segoeui', 14, bold=True)
        self.f_small  = pygame.font.SysFont('segoeui', 12)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        mx = self.screen_w // 2 - self.W // 2
        my = self.screen_h // 2 - self.H // 2
        self.panel_rect = pygame.Rect(mx, my, self.W, self.H)

        pad = 24
        iw  = self.W - pad * 2

        # nút đóng
        self.btn_close = pygame.Rect(mx + self.W - 36, my + 10, 26, 26)

        # nút chọn ảnh avatar — ngay dưới info user
        btn_w = 155
        self.btn_avatar = Button(
            mx + pad, my + 145, btn_w, 32,
            text='Chon anh dai dien',
            bg=C_PANEL2, bg_hover=(60, 60, 90),
            text_color=C_TEXT, radius=8)

        # tab buttons — cách nút chọn ảnh 14px
        tab_w = iw // 2
        self.tab_profile_rect = pygame.Rect(mx + pad,         my + 192, tab_w - 4, 34)
        self.tab_history_rect = pygame.Rect(mx + pad + tab_w, my + 192, tab_w - 4, 34)

        # field tên — cách tab 28px (đủ chỗ cho label)
        self.field_name = InputField(
            mx + pad, my + 252, iw, 40,
            label='Ten hien thi (co the doi)',
            placeholder=self.user.get('display_name', ''))
        self.field_name.text = self.user.get('display_name', '')

        # nút lưu — cách field 12px
        self.btn_save = Button(
            mx + pad, my + 308, iw, 42,
            text='Luu thay doi',
            bg=C_ACCENT, bg_hover=(130, 185, 255),
            text_color=(10, 10, 20), radius=10)

        self._avatar_path_new = None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _load_avatar(self, path):
        try:
            raw = pygame.image.load(path).convert_alpha()
            self._avatar_surf = _make_circle_surface(raw, 76)
        except Exception:
            self._avatar_surf = None

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
            self._result = self._saved_user   # trả về user đã lưu (hoặc None nếu chưa lưu)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            if self.btn_close.collidepoint(pos):
                self._result = self._saved_user
                return
            if not self.panel_rect.collidepoint(pos):
                self._result = self._saved_user
                return
            if self.tab_profile_rect.collidepoint(pos):
                self._tab = 'profile'; return
            if self.tab_history_rect.collidepoint(pos):
                self._tab = 'history'; return

        if self._tab == 'profile':
            self.field_name.handle_event(event)
            if self.btn_save.handle_event(event):
                self._save()
            if self.btn_avatar.handle_event(event):
                self._pick_avatar()

    def _pick_avatar(self):
        path = _open_file_dialog()
        if path:
            self._avatar_path_new = path
            self._load_avatar(path)
            self._msg    = 'Da chon anh. Nhan "Luu thay doi" de cap nhat.'
            self._msg_ok = True

    def _save(self):
        new_name = self.field_name.text.strip()
        if not new_name:
            self._msg    = 'Ten hien thi khong duoc de trong'
            self._msg_ok = False
            return

        # dùng path mới nếu vừa chọn, không thì giữ path cũ
        path_to_save = self._avatar_path_new or self.user.get('avatar_path') or None

        res = db.update_profile(
            self.user['username'],
            display_name=new_name,
            avatar_path=path_to_save,
        )
        if res['ok']:
            self.user['display_name'] = new_name
            if path_to_save:
                self.user['avatar_path'] = path_to_save
            self._avatar_path_new = None   # reset sau khi lưu
            self._msg        = 'Da luu thanh cong!'
            self._msg_ok     = True
            self._saved_user = dict(self.user)
        else:
            self._msg    = res.get('error', 'Loi')
            self._msg_ok = False

    # ── draw ──────────────────────────────────────────────────────────────────

    def _draw(self, surface):
        self.field_name.update()   # giữ backspace
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
        sh.fill((0, 0, 0, 70))
        surface.blit(sh, (ox - 10, oy + 10))

        pygame.draw.rect(surface, C_PANEL, pr, border_radius=16)
        pygame.draw.rect(surface, C_BORDER, pr, 1, border_radius=16)
        pygame.draw.rect(surface, C_ACCENT, pygame.Rect(ox, oy, self.W, 4), border_radius=16)

        # tiêu đề
        title = self.f_title.render('Thong tin nguoi dung', True, C_ACCENT)
        surface.blit(title, title.get_rect(centerx=ox + self.W // 2, y=oy + 14))

        # nút đóng
        cr = self.btn_close.move(dx, dy)
        pygame.draw.circle(surface, C_PANEL2, cr.center, 13)
        pygame.draw.circle(surface, C_BORDER, cr.center, 13, 1)
        xl = self.f_label.render('x', True, C_TEXT_DIM)
        surface.blit(xl, xl.get_rect(center=cr.center))

        # ── avatar ──
        av_cx = ox + 55
        av_cy = oy + 90
        av_r  = 34

        if self._avatar_surf:
            surf = pygame.transform.smoothscale(self._avatar_surf, (av_r*2, av_r*2))
            surface.blit(surf, (av_cx - av_r, av_cy - av_r))
            pygame.draw.circle(surface, C_ACCENT, (av_cx, av_cy), av_r, 3)
        else:
            pygame.draw.circle(surface, (40, 100, 80), (av_cx, av_cy), av_r)
            pygame.draw.circle(surface, C_ACCENT,      (av_cx, av_cy), av_r, 3)
            uname = self.user.get('username', '?')
            af  = pygame.font.SysFont('segoeui', av_r, bold=True)
            al  = af.render(uname[0].upper(), True, (255, 255, 255))
            surface.blit(al, al.get_rect(center=(av_cx, av_cy)))

        # icon camera
        cam_cx = av_cx + av_r - 9
        cam_cy = av_cy + av_r - 9
        pygame.draw.circle(surface, C_PANEL2, (cam_cx, cam_cy), 9)
        pygame.draw.circle(surface, C_ACCENT,  (cam_cx, cam_cy), 9, 1)
        cam_lbl = self.f_small.render('📷', True, C_TEXT)
        surface.blit(cam_lbl, cam_lbl.get_rect(center=(cam_cx, cam_cy)))

        # tên + username + email — căn giữa dọc bên phải avatar
        tx   = ox + 100
        uname = self.user.get('username', '?')
        dn   = self.user.get('display_name') or uname
        dn_lbl = self.f_title.render(dn, True, C_TEXT)
        un_lbl = self.f_label.render(f'@{uname}', True, C_TEXT_DIM)
        em_lbl = self.f_label.render(self.user.get('email', ''), True, C_TEXT_DIM)
        surface.blit(dn_lbl, (tx, oy + 62))
        surface.blit(un_lbl, (tx, oy + 88))
        surface.blit(em_lbl, (tx, oy + 106))

        # ── nút chọn ảnh ──
        orig = self.btn_avatar.rect.copy()
        self.btn_avatar.rect = self.btn_avatar.rect.move(dx, dy)
        self.btn_avatar.draw(surface, self.f_small)
        self.btn_avatar.rect = orig

        # tên file đang chọn
        path_to_show = self._avatar_path_new or self.user.get('avatar_path', '')
        if path_to_show:
            fname = os.path.basename(path_to_show)
            if len(fname) > 28:
                fname = '...' + fname[-25:]
            fl = self.f_small.render(fname, True, C_TEXT_DIM)
            surface.blit(fl, (ox + 24 + 163, oy + 152))

        # ── tabs ──
        for tab_id, rect, label in [
            ('profile', self.tab_profile_rect, 'Ho so'),
            ('history', self.tab_history_rect, 'Lich su'),
        ]:
            r   = rect.move(dx, dy)
            act = (self._tab == tab_id)
            bg  = C_ACCENT if act else C_PANEL2
            tc  = (10, 10, 20) if act else C_TEXT_DIM
            pygame.draw.rect(surface, bg, r, border_radius=8)
            pygame.draw.rect(surface, C_BORDER, r, 1, border_radius=8)
            lbl = self.f_tab.render(label, True, tc)
            surface.blit(lbl, lbl.get_rect(center=r.center))

        # ── nội dung tab ──
        content_y = oy + 236
        if self._tab == 'profile':
            self._draw_profile_tab(surface, ox, oy, dx, dy, content_y)
        else:
            self._draw_history_tab(surface, ox, oy, dx, dy, content_y)

    def _draw_profile_tab(self, surface, ox, oy, dx, dy, cy):
        orig = self.field_name.rect.copy()
        self.field_name.rect = self.field_name.rect.move(dx, dy)
        self.field_name.draw(surface, self.f_label, self.f_input)
        self.field_name.rect = orig

        orig = self.btn_save.rect.copy()
        self.btn_save.rect = self.btn_save.rect.move(dx, dy)
        self.btn_save.draw(surface, self.f_btn)
        self.btn_save.rect = orig

        if self._msg:
            c   = C_SUCCESS if self._msg_ok else C_ERROR
            ml  = self.f_label.render(self._msg, True, c)
            surface.blit(ml, ml.get_rect(
                centerx=ox + self.W // 2,
                y=self.btn_save.rect.move(dx, dy).bottom + 6))

    def _draw_history_tab(self, surface, ox, oy, dx, dy, cy):
        # ── thống kê ──
        stat_y = cy
        for i, (label, key, color) in enumerate([
            ('Thang', 'wins',   C_REG),
            ('Thua',  'losses', (220, 80, 80)),
            ('Hoa',   'draws',  (150, 150, 200)),
        ]):
            sx = ox + 28 + i * 170
            val = str(self.user.get(key, 0))
            v_lbl = self.f_stat.render(val, True, color)
            l_lbl = self.f_stat_l.render(label, True, C_TEXT_DIM)
            surface.blit(v_lbl, (sx, stat_y))
            surface.blit(l_lbl, (sx, stat_y + v_lbl.get_height() + 2))

        # ── lịch sử ──
        list_y = cy + 52
        if not self._history:
            lbl = self.f_label.render('Chua co lich su van dau.', True, C_TEXT_DIM)
            surface.blit(lbl, lbl.get_rect(centerx=ox + self.W // 2, y=list_y + 10))
            return

        row_h   = 26
        clip_r  = pygame.Rect(ox + 20, list_y, self.W - 40, self.H - (list_y - oy) - 16)
        old_clip = surface.get_clip()
        surface.set_clip(clip_r)

        for i, m in enumerate(self._history):
            ry = list_y + i * row_h
            if ry > list_y + clip_r.height:
                break
            bg = (28, 28, 44) if i % 2 == 0 else (32, 32, 52)
            pygame.draw.rect(surface, bg,
                             pygame.Rect(ox + 20, ry, self.W - 40, row_h - 2))

            res    = m['result']
            rc     = C_HISTORY_WIN if res == 'win' else (
                     C_HISTORY_LOSS if res == 'loss' else C_HISTORY_DRAW)
            res_lbl = self.f_hist.render(res.upper(), True, rc)
            surface.blit(res_lbl, (ox + 24, ry + 5))

            opp_lbl = self.f_hist.render(f"vs {m['opponent']}", True, C_TEXT)
            surface.blit(opp_lbl, (ox + 80, ry + 5))

            col_lbl = self.f_hist.render(
                'Trang' if m['color'] == 'white' else 'Den', True, C_TEXT_DIM)
            surface.blit(col_lbl, (ox + 220, ry + 5))

            mv_lbl = self.f_hist.render(f"{m['moves']} nuoc", True, C_TEXT_DIM)
            surface.blit(mv_lbl, (ox + 300, ry + 5))

            date = str(m['played_at'])[:10]
            dt_lbl = self.f_hist.render(date, True, C_TEXT_DIM)
            surface.blit(dt_lbl, (ox + 390, ry + 5))

        surface.set_clip(old_clip)
