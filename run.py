import os
import logging
import py2neo
import json

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('py2neo.client.bolt').setLevel(logging.WARNING)
logging.getLogger('py2neo.client').setLevel(logging.WARNING)
logging.getLogger('urllib3.connectionpool').setLevel(logging.WARNING)
logging.getLogger('graphio').setLevel(logging.WARNING)

log = logging.getLogger(__name__)

# import and setup
from covid_graph import helper, post, jhu, unwpp

ROOT_DIR = os.getenv('ROOT_DIR', '/download')
RUN_MODE = os.getenv('RUN_MODE', 'prod')

NEO4J_CONFIG_STRING = os.getenv("NEO4J")
log.debug(f'NEO4J config string from env (not changed): {NEO4J_CONFIG_STRING}')
log.debug(f'Type of config string: {type(NEO4J_CONFIG_STRING)}')

try:
    NEO4J_CONFIG_DICT = json.loads(NEO4J_CONFIG_STRING)
except json.decoder.JSONDecodeError:
    # try to replace single quotes with double quotes
    # JSON always expects double quotes, common mistake when writing JSON strings
    NEO4J_CONFIG_STRING = NEO4J_CONFIG_STRING.replace("'", '"')
    NEO4J_CONFIG_DICT = json.loads(NEO4J_CONFIG_STRING)

log.debug("NEO4J_CONFIG_DICT: ")
log.debug(NEO4J_CONFIG_DICT)

if RUN_MODE.lower() == 'test':
    import pytest

    log.info("Run tests")
    pytest.main()

else:

    graph = py2neo.Graph(**NEO4J_CONFIG_DICT)

    # setup DB
    helper.setup_db(graph)

    # download data
    jhu_zip_file = jhu.download_jhu(ROOT_DIR)
    jhu_dir = helper.unzip_file(jhu_zip_file)

    wpp_csv_file = unwpp.download_population_data(ROOT_DIR, skip_existing=True)
    ###

    # load to Neo4j
    jhu.read_daily_report_JHU(jhu_dir, graph)
    unwpp.load_wpp_data(ROOT_DIR, graph)
    ###

    # post process
    post.set_latest_update(graph)
    ###
