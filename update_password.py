import crypt
import datetime
import random
import string
import paramiko
import yaml

from os.path import exists, getsize


def createPassword(exclude_password_list: list) -> string:
    specialCharacters = "!$%()-/:=?@_{|}"
    password_characters = string.ascii_letters + string.digits + specialCharacters
    password = ''.join(random.choice(password_characters) for i in range(40))
    if password in exclude_password_list:
        createPassword(exclude_password_list)
    else:
        return password


def hashPassword(password):
    randomsalt = ''.join(random.sample(string.ascii_letters, 8))
    hashedPassword = crypt.crypt(password, '$5$' + randomsalt + '$')
    return hashedPassword


def loadYAML(f):
    file = open(f, 'r')
    y = yaml.load(file, Loader=yaml.SafeLoader)
    file.close()
    return y


def writeYAML(s, f):
    file = open(f, 'a')
    yaml.dump(s, file)
    file.close()

def export_puppet_config(password):
    # I think this would work, but I didn't test it becase I don't ahve an instance of puppet
    return "user\n{'fallback':\n  ensure = > present,\n  password = > '" + hashPassword(password) + "'\n}"


def ssh_change_password(host, ssh_user, ssh_password, new_password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=host,
                       username=ssh_user,
                       password=ssh_password)
    cmd = 'echo "' + new_password + '" | passwd --stdin fallback'
    stdin, stdout, stderr = ssh_client.exec_command(cmd)

    out = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    if error:
        raise Exception('There was an error updating the password: {}'.format(error))
    ssh_client.close()

    return out

def updatePassword(server):
    file_name = server + '.yaml'
    used_passwords = []
    if exists(file_name) and getsize(file_name) > 0:
        password_yaml = loadYAML(file_name)
        for password in password_yaml:
            used_passwords.append(password['password'])
        new_password = [{'password': createPassword(used_passwords), 'created': str(datetime.datetime.now())}]
        writeYAML(new_password, file_name)
    else:
        new_password = [{'password': createPassword([]), 'created': str(datetime.datetime.now())}]
        writeYAML(new_password, file_name)

    ssh_user_credentials = loadYAML('config.yaml')

    ssh_change_password(server,ssh_user_credentials['ssh_user'],ssh_user_credentials['ssh_password'],new_password[0]['password'])
    return 'password changed'