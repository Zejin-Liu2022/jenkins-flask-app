"""Deploy the built macOS executable with a persistent user LaunchAgent."""

import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import time
import urllib.request


def launchctl(*arguments, check=True):
    result = subprocess.run(
        ["/bin/launchctl", *arguments], check=False, capture_output=True, text=True
    )
    if check and result.returncode:
        raise RuntimeError(f"launchctl {arguments}: {result.stderr.strip()}")
    return result


def unload_service(service):
    launchctl("bootout", service, check=False)
    for _ in range(75):
        if launchctl("print", service, check=False).returncode != 0:
            return
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for the previous service to unload: {service}")


def load_service(domain, plist):
    for _ in range(30):
        result = launchctl("bootstrap", domain, str(plist), check=False)
        if result.returncode == 0:
            return
        time.sleep(0.5)
    raise RuntimeError(f"Could not load application service: {result.stderr.strip()}")


def main():
    root = Path(os.environ["DEMO_DEPLOY_ROOT"]).resolve()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    build_number = os.environ["BUILD_NUMBER"]
    release = root / "releases" / f"{build_number}-{revision[:12]}"
    release.mkdir(parents=True, exist_ok=True)
    root.joinpath("logs").mkdir(exist_ok=True)
    executable = release / "jenkins-flask-app"
    shutil.copy2("dist/jenkins-flask-app", executable)
    executable.chmod(0o755)
    metadata = {"revision": revision, "build_number": build_number}
    (release / "release.json").write_text(json.dumps(metadata, indent=2))

    label = "local.jenkins.flask-demo"
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{label}"
    plist = Path.home() / "Library/LaunchAgents" / f"{label}.plist"
    plist.parent.mkdir(parents=True, exist_ok=True)
    previous_plist = plist.read_bytes() if plist.exists() else None
    configuration = {
        "Label": label,
        "ProgramArguments": [str(executable)],
        "WorkingDirectory": str(release),
        "EnvironmentVariables": {"APP_PORT": "5001", "APP_REVISION": revision},
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(root / "logs/app.stdout.log"),
        "StandardErrorPath": str(root / "logs/app.stderr.log"),
    }
    try:
        plist.write_bytes(plistlib.dumps(configuration))
        unload_service(service)
        load_service(domain, plist)
        deadline = time.monotonic() + 90
        last_error = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen("http://127.0.0.1:5001/health", timeout=3) as response:
                    actual = json.load(response)
                assert actual == {"status": "ok", "revision": revision}, actual
                with urllib.request.urlopen("http://127.0.0.1:5001/", timeout=3) as response:
                    assert response.read() == b"Hello, CI/CD with Jenkins!"
                (root / "current-release.json").write_text(json.dumps(metadata, indent=2))
                print(f"Deployment verified: build {build_number}, commit {revision}")
                print("Application URL: http://localhost:5001/")
                return
            except (OSError, AssertionError, ValueError) as error:
                last_error = error
                time.sleep(1)
        raise RuntimeError(f"Deployment health check failed: {last_error}")
    except Exception:
        unload_service(service)
        if previous_plist:
            plist.write_bytes(previous_plist)
            load_service(domain, plist)
            print("Restored previous application service.")
        raise


if __name__ == "__main__":
    main()
