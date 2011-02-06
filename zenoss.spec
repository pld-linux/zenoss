# TODO
# - split build/install
# - FHS
# - use system Zope 2.8.8
# - TwistedSNMP-0.3.13
# - pysnmp-3.4.3
# - Twisted-2.5.0
# - TwistedCore-2.5.0
# - pycrypto-1.9a6
# - pynetsnmp-0.27.0
# - ctypes-1.0.1
# - MySQL-python-1.2.0
# - rrdtool-1.2.23
# - epydoc-3.0beta1
# - python-snpp-1.1.1
# - Yapps-2.1.1
# - nagios-plugins-1.4.5
# - libsmi-0.4.5
# - wmi-0.1.5
# - pyip-0.7
# - simplejson-1.4

# the location where zenoss is installed
%define zenhome /opt/zenoss

# the location where zope is installed
%define zopehome %{zenhome}

# mysql is used for the events database
%define mysql_username zenoss
%define mysql_passwd zenoss
%define mysql_database events

# zope is used for the web interface
%define zope_passwd zenoss

# a shell account controls the zenoss processes
%define os_username zenoss
%define os_uid 194
%define os_gid 194
%define os_home /home/zenoss
%define os_shell /bin/bash

# set to 1 if the version of the software to be built is the trunk
# if trunk is set to 0 the version will be extrapolated from the
# rpm information contained in the %{version} and %{release} vars
%define trunk 0

# the location of the snmp configuration file and mysql configuration
%define snmpd_conf /etc/snmp/snmpd.conf
%define my_cnf /etc/my.cnf

# don't terminate the build when there are unpackaged (but installed) files
%define _unpackaged_files_terminate_build 0

Summary:	The Open Source Network Management System
Name:		zenoss
Version:	2.1.3
Release:	1.2
License:	GPL
Group:		Management/Network
Source0:	http://dl.sourceforge.net/zenoss/%{name}-%{version}-0.tar.gz
# Source0-md5:	19ad0dabe9ebce2b2e325aab2dc42301
BuildRequires:	autoconf >= 2.53
BuildRequires:	libstdc++-devel
BuildRequires:	mysql-devel >= 5.0.22
BuildRequires:	python-devel >= 2.3.4
BuildRequires:	rpmbuild(macros) >= 1.202
BuildRequires:	subversion
BuildRequires:	swig >= 1.3
BuildRequires:	zlib-devel
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	net-snmp
Requires:	net-snmp-utils
Requires:	python >= 2.3.4
Suggests:	mysql >= 5.0.22
Provides:	group(%{os_username})
Provides:	user(%{os_username})
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Zenoss is an IT infrastructure monitoring product that allows you to
monitor your entire infrastructure within a single, integrated
software application.

Key features include:
- Monitors the entire stack
  - networks, servers, applications, services, power, environment, etc...
- Monitors across all perspectives
  discovery, configuration, availability, performance, events, alerts, etc.
- Affordable and easy to use
  - unlike the big suites offered by IBM, HP, BMC, CA, etc...
  - unlike first generation open source tools...
- Complete open source package o complete solution available as free,
  open source software

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT

replace() {
    SEARCH=$1
    REPLACE=$2
    FILE=$3
    sed -i -e "s%$SEARCH%$REPLACE%g" $FILE
}

# map environment variables to .spec variables
export ZENHOME=%{zenhome}
export ZOPEPASSWORD=%{zope_passwd}
export PYTHON=/usr/bin/python
export DESTDIR=$RPM_BUILD_ROOT

# load up the build functions
ZEN_BUILD_DIR=$RPM_BUILD_DIR/%{name}-%{version}
PATH=$PATH:. # for sourcing from current dir to work
. $ZEN_BUILD_DIR/build-functions.sh

# set up make and the python path
set_make

# set the SVNTAG variable and honor the trunk flag
if [ "%{trunk}" = "1" ]; then
	SVNTAG="trunk"
else
	SVNTAG="tags/%{name}-%{version}"
fi

# do NOT setuid zensocket
export SETUID=""

# compile external libs and pull down zenoss
compile

# remove the nagios-plugins perl scripts that force ugly deps
DIR=$RPM_BUILD_ROOT/${ZENHOME}/libexec
DIRNAME=$RPM_BUILD_ROOT/${ZENHOME}/libexec

for file in $(grep perl $DIRNAME/* | awk '{print $1}' | cut -d: -f1 | sort -u); do
	rm -f $file
done

# remove the CM artifacts
ZEN_INST_DIR=$RPM_BUILD_ROOT/${ZENHOME}
find $ZEN_INST_DIR -name .svn | xargs rm -rf

# remove the .conf files but leave the .conf.examples
rm $ZEN_INST_DIR/etc/*.conf

# copy some configuration files to the /etc installation directory
ZEN_BUILD_DIR=$RPM_BUILD_DIR/%{name}-%{version}
CONF_DIR=$ZEN_BUILD_DIR/conf
mkdir -p $ZEN_INST_DIR/etc
cp $CONF_DIR/snmpd.conf $ZEN_INST_DIR/etc
cp $CONF_DIR/my.cnf $ZEN_INST_DIR/etc
install -d $ZEN_INST_DIR/log

# land the zenctl into the init.d directory as "zenoss"
INIT_SCRIPT_DIR=$RPM_BUILD_ROOT/etc/rc.d/init.d
START_SCRIPT=$INIT_SCRIPT_DIR/zenoss
INIT_PRE_SCRIPT=$ZEN_INST_DIR/bin/zenoss_init_pre
INIT_POST_SCRIPT=$ZEN_INST_DIR/bin/zenoss_init_post
UPGRADE_PRE_SCRIPT=$ZEN_INST_DIR/bin/zenoss_upgrade_pre
UPGRADE_POST_SCRIPT=$ZEN_INST_DIR/bin/zenoss_upgrade_post
mkdir -p $INIT_SCRIPT_DIR
cp $RPM_BUILD_ROOT/%{zenhome}/bin/zenctl ${START_SCRIPT}

for file in \
	$START_SCRIPT \
	$INIT_PRE_SCRIPT \
	$INIT_POST_SCRIPT \
	$UPGRADE_PRE_SCRIPT \
	$UPGRADE_POST_SCRIPT
do
	replace "\*\*OS_USERNAME\*\*" "%{os_username}" ${file}
	replace "\*\*OS_UID\*\*" "%{os_uid}" ${file}
	replace "\*\*ZENHOME\*\*" "%{zenhome}" ${file}
	replace "\*\*MYSQL_HOST\*\*" "localhost" ${file}
	replace "\*\*MYSQL_ROOT_USERNAME\*\*" "mysql" ${file}
	replace "\*\*MYSQL_ROOT_PASSWD\*\*" "" ${file}
	replace "\*\*MYSQL_HOST\*\*" "localhost" ${file}
	replace "\*\*MYSQL_USERNAME\*\*" "%{mysql_username}" ${file}
	replace "\*\*MYSQL_PASSWD\*\*" "%{mysql_passwd}" ${file}
	replace "\*\*MYSQL_DATABASE\*\*" "%{mysql_database}" ${file}
	replace "\*\*ZOPE_PASSWD\*\*" "%{zope_passwd}" ${file}
	replace "\*\*SNMPD_CONF\*\*" "%{snmpd_conf}" ${file}
	replace "\*\*MY_CNF\*\*" "%{my_cnf}" ${file}
	replace "\*\*ZOPEHOME\*\*" "%{zopehome}" ${file}
	chmod +x $file
done

# copy the [install,shared]-functions because they are used by zenoss_init
cp $ZEN_BUILD_DIR/shared-functions.sh $ZEN_INST_DIR/bin
cp $ZEN_BUILD_DIR/install-functions.sh $ZEN_INST_DIR/bin

# copy filesystem scripts to the real filesystem
cd $ZEN_BUILD_DIR/extras/etc
for file in $(find -type f | grep -v .svn); do
	DEST=$RPM_BUILD_ROOT/etc/$file
	DIR=$(dirname $DEST)
	if [ ! -d $DIR ]; then
		mkdir -p $DIR
	fi

	cp $file $DEST
	replace "\*\*ZENHOME\*\*" "%{zenhome}" $DEST
done

%clean
rm -rf $RPM_BUILD_ROOT

%pre
# called when we are upgrading or reinstalling (but not erasing, or installing)
if [ "$1" -eq 2 ]; then
	# back up the conf files
# XXX using /root, not /tmp for security concern
	TEMP_DIR=/root/zenossrpmupgrade/$$
	mkdir -p $TEMP_DIR
	cp $ZENHOME/etc/*.conf $TEMP_DIR
	echo $TEMP_DIR > /root/zenossrpmupgrade/dirname.txt
fi

# called when we are installing (but not erasing, upgrading, or reinstalling)
if [ "$1" -eq 1 ]; then
	%groupadd -g %{os_gid} %{os_username}
	# TODO: Handle -p '$1$5afX49ZL$sx0UlhhU9QZwbE/howDLk.' ?
	%useradd -r -m -u %{os_uid} -g %{os_username} -d %{os_home} -s %{os_shell} -c "Zenoss Account" %{os_username}
fi

%post
# some files have to be setuid 0.  they are set here
setuid() {
    for file in %{zenhome}/bin/zensocket; do
		chown root:root $file
		chmod 4755 $file
    done
}

# load up the install functions
export ZENHOME=%{zenhome}
. $ZENHOME/bin/shared-functions.sh
. $ZENHOME/bin/install-functions.sh

# kill off any zeo/zope/zen processes that are running
kill_running

# optionally update the bashrc for the user (using the append function)
bashrc=%{os_home}/.bashrc
append ZENHOME %{zenhome} $bashrc
append PATH '${ZENHOME}/bin:${PATH}' $bashrc
append PYTHONPATH %{zenhome}/lib/python $bashrc
append LD_LIBRARY_PATH %{zenhome}/lib $bashrc
chown %{os_username} $bashrc

# run these commands when installing, but not upgrading or reinstalling
if [ "$1" -eq 1 ]; then
	# set environment variables
	export OS_USERNAME=%{os_username}
	export OS_UID=%{os_uid}
	export OS_HOME=%{os_home}
	export OS_SHELL=%{os_shell}

	# set up symlinks for all the runlevels
	/sbin/chkconfig --add zenoss

	# update the files to be setuid
	setuid

	# set the flag to identify this as a fresh install (rather than an
	# upgrade)
	touch $ZENHOME/.fresh_install
fi

# run these commands when upgrading (but not installing or reinstalling)
if [ "$1" -eq 2 ]; then
	# set the flag to identify this as an upgrade (rather than a fresh install)
	touch $ZENHOME/.upgraded

	# update the files to be setuid
	setuid

	# remove the .pyc files that were written by python while zenoss ran
	# XXX: in PLD we (should) package *.py[co]
	find $ZENHOME -name '*.pyc' | xargs rm -f
fi

%preun
# load up the install functions
. %{zenhome}/bin/shared-functions.sh
. %{zenhome}/bin/install-functions.sh

# kill off any zeo/zope/zen processes that are running
kill_running

%postun
# called when we are erasing the package (but not upgrading)
if [ "$1" -eq 0 ]; then
	# restore snmpd.conf and my.cnf
	# XXX: in PLD we should use %config attrs
	if [ -f %{snmpd_conf}.orig ]; then
		cp %{snmpd_conf}.orig %{snmpd_conf}
	fi

	# remove shell account
	%userremove %{os_username}
	%groupremove %{os_username}

	# clean up the various files written by the application
	for target in \
		%{zenhome}/Products \
		%{zenhome}/log \
		%{zenhome}/.fresh_install \
		%{zenhome}/.upgraded
	do
		rm -rf $target
	done
fi

%files
%defattr(644,root,root,755)
%defattr(755,root,root)
%{_sysconfdir}/*

# make the following files owned by zenoss:wheel with the default perms
%defattr(-,zenoss,zenoss)

%dir %{zenhome}
%dir %{zenhome}/Products
%doc %{zenhome}/Products/LICENSE.txt
%doc %{zenhome}/Products/COPYRIGHT.txt
%{zenhome}/Products/AdvancedQuery
%{zenhome}/Products/CMFCore
%{zenhome}/Products/DataCollector
%{zenhome}/Products/Five
%{zenhome}/Products/GenericSetup
%{zenhome}/Products/Hotfix*
%{zenhome}/Products/ManagableIndex
%{zenhome}/Products/OFolder
%{zenhome}/Products/Plug*
%{zenhome}/Products/Zen*

%{zenhome}/doc
%{zenhome}/extras
%{zenhome}/import
%{zenhome}/include
%{zenhome}/lib
%{zenhome}/libexec
%{zenhome}/man
%{zenhome}/share
%{zenhome}/skel
%{zenhome}/etc

%dir %{zenhome}/bin
%{zenhome}/bin/[!z]*
%{zenhome}/bin/z[!e]*
%{zenhome}/bin/ze[!n]*
%{zenhome}/bin/zen[!s]*
%{zenhome}/bin/zens[!o]*

%defattr(4755,root,zenoss)
%{zenhome}/bin/zensocket
