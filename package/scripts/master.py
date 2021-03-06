#!/usr/bin/env python

import sys, os, pwd, signal, time
import urllib, tarfile
from resource_management import *
from subprocess import call

class Master(Script):

  def install(self, env):
    import params
    env.set_params(params)

    print 'Install the Mist Master';
    # Install packages listed in metainfo.xml
    self.install_packages(env)
    self.configure(env)

    Execute('find ' + params.service_packagedir + ' -iname "*.sh" | xargs chmod +x')

   # create the log, pid, mits dirs
    Directory([params.mist_pid_dir, params.mist_log_dir, params.mist_dir],
              owner=params.mist_user,
              group=params.mist_group
              )

    print 'Getting mist'
    urllib.urlretrieve ("http://35.157.13.60/mist.tar.gz", "/tmp/mist.tar.gz")

    print 'Untar archive'
    tar = tarfile.open("/tmp/mist.tar.gz")
    tar.extractall(path="/usr/share")
    tar.close()

    print 'Create Mist service'
    Execute (format('cp {service_packagedir}/scripts/mist_service.sh /etc/init.d/mist'),
            user=params.mist_user)
    Execute ('chmod +x /etc/init.d/mist')

    print 'Setup snapshot'
    Execute(format("{service_packagedir}/scripts/setup_snapshot.sh {mist_dir} "
                   "{mist_addr} {mist_port} {setup_view} {service_packagedir} "
                   "{java64_home} >> {mist_log_file}"),
            user=params.mist_user)

    if params.setup_view:
        if params.ambari_host == params.mist_internalhost and not os.path.exists(
                '/var/lib/ambari-server/resources/views/mist-view-1.0.0-SNAPSHOT.jar'):
            Execute('echo "Copying mist view jar to ambari views dir"')
            Execute(format("cp {mist_dir}/mist-view-1.0.0-SNAPSHOT.jar "
                           "/var/lib/ambari-server/resources/views"), ignore_failures=True)

  def configure(self, env):
    import params
    import status_params
    env.set_params(params)
    env.set_params(status_params)

    mist_default=InlineTemplate(status_params.mist_default_template_config)
    File(format("{conf_dir}/default.conf"), content=mist_default, owner='root',group='root', mode=0644)

    mist_routers=InlineTemplate(status_params.mist_routers_template_config)
    File(format("{conf_dir}/router-examples.conf"), content=mist_routers, owner='root',group='root', mode=0644)


  def stop(self, env):
    print 'Stop the Mist Master';
    Execute ('service mist stop')

  def start(self, env):
    self.configure(env)
    print 'Start the Mist Master';
    Execute ('service mist start')

  def status(self, env):
    import status_params
    env.set_params(status_params)

    pid_file = glob.glob(status_params.mist_pid_dir + '/mist.pid')[0]
    check_process_status(pid_file)

if __name__ == "__main__":
  Master().execute()
