import sys, math, random, time, requests
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QLinearGradient
import keyboard

SERVIDOR = "http://127.0.0.1:5000"
SCREEN_W, SCREEN_H, BAR_H = 1920, 1080, 52

COLORS = {
    'en_espera':  (0, 74, 110),
    'escuchando': (0, 180, 255),
    'procesando': (0, 212, 255),
    'hablando':   (0, 180, 255),
}
LABELS = {
    'en_espera': 'EN ESPERA',
    'escuchando': 'ESCUCHANDO',
    'procesando': 'PROCESANDO',
    'hablando': 'HABLANDO',
}
DIAS  = ['DOM','LUN','MAR','MIÉ','JUE','VIE','SÁB']
MESES = ['ENE','FEB','MAR','ABR','MAY','JUN','JUL','AGO','SEP','OCT','NOV','DIC']

# ── 8 independent orbital rings ──────────────────────────────────────────────
RINGS = [
    {'tX': 0,              'tZ': 0,              'speed':  1.1},
    {'tX': math.pi/2,      'tZ': 0,              'speed': -0.8},
    {'tX': 0,              'tZ': math.pi/2,      'speed':  1.4},
    {'tX': math.pi/4,      'tZ': 0,              'speed': -1.2},
    {'tX': 0,              'tZ': math.pi/4,      'speed':  0.9},
    {'tX': math.pi/3,      'tZ': math.pi/6,      'speed': -1.6},
    {'tX': math.pi/6,      'tZ': math.pi/3,      'speed':  1.3},
    {'tX': math.pi*2/3,    'tZ': math.pi/4,      'speed': -0.7},
]
NR = len(RINGS)
N  = 480

def _sphere_uv(i, n):
    phi   = math.acos(max(-1, min(1, 1 - 2*(i+0.5)/n)))
    theta = math.pi * (1 + math.sqrt(5)) * i
    return math.sin(phi)*math.cos(theta), math.sin(phi)*math.sin(theta), math.cos(phi)

def _atom_base(i):
    ring  = i % NR
    j     = i // NR
    total = max(1, N // NR)
    a     = (j / total) * math.pi * 2
    R     = 82
    tX, tZ = RINGS[ring]['tX'], RINGS[ring]['tZ']
    x, y = math.cos(a)*R, math.sin(a)*R
    y1 = y*math.cos(tX); z1 = y*math.sin(tX)
    x2 = x*math.cos(tZ) - z1*math.sin(tZ)
    z2 = x*math.sin(tZ) + z1*math.cos(tZ)
    return x2, y1, z2

def _lerp(a, b, k): return a + (b-a)*k
def _ease(x): return 2*x*x if x < 0.5 else 1 - ((-2*x+2)**2)/2

class Particle:
    __slots__ = ['ux','uy','uz','bA','bB','bC','ax','ay','az',
                 'ring_idx','base_angle',
                 'phase','phase2','phase3',
                 'drift_amp','drift_speed','size',
                 'px','py','pz','snap_x','snap_y','snap_z',
                 'lit','lit_t']
    def __init__(self, i):
        ux,uy,uz = _sphere_uv(i, N)
        self.ux,self.uy,self.uz = ux,uy,uz
        self.bA = 0.75 + random.random()*0.55
        self.bB = 0.75 + random.random()*0.55
        self.bC = 0.75 + random.random()*0.55
        ax,ay,az = _atom_base(i)
        self.ax,self.ay,self.az = ax,ay,az
        self.ring_idx   = i % NR
        j = i // NR; total = max(1, N//NR)
        self.base_angle = (j/total)*math.pi*2
        self.phase      = random.random()*math.pi*2
        self.phase2     = random.random()*math.pi*2
        self.phase3     = random.random()*math.pi*2
        self.drift_amp  = 3 + random.random()*9
        self.drift_speed= 0.18 + random.random()*0.28
        self.size       = 0.4 + random.random()*1.0
        self.px=self.py=self.pz=0.0
        self.snap_x=self.snap_y=self.snap_z=0.0
        self.lit=False; self.lit_t=0.0

pts = [Particle(i) for i in range(N)]

class Ray:
    __slots__ = ['pt','progress','speed']
    def __init__(self, pt):
        self.pt       = pt
        self.progress = 0.0
        self.speed    = 0.013 + random.random()*0.017

class JarvisHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.estado       = 'en_espera'
        self.cpu          = 0
        self.ram_pct      = 0
        self.ram_usada    = 0.0
        self.ram_total    = 0.0
        self.compact      = True
        self.toggle_flag  = False
        self.t            = 0.0
        self.trans        = 1.0
        self.next_ray     = 0.0
        self.rays: list[Ray] = []
        self._spawn_rays()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(0, 0, SCREEN_W, BAR_H)

        self.anim = QTimer(); self.anim.timeout.connect(self._tick); self.anim.start(16)
        self.poll_t = QTimer(); self.poll_t.timeout.connect(self._poll); self.poll_t.start(250)
        keyboard.add_hotkey('alt+c', lambda: setattr(self, 'toggle_flag', True))

    def _set_estado(self, s):
        if s != self.estado:
            for p in pts:
                p.snap_x=p.px; p.snap_y=p.py; p.snap_z=p.pz
            self.estado = s
            self.trans  = 0.0

    def _spawn_rays(self):
        n = 5 if self.estado=='escuchando' else 2 if self.estado=='en_espera' else 0
        if not n: return
        for p in random.sample(pts, n):
            self.rays.append(Ray(p))
            p.lit=False; p.lit_t=0.0

    def _tick(self):
        if self.toggle_flag:
            self.toggle_flag = False
            self._toggle()
        dt = 0.016
        self.t += dt
        if self.trans < 1.0: self.trans = min(1.0, self.trans + 0.018)
        if self.t > self.next_ray:
            iv = 1.4 if self.estado=='escuchando' else 2.8
            self.next_ray = self.t + iv + random.random()*0.7
            self._spawn_rays()
        self.rays = [r for r in self.rays if r.progress < 1.35]
        self._update_particles()
        self.update()

    def _update_particles(self):
        t = self.t; te = _ease(self.trans)
        estado = self.estado
        breathe_amp  = 7 if estado=='escuchando' else 3
        breathe_freq = 2.2 if estado=='escuchando' else 0.9
        breathe = math.sin(t*breathe_freq)*breathe_amp
        noise_amp = 8 if estado=='escuchando' else 4 if estado=='en_espera' else 0

        spin_y = 0.12 if estado=='escuchando' else 0.05
        spin_x = 0.06 if estado=='escuchando' else 0.035
        spin_z = 0.0
        if estado in ('procesando',):
            spin_y = 0.12; spin_x = 0.08; spin_z = 0.05

        ry = t*spin_y; rx = t*spin_x; rz = t*spin_z
        cy_=math.cos(ry); sy_=math.sin(ry)
        cx_=math.cos(rx); sx_=math.sin(rx)
        cz_=math.cos(rz); sz_=math.sin(rz)

        for p in pts:
            if estado == 'procesando':
                ring  = RINGS[p.ring_idx]
                a     = p.base_angle + t*ring['speed']*1.8
                tX,tZ = ring['tX'], ring['tZ']
                R = 82
                x = math.cos(a)*R; y = math.sin(a)*R
                y1= y*math.cos(tX); z1= y*math.sin(tX)
                x2= x*math.cos(tZ)-z1*math.sin(tZ)
                z2= x*math.sin(tZ)+z1*math.cos(tZ)
                wx=_lerp(p.snap_x,x2,te); wy=_lerp(p.snap_y,y1,te); wz=_lerp(p.snap_z,z2,te)
            elif estado == 'hablando':
                lat = math.asin(max(-1,min(1,p.uz)))
                lon = math.atan2(p.uy, p.ux)
                r = (82
                     + math.sin(lat*3+t*2.2)*math.cos(lon*2+t*1.4)*18
                     + math.sin(lat*5+t*3.1+p.phase)*10
                     + math.cos(lon*3-t*1.8+p.phase2)*8
                     + math.sin(t*1.1+p.phase3)*4)
                wx=_lerp(p.snap_x,p.ux*r,te)
                wy=_lerp(p.snap_y,p.uy*r,te)
                wz=_lerp(p.snap_z,p.uz*r,te)
            else:
                noise = noise_amp*math.sin(t*p.drift_speed+p.phase)*math.cos(t*p.drift_speed*0.6+p.phase2)
                w  = math.sin(t*p.drift_speed+p.phase)*p.drift_amp*(noise_amp/8 or 0.5)
                w2 = math.cos(t*p.drift_speed*0.65+p.phase2)*p.drift_amp*0.6*(noise_amp/8 or 0.5)
                bR = (82+breathe+noise)*p.bA
                wx=_lerp(p.snap_x, p.ux*bR*p.bB+w*p.ux*0.5, te)
                wy=_lerp(p.snap_y, p.uy*bR*p.bC+w2*p.uy*0.5, te)
                wz=_lerp(p.snap_z, p.uz*bR*p.bA+w*p.uz*0.4, te)

            x0=wx*cz_-wy*sz_; y0=wx*sz_+wy*cz_
            x1=x0*cy_-wz*sy_; z1=x0*sy_+wz*cy_
            y1=y0*cx_-z1*sx_; z2=y0*sx_+z1*cx_
            p.px=x1; p.py=y1; p.pz=z2
            if p.lit: p.lit_t += 0.032

    def _toggle(self):
        self.compact = not self.compact
        if self.compact:
            self.setGeometry(0, 0, SCREEN_W, BAR_H)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        else:
            self.setGeometry(0, 0, SCREEN_W, SCREEN_H)
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    def _poll(self):
        try:
            r = requests.get(f"{SERVIDOR}/estado_actual", timeout=0.3)
            self._set_estado(r.json().get('estado','en_espera'))
        except: pass
        try:
            r = requests.get(f"{SERVIDOR}/sistema_actual", timeout=0.3)
            d = r.json()
            self.cpu=d.get('cpu',0); self.ram_pct=d.get('ram_pct',0)
            self.ram_usada=d.get('ram_usada',0.0); self.ram_total=d.get('ram_total',0.0)
        except: pass
        try:
            r = requests.get(f"{SERVIDOR}/minimizar_hud", timeout=0.3)
            if r.json().get('minimizar') and not self.compact:
                self._toggle()
        except: pass

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.compact: self._draw_compact(p)
        else:            self._draw_full(p)
        p.end()

    def _qc(self, alpha=255):
        r,g,b = COLORS[self.estado]
        return QColor(r,g,b,alpha)

    def _font(self, size, bold=False, spacing=3):
        f = QFont('Consolas', size)
        f.setBold(bold)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, spacing)
        return f

    def _draw_compact(self, p):
        p.fillRect(0,0,SCREEN_W,BAR_H, QColor(0,0,0,235))
        p.setPen(QPen(QColor(0,25,40),1))
        p.drawLine(0,BAR_H-1,SCREEN_W,BAR_H-1)
        c = self._qc()
        dim = QColor(0,55,80)
        # dot
        p.setBrush(QBrush(c)); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(24, BAR_H//2-5, 10, 10)
        # state
        p.setFont(self._font(10,True,4)); p.setPen(QPen(c))
        p.drawText(46, BAR_H//2+5, LABELS[self.estado])
        # metrics
        p.setFont(self._font(9,False,2))
        p.setPen(QPen(dim)); p.drawText(280,BAR_H//2+5,"CPU")
        p.setPen(QPen(c));   p.drawText(315,BAR_H//2+5,f"{self.cpu}%")
        p.setPen(QPen(dim)); p.drawText(385,BAR_H//2+5,"RAM")
        p.setPen(QPen(c));   p.drawText(420,BAR_H//2+5,f"{self.ram_pct}%")
        # clock
        now = datetime.now()
        p.setFont(self._font(11,True,3)); p.setPen(QPen(c))
        p.drawText(SCREEN_W-135, BAR_H//2+5, now.strftime("%H:%M:%S"))

    def _draw_full(self, p):
        p.fillRect(0,0,SCREEN_W,SCREEN_H,QColor(0,0,0))
        c = self._qc()
        cx, cy = SCREEN_W//2, SCREEN_H//2
        self._draw_corners(p,c)
        # header
        hc = self._qc(110)
        p.setFont(self._font(11,False,14)); p.setPen(QPen(hc))
        from PyQt6.QtCore import QRect
        p.drawText(QRect(0,22,SCREEN_W,36), Qt.AlignmentFlag.AlignHCenter,
                   "J  ·  A  ·  R  ·  V  ·  I  ·  S")
        self._draw_left_panel(p,c,80,cy)
        self._draw_right_panel(p,c,SCREEN_W-80,cy)
        self._draw_orb(p,c,cx,cy)
        # state label
        p.setFont(self._font(13,True,9)); p.setPen(QPen(c))
        p.drawText(QRect(cx-220,cy+162,440,40), Qt.AlignmentFlag.AlignHCenter, LABELS[self.estado])
        # footer
        p.setFont(self._font(8,False,4)); p.setPen(QPen(QColor(0,22,35)))
        p.drawText(QRect(0,SCREEN_H-38,SCREEN_W,28), Qt.AlignmentFlag.AlignHCenter,
                   "JARVIS v1.0  ·  PERSONAL AI ASSISTANT  ·  POWERED BY OLLAMA")

    def _draw_corners(self, p, c):
        cc = QColor(c); cc.setAlpha(120)
        p.setPen(QPen(cc,2)); p.setBrush(Qt.BrushStyle.NoBrush)
        s,m = 44,20
        for x1,y1,x2,y2 in [
            (m,m,m+s,m),(m,m,m,m+s),
            (SCREEN_W-m-s,m,SCREEN_W-m,m),(SCREEN_W-m,m,SCREEN_W-m,m+s),
            (m,SCREEN_H-m,m+s,SCREEN_H-m),(m,SCREEN_H-m-s,m,SCREEN_H-m),
            (SCREEN_W-m-s,SCREEN_H-m,SCREEN_W-m,SCREEN_H-m),
            (SCREEN_W-m,SCREEN_H-m-s,SCREEN_W-m,SCREEN_H-m),
        ]: p.drawLine(x1,y1,x2,y2)

    def _draw_left_panel(self, p, c, x, cy):
        from PyQt6.QtCore import QRect
        dim = QColor(0,50,75); bw = 185
        p.setFont(self._font(9,False,3)); p.setPen(QPen(dim))
        p.drawText(x, cy-82, "PROCESADOR")
        p.setFont(self._font(24,True,2)); p.setPen(QPen(c))
        p.drawText(x, cy-50, f"{self.cpu}%")
        p.setBrush(QBrush(QColor(0,15,25))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(x,cy-36,bw,3)
        fc = QColor(255,107,0) if self.cpu>80 else c
        p.setBrush(QBrush(fc))
        p.drawRect(x,cy-36,max(0,int(bw*self.cpu/100)),3)
        p.setFont(self._font(9,False,3)); p.setPen(QPen(dim))
        p.drawText(x,cy+22,"MEMORIA RAM")
        p.setFont(self._font(24,True,2)); p.setPen(QPen(c))
        p.drawText(x,cy+54,f"{self.ram_pct}%")
        p.setBrush(QBrush(QColor(0,15,25))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(x,cy+66,bw,3)
        fc2 = QColor(255,107,0) if self.ram_pct>85 else c
        p.setBrush(QBrush(fc2))
        p.drawRect(x,cy+66,max(0,int(bw*self.ram_pct/100)),3)
        p.setFont(self._font(9,False,2)); p.setPen(QPen(QColor(0,38,58)))
        p.drawText(x,cy+84,f"{self.ram_usada} / {self.ram_total} GB")

    def _draw_right_panel(self, p, c, x, cy):
        from PyQt6.QtCore import QRect
        now = datetime.now()
        dim = QColor(0,50,75); dark = QColor(0,32,50)
        ts = now.strftime("%H:%M:%S")
        ds = f"{DIAS[now.weekday()]} {now.day} {MESES[now.month-1]} {now.year}"
        p.setFont(self._font(9,False,3)); p.setPen(QPen(dim))
        p.drawText(QRect(x-200,cy-94,200,22), Qt.AlignmentFlag.AlignRight,"HORA LOCAL")
        p.setFont(self._font(28,True,4)); p.setPen(QPen(c))
        p.drawText(QRect(x-250,cy-70,250,52), Qt.AlignmentFlag.AlignRight, ts)
        p.setFont(self._font(9,False,3)); p.setPen(QPen(dim))
        p.drawText(QRect(x-200,cy-10,200,22), Qt.AlignmentFlag.AlignRight, ds)
        p.drawText(QRect(x-200,cy+22,200,22), Qt.AlignmentFlag.AlignRight,"SISTEMA")
        p.setFont(self._font(9,False,2)); p.setPen(QPen(dark))
        for i,line in enumerate(["BARCELONA · ES","ALEX · ADMIN","OLLAMA · LOCAL"]):
            p.drawText(QRect(x-200,cy+48+i*20,200,20), Qt.AlignmentFlag.AlignRight, line)

    def _draw_orb(self, p, c, cx, cy):
        t = self.t
        r,g,b = COLORS[self.estado]

        # ── rays (en_espera + escuchando) ──
        if self.estado in ('en_espera','escuchando'):
            for ray in self.rays:
                ray.progress += ray.speed
                prog = min(1.0, ray.progress)
                pt = ray.pt
                ex = cx + pt.px*prog; ey = cy + pt.py*prog
                pr = ray.progress
                fade = pr/0.35 if pr<0.35 else (1.35-pr)/0.53 if pr>0.82 else 1.0
                if fade <= 0: continue
                grad = QLinearGradient(cx,cy,ex,ey)
                grad.setColorAt(0,   QColor(r,g,b,int(fade*230)))
                grad.setColorAt(0.6, QColor(r,g,b,int(fade*64)))
                grad.setColorAt(1,   QColor(r,g,b,0))
                p.setPen(QPen(QBrush(grad),0.8))
                p.drawLine(int(cx),int(cy),int(ex),int(ey))
                if ray.progress >= 0.9 and not pt.lit:
                    pt.lit = True; pt.lit_t = 0.0

        # ── hablando ripple rings ──
        if self.estado == 'hablando':
            for i in range(4):
                rp = (t*0.8 + i*0.7) % 2.8
                rad = 20 + rp*55
                alpha = max(0, int((1-rp/2.8)*90))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor(r,g,b,alpha),1))
                p.drawEllipse(int(cx-rad),int(cy-rad),int(rad*2),int(rad*2))

        # ── center glow ──
        gp = math.sin(t*(3.5 if self.estado=='procesando' else 3.0 if self.estado=='hablando' else 1.3))*0.28+0.72
        gs = 30 if self.estado=='procesando' else 28 if self.estado=='hablando' else 20
        for s_,a_ in [(gs*gp,0.95),(gs*gp*1.9,0.22),(gs*gp*3.8,0.07)]:
            grad = QRadialGradient(cx,cy,s_)
            grad.setColorAt(0, QColor(r,g,b,int(a_*255)))
            grad.setColorAt(1, QColor(r,g,b,0))
            p.setBrush(QBrush(grad)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx-s_),int(cy-s_),int(s_*2),int(s_*2))

        # ── particles ──
        sorted_pts = sorted(pts, key=lambda pp: -pp.pz)
        for pt in sorted_pts:
            depth = max(0.0, (pt.pz+130)/260)
            alpha = 0.1 + depth*0.75
            sz    = (0.4 + depth*1.4)*pt.size
            if self.estado == 'hablando':
                lat = math.asin(max(-1,min(1,pt.uz)))
                wave = math.sin(lat*3+t*2.2)*0.5+0.5
                alpha = 0.15 + depth*0.85 + wave*0.1
                sz    = (0.5+depth*1.6)*pt.size*(0.9+wave*0.3)
            if pt.lit and pt.lit_t < 2.5:
                fade = pt.lit_t/0.2 if pt.lit_t<0.2 else 1-(pt.lit_t-0.2)/2.3
                alpha = min(1.0, alpha+fade)
                sz *= (1+fade*1.8)
            alpha = min(1.0, max(0.0, alpha))
            sz    = max(0.2, sz)
            p.setBrush(QBrush(QColor(r,g,b,int(alpha*255))))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(cx+pt.px-sz),int(cy+pt.py-sz),int(sz*2),int(sz*2))

        # center dot
        p.setBrush(QBrush(QColor(r,g,b,255))); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx-3,cy-3,6,6)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    hud = JarvisHUD()
    hud.show()
    sys.exit(app.exec())