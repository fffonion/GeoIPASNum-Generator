import os
import re
#os.system("cat GeoIPASNumC.csv |sort -n|uniq > GeoIPASNum1.csv")
f = open("GeoIPASNum2.csv", "w")
last = [float("inf"), 0, ""]
def combine_desc(s, p):
    asn_p, desc_p = re.findall("(AS\d+)\s([^\"]*?)\"", p)[0]
    r = [s[1:-1]]
    if asn_p not in s:
        if desc_p in s:
            asn_s = re.findall("((?:AS\d+\/*){1,})", s)[0]
            return s.replace(asn_s, "%s/%s" % (asn_s, asn_p))
        r+= [" ", p[1:-1]]
    else:
        a = []
        a.append("")
        for _ in desc_p.split(", "):
            if _ not in s:
                a.append(_)
        r.append(", ".join(a))
    return "\"%s\"" % "".join(r).strip()

def writeln(l, h, de):
    while l < h:
        step = 1
        _ = list(bin(l)[2:])
        while _.pop() == '0' and l + (step << 1) - 1 <= h:
            step = step << 1
        f.write("%d,%d,%s" % (l, l + step - 1, de))
        f.write("\n")
        l += step
    if l == h:
        f.write("%d,%d,%s" % (l, l, de))
        f.write("\n")


for p in open("GeoIPASNum1.csv").xreadlines():
    if not p.strip():
        continue
    _ = p.split(",")
    l = int(_[0])
    h = int(_[1])
    de = ",".join(_[2:]).strip()
    if l == last[0] and h == last[1]:
        # combine same block
        last[2] = combine_desc(last[2], de) 
    if l >= last[0] and h < last[1]:
        # smaller block, substrate last and write this
        writeln(l, h, combine_desc(de, last[2]))
        if l > last[0]:
            pass
        last = [h + 1, last[1], last[2]]
    elif l == last[0] and h > last[1]:
        # bigger block, substrate current and write last
        last[2] = combine_desc(last[2], de)
        writeln(*last)
        last = [last[1] + 1, h, de]
    elif l > last[1]:# different block
        writeln(*last)
        last = [l, h, de]
    elif l > last[0] and h > last[1]:
        #crossed block, substrate last, merge, write last, put this
        writeln(last[0], l - 1, last[2])
        writeln(l, last[1], combine_desc(last[2], de))
        last = [last[1] + 1, h, de]

writeln(*last)
f.close()

