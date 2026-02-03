import os
import json
import shutil
import subprocess
import tempfile
import argparse
import sys

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_ROOT = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(BASE_DIR, "config", "sources.json")

class SkillManager:
    def __init__(self):
        self.config = self._load_config()
        self.temp_dir = tempfile.mkdtemp()
        self.registries = self.config.get("registries", [])
        # Sort registries by priority (high to low)
        self.registries.sort(key=lambda x: x.get("priority", 0), reverse=True)

    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            print(f"⚠️ Config file not found at {CONFIG_FILE}")
            return {}
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)

    def cleanup(self):
        shutil.rmtree(self.temp_dir)

    def _clone_registry(self, registry):
        """Clones a registry to a temp path and returns the path to skills root."""
        repo_name = registry["name"]
        repo_url = registry["url"]
        branch = registry.get("branch", "main")
        skills_subpath = registry.get("skills_root", "")
        
        target_dir = os.path.join(self.temp_dir, repo_name)
        
        # print(f"   ⬇️  Fetching registry: {repo_name}...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, repo_url, target_dir],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to clone {repo_name}: {e}")
            return None

        full_skills_path = os.path.join(target_dir, skills_subpath)
        if not os.path.exists(full_skills_path):
            print(f"   ❌ Skills root '{skills_subpath}' not found in {repo_name}")
            return None
            
        return full_skills_path

    def list_skills(self):
        print("\n🔍 Available Skills in Remote Registries:\n")
        seen_skills = set()
        
        for reg in self.registries:
            path = self._clone_registry(reg)
            if not path:
                continue
            
            print(f"📦 Registry: {reg['name']}")
            if os.path.exists(path):
                skills = sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and not d.startswith('.')])
                for skill in skills:
                    if skill not in seen_skills:
                        installed = "✅ Installed" if os.path.exists(os.path.join(SKILLS_ROOT, skill)) else "   Available"
                        print(f"  - {skill:<30} {installed}")
                        seen_skills.add(skill)
        print("")

    def install_skill(self, skill_name, force=False):
        target_path = os.path.join(SKILLS_ROOT, skill_name)
        if os.path.exists(target_path) and not force:
            print(f"⚠️  Skill '{skill_name}' is already installed. Use --force to reinstall or 'update' command.")
            return

        print(f"🚀 Installing '{skill_name}'...")
        
        found = False
        for reg in self.registries:
            path = self._clone_registry(reg)
            if not path:
                continue
                
            source_skill_path = os.path.join(path, skill_name)
            if os.path.exists(source_skill_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(source_skill_path, target_path)
                print(f"✅ Successfully installed '{skill_name}' from {reg['name']}")
                found = True
                break
        
        if not found:
            print(f"❌ Skill '{skill_name}' not found in any registry.")

    def update_all(self):
        print("🚀 Updating all installed skills...\n")
        
        # 1. Identify what skills are installed locally
        installed_skills = [d for d in os.listdir(SKILLS_ROOT) if os.path.isdir(os.path.join(SKILLS_ROOT, d)) and not d.startswith('.')]
        
        if not installed_skills:
            print("No skills found to update.")
            return

        print(f"📋 Local skills identified: {len(installed_skills)}")
        
        updated_count = 0
        
        # 2. Iterate through registries
        for reg in self.registries:
            # Optimization: Clone registry ONCE
            reg_path = self._clone_registry(reg)
            if not reg_path:
                continue
                
            # Check for matches
            for skill in installed_skills:
                source_path = os.path.join(reg_path, skill)
                dest_path = os.path.join(SKILLS_ROOT, skill)
                
                if os.path.exists(source_path):
                    # Found a match! Update it.
                    # print(f"   🔄 Updating {skill}...")
                    
                    # Remove and copy to ensure clean state (deleting removed files)
                    shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    print(f"   ✅ Updated: {skill}")
                    updated_count += 1
        
        print(f"\n✨ Update complete. {updated_count} skills processed.")


def main():
    parser = argparse.ArgumentParser(description="Agent Skill Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Command: list
    subparsers.add_parser("list", help="List all available skills from remote registries")

    # Command: install
    install_parser = subparsers.add_parser("install", help="Install a specific skill")
    install_parser.add_argument("skill_name", help="Name of the skill to install")
    install_parser.add_argument("--force", action="store_true", help="Force overwrite if exists")

    # Command: update
    subparsers.add_parser("update", help="Update all currently installed skills")

    args = parser.parse_args()
    
    manager = SkillManager()
    try:
        if args.command == "list":
            manager.list_skills()
        elif args.command == "install":
            manager.install_skill(args.skill_name, args.force)
        elif args.command == "update":
            manager.update_all()
        else:
            # Default behavior if no command: update
            manager.update_all()
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main()
