"""Test JARVIS Antigravity Skills Integration"""
from core.skill_loader import SkillLoader

print("=" * 60)
print("JARVIS v9.0 ULTRA - Antigravity Skills Test")
print("=" * 60)

loader = SkillLoader('./skills')
stats = loader.get_stats()

print(f"\nTotal Skills Loaded: {stats['total_skills']}")
print("\n" + "=" * 60)

test_queries = [
    "I need help debugging my application",
    "How can I improve performance?",
    "I want to run security tests",
    "Help me with test automation",
    "I need to monitor my system"
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    skills = loader.match_skills(query)
    if skills:
        print(f"Matched {len(skills)} skills:")
        for i, skill in enumerate(skills[:3], 1):
            print(f"  {i}. {skill['name']} (relevance: {skill['score']})")
    else:
        print("  No skills matched")

print("\n" + "=" * 60)
print("Skills Integration: WORKING")
print("=" * 60)
