#!/bin/bash
pushd .
cd /tmp
wget http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum2.zip -O /tmp/GeoIPASNum2.zip
unzip GeoIPASNum2.zip
popd
cat /tmp/GeoIPASNum2.csv |grep -aoP "AS\d+"|grep -aoP "\d+"|sort|uniq > asn.txt
mkdir -p html/graphs
echo "cd html/graphs" >> svg.sh
cp asn.txt _
sed -i "s/^/wget -N --header \"user-agent:1\" http:\/\/bgp.he.net\/graphs\/as/g" _
sed -i "s/$/-ipv4.svg/g" _
cat _ >> svg.sh
rm _
cp svg{,6}.sh
sed -i "s/ipv4/ipv6/g" svg6.sh
chmod +x svg{,6}.sh
rm /tmp/GeoIPASNum2.{csv,zip}
