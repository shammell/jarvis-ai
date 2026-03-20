import os
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.skill_loader import SkillLoader


def cleanup_non_working_skills(dry_run=True):
    """Remove skill directories that don't have valid parseable skills"""

    # Load working skills
    print("Loading working skills...")
    loader = SkillLoader('./skills')
    working_skill_paths = set()

    # Get all paths of working skills
    for skill_data in loader.registry.values():
        skill_path = Path(skill_data['path'])
        working_skill_paths.add(skill_path.name)

    print(f"Found {len(working_skill_paths)} working skills")

    # Get all skill directories
    skills_path = Path('./skills')
    all_dirs = [d for d in skills_path.iterdir() if d.is_dir()]
    print(f"Found {len(all_dirs)} total skill directories")

    # Find non-working skills
    removed = []
    for skill_dir in all_dirs:
        skill_name = skill_dir.name

        # Check if this directory has a working skill
        if skill_name not in working_skill_paths:
            if dry_run:
                print(f"Would remove: {skill_dir}")
            else:
                try:
                    shutil.rmtree(skill_dir)
                    print(f"Removed: {skill_dir}")
                except Exception as e:
                    print(f"Error removing {skill_dir}: {e}")
            removed.append(str(skill_dir))

    # Save removal log
    log_file = 'removed_skills.log'
    with open(log_file, 'w') as f:
        f.write('\n'.join(removed))

    print(f"\nTotal to remove: {len(removed)}")
    print(f"Removal log saved to: {log_file}")

    return removed


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Clean up non-working skills')
    parser.add_argument('--execute', action='store_true',
                       help='Actually remove skills (default is dry-run)')
    parser.add_argument('--yes', action='store_true',
                       help='Skip confirmation prompt')
    args = parser.parse_args()

    if args.execute:
        print("=== EXECUTING ACTUAL REMOVAL ===")
        if args.yes:
            cleanup_non_working_skills(dry_run=False)
        else:
            response = input("Are you sure you want to remove non-working skills? (yes/no): ")
            if response.lower() == 'yes':
                cleanup_non_working_skills(dry_run=False)
            else:
                print("Cancelled.")
    else:
        print("=== DRY RUN (use --execute to actually remove) ===")
        cleanup_non_working_skills(dry_run=True)
