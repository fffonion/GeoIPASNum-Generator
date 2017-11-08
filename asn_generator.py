from __future__ import print_function
import requests
import re
import os
import time
import random
from hashlib import md5
import json
import time
import math
import lxml.html as lhtml
from lxml import etree
from threading import Thread, RLock
from Queue import Queue, Empty
import ipaddr

# the number of http threads
TCNT = 5
# the number of local threads - 1 (0 menas 1 thread)
LCNT = 0
CACHE_EXPIRE = 5

flock = RLock()
plock = RLock()
slock = RLock()
taskq = Queue()
outf = open("GeoIPASNumC.csv", "ab", False)
outfv6 = open("GeoIPASNumCv6.csv", "ab", False)

if not os.path.exists("html"):
    os.mkdir("html")

class ASRun(Thread):
    def __init__(self, tid, proxy_port = 16963):
        Thread.__init__(self)
        self.cookies = {}
        self.headers = {
            "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding":"gzip, deflate",
            "Accept-Language":"en,zh-CN;q=0.8,zh;q=0.6",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "DNT":"1",
            "Host":"bgp.he.net",
            "User-Agent":"Mozilla/5.0 (NT 6.2; AppleWebKit/535.23 (KHTML, like Gecko) Chrome/52.10.6154.12 Safari/535.23",
        }
        self.proxies = dict(http = 'socks5://127.0.0.1:%d' % proxy_port, https = 'socks5://127.0.0.1:%d' % proxy_port)
        self.req = requests.Session()
        self.tid = tid
        self._term = False

    def _log(self, s):
        plock.acquire()
        s = "[%s] - %s %s" % (time.strftime("%X", time.localtime(time.time())), self.tid, s)
        print(s)
        open("hehe.log", "a").write("%s\n" % s)
        plock.release()


    def http_get(self, url, headers = None, proxies = None, allow_redirects = False):
        c = self.req.get(url, headers = headers or self.headers, proxies = proxies or self.proxies, allow_redirects = False)
        if c.headers.get("set-cookie"):
            self.mkcookie(c.headers.get("set-cookie"))
        return c

    def http_post(self, url, data, headers = None, proxies = None, allow_redirects = False):
        c = self.req.post(url, data, headers = headers or self.headers, proxies = proxies or self.proxies, allow_redirects = False)
        if c.headers.get("set-cookie"):
            self.mkcookie(c.headers.get("set-cookie"))
        return c

    def mkcookie(self, coostr = ""):
        if coostr:
            for k, v in re.findall("([^=\s]+)\s*=([^;,\s]+)\s*[;,$]", coostr):
                if k in ['expires']:
                    continue
                elif k == 'path' and '--' not in v:
                    continue
                self.cookies[k] = v
            #self._log("new cookie %s" % self.cookies)
        self.headers['Cookie'] = ";".join(["=".join(_) for _ in self.cookies.iteritems()])

    def ccbypass(self):
        raise NotImplementedError("figure it yourself!")

    def bgpheget(self, url):
        slp = 1
        while not self._term:
            try:
                c = self.http_get(url)
            except Exception as ex:
                self._log("exception: %s" % ex)
            else:
                self.mkcookie(c.headers.get("set-cookie") or "")
                if c.status_code == 302:
                    if "resourceerror" in c.text:
                        self._log("wait 6h")
                    elif not self.ccbypass():
                        self._log("can't acquire session cookies, abort")
                    else:
                        c = self.http_get(url)
                        return c.text
                else:
                    return c.text
            for i in range(16000 + random.randrange(0, 2000)):
                time.sleep(1)
                if self._term:
                    return ""

            #slp += 1
            #slp = min(slp, 20)
        return ""


    def parse_asn(self, asnum):
        htmlf = os.path.join("html", "AS%s.htm" % asnum)
        if os.path.exists(htmlf) and os.path.getsize(htmlf) > 256 and os.stat(htmlf).st_mtime > time.time() - 86400 * CACHE_EXPIRE:
            if self.tid < TCNT:
                time.sleep(0.1)
                return False
            t = open(htmlf).read()
            self._log("load AS%s from file" % asnum)
        elif self.tid > TCNT:
            time.sleep(0.1)
            return False
        else:
            time.sleep(1 * random.random())
            t = self.bgpheget("https://bgp.he.net/AS%s" % asnum)
            if not t or len(t) < 256:
                return False
            open(htmlf, "wb").write(t.encode("utf-8"))
        #open("1.htm", "wb").write(t.encode("utf-8"))
        htmldoc = lhtml.fromstring(t)
        try:
            basic_name = re.findall("AS\d+\s+(.*?)$", htmldoc.xpath('//a[@href="/AS%s"]' % asnum)[0].text)[0].encode("utf-8")
        except IndexError:
            return 'did not return any results' in t
        self._log(basic_name)
        # i=0 ipv4; i=1 ipv6
        for ipver in range(2):
            if ipver == 0:
                el_cidr = htmldoc.xpath('//table[@id="table_prefixes4"]/tbody/tr/td/a')
                el_desc = htmldoc.xpath('//table[@id="table_prefixes4"]/tbody/tr/td[2]')
            else:
                el_cidr = htmldoc.xpath('//table[@id="table_prefixes6"]/tbody/tr/td/a')
                el_desc = htmldoc.xpath('//table[@id="table_prefixes6"]/tbody/tr/td[2]')
            last_cidr_s = float("inf")
            last_cidr_e = 0 
            cache = []
            for i in range(len(el_cidr)):
                lo_s, mask = re.findall("([a-fA-F\d\.\:]+)/(\d+)", el_cidr[i].text)[0]
                mask = int(mask)
                # _1, _2, _3, _4, _m = map(int, re.findall("(\d+)\.(\d+)\.(\d+)\.(\d+)/(\d+)", el_cidr[i].text)[0])
                # _ = (_1<<24) + (_2<<16) +(_3<<8) + _4
                if ipver == 0:
                    lo_n = ipaddr.IPv4Network(lo_s)._ip 
                    hi_n = lo_n + (2 << (31 - mask)) - 1
                else:
                    lo_n = ipaddr.IPv6Network(lo_s)._ip 
                    hi_n = lo_n + (2 << (127 - mask)) - 1
                # hi_s = str(ipaddr.IPAddress(hi_n))

                _s = el_desc[i].text.strip().encode("utf-8")
                _sc = ''.join(re.findall("([a-zA-Z\d])", _s))
                _bc = ''.join(re.findall("([a-zA-Z\d])", basic_name))
                # if _ > last_cidr_s and __e < last_cidr_e :
                #     continue
                # elif _ == last_cidr_s and __e > last_cidr_e: #larger block, pop former one
                #     last_cidr_e = __e
                #     cache.pop()
                #     continue
                # else:
                #     last_cidr_s = _
                #     last_cidr_e = __e
                if _sc != _bc and _sc not in _bc and _sc.strip():
                    desc = "%s##%s" % (_s, basic_name)
                elif _bc in _sc:
                    desc = _s
                else:
                    desc = basic_name
                cache.append((lo_n, hi_n, asnum, desc.replace("\"", "'")))
                # cache.append((lo_s, hi_s, lo_n, hi_n, asnum, desc.replace("\"", "'")))

            flock.acquire()
            if ipver == 0:
                outf.write("\n".join(["%d,%d,\"AS%s %s\"" % x for x in cache]))
                outf.write("\n")
            else:
                outfv6.write("\n".join(["%d,%d,\"AS%s %s\"" % x for x in cache]))
                outfv6.write("\n")
            flock.release()
            self._log("%d IPv%d entries for AS%s" % (len(cache), 4 if ipver==0 else 6, asnum))
        return True

    def term(self):
        self._term = True

    def run(self):
        while not self._term:
            try:
                asnum = taskq.get(False)
            except Empty:
                self._log("no tasks, exiting")
                break

            if self.parse_asn(asnum):
                slock.acquire()
                done_list.add(asnum)
                open(donefile, "a", False).write("%s\n" % asnum)
                slock.release()
            else:
                taskq.put(asnum)


if __name__ == "__main__":
    #import os
    #os._exit(0)
    donefile = "asn.done.txt"
    done_list = set()
    if os.path.exists(donefile):
        done_list = set(open(donefile).read().split())
        print("%d already done" % len(done_list))
    for asnum in open("asn.txt").xreadlines():
        _ = re.findall("\d+", asnum)
        if not _:
            print("not asn %s" % asnum)
            continue
        elif _[0] in done_list:
            print("skip %s" % asnum)
            continue
        taskq.put(_[0])
    print("%s remaining tasks" % taskq.qsize())
    tlist = [ASRun(i + 1, 60000 + i) for i in range(TCNT + LCNT)]
    map(lambda x:x.setDaemon(True), tlist)
    map(lambda x:x.start(), tlist)
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            map(lambda x:x.term(), tlist)
            break
    print("cleaning")
    map(lambda x:x.join(), tlist)
