import os
import re
from pathlib import Path

def update_skill(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.startswith('---'):
            return False

        parts = content.split('---', 2)
        if len(parts) < 3:
            return False

        frontmatter = parts[1]
        
        # Skip if already has preconditions
        if 'preconditions:' in frontmatter:
            return False

        # Infer signatures from name/description
        name_match = re.search(r'name:\s*(.+)', frontmatter)
        if not name_match:
            return False
            
        name = name_match.group(1).strip()
        
        # Add signatures to frontmatter
        new_frontmatter = frontmatter.rstrip()
        new_frontmatter += f"\npreconditions: []"
        new_frontmatter += f"\neffects: []"
        new_frontmatter += f"\ninput_type: any"
        new_frontmatter += f"\noutput_type: any\n"

        new_content = f"---{new_frontmatter}---{parts[2]}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

# Just update a few key ones for testing the workflow
skills_dir = Path("../antigravity-awesome-skills/skills")
test_skills = [
    "api-security-testing",
    "007",
    "generate-security-report",
    "static-security-analysis",
    "performance-profiling",
    "bottleneck-detection",
    "application-performance-optimization",
    "benchmark-verification"
]

updated = 0
for skill in test_skills:
    # Try exact match or partial match
    found = False
    for d in skills_dir.iterdir():
        if d.is_dir() and skill in d.name:
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                if update_skill(skill_md):
                    print(f"Updated {d.name}")
                    updated += 1
                found = True
                break

print(f"Updated {updated} skills with type signatures.")
