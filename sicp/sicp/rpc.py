import os
from common.rpc.auth_utils import set_token_path

set_token_path(f"{os.path.expanduser('~')}/.sicp_token")

from common.rpc import auth
from common.rpc import buildserver
from common.rpc import domains
from common.rpc import hosted
from common.rpc import howamidoing
from common.rpc import indexer
from common.rpc import mail
from common.rpc import oh
from common.rpc import paste
from common.rpc import sandbox
from common.rpc import search
from common.rpc import secrets
from common.rpc import sections
from common.rpc import slack
from common.rpc import ag_master
from common.rpc import ag_worker
