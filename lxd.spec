Summary:	Fast, dense and secure container and virtual machine management
Name:		lxd
Version:	3.22
Release:	1
License:	Apache v2.0
Group:		Applications/System
Source0:	https://linuxcontainers.org/downloads/lxd/%{name}-%{version}.tar.gz
# Source0-md5:	3bbcfd764058f0383dfb599df635e0bb
Source1:	%{name}.service
Source2:	%{name}.init
Source3:	%{name}.sysconfig
Source4:	%{name}.sh
URL:		http://linuxcontainers.org/
BuildRequires:	acl-devel
%ifarch %{x8664} arm aarch64 ppc64
BuildRequires:	criu-devel >= 1.7
%endif
BuildRequires:	dqlite-devel >= 1.4.0
BuildRequires:	golang >= 1.5
BuildRequires:	libco-devel
BuildRequires:	libuv-devel
BuildRequires:	lxc-devel >= 3.0
BuildRequires:	pkgconfig
BuildRequires:	raft-devel
BuildRequires:	rpmbuild(macros) >= 1.228
BuildRequires:	udev-devel
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires:	dnsmasq
Requires:	iproute2
Requires:	libcgroup
Requires:	rc-scripts >= 0.4.0.10
Requires:	rsync
Requires:	squashfs
# for sqfs2tar
Requires:	squashfs-tools-ng
Requires:	tar
Requires:	uname(release) >= 4.1
Requires:	xz
Provides:	group(lxd)
ExclusiveArch:	%{ix86} %{x8664} %{arm}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_enable_debug_packages 0
%define		gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**};
%define		goinstall go install -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x
%define		gopath		%{_libdir}/golang
%define		import_path	github.com/lxc/lxd
%define		_libexecdir	%{_prefix}/lib

%description
LXD is a next generation system container and virtual machine manager.

Specifically, it is made of three components:
- A system-wide daemon (lxd)
- A command line client (lxc)
- An OpenStack Nova plugin (nova-compute-lxd)

The daemon exports a REST API both locally and if enabled, over the
network.

The command line tool is designed to be a very simple, yet very
powerful tool to manage all your containers. It can handle connect to
multiple container hosts and easily give you an overview of all the
containers on your network, let you create some more where you want
them and even move them around while they are running.

The OpenStack plugin then allows you to use your lxd hosts as compute
nodes, running workloads on containers rather than virtual machines.

%package agent
Summary:	LXD Agent

%description agent
This package contains lxd-agent program to be used inside virtual
machines (not containers) managed by LXD.

%package -n bash-completion-%{name}
Summary:	bash-completion for %{name}
Summary(pl.UTF-8):	Bashowe dopełnianie parametrów dla %{name}
Group:		Applications/Shells
Requires:	%{name} = %{version}-%{release}
Requires:	bash-completion >= 2.0
%if "%{_rpmversion}" >= "5"
BuildArch:	noarch
%endif

%description -n bash-completion-%{name}
bash-completion for %{name}

%description -n bash-completion-%{name} -l pl.UTF-8
Bashowe dopełnianie parametrów dla %{name}

%prep
%setup -q

%build
export GOPATH=$(pwd)/_dist
export GOBIN=$GOPATH/bin

%goinstall -tags libsqlite3 ./...
CGO_ENABLED=0 %goinstall -tags netgo ./lxd-p2c
%goinstall -tags agent ./lxd-agent

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_bindir},%{_sbindir},%{_mandir}/man1,/etc/{rc.d/init.d,sysconfig},%{systemdunitdir}} \
	$RPM_BUILD_ROOT%{_libexecdir} \
	$RPM_BUILD_ROOT%{bash_compdir} \
	$RPM_BUILD_ROOT/var/lib/%{name}/{containers,devices,devlxd,images,security,shmounts,snapshots} \
	$RPM_BUILD_ROOT/var/log/%{name}

# lxd refuses to start containter without this directory
install -d $RPM_BUILD_ROOT%{_libdir}/%{name}/rootfs

install -p _dist/bin/{lxd,lxd-agent,lxc-to-lxd,lxd-p2c} $RPM_BUILD_ROOT%{_sbindir}
install -p _dist/bin/{lxc,fuidshift} $RPM_BUILD_ROOT%{_bindir}

# FIXME: it seems that bash completions must be named as command (lxc), so
# it conflicts with lxc completions (bash-completion-lxc)
install -p scripts/bash/lxd-client $RPM_BUILD_ROOT%{bash_compdir}/lxc

cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdunitdir}
install -p %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/%{name}

install -p %{SOURCE4} $RPM_BUILD_ROOT%{_libexecdir}/lxd-wrapper

%pre
%groupadd -g 273 %{name}

%post
/sbin/chkconfig --add %{name}
%service -n %{name} restart
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
%attr(754,root,root) /etc/rc.d/init.d/%{name}
%attr(755,root,root) %{_bindir}/lxc
%attr(755,root,root) %{_bindir}/fuidshift
%attr(755,root,root) %{_sbindir}/lxd
%attr(755,root,root) %{_sbindir}/lxd-p2c
%attr(755,root,root) %{_sbindir}/lxc-to-lxd
%{systemdunitdir}/%{name}.service
%dir %attr(750,root,root) %{_libdir}/%{name}
%dir %attr(750,root,root) %{_libdir}/%{name}/rootfs
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

%files -n bash-completion-%{name}
%defattr(644,root,root,755)
%{bash_compdir}/lxc
