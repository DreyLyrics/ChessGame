"""
UI/CreateMatch.py — Phòng chờ, kết nối Railway socket thật.
"""
import pygame, os, sys, time, math, threading

_HERE   = os.path.dirname(os.path.abspath(__file__))
_ONLINE = os.path.join(os.path.dirname(_HERE), 'Online')
for _p in (_HERE, _ONLINE):
    if _p not in sys.path: sys.path.insert(0, _p)

from LoginAndResgister import (C_PANEL, C_PANEL2, C_BORDER, C_ACCENT,
    C_TEXT, C_TEXT_DIM, C_OVERLAY, C_SUCCESS, C_ERROR, Button)
from socket_client import SocketClient

C_HOST_COLOR=(255,215,80); C_GUEST_COLOR=(100,200,255)
C_START_BG=(50,160,100);   C_START_HOV=(70,200,130); C_START_DIS=(40,60,40)
C_LEAVE_BG=(160,50,50);    C_LEAVE_HOV=(200,70,70)
C_INVITE_BG=(70,70,130);   C_INVITE_HOV=(100,100,180)


class CreateMatch:
    W, H = 480, 460

    def __init__(self, screen_w, screen_h, pin, host, username,
                 display_name='', client: SocketClient=None):
        self.screen_w=screen_w; self.screen_h=screen_h
        self.pin=pin; self.host=host; self.username=username
        self.display_name=display_name or username
        self.host_display=host   # sẽ được cập nhật từ DB hoặc room_joined
        self.is_host=(username==host)
        self._client=client
        self._result=...; self._open_t=0
        self._msg=''; self._msg_ok=False; self._msg_timer=0
        # nếu là guest → slot guest hiện tên mình ngay
        self._guest = '' if self.is_host else (display_name or username)
        self._game_color=None
        self._game_ready=threading.Event()
        self._init_fonts(); self._build()
        self._overlay=pygame.Surface((screen_w,screen_h),pygame.SRCALPHA)
        self._overlay.fill(C_OVERLAY)
        if client:
            pass   # game_started được xử lý trong run() poll loop
        # nếu là guest → load host_display từ DB ngay
        if not self.is_host:
            threading.Thread(target=self._load_host_display, daemon=True).start()

    def _wait_game_started(self):
        """Chờ game_started event dùng wait_for — không miss event."""
        data = self._client.wait_for('game_started', timeout=600)
        if data:
            self._game_color = data.get('color', 'white')
            self._game_ready.set()

    def _load_host_display(self):
        """Guest load host_display từ DB ngay khi vào phòng."""
        try:
            import DataSeverConfig as db
            rooms = db.get_open_rooms()
            for r in rooms:
                if r['pin'] == self.pin:
                    hd = r.get('host_display') or r.get('host', '')
                    if hd:
                        self.host_display = hd
                    break
        except Exception:
            pass

    def _poll_db_guest(self):
        """Poll DB để lấy tên guest mới nhất."""
        try:
            import DataSeverConfig as db
            rooms = db.get_open_rooms()
            for r in rooms:
                if r['pin'] == self.pin:
                    guest = r.get('guest_display') or r.get('guest', '')
                    if guest:
                        self._guest = guest
                    break
        except Exception:
            pass

    def _init_fonts(self):
        self.f_title=pygame.font.SysFont('segoeui',18,bold=True)
        self.f_pin=pygame.font.SysFont('segoeui',48,bold=True)
        self.f_label=pygame.font.SysFont('segoeui',13)
        self.f_player=pygame.font.SysFont('segoeui',15,bold=True)
        self.f_btn=pygame.font.SysFont('segoeui',14,bold=True)
        self.f_small=pygame.font.SysFont('segoeui',11)

    def _build(self):
        mx=self.screen_w//2-self.W//2; my=self.screen_h//2-self.H//2
        self.panel_rect=pygame.Rect(mx,my,self.W,self.H)
        pad=28; iw=self.W-pad*2
        self.btn_close=pygame.Rect(mx+self.W-36,my+10,26,26)
        self.btn_invite=Button(mx+pad,my+230,iw,40,text='📋  Sao chep ma PIN',
            bg=C_INVITE_BG,bg_hover=C_INVITE_HOV,text_color=C_TEXT,radius=10)
        self.btn_start=Button(mx+pad,my+284,iw,44,text='▶  Bat dau tran',
            bg=C_START_BG,bg_hover=C_START_HOV,text_color=(255,255,255),radius=12)
        self.btn_leave=Button(mx+pad,my+344,iw,40,text='✕  Thoat phong',
            bg=C_LEAVE_BG,bg_hover=C_LEAVE_HOV,text_color=(255,255,255),radius=10)

    def run(self, surface):
        self._result=...; self._open_t=pygame.time.get_ticks()
        clock=pygame.time.Clock()
        self._last_db_poll = 0.0

        while self._result is ...:
            # kiểm tra game_started (từ thread wait)
            if self._game_ready.is_set():
                self._result='start'; break

            # poll DB mỗi 5s để cập nhật guest (chỉ khi là host và chưa có guest)
            if self.is_host and not self._guest:
                now = time.time()
                if now - self._last_db_poll >= 5.0:
                    self._last_db_poll = now
                    threading.Thread(target=self._poll_db_guest, daemon=True).start()

            # poll socket events — xử lý tất cả kể cả game_started
            if self._client:
                for ev,data in self._client.poll():
                    if ev=='game_started':
                        self._game_color = data.get('color', 'white')
                        self._game_ready.set()
                    elif ev=='room_updated':
                        self._guest=data.get('guest','')
                        if data.get('host_display'):
                            self.host_display = data['host_display']
                    elif ev=='room_joined':
                        self._guest=data.get('guest','')
                        if data.get('host_display'):
                            self.host_display = data.get('host_display', self.host)
                    elif ev=='room_closed':
                        self._result='leave'
                    elif ev=='error':
                        self._msg=data.get('msg','Loi')
                        self._msg_ok=False; self._msg_timer=pygame.time.get_ticks()+2500

            # check lại ngay sau poll — không chờ frame tiếp
            if self._game_ready.is_set():
                self._result='start'; break

            for event in pygame.event.get():
                if event.type==pygame.QUIT: self._leave(); break
                self._handle(event)

            self._draw(surface); pygame.display.flip(); clock.tick(60)
        return self._result

    def _handle(self, event):
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
            self._leave(); return
        if event.type==pygame.MOUSEBUTTONDOWN:
            if self.btn_close.collidepoint(event.pos): self._leave(); return
            if not self.panel_rect.collidepoint(event.pos): return
        if self.btn_invite.handle_event(event): self._copy_pin()
        if self.btn_leave.handle_event(event): self._leave()
        if self.btn_start.handle_event(event):
            if self.is_host and self._guest:
                if self._client: self._client.emit('start_game',{'pin':self.pin})
            elif self.is_host:
                self._msg='Can 2 nguoi choi de bat dau!'; self._msg_ok=False
                self._msg_timer=pygame.time.get_ticks()+2500

    def _copy_pin(self):
        try:
            import tkinter as tk
            root=tk.Tk(); root.withdraw()
            root.clipboard_clear(); root.clipboard_append(self.pin)
            root.update(); root.destroy()
            self._msg=f'Da sao chep: {self.pin}'
        except Exception:
            self._msg=f'Ma PIN: {self.pin}'
        self._msg_ok=True; self._msg_timer=pygame.time.get_ticks()+2500

    def _leave(self):
        if self._client:
            self._client.emit('leave_room',{'pin':self.pin,'username':self.username})
        self._result='leave'

    def _draw(self, surface):
        surface.blit(self._overlay,(0,0))
        elapsed=(pygame.time.get_ticks()-self._open_t)/200.0
        ease=1-(1-min(1.0,elapsed))**3
        ox,oy=self.panel_rect.x,self.panel_rect.y
        if ease<1.0:
            old=surface.get_clip()
            sw=max(1,int(self.W*ease)); sh=max(1,int(self.H*ease))
            surface.set_clip(pygame.Rect(ox+(self.W-sw)//2,oy+(self.H-sh)//2,sw,sh))
        else: old=None
        self._draw_panel(surface,ox,oy)
        if old is not None: surface.set_clip(old)

    def _draw_panel(self, surface, ox, oy):
        pr=pygame.Rect(ox,oy,self.W,self.H)
        dx=ox-self.panel_rect.x; dy=oy-self.panel_rect.y
        sh=pygame.Surface((self.W+20,self.H+20),pygame.SRCALPHA)
        sh.fill((0,0,0,80)); surface.blit(sh,(ox-10,oy+10))
        pygame.draw.rect(surface,C_PANEL,pr,border_radius=16)
        pygame.draw.rect(surface,C_BORDER,pr,1,border_radius=16)
        pygame.draw.rect(surface,C_ACCENT,pygame.Rect(ox,oy,self.W,4),border_radius=16)
        title=self.f_title.render('Phong cho',True,C_ACCENT)
        surface.blit(title,title.get_rect(centerx=ox+self.W//2,y=oy+14))
        cr=self.btn_close.move(dx,dy)
        pygame.draw.circle(surface,C_PANEL2,cr.center,13)
        pygame.draw.circle(surface,C_BORDER,cr.center,13,1)
        xl=self.f_label.render('x',True,C_TEXT_DIM); surface.blit(xl,xl.get_rect(center=cr.center))
        pad=28
        pin_lbl=self.f_pin.render(self.pin,True,C_HOST_COLOR)
        surface.blit(pin_lbl,pin_lbl.get_rect(centerx=ox+self.W//2,y=oy+44))
        hint=self.f_small.render('Ma PIN phong — chia se cho ban be',True,C_TEXT_DIM)
        surface.blit(hint,hint.get_rect(centerx=ox+self.W//2,y=oy+104))
        pygame.draw.line(surface,C_BORDER,(ox+pad,oy+122),(ox+self.W-pad,oy+122),1)
        # host row
        player_y=oy+132
        host_bg=pygame.Rect(ox+pad,player_y,self.W-pad*2,36)
        pygame.draw.rect(surface,C_PANEL2,host_bg,border_radius=8)
        crown=self.f_player.render('👑',True,C_HOST_COLOR)
        surface.blit(crown,(host_bg.x+10,host_bg.centery-crown.get_height()//2))
        hl=self.f_player.render(self.display_name if self.is_host else self.host_display,True,C_HOST_COLOR)
        surface.blit(hl,(host_bg.x+38,host_bg.centery-hl.get_height()//2))
        rl=self.f_small.render('Chu phong',True,C_TEXT_DIM)
        surface.blit(rl,(host_bg.right-rl.get_width()-10,host_bg.centery-rl.get_height()//2))
        # guest row
        guest_y=player_y+44
        guest_bg=pygame.Rect(ox+pad,guest_y,self.W-pad*2,36)
        pygame.draw.rect(surface,C_PANEL2,guest_bg,border_radius=8)
        if self._guest:
            gl=self.f_player.render('👤',True,C_GUEST_COLOR)
            surface.blit(gl,(guest_bg.x+10,guest_bg.centery-gl.get_height()//2))
            gn=self.f_player.render(self._guest,True,C_GUEST_COLOR)
            surface.blit(gn,(guest_bg.x+38,guest_bg.centery-gn.get_height()//2))
            gr=self.f_small.render('Nguoi tham gia',True,C_TEXT_DIM)
            surface.blit(gr,(guest_bg.right-gr.get_width()-10,guest_bg.centery-gr.get_height()//2))
        else:
            t=pygame.time.get_ticks()/600.0; dots='.'*(int(t)%4)
            wait=self.f_label.render(f'Dang cho nguoi choi{dots}',True,C_TEXT_DIM)
            surface.blit(wait,wait.get_rect(center=guest_bg.center))
            alpha=int(100+80*math.sin(t*2))
            pulse=pygame.Surface((guest_bg.w,guest_bg.h),pygame.SRCALPHA)
            pygame.draw.rect(pulse,(*C_ACCENT,alpha),pulse.get_rect(),2,border_radius=8)
            surface.blit(pulse,guest_bg.topleft)
        for btn in (self.btn_invite,self.btn_start,self.btn_leave):
            orig=btn.rect.copy(); btn.rect=btn.rect.move(dx,dy)
            if btn is self.btn_start:
                btn.bg=C_START_BG if (self.is_host and self._guest) else C_START_DIS
            btn.draw(surface,self.f_btn); btn.rect=orig
        if not self.is_host:
            w2=self.f_small.render('Cho chu phong bat dau...',True,C_TEXT_DIM)
            surface.blit(w2,w2.get_rect(centerx=ox+self.W//2,
                y=self.btn_start.rect.move(dx,dy).centery-w2.get_height()//2))
        if self._msg and pygame.time.get_ticks()<self._msg_timer:
            c=C_SUCCESS if self._msg_ok else C_ERROR
            ml=self.f_label.render(self._msg,True,c)
            surface.blit(ml,ml.get_rect(centerx=ox+self.W//2,
                y=self.btn_leave.rect.move(dx,dy).bottom+8))
