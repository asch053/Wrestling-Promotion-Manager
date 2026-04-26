import os
import re

replacements = {
    r'\bdamage\b': 'selling_burden',
    r'\bhealth\b': 'integrity',
    r'\balignment\b': 'kayfabe_status',
    r'\bconclude_storyline\b': 'execute_payoff',
    r'\bconclude\b': 'execute_payoff',
    r'\bAlignment\b': 'KayfabeStatus'
}

def sweep():
    path = 'requirements-documents'
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.md'):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = re.sub(old, new, new_content)
                
                if new_content != content:
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated: {full_path}")

if __name__ == "__main__":
    sweep()
