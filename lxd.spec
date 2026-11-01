Summary:	Fast, dense and secure container and virtual machine management
Name:		lxd
Version:	6.10.1
Release:	1
License:	AGPL v3.0
Group:		Applications/System
Source0:	https://github.com/canonical/lxd/archive/refs/tags/%{name}-%{version}.tar.gz
# Source0-md5:	76c77c5cedf3fefe2351e5bb90dc4af8
Source1:	%{name}.service
Source2:	%{name}.init
Source3:	%{name}.sysconfig
Source4:	%{name}.sh
# cd %{name}-%{name}-%{version}
# go mod vendor
# tar cJf ../%{name}-vendor-%{version}.tar.xz vendor
Source5:	%{name}-vendor-%{version}.tar.xz
# Source5-md5:	7b4d3b97dde7e67358341d1d0c9e600c
Source6:	%{name}-dnsmasq.conf
Patch0:		%{name}-leaf-cert-auth.patch
URL:		https://canonical.com/lxd/
BuildRequires:	acl-devel
BuildRequires:	dqlite-devel >= 1.18.0
BuildRequires:	golang >= 1.27.1
BuildRequires:	libcap-devel
BuildRequires:	lxc-devel >= 5.0.0
BuildRequires:	pkgconfig
BuildRequires:	rpmbuild(macros) >= 1.644
BuildRequires:	sqlite3-devel
BuildRequires:	udev-devel
Requires(post,preun):	/sbin/chkconfig
# usermod --add-subuids
Requires(post):	shadow >= 4.9
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(post,preun,postun):	systemd-units >= 38
# /etc/dnsmasq.d read by default config
Requires:	dnsmasq >= 2.93-3
Requires:	iproute2
# preferred firewall backend for managed networks (NAT, DHCP, ACLs)
Requires:	nftables
Requires:	rc-scripts >= 0.4.0.10
Requires:	rsync
Requires:	squashfs
# for sqfs2tar
Requires:	squashfs-tools-ng
Requires:	tar
Requires:	uidmap
Requires:	uname(release) >= 4.1
Requires:	systemd-units >= 38
Requires:	xz
Suggests:	%{name}-agent = %{version}-%{release}
Suggests:	cdrkit-mkisofs
Suggests:	edk2-ovmf
Suggests:	lxcfs
Suggests:	qemu-img >= 8.2.2
%ifarch %{x8664}
Suggests:	qemu-system-x86 >= 8.2.2
%endif
Suggests:	swtpm
Suggests:	virtiofsd >= 1.10.0
Provides:	group(lxd)
ExclusiveArch:	%{ix86} %{x8664} %{arm} aarch64
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_enable_debug_packages 0
%define		gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%define		goinstall go install -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v
%define		gopath		%{_libdir}/golang
%define		import_path	github.com/lxc/lxd
%define		_libexecdir	%{_prefix}/lib

%description
LXD is a next generation system container and virtual machine manager.

Specifically, it is made of two components:
- A system-wide daemon (lxd)
- A command line client (lxc)

The daemon exports a REST API both locally and if enabled, over the
network.

The command line tool is designed to be a very simple, yet very
powerful tool to manage all your containers. It can handle connect to
multiple container hosts and easily give you an overview of all the
containers on your network, let you create some more where you want
them and even move them around while they are running.

%package agent
Summary:	LXD Agent
Group:		Applications/System

%description agent
This package contains lxd-agent, a statically linked program that LXD
injects into the virtual machines (not containers) it manages. Install
it on the LXD host.

%package tools
Summary:	LXD Tools
Group:		Applications/System

%description tools
This package contains lxd extra tools

%package -n bash-completion-%{name}
Summary:	bash-completion for %{name}
Summary(pl.UTF-8):	Bashowe dopełnianie parametrów dla %{name}
Group:		Applications/Shells
Requires:	%{name} = %{version}-%{release}
Requires:	bash-completion >= 2.0
BuildArch:	noarch

%description -n bash-completion-%{name}
bash-completion for %{name}

%description -n bash-completion-%{name} -l pl.UTF-8
Bashowe dopełnianie parametrów dla %{name}

%prep
%setup -q -n %{name}-%{name}-%{version} -a5
%patch -P0 -p1

%build
export GOPATH=$(pwd)/_dist
export GOBIN=$GOPATH/bin
# flags from ArchLinux package
export GOFLAGS="-buildmode=pie -trimpath -mod=vendor"
export GOCACHE=$(pwd)/.go-cache
export CGO_CPPFLAGS="%{rpmcppflags}"
export CGO_CFLAGS="%{rpmcflags}"
export CGO_LDFLAGS="%{rpmldflags}"
export CGO_LDFLAGS_ALLOW="-Wl,-z,now"

# cgo and tags as in upstream Makefile
%goinstall -tags libsqlite3 ./lxd
%goinstall ./lxc ./fuidshift
CGO_ENABLED=0 %goinstall -tags netgo ./lxd-user ./lxd-benchmark
# lxd-agent runs in VM guests and lxd-convert on migration sources of any
# distribution: fully static, and PIE would add an ld.so interpreter
CGO_ENABLED=0 GOFLAGS="-trimpath -mod=vendor" %goinstall -tags netgo ./lxd-convert
CGO_ENABLED=0 GOFLAGS="-trimpath -mod=vendor" %goinstall -tags agent,netgo ./lxd-agent

# the client wants a writable config dir even for completion and manpage
export LXD_CONF=$(pwd)/.lxd-conf
$GOBIN/lxc completion bash > lxc.bash
install -d man
$GOBIN/lxc manpage man
$GOBIN/lxd manpage man

# conflict
mv doc/README.md doc/README.doc.md

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_bindir},%{_sbindir},%{_mandir}/man1,/etc/{rc.d/init.d,sysconfig,dnsmasq.d},%{systemdunitdir}} \
	$RPM_BUILD_ROOT%{_libexecdir} \
	$RPM_BUILD_ROOT%{bash_compdir} \
	$RPM_BUILD_ROOT/var/lib/%{name}/{containers,devices,devlxd,images,security,shmounts,snapshots} \
	$RPM_BUILD_ROOT/var/log/%{name}

install -p _dist/bin/{lxd,lxd-user,lxd-agent} $RPM_BUILD_ROOT%{_sbindir}
install -p _dist/bin/{lxc,fuidshift,lxd-benchmark,lxd-convert} $RPM_BUILD_ROOT%{_bindir}

cp -p lxc.bash $RPM_BUILD_ROOT%{bash_compdir}/lxc
cp -p man/*.1 $RPM_BUILD_ROOT%{_mandir}/man1

cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdunitdir}
install -p %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/%{name}
cp -p %{SOURCE6} $RPM_BUILD_ROOT/etc/dnsmasq.d/%{name}.conf

install -p %{SOURCE4} $RPM_BUILD_ROOT%{_libexecdir}/lxd-wrapper

%pre
%groupadd -g 273 %{name}

%post
# unprivileged containers need a subordinate id range for root; PLD's
# /etc/subuid and /etc/subgid ship without one
if ! grep -qs '^root:' /etc/subuid; then
	/usr/sbin/usermod --add-subuids 1000000-1000999999 root
fi
if ! grep -qs '^root:' /etc/subgid; then
	/usr/sbin/usermod --add-subgids 1000000-1000999999 root
fi
# a running system dnsmasq reads /etc/dnsmasq.d/%{name}.conf only at start
%service -q dnsmasq restart
%systemd_service_restart dnsmasq.service
/sbin/chkconfig --add %{name}
# no service restart here: stopping lxd runs "lxd shutdown", which stops every instance
%systemd_post %{name}.service


%preun
if [ "$1" = "0" ]; then
	%service -q %{name} stop
	/sbin/chkconfig --del %{name}
fi
%systemd_preun %{name}.service

%postun
if [ "$1" = "0" ]; then
	%groupremove %{name}
fi
%systemd_reload

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc README.md AUTHORS doc/*
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%config(noreplace) %verify(not md5 mtime size) /etc/dnsmasq.d/%{name}.conf
%attr(754,root,root) /etc/rc.d/init.d/%{name}
%attr(755,root,root) %{_bindir}/lxc
%attr(755,root,root) %{_sbindir}/lxd
%attr(755,root,root) %{_sbindir}/lxd-user
%{systemdunitdir}/%{name}.service
%{_mandir}/man1/lxc*.1*
%{_mandir}/man1/lxd*.1*
%attr(750,root,root) %{_libexecdir}/%{name}-wrapper
%dir %attr(750,root,logs) /var/log/%{name}
%dir %attr(711,root,lxd) /var/lib/%{name}
%dir %attr(711,root,root) /var/lib/%{name}/containers
%dir %attr(700,root,root) /var/lib/%{name}/devices
%dir %attr(700,root,root) /var/lib/%{name}/devlxd
%dir %attr(700,root,root) /var/lib/%{name}/images
%dir %attr(700,root,root) /var/lib/%{name}/security
%dir %attr(711,root,root) /var/lib/%{name}/shmounts
%dir %attr(700,root,root) /var/lib/%{name}/snapshots

%files agent
%defattr(644,root,root,755)
%attr(755,root,root) %{_sbindir}/lxd-agent

%files tools
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/fuidshift
%attr(755,root,root) %{_bindir}/lxd-benchmark
%attr(755,root,root) %{_bindir}/lxd-convert

%files -n bash-completion-%{name}
%defattr(644,root,root,755)
%{bash_compdir}/lxc
