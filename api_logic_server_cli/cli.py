# -*- coding: utf-8 -*-

'''
CLICK functions for API Logic Server CLI

To add a new arg:

    * update cli_args_base.py
    
    * add args here (arg, and call to Project.run)

    * update Project.run() 

Main code is api_logic_server.py (PR)
'''

from contextlib import closing

import yaml

temp_created_project = "temp_created_project"   # see if_mounted

import subprocess, os, time, requests, sys, re, io
import socket
import subprocess
from os.path import abspath
from os.path import realpath
from pathlib import Path
from shutil import copyfile
import shutil
import importlib.util
from pathlib import Path
from dotmap import DotMap
import json

from flask import Flask

import logging
import datetime
from typing import NewType
import sys
import os
import importlib
import click

class HideDunderCommand(click.Command):
    """remove redundant option_name from --help
    https://stackoverflow.com/questions/62182687/custom-help-in-python-click
    Args:
        click (_type_): _description_

Options:

Project Location

  --project-name TEXT
             
Project location

SQLAlchemy Database URL - see above

  --db-url TEXT
                   
SQLAlchemy Database URL - see above

Last node of API Logic Server url    
    """
    def format_help(self, ctx, formatter):
        text = click.Command.format_help(self, ctx, formatter)  # req'd to populate formatter.buffer
        buffer = formatter.buffer
        buffer_new = []
        buffer_line = 0
        while buffer_line < len(buffer):
            this_line = buffer[buffer_line]
            if '--infer_primary_key' in this_line:
                debug_string = 'nice breakpoint'
            if "_" in this_line:
                if '\n' in buffer[buffer_line+1]:
                    buffer_line += 1
                buffer_line += 2
            else:
                truncate = this_line.find('/ --no')
                if False and truncate > 0:
                    debug_string = 'nice breakpoint'
                    this_line = this_line[0: truncate] + '/ --no..'
                    buffer_line += 1
                buffer_new.append(this_line)
                if 'Show this message and exit' in this_line:
                    debug_string = 'nice breakpoint'
            buffer_line += 1
        formatter.buffer = buffer_new
        pass


def get_api_logic_server_path() -> Path:
    """
    :return: ApiLogicServer path, eg, /Users/val/dev/ApiLogicServer/api_logic_server_cli
    """
    running_at = Path(__file__)
    python_path = running_at.parent.absolute()
    return python_path


def get_api_logic_server_dir() -> str:
    """
    :return: ApiLogicServer dir, eg, /Users/val/dev/ApiLogicServer
    """
    running_at = Path(__file__)
    python_path = running_at.parent.absolute()
    return str(python_path)


# print("sys.path.append(get_api_logic_server_dir())\n",get_api_logic_server_dir())
sys.path.append(get_api_logic_server_dir())  # e.g, on Docker: export PATH="/home/api_logic_server/api_logic_server_cli"
api_logic_server_path = os.path.dirname(get_api_logic_server_dir())  # e.g: export PATH="/home/api_logic_server"
sys.path.append(api_logic_server_path)
from create_from_model.model_creation_services import ModelCreationServices
import create_from_model.api_logic_server_utils as create_utils
import api_logic_server_cli.create_from_model.uri_info as uri_info
import api_logic_server_cli.api_logic_server as PR
''' ProjectRun (main class) '''
from api_logic_server_cli.cli_args_base import OptLocking

api_logic_server_info_file_name = str(get_api_logic_server_path().joinpath("api_logic_server_info.yaml"))

api_logic_server_info_file_dict = {}  # last-run (debug, etc) info
""" contains last-run info, debug switches to show args, etc """

if Path(api_logic_server_info_file_name).is_file():
    api_logic_server_info_file = open(api_logic_server_info_file_name)
    api_logic_server_info_file_dict = yaml.load(api_logic_server_info_file, Loader=yaml.FullLoader)
    api_logic_server_info_file.close()


last_created_project_name = api_logic_server_info_file_dict.get("last_created_project_name","")
default_db = "default = nw.sqlite, ? for help"
default_project_name = "ApiLogicProject"
default_fab_host = "localhost"
os_cwd = os.getcwd()
default_bind_key_url_separator = "-"  # admin app fails with "/" or ":" (json issues?)
last_login_token = api_logic_server_info_file_dict.get("last_login_token","")

if os.path.exists('/home/api_logic_server'):  # docker?
    default_project_name = "/localhost/ApiLogicProject"
    default_fab_host = "0.0.0.0"


def resolve_blank_project_name(project_name: str, as_project: str = "ApiLogicProject") -> str:
    """if project_name is "", and running from dev, resolve to as_project

    Args:
        project_name (str): project_name provided to CLI
        as_project (str, optional): project name to use. Defaults to "ApiLogicProject".

    Returns:
        str: str of full resolved path
    """
    if project_name == "":
        project_name=os.getcwd()
        if project_name == get_api_logic_server_dir():  # for ApiLogicServer dev (from |> Run and Debug )
            project_name = str(
                Path(project_name).parent.parent.joinpath("servers").joinpath(as_project)
            )
    return project_name


def is_docker() -> bool:
    """ running docker?  dir exists: /home/api_logic_server """
    path = '/home/api_logic_server'
    path_result = os.path.isdir(path)  # this *should* exist only on docker
    env_result = "DOCKER" == os.getenv('APILOGICSERVER_RUNNING')
    # assert path_result == env_result
    return path_result or env_result


@click.group(invoke_without_command=True)
# @click.group()
@click.pass_context
def main(ctx):
    """
    Creates [and runs] logic-enabled Python database API Logic Projects.

\b    
        Creation is from your database (--db-url identifies a SQLAlchemy database)

\b
        Doc: https://apilogicserver.github.io/Docs
        And: https://apilogicserver.github.io/Docs/Database-Connectivity/
\b
    Suggestions:

\b
        ApiLogicServer start                                # create and manage projects
        ApiLogicServer create --db-url= --project-name=     # defaults to Northwind sample
    """
    pass  # all commands come through here
    if not ctx.invoked_subcommand:  # no command, per invoke_without_command=True
            sys.stdout.write("    Suggestion: ApiLogicServer start \n\n\n")
     

@main.command("start")
@click.pass_context
@click.option('--open-with', 'open_with',
              default='code',
              help="Simplifies creating and managing projects")
@click.option('--clean/--no-clean', "clean",
              default=False, is_flag=True,
              help="Overlay existing manager")
def create_start_manager(ctx, open_with, clean: click.BOOL = False):
    """
        Create and Manage API Logic Projects.
    """
    to_dir = Path(os.getcwd())
    path = Path(__file__)
    from_dir = get_api_logic_server_path().joinpath('prototypes/code')
    to_dir_str = str(to_dir)
    to_dir_check = Path(to_dir).joinpath('venv')
    if not Path(to_dir).joinpath('venv').exists():
        log.info(f"    No action taken - no venv found at: \n      {to_dir}\n\n")
        exit(1)
    to_dir_check = Path(to_dir).joinpath('.vscode')
    if to_dir_check.exists() and not clean:
        log.info(f"    Using manager at: {to_dir}\n\n")
    else:
        if to_dir_check.exists():
            log.info(f"    Cleaning manager at: {to_dir}\n\n")
        copied_path = shutil.copytree(src=from_dir, dst=to_dir, dirs_exist_ok=True)
        log.info(f"    Created manager at: {copied_path}\n\n")
    pass

    set_defaultInterpreterPath = False
    defaultInterpreterPath_str = ""
    project = PR.ProjectRun(command= "start", project_name='ApiLogicServer', db_url='sqlite', execute=False)
    # find cli in subdirectories of the lib path for manager run launches
    lib_path = project.default_interpreter_path.parent.parent.joinpath('lib')
    ''' if only 1 puthon, lib contains site-packages, else python3.8, python3.9, etc '''
    subdirs = [x for x in lib_path.iterdir() if x.is_dir()]
    for subdir in subdirs:
        if 'site-packages' in str(subdir):
            site_packages_dir = lib_path.joinpath('site-packages')
            break
        sub_subdirs = [x for x in subdir.iterdir() if x.is_dir()]
        for sub_subdir in sub_subdirs:
            assert 'site-packages' in str(sub_subdir)
            site_packages_dir = sub_subdir  # lib_path.joinpath('site-packages')
    cli_path = site_packages_dir.joinpath('api_logic_server_cli/cli.py')
    # replace the path with the site-packages path , eg
    # "program": "cli_path" --> "program": "./venv/lib/python3.12/site-packages/api_logic_server_cli/cli.py",
    pass
    cli_str = str(cli_path)
    if os.name == "nt":
        cli_str = create_utils.windows_path_fix(dir_str=cli_str)
    vscode_launch_path = to_dir.joinpath('.vscode/launch.json')
    create_utils.replace_string_in_file(search_for = 'cli_path',
                                        replace_with=str(cli_str),
                                        in_file=vscode_launch_path)

    if set_defaultInterpreterPath:  # FIXME OLD CODE if dev-ide, override default venv: ./venv/bin/python
        global api_logic_server_path
        assert project.api_logic_server_dir_path == get_api_logic_server_path(), "dir mismatch"
        project.api_logic_server_dir_path = get_api_logic_server_path()  # for compatibility to api_logic_server.py
        defaultInterpreterPath_str = sys.executable
        defaultInterpreterPath = Path(defaultInterpreterPath_str)
        if 'ApiLogicServer-dev' in str(project.api_logic_server_dir_path):  # apilogicserver dev is special case
            if os.name == "nt":
                defaultInterpreterPath = project.api_logic_server_dir_path.parent.parent.parent.joinpath('build_and_test/ApiLogicServer/venv/scripts/python.exe')
            else:
                defaultInterpreterPath = project.api_logic_server_dir_path.parent.parent.parent.parent.joinpath('bin/python')
                if 'org_git' in str(project.api_logic_server_dir_path):  # running from dev-source
                    defaultInterpreterPath = project.api_logic_server_dir_path.parent.parent.parent.joinpath('clean/ApiLogicServer/venv/bin/python')
            defaultInterpreterPath_str = str(defaultInterpreterPath)
            # ApiLogicServerPython
            vscode_settings_path = to_dir / '.vscode/settings.json'
            if os.name == "nt":
                defaultInterpreterPath_str = get_windows_path_with_slashes(url=defaultInterpreterPath_str)
                # vscode_settings_path = get_windows_path_with_slashes(url=vscode_settings_path)
            create_utils.replace_string_in_file(search_for = './venv/bin/python',
                                                replace_with=defaultInterpreterPath_str,
                                                in_file=vscode_settings_path)
            log.debug(f'.. ..Updated .vscode/settings.json with "python.defaultInterpreterPath": "{defaultInterpreterPath_str}"...')

    os.putenv("APILOGICSERVER_AUTO_OPEN", "code")
    os.putenv("APILOGICSERVER_VERBOSE", "false")
    os.putenv("APILOGICSERVER_HOME", str(project.api_logic_server_dir_path.parent) )
    # assert defaultInterpreterPath_str == str(project.default_interpreter_path)
    try:
        with_readme = '. readme.md' if open_with == "xxcode" else ' '  # loses project context (no readme preview)
        create_utils.run_command(
            cmd=f'{open_with} {to_dir_str} {with_readme}',  # passing readme here fails - loses project setttings
            env=None, 
            msg="no-msg", 
            project=project)
    except Exception as e:
        log.error(f"\n\nError: {e}")
        log.error(f"\nSuggestion: open code (Ctrl+Shift+P or Command+Shift+P), and run Shell Command\n")
        exit(1)


@main.command("about")
@click.pass_context
def about(ctx):
    """
        Recent Changes, system information.
    """

    print(f'\tInstalled at {abspath(__file__)}\n')
    print(f'\thttps://apilogicserver.github.io/Docs/Tutorial/\n')

    def print_at(label: str, value: str):
        tab_to = 30 - len(label)
        spaces = ' ' * tab_to
        print(f'{label}: {spaces}{value}')

    print("\nPYTHONPATH..")
    for p in sys.path:
        print(".." + p)
    print("")
    print("api_logic_server_info...")
    for key, value in api_logic_server_info_file_dict.items():
        print_at(f'  {key}', value)
    print("")
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = f"cannot get local ip from {hostname}"
        log.debug(f"{local_ip}")

    print_at('ApiLogicServer version', PR.__version__)
    print_at('ip (gethostbyname)', local_ip)
    print_at('on hostname', hostname)
    print_at('cwd', os. getcwd())
    print_at("Python version", create_utils.run_command(f'python --version', msg="no-msg"))
    print_at("Docker", is_docker())

    click.echo(
        click.style(PR.recent_changes)
    )


@main.command("welcome")
@click.pass_context
def welcome(ctx):
    """
        Just print version and exit.
    """

def login_and_get_token(user: str, password: str) -> str:
    """

    Login as <specified user>, password <specified password>

    Raises:
        Exception: if login fails

    Returns:
        _type_: str token
    """
    post_uri = 'http://localhost:5656/api/auth/login'
    post_data = {"username": user, "password": password}
    r = requests.post(url=post_uri, json = post_data)
    response_text = r.text
    status_code = r.status_code
    if status_code > 300:
        if 'is not authorized for this system' in r.text:
            log.info('\n*** Login Failed: User not Authorized ***\n')
            exit(1)
        raise Exception(f'POST login failed - status_code = {status_code}, with response text {r.text}')
    result_data = json.loads(response_text)
    result_map = DotMap(result_data)
    token = result_map.access_token
    return token

def login_exec(user: str, password: str):
    """For direct debug (since VSCode WILL NOT support args with quotes etc)

    Args:
        user (str): _description_
        password (str): _description_
    """
    log.info(f"\nLogging in as {user}, {password}")
    token = login_and_get_token(user=user, password=password)
    api_logic_server_info_file_dict["last_login_token"] = token
    with open(api_logic_server_info_file_name, 'w') as api_logic_server_info_file_file:
        yaml.dump(api_logic_server_info_file_dict, api_logic_server_info_file_file, default_flow_style=False)

    log.debug("Success - stored internally in api_logic_server_info_file.yaml - curl header now:\n")
    # log.info("-H 'accept: application/vnd.api+json' ")
    # log.info(f"-H 'Content-Type: application/vnd.api+json'")
    log.info(f"-H 'Authorization: Bearer {last_login_token}'")
    log.info("\nNow run ApiLogicServer curl <curl command>\n")


def curl_exec(curl_command: [], data: str="", security: bool=True):
    auth = ""
    # auth += f"-H 'accept: application/vnd.api+json' "
    # auth += f" -H 'Content-Type: application/vnd.api+json'"
    auth += f" -H 'Authorization: Bearer {last_login_token}'"
        
    command_parseable = curl_command[0]
    log.debug(f"\nReceived command:\n{command_parseable}\n")

    # command_parseable = command_parseable.replace("?", "\?")
    command_with_auth = f"curl {command_parseable}"
    if security:
        command_with_auth = f"curl '{command_parseable}' {auth}"
        if data != "":  # updates seem to have extra quotes
            command_with_auth = f"curl {command_parseable} {auth}"
    log.debug(f"\nPreparing command with security: {security}\ncmd stripped: {command_with_auth}\n")

    command_complete = command_with_auth
    if data != "":
        command_complete = command_complete.replace('curl', 'curl -X ')
        command_complete += f" -H 'accept: application/vnd.api+json'"
        command_complete += f" -H 'Content-Type: application/json'"
        command_complete += f" -d '{data}'"
    log.debug(f"\nNow executing:\n{command_complete}\n")
    try:
        result = create_utils.run_command(f'{command_complete}', msg="Run curl command with auth", new_line=True)
    except Exception as e:  # TODO: why does this not catch bad json (async?)
        print(f'\nFailed: {e}\nCommand:\n{command_complete}\nesult: \n{result}\n')
    print(f'\nresult: \n{result}\n')
    pass


@main.command("login")
@click.pass_context
@click.option('--user',
              default=f'admin',
              prompt="User Name",
              help="Name of Authorized User")  # option text shown on create --help
@click.option('--password',
              default=f'p',
              prompt="Password",
              help="Users Password")  # option text shown on create --help
def login(ctx, user: str, password: str):
    """
        Login and save token for curl command.
    """
    login_exec(user=user, password=password)



@main.command("curl")
@click.pass_context
@click.argument('curl_command', nargs=-1, type=click.UNPROCESSED)
@click.option('--data',
              default=f'',
              help="Payload for Post, Patch\n")
@click.option('--security/--no_security',
              default=True, is_flag=True,
              help="Include -H Bearer xxx")
@click.option('--security/--no-security', 'security',
              default=True, is_flag=True,
              help="Include -H Bearer xxx")
def curl(ctx, curl_command: str, data: str="", security: click.BOOL=False):
    """
        Execute cURL command, providing auth headers from login.
    """
    # https://click.palletsprojects.com/en/8.1.x/advanced/#forwarding-unknown-options
    curl_exec(curl_command=curl_command, data=data, security=security)


@main.command("curl-test")
@click.pass_context
@click.option('--message',
              default=f'cURL Test',
              help="Proceed\n")
def curl_test(ctx, message):
    """
        Test curl commands (nw only; must be r)
    """
    # https://click.palletsprojects.com/en/8.1.x/advanced/#forwarding-unknown-options

    do_get = True
    if do_get:
        login_exec(user="admin", password="p")
        curl_exec(curl_command=["http://localhost:5656/ProductDetails_View?id=1", None])
        pass

    do_post = True
    if do_post:
        data = """ {"meta": {
                "method": "add_order_by_id",
                "args": {
                "AccountId": "ALFKI",
                "Items": [
                    {
                    "ProductId": 1,
                    "QuantityOrdered": 1
                    },
                    {
                    "ProductId": 2,
                    "QuantityOrdered": 2
                    }
                ]
                }
                }
            }"""
        command = [" 'POST' 'http://localhost:5656/api/ServicesEndPoint/add_order_by_id' ", None]
        curl_exec(curl_command = command, security = False, data = data)


@main.command("app-create")
@click.option('--project-name', 'project_name',
              default=f'',
              help="Project location")
@click.option('--app',
              default='app',
              help="App directory name")
@click.option('--admin-app', 'admin_app',
              default='admin',
              help="Input admin app")
@click.pass_context
def app_create(ctx, project_name, app, admin_app):
    """
    Creates Ontomize app model: ui/<app>/app-model.yaml

    Example: 

        ApiLogicServer create-app —app=name=app1
    
    This creates app1/app-model.yml — edit that to deselect tables, tweak fields etc
    """

    from api_logic_server_cli.create_from_model.ont_create import OntCreator

    global command
    command = "app-create"

    project_name = resolve_blank_project_name(project_name)

    project = PR.ProjectRun(command=command, 
              project_name=project_name, 
              db_url = "",
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)

    ont_creator = OntCreator(project = project, app = app, admin_app = admin_app)
    ont_creator.create_application()
    log.info("")


@main.command("app-build")
@click.option('--project-name', 'project_name',
              default=f'',
              help="Project containing App")
@click.option('--app',
              default='app',
              help="App directory name")
@click.pass_context
def app_build(ctx, project_name, app):
    """
    Builds runnable app from: ui/<app>/app-model.yaml

    example: 

        ApiLogicServer create-app —app=name=app1
    
    This creates app1/app-model.yml. — edit that to deselect tables, tweak fields etc
    """

    from api_logic_server_cli.create_from_model.ont_build import OntBuilder

    global command
    command = "app-build"

    project_name = resolve_blank_project_name(project_name)

    project = PR.ProjectRun(command=command, 
              project_name=project_name, 
              db_url="",
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)

    ont_creator = OntBuilder(project = project, app = app)
    ont_creator.build_application()
    log.info("")



@main.command("tutorial")
@click.option('--create',
              default='tutorial',
              help="tutorial or fiddle")
@click.pass_context
def tutorial(ctx, create):
    """
    Creates (updates) Tutorial.

    Contains 3 projects: basic_flask, ApiLogicProject, ApiLogicProjectNoCustomizations
    
    example: 
    cd ApiLogicProject  # any empty folder, perhaps where ApiLogicServer is installed
    ApiLogicServer tutorial
    
    """
    project_name=os.getcwd()
    if project_name == get_api_logic_server_dir():  # for ApiLogicServer dev (from |> Run and Debug )
        project_name = str(Path(project_name).parent.parent)  #  .joinpath("Org-ApiLogicServer"))
    else:
        project_name = str(Path(project_name))

    project = PR.ProjectRun(command="tutorial", 
              project_name=project_name, 
              db_url="",
              execute=False
              )
    project.tutorial(msg="Creating:", create=create)
    log.info("")


@main.command("genai", cls=HideDunderCommand)
@click.option('--using',
              default=f'genai_demo',
              prompt="Project description file",
              help="Project description file")
@click.option('--db-url', 'db_url',
              default=f'sqlite',
              help="SQLAlchemy Database URL\n")
@click.option('--gen-using-file', 'gen_using_file',
              default='',
              help="Use ChatGPT API")
@click.pass_context
def genai(ctx, using, db_url, gen_using_file: click.BOOL):
    """
        Creates new customizable project (overwrites).
    """
    global command
    db_types = ""
    if using.endswith('.prompt'):
        using = using.replace('.prompt','')
    PR.ProjectRun(command="create", project_name=using, db_url=db_url, from_genai=using, gen_using_file=gen_using_file)


@main.command("create", cls=HideDunderCommand)
@click.option('--project_name',   # notice - old _names have no prompt
              default=f'{default_project_name}',
              help="Project Location")  # option text shown on create --help
@click.option('--project-name', 'project_name',
              default=f'{default_project_name}',
              prompt="Project Name",
              help="Project directory name")
@click.option('--db_url',
              default=f'{default_db}',
              help="SQLAlchemy Database URL\n")
@click.option('--db-url', 'db_url',
              default=f'{default_db}',  # tho -db_url= comes in as 
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--from-model', 'from_model',
              default=f'',
              help="SQLAlchemy Database URL\n")
@click.option('--api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--opt_locking',
              default=OptLocking.OPTIONAL.value,
              help="Optimistic Locking [ignore, optional, required]")
@click.option('--opt-locking', 'opt_locking',
              default=OptLocking.OPTIONAL.value,
              help="Optimistic Locking [ignore, optional, required]")
@click.option('--opt_locking_attr',
              default="S_CheckSum",
              help="Attribute Name for Optimistic Locking CheckSum (unused)")
@click.option('--opt-locking-attr', 'opt_locking_attr',
              default="S_CheckSum",
              help="Attribute Name for Optimistic Locking CheckSum (unused)")
@click.option('--id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--id-column-alias', 'id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--from-git', 'from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--run', is_flag=True,
              default=False,
              help="Run created project")
@click.option('--quote', is_flag=True,
              default=False,
              help="Use Quoted column names")
@click.option('--open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--open-with', 'open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--not-exposed', 'not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--admin_app/--no_admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--admin-app/--no-admin-app', 'admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--multi_api/--no_multi_api',
              default=False, is_flag=True,
              help="Create multiple APIs")
@click.option('--multi-api/--no-multi-api', 'multi_api',
              default=False, is_flag=True,
              help="Create multiple APIs")
@click.option('--flask_appbuilder/--no_flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--flask-appbuilder/--noflask-appbuilder', 'flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--react_admin/--no_react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--react-admin/--no-react-admin', 'react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--favorites',
              default="name description",
              help="Columns named like this displayed first")
@click.option('--non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--non-favorites', 'non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--use-model', 'use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--host',
              default=f'localhost',
              help="Server hostname (default is localhost)")
@click.option('--port',
              default=f'5656',
              help="Port (default 5656, or leave empty)")
@click.option('--swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--swagger-host', 'swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--extended-builder', 'extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--include_tables',
              default=f'',
              help="yml for include: exclude:")
@click.option('--include-tables', 'include_tables',
              default=f'',
              help="yml for include: exclude:")
@click.option('--infer_primary_key/--no_infer_primary_key',
              default=False, is_flag=True,
              help="xInfer primary_key for unique cols")
@click.option('--infer-primary-key/--no-infer-primary-key', 'infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.pass_context
def create(ctx, project_name: str, db_url: str, not_exposed: str, api_name: str,
           from_model: str,
           from_git: str,
           # db_types: str,
           open_with: str,
           run: click.BOOL,
           admin_app: click.BOOL,
           flask_appbuilder: click.BOOL,
           react_admin: click.BOOL,
           quote: click.BOOL,
           use_model: str,
           host: str,
           port: str,
           swagger_host: str,
           favorites: str, non_favorites: str,
           extended_builder: str,
           include_tables: str,
           multi_api: click.BOOL,
           opt_locking: str, opt_locking_attr: str,
           infer_primary_key: click.BOOL,
           id_column_alias: str):
    """
        Creates new customizable project (overwrites).
    """
    global command
    db_types = ""
    PR.ProjectRun(command="create", project_name=project_name, db_url=db_url, api_name=api_name,
                    not_exposed=not_exposed, from_model=from_model,
                    run=run, use_model=use_model, from_git=from_git, db_types=db_types,
                    flask_appbuilder=flask_appbuilder,  host=host, port=port, swagger_host=swagger_host,
                    react_admin=react_admin, admin_app=admin_app, quote=quote,
                    favorites=favorites, non_favorites=non_favorites, open_with=open_with,
                    extended_builder=extended_builder, include_tables=include_tables,
                    multi_api=multi_api, infer_primary_key=infer_primary_key, 
                    opt_locking=opt_locking, opt_locking_attr=opt_locking_attr,
                    id_column_alias=id_column_alias)


@main.command("create-and-run", cls=HideDunderCommand)
@click.option('--project_name',
              default=f'{default_project_name}',
              help="Create new directory named this")
@click.option('--project-name', 'project_name',
              prompt="Project to create/run",
              default=f'{default_project_name}',
              help="Project location")
@click.option('--db_url',
              default=f'{default_db}',
              help="SQLAlchemy Database URL - see above\n")
@click.option('--db-url', 'db_url',
              prompt="SQLAlchemy Database URI",
              default=f'{default_db}',
              help="SQLAlchemy Database URL - see above\n")
@click.option('--api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--opt_locking',
              default=OptLocking.OPTIONAL.value,
              help="Optimistic Locking [ignore, optional, required]")
@click.option('--opt-locking', 'opt_locking',
              default=OptLocking.OPTIONAL.value,
              help="Optimistic Locking [ignore, optional, required]")
@click.option('--opt_locking_attr',
              default="S_CheckSum",
              help="Attribute Name for Optimistic Locking CheckSum (unused)")
@click.option('--opt-locking-attr', 'opt_locking_attr',
              default="S_CheckSum",
              help="Attribute Name for Optimistic Locking CheckSum (unused)")
@click.option('--id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--id-column-alias', 'id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--from-git', 'from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--run', is_flag=True,
              default=True,
              help="Run created project")
@click.option('--open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--open-with', 'open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--not-exposed', 'not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--admin_app/--no_admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--admin-app/--no-admin-app', 'admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--quote', is_flag=True,
              default=False,
              help="Use Quoted column names")
@click.option('--flask_appbuilder/--no_flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--flask-appbuilder/--noflask-appbuilder', 'flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--react_admin/--no_react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--react-admin/--no-react-admin', 'react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--multi_api/--no_multi_api',
              default=False, is_flag=True,
              help="Create multiple APIs")
@click.option('--multi-api/--no-multi-api', 'multi_api',
              default=False, is_flag=True,
              help="Create multiple APIs")
@click.option('--favorites',
              default="name description",
              help="Columns named like this displayed first")
@click.option('--non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--non-favorites', 'non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--use-model', 'use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--host',
              default=f'localhost',
              help="Server hostname (default is localhost)")
@click.option('--port',
              default=f'5656',
              help="Port (default 5656, or leave empty)")
@click.option('--swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--swagger-host', 'swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--extended-builder', 'extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--include_tables',
              default=f'',
              help="yml for include: exclude:")
@click.option('--include-tables', 'include_tables',
              default=f'',
              help="yml for include: exclude:")
@click.option('--infer_primary_key/--no_infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.option('--infer-primary-key/--no-infer-primary-key', 'infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.pass_context
def create_and_run(ctx, project_name: str, db_url: str, not_exposed: str, api_name: str,
        from_git: str,
        # db_types: str,
        open_with: str,
        run: click.BOOL,
        admin_app: click.BOOL,
        flask_appbuilder: click.BOOL,
        react_admin: click.BOOL,
        quote: click.BOOL,
        use_model: str,
        host: str,
        port: str,
        swagger_host: str,
        favorites: str, non_favorites: str,
        extended_builder: str,
        include_tables: str,
        multi_api: click.BOOL,
        opt_locking: str, opt_locking_attr: str,
        id_column_alias: str,
        infer_primary_key: click.BOOL):
    """
        Creates new project and runs it (overwrites).
    """
    global command  # TODO drop this global
    log.debug(f"\n\ncreate_and_run: projName={project_name}, dbUrl={db_url}\n") 
    db_types = ""
    PR.ProjectRun(command="create-and-run", project_name=project_name, db_url=db_url, api_name=api_name,
                    not_exposed=not_exposed,
                    run=run, use_model=use_model, from_git=from_git, db_types=db_types,
                    flask_appbuilder=flask_appbuilder,  host=host, port=port, swagger_host=swagger_host,
                    react_admin=react_admin, admin_app=admin_app, quote=quote,
                    favorites=favorites, non_favorites=non_favorites, open_with=open_with,
                    extended_builder=extended_builder, include_tables=include_tables,
                    multi_api=multi_api, infer_primary_key=infer_primary_key,
                    opt_locking=opt_locking, opt_locking_attr=opt_locking_attr,
                    id_column_alias=id_column_alias)


@main.command("rebuild-from-database", cls=HideDunderCommand)
@click.option('--project_name',
              default=f'.',
              help="Create new directory named this")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--db_url',
              default=f'{default_db}',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--db-url', 'db_url',
              default=f'{default_db}',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--id-column-alias', 'id_column_alias',
              default="Id",
              help="Attribute Name for db cols named 'id'")
@click.option('--from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--from-git', 'from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--run', is_flag=True,
              default=False,
              help="Run created project")
@click.option('--open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--open-with', 'open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--not-exposed', 'not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--admin_app/--no_admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--admin-app/--no-admin-app', 'admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--flask_appbuilder/--no_flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--flask-appbuilder/--noflask-appbuilder', 'flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--react_admin/--no_react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--react-admin/--no-react-admin', 'react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--quote', is_flag=True,
              default=False,
              help="Use Quoted column names")
@click.option('--favorites',
              default="name description",
              help="Columns named like this displayed first")
@click.option('--non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--non-favorites', 'non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--use-model', 'use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--host',
              default=f'localhost',
              help="Server hostname (default is localhost)")
@click.option('--port',
              default=f'5656',
              help="Port (default 5656, or leave empty)")
@click.option('--swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--swagger-host', 'swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--extended-builder', 'extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--infer_primary_key/--no_infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.option('--infer-primary-key/--no-infer-primary-key', 'infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.pass_context
def rebuild_from_database(ctx, project_name: str, db_url: str, api_name: str, not_exposed: str,
           from_git: str,
           # db_types: str,
           open_with: str,
           run: click.BOOL,
           admin_app: click.BOOL,
           flask_appbuilder: click.BOOL,
           react_admin: click.BOOL,
           quote: click.BOOL,
           use_model: str,
           host: str,
           port: str,
           swagger_host: str,
           favorites: str, non_favorites: str,
           extended_builder: str,
           infer_primary_key: click.BOOL,
           id_column_alias: str):
    """
        Updates database, api, and ui from changed db.

\b
        ex
\b
        ApiLogicServer rebuild-from-database --project_name=~/dev/servers/ApiLogicProject --db_url=nw

    """
    db_types = ""
    PR.ProjectRun(command="rebuild-from-database", project_name=project_name, db_url=db_url, api_name=api_name,
                    not_exposed=not_exposed,
                    run=run, use_model=use_model, from_git=from_git, db_types=db_types,
                    flask_appbuilder=flask_appbuilder,  host=host, port=port, swagger_host=swagger_host,
                    react_admin=react_admin, admin_app=admin_app, quote=quote,
                    favorites=favorites, non_favorites=non_favorites, open_with=open_with,
                    extended_builder=extended_builder, multi_api=False, infer_primary_key=infer_primary_key,
                    id_column_alias=id_column_alias)


@main.command("add-db", cls=HideDunderCommand) 
@click.option('--db_url',
              default=f'todo',
              prompt="Database url",
              help="Connect new database here")
@click.option('--db-url', 'db_url',
              default=f'{default_db}',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--bind_key',
              default=f'Alt',
              prompt="Bind key",
              help="Add new bind key here")
@click.option('--bind-key', 'bind_key',
              default=f'Alt',
              prompt="Bind key",
              help="Add new bind key here")
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--quote', is_flag=True,
              default=False,
              help="Use Quoted column names")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context # Kat
def add_db(ctx, db_url: str, bind_key: str, bind_key_url_separator: str, api_name: str, project_name: str,
           quote: click.BOOL):
    """
    Adds db (model, binds, api, app) to curr project.
    
    example: 

    cd existing_project

    ApiLogicServer add-db --db-url="todo" --bind-key="Todo"
    
    """
    project_name == resolve_blank_project_name(project_name)
    if db_url == "auth":
        bind_key = "authentication"
    PR.ProjectRun(command="add_db", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url, 
              quote=quote,
              bind_key=bind_key,
              bind_key_url_separator=bind_key_url_separator
              )
    print("DB Added")


@main.command("add-auth", cls=HideDunderCommand) 
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--provider-type',
              default='sql',
              help="sql or keycloak")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--db_url',
              default=f'auth',
              help="SQLAlchemy Database URL - see above\n")
@click.option('--db-url', 'db_url',
              default=f'auth',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context
def add_auth_cmd(ctx, bind_key_url_separator: str, provider_type :str, db_url: str, project_name: str, api_name: str):
    """
    Adds authorization/authentication to curr project.
    
    example: 

    cd existing_project

    ApiLogicServer add-auth project_name=.
    ApiLogicServer add-auth provider_type=keycloak
    
    """
    project_name == resolve_blank_project_name(project_name)
    bind_key = "authentication"
    project = PR.ProjectRun(command="add_security", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url, 
              bind_key=bind_key,
              bind_key_url_separator=bind_key_url_separator,
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)
    models_py_path = project.project_directory_path.joinpath('database/models.py')
    project.abs_db_url, project.nw_db_status, project.model_file_name = create_utils.get_abs_db_url("0. Using Sample DB", project)
    if not models_py_path.exists():
        log.info(f'... Error - does not appear to be a project: {str(project.project_directory_path)}')
        log.info(f'... Typical usage - cd into project, use --project_name=. \n')
        exit (1)
    is_nw = False
    if create_utils.does_file_contain(search_for="CategoryTableNameTest", in_file=models_py_path):
        is_nw = True
    project.add_auth(msg="Adding Security", is_nw=is_nw, provider_type=provider_type)
    log.info("")



@main.command("genai-cust", cls=HideDunderCommand) 
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context
def genai_cust(ctx, bind_key_url_separator: str, api_name: str, project_name: str):
    """
    Adds customizations to genai project.
    
    example: 
    cd existing_project
    als genai-cust
    
    """
    project_name == resolve_blank_project_name(project_name, as_project="NW_NoCust")
    db_url = "auth"
    bind_key = "authentication"
    project = PR.ProjectRun(command="add_cust", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url,
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    # eg /Users/val/dev/ApiLogicServer/ApiLogicServer-dev/clean/ApiLogicServer/genai_demo
    # vs /Users/val/dev/ApiLogicServer/clean/ApiLogicServer/genai_demo'
    project.project_directory_path = Path(project.project_directory_actual)
    models_py_path = project.project_directory_path.joinpath('database/models.py')
    project.abs_db_url, project.nw_db_status, project.model_file_name = create_utils.get_abs_db_url("0. Using Sample DB", project)
    is_nw = False
    if create_utils.does_file_contain(search_for="Customer", in_file=models_py_path):
        is_nw = True
    else:
        raise Exception("Customizations are genai-specific - this does not contain 'Customer`")
    project.add_genai_customizations(do_security=False)
    log.info("\nNext step - add authentication:\n  $ ApiLogicServer add-auth --db_url=auth\n\n")



@main.command("add-cust", cls=HideDunderCommand) 
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context
def add_cust(ctx, bind_key_url_separator: str, api_name: str, project_name: str):
    """
    Adds customizations to northwind project.
    
    example: 
    cd existing_project
    ApiLogicServer add-cust
    
    """
    project_name == resolve_blank_project_name(project_name, as_project="NW_NoCust")
    db_url = "auth"
    bind_key = "authentication"
    project = PR.ProjectRun(command="add_cust", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url,
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)
    models_py_path = project.project_directory_path.joinpath('database/models.py')
    project.abs_db_url, project.nw_db_status, project.model_file_name = create_utils.get_abs_db_url("0. Using Sample DB", project)
    is_nw = False
    if create_utils.does_file_contain(search_for="CategoryTableNameTest", in_file=models_py_path):
        is_nw = True
    else:
        raise Exception("Customizations are northwind-specific - this does not appear to be a northwind database")
    project.add_nw_customizations(do_security=False)
    log.info("\nNext step - add authentication:\n  $ ApiLogicServer add-auth --db_url=auth\n\n")


@main.command("sample-ai", cls=HideDunderCommand, hidden=True) 
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context
def sample_ai(ctx, bind_key_url_separator: str, api_name: str, project_name: str):
    """
    Adds customizations to current sample_ai project. (Create was standard)
    
    example - in IDE terminal window: 
    ApiLogicServer sample-ai
    
    """
    project_name == resolve_blank_project_name(project_name, as_project="sample_ai")
    db_url = "auth"
    bind_key = "authentication"
    project = PR.ProjectRun(command="add_cust", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url,
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)
    models_py_path = project.project_directory_path.joinpath('database/models.py')
    project.abs_db_url, project.nw_db_status, project.model_file_name = create_utils.get_abs_db_url("0. Using Sample DB", project)
    is_nw = False
    if create_utils.does_file_contain(search_for="CustomerName = Column(Text", in_file=models_py_path):
        is_nw = True
    else:
        raise Exception("Customizations are sample-ai specific - this does not appear to be a northwind database")
    project.add_sample_ai_customizations()


@main.command("sample-ai-iteration", cls=HideDunderCommand, hidden=True) 
@click.option('--bind_key_url_separator',
              default=default_bind_key_url_separator,
              help="bindkey / class name url separator")
@click.option('--project_name',
              default=f'.',
              help="Project location")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--api_name',
              default="api",
              help="api prefix name")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.pass_context
def sample_ai_iteration(ctx, bind_key_url_separator: str, api_name: str, project_name: str):
    """
    Iterate model for current sample_ai project.
    
    example - in IDE terminal window: 
    ApiLogicServer sample-ai-iterate
    
    """
    project_name == resolve_blank_project_name(project_name, as_project="sample_ai")
    db_url = "auth"
    bind_key = "authentication"
    project = PR.ProjectRun(command="add_cust", 
              project_name=project_name, 
              api_name=api_name, 
              db_url=db_url,
              execute=False
              )
    project.project_directory, project.api_name, project.merge_into_prototype = \
        create_utils.get_project_directory_and_api_name(project)
    project.project_directory_actual = os.path.abspath(project.project_directory)  # make path absolute, not relative (no /../)
    project.project_directory_path = Path(project.project_directory_actual)
    models_py_path = project.project_directory_path.joinpath('database/models.py')
    project.abs_db_url, project.nw_db_status, project.model_file_name = create_utils.get_abs_db_url("0. Using Sample DB", project)
    if create_utils.does_file_contain(search_for="CustomerName = Column(Text", in_file=models_py_path):
        is_nw = True
    else:
        raise Exception("Customizations are sample-ai specific - this does not appear to be a northwind database")
    project.add_sample_ai_iteration()


@main.command("rebuild-from-model", cls=HideDunderCommand)
@click.option('--project_name',
              default=f'.',
              help="Create new directory named this")
@click.option('--project-name', 'project_name',
              default=f'.',
              help="Project location")
@click.option('--db_url',
              default=f'{default_db}',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--db-url', 'db_url',
              default=f'{default_db}',
              prompt="SQLAlchemy Database URI",
              help="SQLAlchemy Database URL - see above\n")
@click.option('--api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--api-name', 'api_name',
              default=f'api',
              help="Last node of API Logic Server url\n")
@click.option('--from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--from-git', 'from_git',
              default="",
              help="Template clone-from project (or directory)")
@click.option('--run', is_flag=True,
              default=False,
              help="Run created project")
@click.option('--open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--open-with', 'open_with',
              default='',
              help="Open created project (eg, charm, atom)")
@click.option('--not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--not-exposed', 'not_exposed',
              default="ProductDetails_V",
              help="Tables not written to api/expose_api_models")
@click.option('--admin_app/--no_admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--admin-app/--no-admin-app', 'admin_app',
              default=True, is_flag=True,
              help="Creates ui/react app (yaml model)")
@click.option('--flask_appbuilder/--no_flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--flask-appbuilder/--noflask-appbuilder', 'flask_appbuilder',
              default=False, is_flag=True,
              help="Creates ui/basic-web-app")
@click.option('--react_admin/--no_react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--react-admin/--no-react-admin', 'react_admin',
              default=False, is_flag=True,
              help="Creates ui/react-admin app")
@click.option('--favorites',
              default="name description",
              help="Columns named like this displayed first")
@click.option('--non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--non-favorites', 'non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--use-model', 'use_model',
              default="",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--host',
              default=f'localhost',
              help="Server hostname (default is localhost)")
@click.option('--port',
              default=f'5656',
              help="Port (default 5656, or leave empty)")
@click.option('--swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--swagger-host', 'swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--extended-builder', 'extended_builder',
              default=f'',
              help="your_code.py for additional build automation")
@click.option('--infer_primary_key/--no_infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.option('--infer-primary-key/--no-infer-primary-key', 'infer_primary_key',
              default=False, is_flag=True,
              help="Infer primary-key for unique cols")
@click.pass_context # Kat
def rebuild_from_model(ctx, project_name: str, db_url: str, api_name: str, not_exposed: str,
           from_git: str,
           # db_types: str,
           open_with: str,
           run: click.BOOL,
           admin_app: click.BOOL,
           flask_appbuilder: click.BOOL,
           react_admin: click.BOOL,
           use_model: str,
           host: str,
           port: str,
           swagger_host: str,
           favorites: str, non_favorites: str,
           extended_builder: str,
           infer_primary_key: click.BOOL):
    """
        Updates database, api, and ui from changed models.
    """
    db_types = ""
    if project_name == "":
        project_name = '.'
    PR.ProjectRun(command="rebuild-from-model", project_name=project_name, db_url=db_url, api_name=api_name,
                    not_exposed=not_exposed,
                    run=run, use_model=use_model, from_git=from_git, db_types=db_types,
                    flask_appbuilder=flask_appbuilder,  host=host, port=port, swagger_host=swagger_host,
                    react_admin=react_admin, admin_app=admin_app,
                    favorites=favorites, non_favorites=non_favorites, open_with=open_with,
                    extended_builder=extended_builder, multi_api=False, infer_primary_key=infer_primary_key)


@main.command("run", cls=HideDunderCommand)
@click.option('--project_name',
              default=f'{last_created_project_name}',
              help="Project to run")
@click.option('--project-name', 'project_name',
              default=f'{last_created_project_name}',
              prompt="Project to run",
              help="Project location")
@click.option('--host',
              default=f'localhost',
              help="Server hostname (default is localhost)")
@click.option('--port',
              default=f'5656',
              help="Port (default 5656, or leave empty)")
@click.option('--swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.option('--swagger-host', 'swagger_host',
              default=f'localhost',
              help="Swagger hostname (default is localhost)")
@click.pass_context
def run_api(ctx, project_name: str, host: str="localhost", port: str="5656", swagger_host: str="localhost"):
    """
        Runs existing project.


\b
        Example

\b
            ApiLogicServer run --project_name=/localhost/ApiLogicProject
            ApiLogicServer run --project_name=    # runs last-created project
    """
    global command
    command = "run-api"
    proj_dir = project_name
    if proj_dir == "":
        proj_dir = last_created_project_name
        # print(f'Blank - using last created project: {proj_dir}')
    else:
        proj_dir = os.path.abspath(f'{create_utils.resolve_home(project_name)}')
        # print(f'Running specified project: {proj_dir}')
    run_file = f'{proj_dir}/api_logic_server_run.py '  # alert: sending args makes it hang: {host} {port} {swagger_host}
    create_utils.run_command(f'python {run_file}', msg="Run Created ApiLogicServer Project", new_line=True)
    print("run complete")


@main.command("create-ui", cls=HideDunderCommand)
@click.option('--use_model',
              default="models.py",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--use-model', 'use_model',
              default="models.py",
              help="See ApiLogicServer/wiki/Troubleshooting")
@click.option('--favorites',
              default="name description",
              help="Columns named like this displayed first")
@click.option('--non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.option('--non-favorites', 'non_favorites',
              default="id",
              help="Columns named like this displayed last")
@click.pass_context
def create_ui(ctx, use_model: str,
              favorites: str, non_favorites: str,
              ):
    """
        Creates models.yaml from models.py (internal).


\b
        Example

\b
            ApiLogicServer create-ui --use_model=~/dev/ApiLogicServer/tests/models-nw-plus.py
    """
    global command
    command = "create-ui"
    admin_out = create_utils.resolve_home(use_model.replace("py","yaml"))
    project_directory, ignore = os.path.split(create_utils.resolve_home(use_model))
    print(f'1. Loading existing model: {use_model}')
    model_creation_services = ModelCreationServices(  # fills in rsource_list for ui_admin_creator
        use_model=use_model,
        favorite_names=favorites, non_favorite_names=non_favorites,
        project_directory=project_directory,
        command=command,
        version=PR.__version__)

    print(f'2. Creating yaml from model')
    creator_path = abspath(f'{abspath(get_api_logic_server_dir())}/create_from_model')
    spec = importlib.util.spec_from_file_location("module.name", f'{creator_path}/ui_admin_creator.py')
    creator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(creator)
    admin_yaml_dump = creator.create(model_creation_services)

    print(f'3. Writing yaml: {admin_out}')
    with open(admin_out, 'w') as yaml_file:
        yaml_file.write(admin_yaml_dump)


@main.command("examples")
@click.pass_context
def examples(ctx):
    """
    Example commands, including SQLAlchemy URIs.
    """
    uri_info.print_uri_info()


log = logging.getLogger(__name__)


def print_args(args, msg):
    print(msg)
    for each_arg in args:
        print(f'  {each_arg}')
    print(" ")


def check_ports():
    try:
        rtn_hostname = socket.gethostname()
        rtn_local_ip = socket.gethostbyname(rtn_hostname)
    except:
        rtn_local_ip = f"cannot get local ip from {rtn_hostname}"
        print(f"{rtn_local_ip}")
    port_check = False
    if port_check or is_docker():
        s = socket.socket()  # Create a socket object
        host = socket.gethostname()  # Get local machine name
        port = 5656  # Reserve a port for your service.
        port_is_available = True
        try:
            s.bind((host, port))  # Bind to the port
        except:
            port_is_available = False
        if not port_is_available:
            msg = "\nWarning - port 5656 does not appear to be available\n" \
                  "  Version 3.30 has changed port assignments to avoid port conflicts\n" \
                  "  For example, docker start:\n" \
                  "    docker run -it --name api_logic_server --rm -p 5656:5656 -p 5002:5002 -v ${PWD}:/localhost apilogicserver/api_logic_server \n" \
                  "Ports are sometimes freed slowly, you may need to re-issue this command.\n\n"
            log.warning(msg)
            # sys.exit(msg)
        s.close()
    return rtn_hostname, rtn_local_ip


def start():               # target of setup.py
    sys.stdout.write("\nWelcome to API Logic Server " + PR.__version__ + "\n\n")
    hostname, local_ip = check_ports()  #  = socket.gethostname()
    # sys.stdout.write("    SQLAlchemy Database URI help: https://docs.sqlalchemy.org/en/14/core/engines.html\n")
    main(obj={})


command = "not set"
if __name__ == '__main__':  # debugger & python command line start here
    # eg: python api_logic_server_cli/cli.py create --project_name=~/Desktop/test_project
    # unix: python api_logic_server_cli/cli.py create --project_name=/home/ApiLogicProject

    print(f'\nWelcome to API Logic Server, {PR.__version__}\n')  #  at {local_ip} ')
    hostname, local_ip = check_ports()
    commands = sys.argv
    if len(sys.argv) > 1 and sys.argv[1] not in ["version", "sys-info", "welcome"] and \
            "show-args" in api_logic_server_info_file_dict:
        print_args(commands, f'\nCommand Line Arguments:')
    python_version = sys.version_info
    assert python_version[0] >= 3 and python_version[1] in [8,9,10,11,12], \
        "... Requires Python >=3.8, !=3.11.0, !=3.11.1, 3.12"
    main()

