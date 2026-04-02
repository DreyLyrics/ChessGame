"""
UI/menu.py  —  Menu chính ChessGamePlay  (fullscreen)
Chạy trực tiếp: python UI/menu.py
"""

import pygame
import sys
import os
import math

_HERE        = os.path.dirname(os.path.abspath(__file__))
_SRC         = os.path.join(os.path.dirname(_HERE), 'src')
_BOT_DIR     = os.path.join(os.path.dirname(_HERE), 'Bot')
_LOCAL_DIR   = os.path.join(os.path.dirname(_HERE), 'LocalBattle')
for _p in (_HERE, _SRC, _BOT_DIR, _LOCAL_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from LoginAndResgister import (
    AvatarButton, Button,
    C_BG, C_PANEL, C_BORDER, C_ACCENT, C_ACCENT_HOV,
    C_TEXT, C_TEXT_DIM,
    _draw_rounded_rect,
)

C_TITLE      = (255, 215,  80)
C_TITLE_GLOW = (255, 160,  20)
C_PVP_BG     = ( 60, 130, 220)
C_PVP_HOV    = ( 90, 160, 255)
C_PVE_BG     = ( 50, 170, 110)
C_PVE_HOV    = ( 80, 210, 140)
C_LOCAL_BG   = (130,  80, 200)
C_LOCAL_HOV  = (160, 110, 230)
C_BTN_TXT    = (255, 255, 255)


class MenuScreen:

    def __init__(self, screen: pygame.Surface, avatar_btn=None):
        self.screen  = screen
        self.clock   = pygame.time.Clock()
        self.result  = None
        self.W, self.H = screen.get_size()

        self._init_fonts()
        self._build_widgets(avatar_btn)
        self._particles = [self._new_particle() for _ in range(60)]

    # ------------------------------------------------------------------ #
    #  FONTS — scale theo chiều cao màn hình                              #
    # ------------------------------------------------------------------ #

    def _init_fonts(self):
        s = self.H / 900          # scale factor
        self.font_app    = pygame.font.SysFont('georgia', int(58 * s), bold=True)
        self.font_sub    = pygame.font.SysFont('segoeui', int(18 * s))
        self.font_btn    = pygame.font.SysFont('segoeui', int(24 * s), bold=True)
        self.font_label  = pygame.font.SysFont('segoeui', int(14 * s))
        self.font_footer = pygame.font.SysFont('segoeui', int(13 * s))

    # ------------------------------------------------------------------ #
    #  WIDGETS                                                             #
    # ------------------------------------------------------------------ #

    def _build_widgets(self, avatar_btn=None):
        W, H  = self.W, self.H
        cx    = W // 2
        s     = H / 900

        btn_w = int(340 * s)
        btn_h = int(62 * s)
        gap   = int(52 * s)   # đủ chỗ cho label mô tả bên dưới mỗi nút

        total_h = btn_h * 3 + gap * 2
        start_y = H // 2 - total_h // 2 + int(20 * s)

        self.btn_pvp = Button(
            cx - btn_w // 2, start_y, btn_w, btn_h,
            text='PVP', bg=C_PVP_BG, bg_hover=C_PVP_HOV,
            text_color=C_BTN_TXT, radius=16)

        self.btn_pve = Button(
            cx - btn_w // 2, start_y + btn_h + gap, btn_w, btn_h,
            text='PVE', bg=C_PVE_BG, bg_hover=C_PVE_HOV,
            text_color=C_BTN_TXT, radius=16)

        self.btn_local = Button(
            cx - btn_w // 2, start_y + (btn_h + gap) * 2, btn_w, btn_h,
            text='Local', bg=C_LOCAL_BG, bg_hover=C_LOCAL_HOV,
            text_color=C_BTN_TXT, radius=16)

        if avatar_btn is not None:
            self.avatar_btn = avatar_btn
        else:
            self.avatar_btn = AvatarButton(W, H, margin=int(20 * s))

    # ------------------------------------------------------------------ #
    #  PARTICLES                                                           #
    # ------------------------------------------------------------------ #

    def _new_particle(self):
        import random
        return {
            'x':     random.randint(0, self.W),
            'y':     random.randint(0, self.H),
            'r':     random.uniform(1.2, 4.0),
            'speed': random.uniform(0.15, 0.6),
            'alpha': random.randint(30, 120),
        }

    def _update_particles(self, surface):
        import random
        for p in self._particles:
            p['y'] -= p['speed']
            if p['y'] < -10:
                p['y'] = self.H + 5
                p['x'] = random.randint(0, self.W)
            r = int(p['r'])
            if r < 1:
                continue
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (180, 200, 255, p['alpha']), (r, r), r)
            surface.blit(s, (int(p['x'] - r), int(p['y'] - r)))

    # ------------------------------------------------------------------ #
    #  DRAW                                                                #
    # ------------------------------------------------------------------ #

    def _draw_bg(self):
        W, H = self.W, self.H
        self.screen.fill(C_BG)
        # gradient nhẹ phía trên
        grad = pygame.Surface((W, H // 2), pygame.SRCALPHA)
        for i in range(H // 2):
            a = int(25 * (1 - i / (H // 2)))
            pygame.draw.line(grad, (80, 100, 180, a), (0, i), (W, i))
        self.screen.blit(grad, (0, 0))
        self._update_particles(self.screen)

    def _draw_title(self):
        t   = pygame.time.get_ticks() / 1000.0
        cx  = self.W // 2
        ty  = self.btn_pvp.rect.top - int(130 * self.H / 900)

        # double glow
        for offset, alpha in [(4, 25), (2, 45)]:
            glow = self.font_app.render('ChessGamePlay', True, C_TITLE_GLOW)
            glow.set_alpha(int(alpha + 20 * abs(math.sin(t * 1.2))))
            self.screen.blit(glow, glow.get_rect(center=(cx + offset, ty + offset)))

        title = self.font_app.render('ChessGamePlay', True, C_TITLE)
        self.screen.blit(title, title.get_rect(center=(cx, ty)))

        sub = self.font_sub.render('Chon che do choi', True, C_TEXT_DIM)
        self.screen.blit(sub, sub.get_rect(center=(cx, ty + int(56 * self.H / 900))))

        # đường kẻ trang trí
        lw = int(180 * self.W / 1920)
        ly = ty + int(76 * self.H / 900)
        pygame.draw.line(self.screen, C_BORDER, (cx - lw - 18, ly), (cx - 18, ly), 1)
        pygame.draw.line(self.screen, C_BORDER, (cx + 18, ly), (cx + lw + 18, ly), 1)
        pygame.draw.circle(self.screen, C_ACCENT, (cx, ly), 3)

    def _draw_btn_labels(self):
        descs = [
            ('⚔  Nguoi vs Nguoi', self.btn_pvp),
            ('🤖  Nguoi vs May',   self.btn_pve),
            ('🖥  Choi tren may nay', self.btn_local),
        ]
        for desc, btn in descs:
            lbl = self.font_label.render(desc, True, C_TEXT_DIM)
            self.screen.blit(lbl, lbl.get_rect(
                centerx=btn.rect.centerx, top=btn.rect.bottom + 8))

    def _draw_footer(self):
        lbl = self.font_footer.render(
            'ESC  thoat     M  ve menu     R  choi lai', True, C_TEXT_DIM)
        self.screen.blit(lbl, lbl.get_rect(
            centerx=self.W // 2, bottom=self.H - 12))

    def draw(self):
        self._draw_bg()
        self._draw_title()
        self.btn_pvp.draw(self.screen, self.font_btn)
        self.btn_pve.draw(self.screen, self.font_btn)
        self.btn_local.draw(self.screen, self.font_btn)
        self._draw_btn_labels()
        self.avatar_btn.draw(self.screen)
        self._draw_footer()

    # ------------------------------------------------------------------ #
    #  EVENTS                                                              #
    # ------------------------------------------------------------------ #

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            # avatar xử lý trước — nếu modal/dropdown đang mở thì chặn nút khác
            avatar_result = self.avatar_btn.handle_event(event)
            if avatar_result == 'modal_active':
                continue   # bỏ qua PVP/PVE/Local khi modal đang mở

            if avatar_result == 'user_info':
                # mở UserModal
                _UI_DIR = os.path.dirname(os.path.abspath(__file__))
                if _UI_DIR not in sys.path:
                    sys.path.insert(0, _UI_DIR)
                from UserModal import UserModal
                _ONLINE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Online')
                if _ONLINE_DIR not in sys.path:
                    sys.path.insert(0, _ONLINE_DIR)
                import DataSeverConfig as _db
                full_user = _db.get_user(self.avatar_btn.username) or {}
                user_data = {
                    'id':           full_user.get('id', 0),
                    'username':     full_user.get('username', self.avatar_btn.username),
                    'email':        full_user.get('email', self.avatar_btn.email),
                    'display_name': full_user.get('display_name', '') or self.avatar_btn.username,
                    'avatar_path':  full_user.get('avatar_path', ''),
                    'wins':         full_user.get('wins', 0),
                    'losses':       full_user.get('losses', 0),
                    'draws':        full_user.get('draws', 0),
                }
                modal  = UserModal(self.W, self.H, user_data)
                result = modal.run(self.screen)
                if result and isinstance(result, dict):
                    self.avatar_btn.update_from_user(result)
                continue

            if avatar_result == 'settings':
                _UI_DIR = os.path.dirname(os.path.abspath(__file__))
                if _UI_DIR not in sys.path:
                    sys.path.insert(0, _UI_DIR)
                from OpModal import OpModal
                modal  = OpModal(self.W, self.H, getattr(self, '_settings', {}))
                result = modal.run(self.screen)
                if result and isinstance(result, dict):
                    self._settings = result
                    # áp dụng âm lượng ngay
                    vol = result.get('volume', 80) / 100.0
                    try:
                        pygame.mixer.music.set_volume(vol)
                        for ch in range(pygame.mixer.get_num_channels()):
                            pygame.mixer.Channel(ch).set_volume(vol)
                    except Exception:
                        pass
                continue

            if self.btn_pvp.handle_event(event):
                # mở ModalPvp
                _UI_DIR = os.path.dirname(os.path.abspath(__file__))
                if _UI_DIR not in sys.path:
                    sys.path.insert(0, _UI_DIR)
                from ModalPvp import ModalPvp
                pvp_modal = ModalPvp(self.W, self.H)
                pvp_result = pvp_modal.run(self.screen)
                if pvp_result == 'matchmaking':
                    _ONLINE = os.path.join(os.path.dirname(_UI_DIR), 'Online')
                    if _ONLINE not in sys.path:
                        sys.path.insert(0, _ONLINE)
                    from OnMatch import launch_matchmaking
                    uname = self.avatar_btn.username if self.avatar_btn.logged_in else 'Guest'
                    def _back():
                        pass   # quay lại menu loop bình thường
                    launch_matchmaking(
                        self.screen, self.W, self.H, uname,
                        on_menu=_back,
                        apply_settings=lambda g: None)
                elif pvp_result == 'custom':
                    from ModalOpPvp import ModalOpPvp
                    uname    = self.avatar_btn.username     if self.avatar_btn.logged_in else 'Guest'
                    dname    = self.avatar_btn.display_name if self.avatar_btn.logged_in else 'Guest'
                    op_modal = ModalOpPvp(self.W, self.H, username=uname, display_name=dname)
                    op_result = op_modal.run(self.screen)
                    if op_result and isinstance(op_result, dict):
                        from CreateMatch import CreateMatch
                        client   = op_result.get('client')
                        pin      = op_result['pin']
                        host     = op_result['host']
                        # người join: host là chủ phòng, không phải mình
                        is_guest = (op_result.get('action') == 'join')
                        cm = CreateMatch(
                            self.W, self.H,
                            pin=pin,
                            host=host,
                            username=uname,
                            display_name=dname,
                            client=client)
                        cm_result = cm.run(self.screen)
                        if cm_result == 'start':
                            _ONLINE = os.path.join(os.path.dirname(_UI_DIR), 'Online')
                            if _ONLINE not in sys.path:
                                sys.path.insert(0, _ONLINE)
                            from OnMatch import _run_online_game
                            my_color = cm._game_color or 'white'
                            # host thấy guest, guest thấy host
                            opponent = cm._guest if not is_guest else host
                            _run_online_game(
                                self.screen, self.W, self.H,
                                uname, opponent, my_color, pin, client)
            if self.btn_pve.handle_event(event):
                self.result = 'pve'
            if self.btn_local.handle_event(event):
                self.result = 'local'

    # ------------------------------------------------------------------ #
    #  RUN                                                                 #
    # ------------------------------------------------------------------ #

    def run(self) -> str:
        while self.result is None:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        return self.result


# ------------------------------------------------------------------ #
#  ENTRY POINT                                                         #
# ------------------------------------------------------------------ #

def _handle_choice(choice, screen, avatar_btn=None, settings=None):
    settings = settings or {}

    def back_to_menu():
        pygame.display.set_caption('ChessGamePlay')
        s    = pygame.display.get_surface()
        menu = MenuScreen(s, avatar_btn=avatar_btn)
        if settings:
            menu._settings = settings
        c = menu.run()
        _handle_choice(c, s, avatar_btn=menu.avatar_btn,
                       settings=getattr(menu, '_settings', {}))

    def _apply_settings_to_game(game_obj):
        """Áp dụng settings vào Game instance."""
        if not settings:
            return
        try:
            game_obj.config.set_theme(settings.get('theme', 0))
            game_obj.config.set_volume(settings.get('volume', 80))
            game_obj.config.show_hints = settings.get('show_hints', True)
            game_obj._bg_dirty = True
        except Exception:
            pass

    if choice == 'local':
        pygame.display.set_caption('Chess  |  Local')
        from LocalBattle import launch_local
        launch_local(on_menu=back_to_menu, screen=screen,
                     apply_settings=_apply_settings_to_game)

    elif choice == 'pve':
        from ModalChessColor import ColorPickerModal
        modal       = ColorPickerModal(screen.get_width(), screen.get_height())
        human_color = modal.run(screen)

        if human_color is None:
            menu = MenuScreen(screen, avatar_btn=avatar_btn)
            if settings:
                menu._settings = settings
            c = menu.run()
            _handle_choice(c, screen, avatar_btn=menu.avatar_btn,
                           settings=getattr(menu, '_settings', {}))
            return

        label = 'Trang' if human_color == 'white' else 'Den'
        pygame.display.set_caption(f'Chess  |  vs Bot  (Ban = {label})')
        from BotBattle import launch_bot
        launch_bot(on_menu=back_to_menu, screen=screen, human_color=human_color,
                   apply_settings=_apply_settings_to_game)

    else:
        pygame.quit()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
    pygame.display.set_caption('ChessGamePlay')
    menu = MenuScreen(screen)
    choice = menu.run()
    _handle_choice(choice, screen, avatar_btn=menu.avatar_btn,
                   settings=getattr(menu, '_settings', {}))
