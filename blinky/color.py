def rgb_to_hsl(color):
    r = color[0] / 255
    g = color[1] / 255
    b = color[2] / 255

    mx = max(r, g, b)
    mn = min(r, g, b)
    l = (mx + mn) / 2

    if mx == mn:
        h = s = 0
    else:
        d = mx - mn
        if l > 0.5:
            s = d / (2 - mx - mn)
        else:
            s = d / (mx + mn)

        if mx == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif mx == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4

        h /= 6

    return (h, s, l)

def hsl_to_rgb(color):
    (h, s, l) = color

    if s == 0:
        r = g = b = l
    else:
        def hue2rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6

            return p

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q

        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)

    return (round(r * 255), round(g * 255), round(b * 255))

def mix_colors_by_rgb(a, b, offset):
    def mix_val(a, b, offset):
        return round(a + ((b - a) * offset))

    if offset <= 0:
        return a
    if offset >= 1:
        return b

    return (
        mix_val(a[0], b[0], offset),
        mix_val(a[1], b[1], offset),
        mix_val(a[2], b[2], offset),
    )

def mix_colors_by_hsl(a, b, offset):
    def mix_val(a, b, offset):
        return a + ((b - a) * offset)

    def mix_hue(a, b, offset):
        if abs(a - b) > 0.5:
            if a < b:
                a += 1
            else:
                b += 1

        return mix_val(a, b, offset) % 1

    if offset <= 0:
        return a
    if offset >= 1:
        return b

    hsl_a = rgb_to_hsl(a)
    hsl_b = rgb_to_hsl(b)

    mixed = (
        mix_hue(hsl_a[0], hsl_b[0], offset),
        mix_val(hsl_a[1], hsl_b[1], offset),
        mix_val(hsl_a[2], hsl_b[2], offset),
    )

    return hsl_to_rgb(mixed)

def mix_colors(a, b, offset):
    return mix_colors_by_hsl(a, b, offset)
