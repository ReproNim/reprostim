#!/bin/bash
#
# A rudimentary (and potentially still incomplete) script to configure reproiner.
# reproiner is a small box which is attached to magewell screen grabbers, our custom
# micropython events capturer attached to curdes (birch), and also network (usb ethernet) attached
# to the same birch to be able to harvest events on it directly and also to provide it
# with ntp and internet.
# 
# For reuse, it needs to be parametrized since now it has dartmouth and hardware specific
# (e.g. MAC) addresses here and there.
# And may be potentially converted to ansible playbook.
#
set -eu

topd=$(readlink -f "$0" | xargs dirname | xargs dirname)

# default network interface
net_if=$(ip route | awk '/^default/{print $5}')
# configured usb dongle network
birch_if=enx8cae4cdd98c0
udev_rules="$topd/Capture/etc/udev/189-reprostim.rules"
data_path=/data/reprostim
user_name=reprostim




# helper tools installed
apt install -y net-tools ncdu dstat
# tools which will be used by our tools
apt install -y git-annex

if ! id "$user_name" > /dev/null; then
	# might add --disabled-password here
	adduser "$user_name"
	for g in dialout audio dip video plugdev ; do
		adduser "$user_name" $g || echo "failed adding to $g"
	done
	# To stream line future git operations
	su -c 'git config --global user.name "ReproStim User"' "$user_name"
	su -c 'git config --global user.email "changeme@example.com"' "$user_name"
	su -c 'ssh-keygen -q -N "" -f ~/.ssh/id_ed25519 -t ed25519' "$user_name"
fi

#
## Magewell devices "support" for audio/video capture
#
udev_rules_file=$(basename "$udev_rules")
c=/etc/udev/rules.d/"$udev_rules_file"
[ -e "$c" ] || {
	cp "$udev_rules" "$c"
	udevadm control --reload
	# But above is not sufficient if device already connected
	if lsusb | grep -q "ID 2935"; then
		echo "Need to reboot computer for udevd changes to take effect for already attached devices!"
	fi
}

# Install build and run time dependencies -- for now just copy pasted from README.md
apt-get install -y ffmpeg libudev-dev libasound-dev libv4l-dev libyaml-cpp-dev v4l-utils g++ make

#
# Prepare folder/config copy for data
#

[ -e "$data_path" ] || {
	mkdir -p "$data_path"
	cp "$topd/Capture/videocapture/config.yaml" "$data_path"
	chmod o-rwX "$data_path"
	# Let's make it into datalad dataset for git-annex webapp to sync etc
	apt install -y datalad
	datalad create -c text2git -f "$data_path"
	datalad save -d "$data_path" -m "Initial content - just config"
	# TODO: yet to make sure it works -- do not need to bother to add them unlocked
	# seems to not work: https://git-annex.branchable.com/forum/Is_there_a_way_to_have_assistant_add_files_locked__63__/?updated#comment-f24e81205fec4165237a27a53886349c
	git -C "$data_path" config annex.addunlocked  false
	chown "$user_name:$user_name" -R "$data_path"
	if [ $(lsusb | grep -c "ID 2935") -gt 1 ]; then
		echo "Multiple magewell devices detected -- adjust $data_path/config.yaml with device id"
	fi
	# TODO: start here git annex webapp as service - configure to offload to remote
	# location while removing locally
	
}

#
## Install binaries
#
# TODO: rename/package/instlal consistently
if [ ! -e /usr/local/bin/reprostim-videocapture ] && [ -e "$topd/Capture/videocapture/VideoCapture" ]; then
	cp -p "$topd/Capture/videocapture/VideoCapture" "/usr/local/bin/reprostim-videocapture"
	# TODO: add service script setup etc
else
	echo "Need to build VideoCapture"
fi


#
# Connecting to Birch.  It needs us to provide it with dhcp server.
#
# Installed/configured DHCP server for birch to get an address

apt install -y isc-dhcp-server
c=/etc/dhcp/dhcpd.conf

if ! grep birch "$c"; then
	ns=$(awk '/^nameserver/{print $2}' /etc/resolv.conf | head -n 1)
	cat >| $c <<EOF
option domain-name "centerforopenneuroscience.org";
option domain-name-servers $ns, 8.8.8.8;

default-lease-time 600;
max-lease-time 7200;

subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.110 192.168.1.120;
}
  
host birch {
	hardware ethernet b8:27:eb:d0:3f:77;
	fixed-address 192.168.1.10;
	option subnet-mask 255.255.255.0;
	option routers 192.168.1.2;
}
  
ddns-update-style none;
EOF

	service isc-dhcp-server restart
fi

if ! grep -q "$birch_if" /etc/default/isc-dhcp-server; then
	sed -i -e "s,INTERFACESv4=.*,INTERFACESv4=\"$birch_if\",g" /etc/default/isc-dhcp-server
	service isc-dhcp-server restart
fi

# simple way to define custom firewall so we could setup masquarading for birch
apt install -y iptables-persistent
c=/etc/iptables/rules.v4

if ! grep -q "NAT for birch" "$c"; then

	cat >| "$c" << EOF
# Created following a basic tutorial
# https://gridscale.io/en/community/tutorials/debian-router-gateway/
# to establish NAT for birch

*nat
-A POSTROUTING -o $net_if -j MASQUERADE
COMMIT

*filter
-A INPUT -i lo -j ACCEPT
# allow ssh, so that we do not lock ourselves
-A INPUT -i $net_if -p tcp -m tcp --dport 22 -j ACCEPT
# allow ntp
-A INPUT -i $net_if -p udp -m udp --dport 123 -j ACCEPT

# allow incoming traffic to the outgoing connections,
# et al for clients from the private network
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
# prohibit everything else incoming
-A INPUT -i $net_if -j DROP

COMMIT
EOF

	service iptables restart
fi

c=/etc/sysctl.conf
if [ "$(sysctl net.ipv4.ip_forward)" == "net.ipv4.ip_forward = 0" ]; then
	echo "net.ipv4.ip_forward=1" >> "$c"
	sysctl -p
	test "$(sysctl net.ipv4.ip_forward)" = "net.ipv4.ip_forward = 1"
fi

# ntp server
apt install -y ntpsec

s=ntp.dartmouth.edu 

c=/etc/ntpsec/ntp.conf
if ! grep "$s" "$c"; then
	sed -i -e "s,^\(# server .*nts\$\),\1\nserver $s,g" "$c"
fi
