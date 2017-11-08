import os
import re
import sys
#os.system("cat GeoIPASNumC.csv |sort -n|uniq > GeoIPASNum1.csv")
ipv6 = False
if len(sys.argv) > 1 and sys.argv[1] == "ipv6":
    ipv6 = True
    infile = "GeoIPASNum1v6.csv"
    outfile = "GeoIPASNum2v6.csv"
else:
    infile = "GeoIPASNum1.csv"
    outfile = "GeoIPASNum2.csv"

f = open(outfile, "w")
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

# ipaddr.IPAddress("::FFFF:0:0")._ip
_v4mappedv6 = 281470681743360
def writeln(l, h, de):
    if ipv6:
        # 1,1 is dummy data and csv2dat checks the first charater to be int
        # so we feed it with a simplest dummy data
        fmt = "1,1,%d,%d,%s\n"
    else:
        fmt = "%d,%d,%s\n"
    while l < h:
        step = 1
        _ = list(bin(l)[2:])
        while _.pop() == '0' and l + (step << 1) - 1 <= h:
            step = step << 1
        # ipv4-mapped ipv6 address
        if ipv6 and l < _v4mappedv6:
            f.write(fmt % (l + _v4mappedv6, l + _v4mappedv6 + step - 1, de))
        else:
            f.write(fmt % (l, l + step - 1, de))
        l += step
    if l == h:
        # ipv4-mapped ipv6 address
        if ipv6 and l < _v4mappedv6:
            f.write(fmt % (l + _v4mappedv6, l + _v4mappedv6, de))
        else:
            f.write(fmt % (l, l, de))


for p in open(infile).xreadlines():
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
        if l > last[0]: # if it's [<= last =>][<= current =>][<= last =>]
            writeln(last[0], h, last[2])
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

