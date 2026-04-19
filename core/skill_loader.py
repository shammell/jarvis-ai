import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SkillLoader:
    def __init__(self, skills_path=None):
        # Use environment variable if available, otherwise use provided path
        if skills_path is None:
            skills_path = os.getenv("SKILLS_PATH", "./skills")

        self.skills_path = Path(skills_path)
        self.registry = {}
        self.load_skills()

    def load_skills(self):
        """Scan all SKILL.md files and build registry"""
        search_paths = []

        if self.skills_path.exists() and self.skills_path.is_dir():
            search_paths.append(self.skills_path)
        else:
            fallback = Path("./skills")
            if fallback.exists() and fallback.is_dir():
                search_paths.append(fallback)

        if not search_paths:
            return

        for base_path in search_paths:
            for skill_dir in base_path.iterdir():
                if skill_dir.is_dir():
                    skill_md = skill_dir / "SKILL.md"
                    if skill_md.exists():
                        self.parse_skill(skill_md, skill_dir)

        # Normalize configured path to the first valid path used
        if search_paths:
            self.skills_path = search_paths[0]

        # Deduplicate by skill name while preserving latest parsed entry
        if self.registry:
            self.registry = dict(self.registry)

        # No exception raised for missing external skill packs; system can boot
        # with built-in skills only.

        return

    def parse_skill(self, skill_md_path, skill_dir):
        """Parse SKILL.md frontmatter"""
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]

                    # Parse YAML (enhanced parser for multi-line values)
                    metadata = {}
                    current_key = None
                    current_value = []

                    for line in yaml_content.strip().split('\n'):
                        # Check if line starts a new key
                        if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                            # Save previous key-value if exists
                            if current_key:
                                metadata[current_key] = ' '.join(current_value).strip().strip("'\"")

                            # Start new key
                            key, value = line.split(':', 1)
                            current_key = key.strip()
                            current_value = [value.strip()]
                        elif current_key and line.strip():
                            # Continuation of previous value
                            current_value.append(line.strip())

                    # Save last key-value
                    if current_key:
                        metadata[current_key] = ' '.join(current_value).strip().strip("'\"")

                    # Only register if name exists
                    skill_name = metadata.get('name', '').strip()
                    if skill_name:
                        self.registry[skill_name] = {
                            'name': skill_name,
                            'description': metadata.get('description', ''),
                            'path': str(skill_dir),
                            'tags': [t.strip() for t in metadata.get('tags', '').split(',') if t.strip()],
                            'tools': [t.strip() for t in metadata.get('tools', '').split(',') if t.strip()],
                        }
        except Exception as e:
            pass  # Silently skip unparseable skills

    def match_skills(self, query: str) -> List[Dict]:
        """Match skills by query"""
        matches = []
        query_lower = query.lower()

        for skill_name, skill_data in self.registry.items():
            score = 0

            # Exact name match
            if skill_name.lower() == query_lower:
                score += 15

            # Name contains query
            elif query_lower in skill_name.lower():
                score += 10

            # Description contains query
            elif query_lower in skill_data['description'].lower():
                score += 5

            # Tag match
            for tag in skill_data['tags']:
                if query_lower in tag.lower():
                    score += 3

            if score > 0:
                matches.append({
                    'name': skill_name,
                    'score': score,
                    'data': skill_data
                })

        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches

    def get_skill(self, name: str) -> Optional[Dict]:
        """Get skill by name"""
        return self.registry.get(name)

    def list_skills(self) -> List[str]:
        """List all available skills"""
        return list(self.registry.keys())

    def get_stats(self) -> Dict:
        """Get registry statistics"""
        return {
            'total_skills': len(self.registry),
            'skills': list(self.registry.keys())
        }
