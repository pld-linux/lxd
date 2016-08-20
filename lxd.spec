Summary:	Fast, dense and secure container management
Name:		lxd
Version:	2.1
Release:	0.1
License:	Apache v2.0
Group:		Applications/System
Source0:	https://linuxcontainers.org/downloads/lxd/%{name}-%{version}.tar.gz
# Source0-md5:	535d78758d3ca3542326eb6f3e072ccf
Source1:	%{name}.service
Source2:	%{name}.init
Source3:	%{name}.sysconfig
URL:		http://linuxcontainers.org/
BuildRequires:	criu-devel >= 1.7
BuildRequires:	golang >= 1.5
BuildRequires:	lxc-devel >= 1.1
BuildRequires:	rpmbuild(macros) >= 1.228
Requires(post,preun):	/sbin/chkconfig
Requires(postun):	/usr/sbin/groupdel
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires:	rc-scripts >= 0.4.0.10
Requires:	squashfs
Requires:	uname(release) >= 4.1
Provides:	group(lxd)
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# binary stripped or something
%define		_enable_debug_packages 0

%description
LXD is a container "hypervisor" and a new user experience for LXC.

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

%prep
%setup -q

%build
export GOPATH=$(pwd)/dist
cd $GOPATH/src/github.com/lxc/lxd/
go install -v ./lxd
go install -v ./lxc

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_bindir},%{_sbindir},%{_mandir}/man1,/etc/{rc.d/init.d,sysconfig},%{systemdunitdir}} \
	$RPM_BUILD_ROOT/var/lib/%{name} \
        $RPM_BUILD_ROOT/var/log/%{name}

install -p dist/bin/lxd $RPM_BUILD_ROOT%{_sbindir}/
install -p dist/bin/lxc $RPM_BUILD_ROOT%{_bindir}/

cp -p %{SOURCE1} $RPM_BUILD_ROOT%{systemdunitdir}
install -p %{SOURCE2} $RPM_BUILD_ROOT/etc/rc.d/init.d/%{name}
cp -p %{SOURCE3} $RPM_BUILD_ROOT/etc/sysconfig/%{name}

%pre
%groupadd -g 297 %{name}

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
%doc README.md CONTRIBUTING.md AUTHORS
%config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/%{name}
%attr(754,root,root) /etc/rc.d/init.d/%{name}
%attr(755,root,root) %{_bindir}/lxc
%attr(755,root,root) %{_sbindir}/%{name}
%{systemdunitdir}/%{name}.service
%dir %attr(700,root,root) /var/lib/%{name}
%dir %attr(750,root,logs) /var/log/%{name}
