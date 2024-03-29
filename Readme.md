GeoIPASNum Generator
===================
MaxMind's version of ASN database doesn't include overriden description (e.g. `27.100.36.0/24`) or CIDRs that are announced by multiple ASNs (e.g. `63.223.97.0/24`).

This set of scripts will get ASNs from **bgp.he.net** and generate (legacy) MaxMind format **GeoIPASNum.dat**.

# How to use

1. Run `bash ./new.sh` to generate all ASNum list and save to `asn.txt`.
2. Start your socks5 proxies starting from port **60000** (*60000*, *60001*, ...), modify **TCNT** in `asn_generator.py` to the proxies you have.
3. Run `python ./asn_generator.py`. This will generate `GeoIPASNumC.csv` and `GeoIPASNumCv6.csv`
4. Run `cat GeoIPASNumC.csv |sort -n|uniq > GeoIPASNum1.csv`
5. Run `cp GeoIPASNum1.csv GeoIPASNum1v6.csv && cat GeoIPASNumCv6.csv |sort -n|uniq >> GeoIPASNum1v6.csv`
6. Run `python ./asn_sort.py`. This will generate `GeoIPASNum2.csv`
7. Run `python ./asn_sort.py ipv6`. This will generate `GeoIPASNum2v6.csv`
8. Run `python ./csv2dat.py -w GeoIPASNum2.dat mmasn GeoIPASNum2.csv`. This will generate `GeoIPASNum2.dat`
9. Run `python ./csv2dat.py -w GeoIPASNum2v6.dat mmasn6 GeoIPASNum2v6.csv`. This will generate `GeoIPASNum2v6.dat`
10. Run `bash ./svg.sh`, `bash ./svg6.sh` and `bash ./flags.sh` to download other resources.

# Note

* `GeoIPASNum2.dat` is a IPv4 only version, `GeoIPASNum2v6.dat` supports both IPv4 and IPv6.
* `csv2dat.py` is stolen from [mteodoro/mmutils](https://github.com/mteodoro/mmutils).
* The function to bypass browser test for **bgp.he.net** is deleted to prevent from bad guys XD. You should figure how it works and implement it in `ccbypass` of `asn_generator.py`.
* `asn_sort.py` will combine ASN descriptions if they have same CIDR. If there's containing relation, it will substrate smaller block from bigger block.
* Files are cached in `html` folder and will expire in **5 days**.

# Demo

https://cidr.me

https://bgp-he-net.github.io/AS\d+.htm

# See also

[Set up a light weight GeoIP query server using OpenResty](https://gist.github.com/fffonion/44e5fb59e2a8f0efba5c1965c6043584)
