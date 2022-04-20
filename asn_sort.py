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
lasts = []
def combine_desc(slist, p, p_len):
    asn_p, desc_p = re.findall("((?:AS\d+\/*){1,})\s(.*?)$", p)[0]
    for i in range(len(slist)):
        s, s_len = slist[i]
        if asn_p not in s:
            has = True
            for d in desc_p.split("##"):
                if d not in s:
                    has = False
                    break
            if has:
                asn_s = re.findall("((?:AS\d+\/*){1,})", s)[0]
                # put ASN with smaller block size first
                # set our block size to the smaller block size
                # but bigger than the pure block with same size,
                # since we've merged with a bigger block
                if p_len < s_len:
                    slist[i] = (s.replace(asn_s, "%s/%s" % (asn_p, asn_s)), p_len + 1)
                else:
                    slist[i] = (s.replace(asn_s, "%s/%s" % (asn_s, asn_p)), s_len + (0 if s_len == p_len else 1))
                return
        else: # asn_p in s, merge desc
            if not desc_p:
                return
            a = []
            for d in desc_p.split("##"):
                if d not in s:
                    a.append(d)
            a = "##".join(a)
            if a:
                if p_len < s_len:
                    asn_s = re.findall("((?:AS\d+\/*){1,})", s)[0]
                    # asn_s = s.split(" ")[0]
                    slist[i] = (s.replace(asn_s + " ", "%s %s##" % (asn_s, a)), p_len + 1)
                else:
                    slist[i] = (s + "##%s" % a, s_len + (0 if s_len == p_len else 1))
            return
    slist.append((p, p_len))

# ipaddr.IPAddress("::FFFF:0:0")._ip
_v4mappedv6 = 281470681743360
def writeln(l, h, de):
    # keep order, put shorter asn block first
    de = sorted(de, key = lambda x:x[1])
    de = "\"%s\"" % "; ".join([x[0] for x in de]).strip().replace("##", ", ")
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


for p in open(infile):
    if not p.strip():
        continue
    _ = p.split(",")
    l = int(_[0])
    h = int(_[1])
    block_len = h - l + 1
    de = ",".join(_[2:]).strip().strip('"')
    if not lasts:
        lasts.append([l, h, [(de, block_len)]])
        continue

    i = 0
    while i < len(lasts):
        # make a copy
        last = list(lasts[i])
        # the main idea is only remove a block from 'last' stack
        # if current l is bigger than stack's first element's l

        # combine same block, don't need to check others
        if l == last[0] and h == last[1]:
            combine_desc(lasts[i][2], de, block_len) 
            break
        if l > last[1]:
            # different block
            writeln(*last)
            del lasts[i]
            continue
        # the intersect of last block and current block
        int_l = max(l, last[0])
        int_h = min(h, last[1])
        del lasts[i]
        # we guarantee l >= last[0]
        if int_l > last[0]:
            lasts.insert(i, [last[0], int_l - 1, last[2]])
            i += 1
        if int_l <= int_h:
            _last2 = list(last[2])
            combine_desc(_last2, de, block_len)
            lasts.insert(i, [int_l, int_h, _last2])
            i += 1
        if int_h < last[1]:
            lasts.insert(i, [int_h + 1, last[1], last[2]])
            i += 1
        l = int_h + 1
        # if current block is all splitted, break loop
        if l >= h:
            break

    # current block still has remaining part
    if i >= len(lasts) and l < h:
        lasts.append([l, h, [(de, block_len)]])

# finish up
for last in lasts:
    writeln(*last)
f.close()

