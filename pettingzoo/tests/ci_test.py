import pettingzoo.tests.api_test as api_test
import pettingzoo.tests.bombardment_test as bombardment_test
import pettingzoo.tests.performance_benchmark as performance_benchmark
import pettingzoo.tests.manual_control_test as test_manual_control

import sys
from .all_modules import all_environments
from .all_modules import all_prefixes
from .render_test import test_render
from .error_tests import error_test
from .seed_test import seed_test
from .save_obs_test import test_save_obs
import subprocess

render = sys.argv[2] == 'True'
manual_control = sys.argv[3] == 'True'
bombardment = sys.argv[4] == 'True'
performance = sys.argv[5] == 'True'
save_obs = sys.argv[6] == 'True'


env_id = sys.argv[1]


def perform_ci_test(env_id, render, manual_control, bombardment, performance, save_obs):
    print("running game {}".format(env_id))
    env_module = all_environments[env_id]
    _env = env_module.env()
    error_collected = []
    try:
        api_test.api_test(_env, render=render, verbose_progress=True)
    except Exception as e:
        error_collected.append("API Test: " + str(e))

    seed_test(env_module.env)
    # error_test(env_module.env())

    if save_obs:
        test_save_obs(_env)

    if render:
        try:
            test_render(_env)
        except Exception as e:
            error_collected.append("Render Test:" + str(e))

    if manual_control:
        manual_control_fn = getattr(env_module, "manual_control", None)
        if manual_control_fn is not None:
            status = test_manual_control.test_manual_control(manual_control_fn)
            if status != 0:
                error_collected.append("Manual Control test failed")

    if performance:
        _env = env_module.env()
        performance_benchmark.performance_benchmark(_env)

    if bombardment:
        _env = env_module.env()
        try:
            bombardment_test.bombardment_test(_env, cycles=7000)
        except Exception as e:
            error_collected.append("Bombardment Test: " + str(e))

    return error_collected


if env_id in all_prefixes:
    warning_map = {}
    for e in all_environments:
        if e.startswith(env_id):
            warning_map[e] = perform_ci_test(e, render, manual_control, bombardment, performance, save_obs)
    f = open("test_output.txt", "w")
    for warn in warning_map:
        warn_list = warning_map[warn]
        if len(warn_list) > 0:
            for w in warn_list:
                f.write(warn + ": " + w + "\n")
    # flake8 test
    file_name = "pettingzoo/" + env_id
    style_guide = ["flake8", file_name, "--ignore=E501, E731, E74, E402, F401, W503"]
    process = subprocess.Popen(style_guide, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    flake8_res = stdout.decode("utf-8")
    for misform in flake8_res.split("\n"):
        f.write(misform + "\n")
    f.close()
else:
    print("Environment: '{}' not in the 'all_environments' list".format(env_id))
