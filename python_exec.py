import subprocess

def python_exec(code):

    result = subprocess.run(
        ["python3", "-c", code],
        capture_output=True,
        text=True,
        timeout=5
    )

    return {
        "output": result.stdout,
        "error": result.stderr
    }