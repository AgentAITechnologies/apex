import json
import inspect

from execution_management import exec_python, extract_python


def rsd_b0(csm):
    results = csm.build_action_results()

    action_results_str = "You took these actions to accomplish the task:\n"
    action_results_str += json.dumps(results, indent=4)

    csm.current_state.update_frmt({"action_results": results})
    csm.current_state.update_frmt({"action_results_str": action_results_str}, recursive=False)

    print(action_results_str)

def rstcp_a0(task, csm, parsed_response):
    if isinstance(parsed_response, str) and "python" in parsed_response.lower() and csm.current_state.get_hpath() == "ready_select-tool_compose-python":
        code = extract_python(parsed_response)
        stdout, stderr = exec_python(code)

        print(f"[main] Python script execution results for task \"{task}\":\nstdout:\n{stdout}\nstderr:\n{stderr}")

        frmt_update = {
            "result": {
                "action": "execute python",
                "code": code,
                "output": {"stdout": stdout, "stderr": stderr}
            }
        }

        csm.transition("execute").update_frmt(frmt_update)



callbacks = {
    "ready_select-done": {
        "before": [rsd_b0]
    },
    "ready_select-tool_compose-python": {
        "after": [rstcp_a0]
    }
}

def get_callbacks(f_key, time_str):
    if f_key in callbacks:
        if time_str in callbacks[f_key]:
            return callbacks[f_key][time_str]
    return []

def exec_callbacks(f_key, time_str, locals=None):
    had_callbacks = False
    
    for f in get_callbacks(f_key, time_str):
        had_callbacks = True

        param_names = inspect.signature(f).parameters.keys()

        params = []
        for param in param_names:
            params.append(locals[param])
        
        f(*params)

    return had_callbacks

