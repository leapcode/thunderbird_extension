import os
import shutil
import re
import time
from urlparse import urlparse
import commands

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from leap.common.config import get_path_prefix

DEFAULT_IMPLICIT_WAIT_TIMEOUT_IN_S = 10
HOME_PATH = '/tmp/bitmask-test'


def before_all(context):
    os.environ['HOME'] = HOME_PATH
    _setup_webdriver(context)
    userdata = context.config.userdata
    context.host = userdata.get('host', 'http://localhost')
    if not context.host.startswith('http'):
        context.host = 'https://{}'.format(context.host)
    context.hostname = urlparse(context.host).hostname

    context.username = os.environ['TEST_USERNAME']
    context.password = os.environ['TEST_PASSWORD']
    context.user_email = '{}@{}'.format(context.username, context.hostname)


def _setup_webdriver(context):
    chrome_options = Options()
    # argument to switch off suid sandBox and no sandBox in Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-setuid-sandbox")

    context.browser = webdriver.Chrome(chrome_options=chrome_options)
    context.browser.set_window_size(1280, 1024)
    context.browser.implicitly_wait(DEFAULT_IMPLICIT_WAIT_TIMEOUT_IN_S)
    context.browser.set_page_load_timeout(60)


def after_all(context):
    context.browser.quit()
    commands.getoutput('bitmaskctl stop')


def after_step(context, step):
    if step.status == 'failed':
        _prepare_artifacts_folder(step)
        _save_screenshot(context, step)
        _save_config(context, step)
        _debug_on_error(context, step)


def _prepare_artifacts_folder(step):
    try:
        os.makedirs(_artifact_path(step))
    except OSError as err:
        # directory existed
        if err.errno != 17:
            raise


def _save_screenshot(context, step):
    filepath = _artifact_path(step, 'screenshot.png')
    context.browser.save_screenshot(filepath)
    print('saved screenshot to: file://%s' % filepath)


def _save_config(context, step):
    filepath = _artifact_path(step, 'config')
    shutil.copytree(get_path_prefix(), filepath)
    print('copied config to:    file://%s' % filepath)


def _artifact_path(step, filename=''):
    string = 'failed {}'.format(str(step.name))
    slug = re.sub('\W', '-', string)
    return os.path.join(HOME_PATH, 'artifacts', slug, filename)


def _debug_on_error(context, step):
    if context.config.userdata.getbool("debug"):
        try:
            import ipdb
            ipdb.post_mortem(step.exc_traceback)
        except ImportError:
            import pdb
            pdb.post_mortem(step.exc_traceback)