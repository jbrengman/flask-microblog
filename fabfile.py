from fabric.api import run
from fabric.api import env
from fabric.api import prompt
from fabric.api import execute
from fabric.api import sudo
from fabric.contrib.project import rsync_project
import boto.ec2
import time
import os


env.aws_region = 'us-west-2'
env.hosts = ['localhost', ]
env.active_instance = None
env.password = ''


def host_type():
    run('uname -s')


def get_ec2_connection():
    if 'ec2' not in env:
        conn = boto.ec2.connect_to_region(env.aws_region)
        if conn is not None:
            env.ec2 = conn
            print "Connected to EC2 region %s" % env.aws_region
        else:
            msg = "Unable to connect to EC2 region %s"
            raise IOError(msg % env.aws_region)
    return env.ec2


def provision_instance(wait_for_running=False, timeout=60, interval=2):
    wait_val = int(interval)
    timeout_val = int(timeout)
    conn = get_ec2_connection()
    instance_type = 't1.micro'
    key_name = 'pk-aws'
    security_group = 'ssh-access'
    image_id = 'ami-d0d8b8e0'

    reservations = conn.run_instances(
        image_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=[security_group, ]
    )
    new_instances = (
        [i for i in reservations.instances if i.state == u'pending'])
    running_instance = []
    if wait_for_running:
        waited = 0
        while new_instances and (waited < timeout_val):
            time.sleep(wait_val)
            waited += int(wait_val)
            for instance in new_instances:
                state = instance.state
                print "Instance %s is %s" % (instance.id, state)
                if state == "running":
                    running_instance.append(
                        new_instances.pop(new_instances.index(i))
                    )
                instance.update()


def list_aws_instances(verbose=False, state='all'):
    conn = get_ec2_connection()

    reservations = conn.get_all_reservations()
    instances = []
    for res in reservations:
        for instance in res.instances:
            if state == 'all' or instance.state == state:
                instance = {
                    'id': instance.id,
                    'type': instance.instance_type,
                    'image': instance.image_id,
                    'state': instance.state,
                    'instance': instance,
                }
                instances.append(instance)
    env.instances = instances
    if verbose:
        import pprint
        pprint.pprint(env.instances)


def select_instance(state='running'):
    if env.active_instance:
        return

    list_aws_instances(state=state)

    prompt_text = "Please select from the following instances:\n"
    instance_template = " %(ct)d: %(state)s instance %(id)s\n"
    for idx, instance in enumerate(env.instances):
        ct = idx + 1
        args = {'ct': ct}
        args.update(instance)
        prompt_text += instance_template % args
    prompt_text += "Choose an instance: "

    def validation(input):
        choice = int(input)
        if not choice in range(1, len(env.instances) + 1):
            raise ValueError("%d is not a valid instance" % choice)
        return choice

    choice = prompt(prompt_text, validate=validation)
    env.active_instance = env.instances[choice - 1]['instance']


def run_command_on_selected_server(command, state='running', **kwargs):
    select_instance(state)
    selected_hosts = [
        'ubuntu@' + env.active_instance.public_dns_name
    ]
    execute(command, hosts=selected_hosts, **kwargs)


def stop_instance():
    run_command_on_selected_server(_stop_instance)


def _stop_instance():
    env.active_instance.stop()


def terminate_instance():
    run_command_on_selected_server(_terminate_instance, 'stopped')


def _terminate_instance():
    env.active_instance.terminate()


def install_nginx():
    run_command_on_selected_server(_install_nginx)
    create_nginx_config()
    run_command_on_selected_server(restart_nginx)


def _install_nginx():
    sudo('apt-get install nginx -y')
    sudo('/etc/init.d/nginx start')


def restart_nginx():
    sudo('/etc/init.d/nginx restart')


def install_sup(app_name, app_file):
    run_command_on_selected_server(_install_sup)
    create_supervisor_config(app_name, app_file)


def _install_sup():
    sudo('apt-get install supervisor -y')
    sudo('sudo unlink /run/supervisor.sock')  # Why is this necessary?
    sudo('supervisord')


def create_nginx_config():
    server_name = 'http://' + env.active_instance.public_dns_name
    temp = open('nginx_config.template', 'r').read()
    config = temp % {'server_name': server_name}
    config_file = open('nginx.config', 'w')
    config_file.write(config)
    config_file.close()
    run(
        'scp -i ~/.ssh/pk-aws.pem ' + os.getcwd() + '/nginx.config' +
        ' ubuntu@' + env.active_instance.public_dns_name + ':/home/ubuntu')
    run_command_on_selected_server(_move_nginx_conf)


def _move_nginx_conf():
    sudo('mv /home/ubuntu/nginx.config /etc/nginx/sites-available/default')


def create_supervisor_config(app_name, app_file):
    dest = '/etc/supervisor/conf.d/%s.conf' % app_name
    temp = open('sup_config.template', 'r').read()
    config = temp % {'app_name': app_name, 'app_file': app_file}
    config_file = open('sup.config', 'w')
    config_file.write(config)
    config_file.close()
    run(
        'scp -i ~/.ssh/pk-aws.pem ' + os.getcwd() + '/sup.config' +
        ' ubuntu@' + env.active_instance.public_dns_name + ':/home/ubuntu')
    run_command_on_selected_server(_move_sup_conf, path=dest)


def _move_sup_conf(path):
    sudo('mv /home/ubuntu/sup.config ' + path)


def start_supervisor(app_name):
    run_command_on_selected_server(_start_supervisor, app_name=app_name)


def _start_supervisor(app_name):
    sudo('supervisorctl reread')
    sudo('supervisorctl add ' + app_name)


def install_python():
    run_command_on_selected_server(_install_python())


def _install_python():
    sudo('apt-get install python-all-dev python-setuptools python-pip libpq-dev')


def install_postgres():
    run_command_on_selected_server(_install_postgres())


def _install_postgres():
    sudo('apt-get install postgresql postgresql-contrib')


def install_reqs():
    run_command_on_selected_server(_install_reqs())


def _install_reqs():
    sudo('pip install -r requirements.txt')


def setup(app_name, app_file):
    select_instance()
    # run(
    #     'scp -i ~/.ssh/pk-aws.pem ' + os.getcwd() + '/' + app_file +
    #     ' ubuntu@' + env.active_instance.public_dns_name + ':/home/ubuntu')
    rsync_project('~')
    install_python()
    install_postgres()
    install_reqs()
    install_sup(app_name, app_file)
    install_nginx()
    start_supervisor(app_name)


def deploy():
    select_instance
    rsync_project('~')
    install_reqs()
