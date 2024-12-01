import os
import subprocess
import json
from pathlib import Path
import toml
from git import Repo

# Configure paths and repositories
REPOS = [
    "https://github.com/tiangolo/fastapi.git",  # Popular ASGI framework
    "https://github.com/django/django.git",  # Web framework
    "https://github.com/flask-restful/flask-restful.git",  # REST API framework
    "https://github.com/python-attrs/attrs.git",  # Python boilerplate simplifier
]
WORK_DIR = Path("./open_source_repos")
REPORT_DIR = Path("./vulnerability_reports")

# Ensure directories exist
WORK_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# Function to clone a repository
def clone_repo(repo_url, destination):
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = destination / repo_name
    if repo_path.exists():
        print(f"[INFO] Repository {repo_name} already cloned.")
    else:
        print(f"[INFO] Cloning {repo_url} into {repo_path}...")
        Repo.clone_from(repo_url, repo_path)
    return repo_path


def generate_requirements(repo_path):
    temp_requirements = repo_path / "temp_requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        print(f"[INFO] Found pyproject.toml in {repo_path}, generating requirements.txt...")
        try:
            pyproject_data = toml.load(pyproject_file)
            dependencies = pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            if dependencies:
                with temp_requirements.open("w") as f:
                    for dep, version in dependencies.items():
                        if dep != "python":
                            f.write(f"{dep}{version if isinstance(version, str) else ''}\n")
                return temp_requirements
        except Exception as e:
            print(f"[ERROR] Failed to parse pyproject.toml: {e}")
    pipfile = repo_path / "Pipfile"
    if pipfile.exists():
        print(f"[INFO] Found Pipfile in {repo_path}, generating requirements.txt...")
        try:
            pipfile_data = toml.load(pipfile)
            dependencies = pipfile_data.get("packages", {})
            if dependencies:
                with temp_requirements.open("w") as f:
                    for dep, version in dependencies.items():
                        f.write(f"{dep}{version if isinstance(version, str) else ''}\n")
                return temp_requirements
        except Exception as e:
            print(f"[ERROR] Failed to parse Pipfile: {e}")
    requirements_file = repo_path / "requirements.txt"
    if requirements_file.exists():
        print(f"[INFO] Found requirements.txt in {repo_path}.")
        return requirements_file

    print(f"[WARN] No dependency files found in {repo_path}. Generating placeholder requirements.txt...")
    with temp_requirements.open("w") as f:
        f.write("# Placeholder: No dependencies detected\n")
    return temp_requirements


# Run Bandit and save results
def run_bandit(repo_path, report_path):
    print(f"[INFO] Running Bandit on {repo_path}...")
    bandit_report = report_path / f"{repo_path.name}_bandit_report.json"
    result = subprocess.run(
        ["bandit", "-r", str(repo_path), "-f", "json", "-o", str(bandit_report)],
        capture_output=True,
        text=True
    )
    if bandit_report.exists():
        try:
            with bandit_report.open() as f:
                bandit_data = json.load(f)
                results = bandit_data.get("results", [])
                return {"status": "success", "results": results}
        except Exception as e:
            print(f"[ERROR] Failed to parse Bandit output: {e}")
            return {"status": "failed", "error": f"Parsing error: {e}"}
    print(f"[ERROR] Bandit failed: {result.stderr}")
    return {"status": "failed", "error": result.stderr}


# Run Safety and save results
def run_safety(repo_path, report_path):
    print(f"[INFO] Running Safety on {repo_path}...")
    requirements_file = generate_requirements(repo_path)


    if "# Placeholder" in requirements_file.read_text():
        print(f"[WARN] Skipping Safety: Placeholder requirements.txt in {repo_path}.")
        return {"status": "failed", "error": "Placeholder requirements.txt"}

    safety_report = report_path / f"{repo_path.name}_safety_report.json"
    result = subprocess.run(
        ["safety", "check", "--file", str(requirements_file), "--json"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0 or not result.stdout:
        print(f"[ERROR] Safety failed: {result.stderr}")
        return {"status": "failed", "error": result.stderr}
    try:
        safety_data = json.loads(result.stdout)
        # Handle serialization issues
        for k, v in safety_data.items():
            if isinstance(v, set):
                safety_data[k] = list(v)
        with safety_report.open("w") as f:
            json.dump(safety_data, f, indent=4)
        print(f"[INFO] Safety report saved to {safety_report}")
        return {"status": "success", "data": safety_data}
    except Exception as e:
        print(f"[ERROR] Failed to parse Safety output: {e}")
        return {"status": "failed", "error": f"Parsing error: {e}"}

def display_summary(results):
    print("\n" + "=" * 60)
    print(f"{'Repository':<20} {'Bandit':<15} {'Safety':<15}")
    print("=" * 60)
    for repo, data in results.items():
        bandit_status = f"Success ({len(data['bandit']['results'])} issues)" if data["bandit"][
                                                                                    "status"] == "success" else f"Failed ({data['bandit'].get('error', 'Unknown Error')})"
        safety_status = "Success" if data["safety"][
                                         "status"] == "success" else f"Failed ({data['safety'].get('error', 'Unknown Error')})"
        print(f"{repo:<20} {bandit_status:<15} {safety_status:<15}")
    print("=" * 60)

def main():
    results = {}
    for repo_url in REPOS:
        repo_path = clone_repo(repo_url, WORK_DIR)
        report_path = REPORT_DIR / repo_path.name
        report_path.mkdir(parents=True, exist_ok=True)

        # Run Bandit
        bandit_result = run_bandit(repo_path, report_path)

        # Run Safety
        safety_result = run_safety(repo_path, report_path)

        results[repo_path.name] = {
            "bandit": bandit_result,
            "safety": safety_result,
        }

        # Save final report
        final_report = report_path / f"{repo_path.name}_final_report.json"
        with final_report.open("w") as f:
            json.dump(results[repo_path.name], f, indent=4)
        print(f"[INFO] Final report for {repo_path.name} saved to {final_report}")

    display_summary(results)


if __name__ == "__main__":
    main()
