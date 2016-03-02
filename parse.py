import codecs, json, string, subprocess, os, unicodedata

keysyms = {}
# typeable things
allowed_chars = ("`1234567890-=qwertyuiop[]asdfghjkl;'#\zxcvbnm,./"
    "!\"$%^&*()_+QWERTYUIOP{}ASDFGHJKL:@~|ZXCVBNM<>?")

# default letters and numbers
for c in string.uppercase:
    keysyms[c] = c
    keysyms[c.lower()] = c.lower()
for c in "0123456789":
    keysyms[c] = c

fp = codecs.open("/usr/include/X11/keysymdef.h", encoding="utf-8")
for line in fp:
    parts = line.split()
    if not parts: continue
    if parts[0] != u"#define": continue
    if not parts[1].startswith("XK_"): continue
    if not parts[2].startswith("0x"): continue
    try:
        c = unichr(int(parts[2][2:], 16))
    except ValueError:
        continue
    keysyms[parts[1][3:]] = c

chars = {}
fp = codecs.open("/usr/share/X11/locale/en_US.UTF-8/Compose", encoding="utf-8")
for line in fp:
    parts = line.split()
    if not parts: continue
    if parts[0] != u"<Multi_key>": continue
    keys = []
    result = None
    idx = 1
    while True:
        if idx >= len(parts): break
        if parts[idx] == u":":
            result = parts[idx + 1][1:-1]
            break
        keys.append(parts[idx][1:-1])
        idx += 1
    if result:
        mkeys = [keysyms.get(x) for x in keys]
        try:
            mkeys.index(None)
        except ValueError:
            mallowed = [x in allowed_chars for x in mkeys]
            if False in mallowed: continue
            try:
                codepoint = hex(ord(result))
            except TypeError:
                continue
            try:
                uniname = unicodedata.name(unichr(int(codepoint[2:], 16)))
            except ValueError:
                continue
            if result not in chars:
                chars[result] = {"keys": [], "codepoint": codepoint, "codepoint_dec": int(codepoint[2:], 16), "name": uniname}
            chars[result]["keys"].append(mkeys)
fp.close()

count = 0
for res in chars:
    cd = chars[res]
    c = cd["codepoint_dec"]
    count += 1
    svgpath = "chars/%s.svg" % cd["codepoint"]
    cd["ok"] = True
    if os.path.isfile(svgpath):
        print "Already converted %s (%s/%s) to svg %s, skipping." % (c, count, len(chars), svgpath)
        continue
    print ("Converting %s (%s/%s)..." % (c, count, len(chars))),
    print "to svg...",
    fp = codecs.open("onechar.svg", encoding="utf8")
    content = fp.read()
    fp.close()
    content = content.replace(u"\u24b8", unichr(c))
    fp = codecs.open("temp.svg", mode="w", encoding="utf8")
    fp.write(content)
    fp.close()
    print "to eps...",
    os.system("inkscape temp.svg --export-eps=temp.eps --export-text-to-path >/dev/null 2>&1 ")
    print ("to svg path %s..." % svgpath),
    os.system("inkscape temp.eps --export-plain-svg %s >/dev/null 2>&1" % svgpath)
    os.unlink("temp.svg")
    os.unlink("temp.eps")
    if not os.path.isfile(svgpath):
        print "failed."
        cd["ok"] = False
        continue
    print "done."

chars = dict([x for x in chars.items() if x[1].get("ok")])

print "Writing JSON summary"
fp = codecs.open("chars.json", encoding="utf8", mode="w")
fp.write("chars(");
fp.write(json.dumps(chars, indent=2))
fp.write(");");
fp.close()

