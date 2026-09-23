import zlib, struct

S = 144          # final size
SS = 4           # supersample factor
W = S * SS

def rrect(x, y, w, h, r):
    """Return a predicate for a rounded rectangle in supersampled space."""
    x, y, w, h, r = x*SS, y*SS, w*SS, h*SS, r*SS
    x0, y0, x1, y1 = x, y, x + w, y + h
    cx0, cy0, cx1, cy1 = x0 + r, y0 + r, x1 - r, y1 - r
    def inside(px, py):
        if px < x0 or px >= x1 or py < y0 or py >= y1:
            return False
        qx = cx0 if px < cx0 else (cx1 if px > cx1 else px)
        qy = cy0 if py < cy0 else (cy1 if py > cy1 else py)
        if qx == px and qy == py:
            return True
        return (px - qx) ** 2 + (py - qy) ** 2 <= r * r
    return inside

INK   = (0x1F, 0x2A, 0x37)
LIGHT = (0xE8, 0xED, 0xF3)
AMBER = (0xF5, 0xA6, 0x23)

bg   = rrect(0, 0, 144, 144, 30)
logs = [rrect(26, 42, 62, 15, 7.5),
        rrect(42, 64, 46, 15, 7.5),
        rrect(34, 86, 54, 15, 7.5)]
block = rrect(98, 30, 16, 84, 8)

# accumulate at supersampled resolution into per-final-pixel sums
acc = [[[0, 0, 0, 0] for _ in range(S)] for _ in range(S)]
for py in range(W):
    fy = py // SS
    row = acc[fy]
    for px in range(W):
        if not bg(px, py):
            continue
        if block(px, py):
            c = AMBER
        elif any(f(px, py) for f in logs):
            c = LIGHT
        else:
            c = INK
        a = row[px // SS]
        a[0] += c[0]; a[1] += c[1]; a[2] += c[2]; a[3] += 255

n = SS * SS
raw = bytearray()
for y in range(S):
    raw.append(0)
    for x in range(S):
        r, g, b, al = acc[y][x]
        cov = al // 255
        if cov == 0:
            raw += bytes((0, 0, 0, 0))
        else:
            raw += bytes((r // cov, g // cov, b // cov, al // n))

def chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))

png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", S, S, 8, 6, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
       + chunk(b"IEND", b""))
open(f"/private/tmp/claude-501/-Users-frans-statuspilot/75e15a66-1241-45db-b73b-7ff13da204a8/scratchpad/logo/logo-144.png", "wb").write(png)
print("skrevet", len(png), "bytes")
