# Is this a nightly build?
%global nightly 0

# We need this because we are no longer noarch, since our bundled deps might
# conceivably need to compile arch-specific things. But we currently have no
# useful debuginfo stuff.
%global debug_package %{nil}

%if 0%{?nightly}
%global snap %(date +'%Y%m%d')git
%global nightly_pretag .dev0
%endif

# Disable shebang munging for specific paths.  These files are data files.
# ansible-test munges the shebangs itself.
%global __brp_mangle_shebangs_exclude_from_file %{SOURCE1}

%global commitId 2fdb9767e93eebf4b25be2661bd7bbf756ea5d2e

# RHEL and Fedora add -s to the shebang line.  We do *not* use -s -E -S or -I
# with ansible because it has many optional features which users need to
# install libraries on their own to use.  For instance, paramiko for the
# network connection plugins or winrm to talk to windows hosts.
# Set this to nil to remove -s
%define py_shbang_opts %{nil}
%define py2_shbang_opts %{nil}
%define py3_shbang_opts %{nil}

%define vendor_path %{buildroot}%{python3_sitelib}/ansible/_vendor/
%define vendor_pip /usr/bin/python3 -m pip install --no-deps -v --no-binary :all: -t %{vendor_path}

# These control which bundled dep versions we pin against
%global packaging_version 20.4
%global pyparsing_version 2.4.7


Name: ansible-core
Summary: SSH-based configuration management, deployment, and task execution system
Version: 2.11.5
%if 0%{?nightly}
Release: 0.1.%{snap}%{?dist}
%else
Release: 3%{?dist}
%endif

Group: Development/Libraries
License: GPLv3+
%if 0%{?nightly}
Source0: %{name}-%{version}%{nightly_pretag}.tar.gz
%else
Source0: ansible-2fdb9767e93eebf4b25be2661bd7bbf756ea5d2e.tar.gz
%endif
Source1: ansible-test-data-files.txt

# And bundled deps
Source2: packaging-ded06cedf6e20680eea0363fac894cb4a09e7831.tar.gz
Source3: pyparsing-6a844ee35ca5125490a28dbd6dd2d15b6498e605.tar.gz

# Deps to build man pages
Source5: straightplugin-6634ea8e1e89d5bb23804f50e676f196c52c46ed.tar.gz

URL: http://ansible.com

# We obsolete old ansible, and any version of ansible-base.
Obsoletes: ansible < 2.10.0
Obsoletes: ansible-base

# ... and provide 'ansible' so that old packages still work without updated
# spec files.
# Provides: ansible

# Bundled provides that are sprinkled throughout the codebase.
Provides: bundled(python-backports-ssl_match_hostname) = 3.7.0.1
Provides: bundled(python-distro) = 1.5.0
Provides: bundled(python-selectors2) = 1.1.1
Provides: bundled(python-six) = 1.13.0

# Things we explicitly bundle via src rpm, and put in ansible._vendor
Provides: bundled(python-packaging) = %{packaging_version}
Provides: bundled(python-pyparsing) = %{pyparsing_version}

BuildRequires: python3-devel
BuildRequires: python3-docutils
BuildRequires: python3-jinja2
BuildRequires: python3-pip
BuildRequires: python3-pyyaml
BuildRequires: python3-resolvelib
BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools
BuildRequires: python3-wheel
BuildRequires: make git

Requires: git
Requires: python3
Requires: python3-jinja2
Requires: python3-PyYAML
Requires: python3-cryptography
Requires: python3-resolvelib
Requires: python3-six
Requires: sshpass

%description
Ansible is a radically simple model-driven configuration management,
multi-node deployment, and remote task execution system. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

%package -n ansible-test
Summary: Tool for testing ansible plugin and module code
Requires: %{name} = %{version}-%{release}

%description -n ansible-test
Ansible is a radically simple model-driven configuration management,
multi-node deployment, and remote task execution system. Ansible works
over SSH and does not require any software or daemons to be installed
on remote nodes. Extension modules can be written in any language and
are transferred to managed machines automatically.

This package installs the ansible-test command for testing modules and plugins
developed for ansible.

%prep
%setup -q -T -b 2 -n packaging-ded06cedf6e20680eea0363fac894cb4a09e7831
%setup -q -T -b 3 -n pyparsing-6a844ee35ca5125490a28dbd6dd2d15b6498e605
%setup -q -T -b 5 -n straightplugin-6634ea8e1e89d5bb23804f50e676f196c52c46ed
%setup -q -n ansible-%{commitId}

%build
/usr/bin/python3 setup.py build

%install
/usr/bin/python3 setup.py install --root %{buildroot}

# Handle bundled deps:
%{vendor_pip} \
  ../pyparsing-6a844ee35ca5125490a28dbd6dd2d15b6498e605/ \
  ../packaging-ded06cedf6e20680eea0363fac894cb4a09e7831/

# Create system directories that Ansible defines as default locations in
# ansible/config/base.yml
DATADIR_LOCATIONS='%{_datadir}/ansible/collections
%{_datadir}/ansible/plugins/doc_fragments
%{_datadir}/ansible/plugins/action
%{_datadir}/ansible/plugins/become
%{_datadir}/ansible/plugins/cache
%{_datadir}/ansible/plugins/callback
%{_datadir}/ansible/plugins/cliconf
%{_datadir}/ansible/plugins/connection
%{_datadir}/ansible/plugins/filter
%{_datadir}/ansible/plugins/httpapi
%{_datadir}/ansible/plugins/inventory
%{_datadir}/ansible/plugins/lookup
%{_datadir}/ansible/plugins/modules
%{_datadir}/ansible/plugins/module_utils
%{_datadir}/ansible/plugins/netconf
%{_datadir}/ansible/roles
%{_datadir}/ansible/plugins/strategy
%{_datadir}/ansible/plugins/terminal
%{_datadir}/ansible/plugins/test
%{_datadir}/ansible/plugins/vars'

UPSTREAM_DATADIR_LOCATIONS=$(grep -ri default lib/ansible/config/base.yml | tr ':' '\n' | grep '/usr/share/ansible')

if [ "$SYSTEM_LOCATIONS" != "$UPSTREAM_SYSTEM_LOCATIONS" ] ; then
	echo "The upstream Ansible datadir locations have changed.  Spec file needs to be updated"
	exit 1
fi

mkdir -p %{buildroot}%{_datadir}/ansible/plugins/
for location in $DATADIR_LOCATIONS ; do
	mkdir %{buildroot}"$location"
done
mkdir -p %{buildroot}%{_sysconfdir}/ansible/
mkdir -p %{buildroot}%{_sysconfdir}/ansible/roles/

cp examples/hosts %{buildroot}%{_sysconfdir}/ansible/
cp examples/ansible.cfg %{buildroot}%{_sysconfdir}/ansible/
mkdir -p %{buildroot}/%{_mandir}/man1/
# Build man pages

mkdir /tmp/_vendor
/usr/bin/python3 -m pip install ../straightplugin-6634ea8e1e89d5bb23804f50e676f196c52c46ed -t /tmp/_vendor

# Remove plugins not needed, they bring in more dependencies
find hacking/build_library/build_ansible/command_plugins ! -name 'generate_man.py' -type f -exec rm -f {} +

PYTHON=python3 PYTHONPATH=%{vendor_path}:/tmp/_vendor make docs
cp -v docs/man/man1/*.1 %{buildroot}/%{_mandir}/man1/

cp -pr docs/docsite/rst .
cp -p lib/ansible_core.egg-info/PKG-INFO .

%files
%defattr(-,root,root)
%{_bindir}/ansible*
%exclude %{_bindir}/ansible-test
%config(noreplace) %{_sysconfdir}/ansible/
%doc README.rst PKG-INFO COPYING
%doc changelogs/CHANGELOG-v2.*.rst
%doc %{_mandir}/man1/ansible*
%{_datadir}/ansible/
%{python3_sitelib}/ansible*
%exclude %{python3_sitelib}/ansible_test

%files -n ansible-test
%{_bindir}/ansible-test
%{python3_sitelib}/ansible_test

%changelog
* Thu Oct 07 2021 Alfredo Moralejo <amoralej@redhat.com> - 2.11.5-3
- Adapted to be built in CentOS Stream 8

* Wed Sep 15 2021 Josh Boyer <jwboyer@redhat.com> - 2.11.5-2
- ansible-core 2.11.5-2

* Mon Sep 13 2021 Josh Boyer <jwboyer@redhat.com> - 2.11.3-3
- Bump for build

* Wed Jul 21 2021 Paul Belanger <pabelanger@redhat.com> - 2.11.3-2
- Add git dependency for ansible-galaxy CLI command.

* Tue Jul 20 2021 Yanis Guenane <yguenane@redhat.com> - 2.11.3-1
- ansible-core 2.11.3-1

* Fri Jul 02 2021 Satoe Imaishi <simaishi@redhat.com> - 2.11.2-2
- Add man pages

* Tue Jun 29 2021 Paul Belanger <pabelanger@redhat.com> - 2.11.2-1
- ansible-core 2.11.2 released.
- Drop bundled version of resolvelib in favor of
  python38-resolvelib.

* Wed Mar 31 2021 Rick Elrod <relrod@redhat.com> - 2.11.0b4-1
- ansible-core 2.11.0 beta 4

* Thu Mar 18 2021 Rick Elrod <relrod@redhat.com> - 2.11.0b2-3
- Try adding a Provides for old ansible.

* Thu Mar 18 2021 Rick Elrod <relrod@redhat.com> - 2.11.0b2-2
- Try Obsoletes instead of Conflicts.

* Thu Mar 18 2021 Rick Elrod <relrod@redhat.com> - 2.11.0b2-1
- ansible-core 2.11.0 beta 2
- Conflict with old ansible and ansible-base.

* Thu Mar 11 2021 Rick Elrod <relrod@redhat.com> - 2.11.0b1-1
- ansible-core 2.11.0 beta 1

* Mon Nov 30 2020 Rick Elrod <relrod@redhat.com> - 2.11.0-1
- ansible-core, beta

* Wed Jun 10 2020 Rick Elrod <relrod@redhat.com> - 2.10.0-1
- ansible-base, beta
