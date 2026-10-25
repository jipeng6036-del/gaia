import datetime as dt
import json
import os
import subprocess
from pathlib import Path

r = Path('/evidence')
state = {'started': dt.datetime.now(dt.timezone.utc).isoformat()}
def run(name, command, env=None):
    state['stage'] = name
    (r / 'hub-state.json').write_text(json.dumps(state, indent=2))
    with (r / (name + '.log')).open('w') as log:
        code = subprocess.run(command, cwd='/current', env=env, stdout=log, stderr=subprocess.STDOUT).returncode
    state[name] = code
    (r / 'hub-state.json').write_text(json.dumps(state, indent=2))
    if code:
        raise SystemExit(code)

run('hub-create', ['uv', 'venv', '/hub-venv', '--python', '/usr/local/bin/python'])
run('hub-install', ['uv', 'pip', 'install', '--python', '/hub-venv/bin/python', '-e', '/current[dev,rag,ui,api,browser,publish]', '-e', '/current/hub/agents/chat/python', '-e', '/current/hub/agents/gaia/python', '-e', '/current/hub/agents/email/python', 'pytest-mock', 'pytest-timeout', 'pytest-xdist', 'pyfakefs', 'respx'])
run('hub-ensurepip', ['/hub-venv/bin/python', '-m', 'ensurepip', '--upgrade'])
run('hub-build-ownership', ['chown', '-R', 'gaia-runner:gaia-runner', '/current/hub/agents/email/python/gaia_agent_email.egg-info'])
env = dict(os.environ, PATH='/hub-venv/bin:/opt/node-download/node-v24.14.0-linux-x64/bin:/usr/local/bin:/usr/bin:/bin', GAIA_MEMORY_DISABLED='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', TMPDIR='/tmp')
prefix = ['/usr/sbin/runuser', '-u', 'gaia-runner', '--', '/hub-venv/bin/python']
for workflow, job in [('test_email_agent.yml', 'test-email-agent'), ('test_chat_agent.yml', 'test-chat-agent'), ('test_gaia_agent.yml', 'test-gaia-agent')]:
    run('hub-guard-' + job, [*prefix, 'util/check_module_skips.py', '--workflow', workflow, '--job', job], env)
run('hub-capability-matrix', [*prefix, 'hub/agents/gaia/python/packaging/capability_matrix.py', '--check'], env)
files = ['hub/agents/chat/python/tests/', 'hub/agents/gaia/python/tests/', 'hub/agents/email/python/tests/', 'tests/test_email_openapi_conformance.py', 'tests/unit/agents/email/', 'tests/unit/email/', 'tests/unit/agents/test_email_agent.py', 'tests/unit/agents/test_email_agent_confirmation.py', 'tests/unit/agents/test_email_agent_local_llm_enforcement.py', 'tests/unit/agents/test_email_agent_prompt_injection.py', 'tests/unit/agents/test_email_agent_soft_delete.py', 'tests/unit/agents/test_email_agent_tools.py', 'tests/unit/agents/test_email_llm_triage.py', 'tests/unit/test_email_cli.py', 'tests/integration/test_never_auto_send.py', 'tests/integration/test_email_rest_api_e2e.py', 'tests/integration/test_email_rest_http_corpus.py', 'tests/integration/test_email_corpus_alignment.py', 'tests/test_api.py::TestEmailTriageEndpoint', 'tests/test_api.py::TestEmailSendConfirmationGate']
for name, directory in [('chat', files[0]), ('gaia', files[1])]:
    run('hub-' + name + '-tests', [*prefix, '-m', 'pytest', directory, '-v', '--tb=short', '--timeout=180', '--basetemp=/tmp/gaia-tool-args-hub', '--junitxml=/evidence/hub-' + name + '.xml'], env)
state['command'] = [*prefix, '-m', 'pytest', *files[2:], '-v', '--tb=short', '--timeout=180', '--basetemp=/tmp/gaia-tool-args-hub', '--junitxml=/evidence/hub.xml']
email_env = dict(env)
email_env.pop('GAIA_MEMORY_DISABLED', None)
run('hub-tests', state['command'], email_env)
state['finished'] = dt.datetime.now(dt.timezone.utc).isoformat()
(r / 'hub-state.json').write_text(json.dumps(state, indent=2))
