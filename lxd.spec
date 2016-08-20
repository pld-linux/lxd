Summary:	Fast, dense and secure container management
Name:		lxd
Version:	2.0.3
Release:	0.1
License:	Apache v2.0
Group:		Applications/Networking
URL:		https://linuxcontainers.org/lxd/introduction/
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
LXD is a container "hypervisor" and a new user experience for LXC.

Specifically, it's made of three components:
- A system-wide daemon (lxd)
- A command line client (lxc)
- An OpenStack Nova plugin (nova-compute-lxd)

The daemon exports a REST API both locally and if enabled, over the
network.

The command line tool is designed to be a very simple, yet very
powerful tool to manage all your containers. It can handle connect to
multiple container hosts and easily give you an overview of all the
containers on your network, let you create some more where you want
them and even move them around while they're running.

The OpenStack plugin then allows you to use your lxd hosts as compute
nodes, running workloads on containers rather than virtual machines.

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
