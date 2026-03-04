content = open('/project/blindnav/vision.py').read()
old_prompt = '''PROMPT = """You are a navigation assistant for a blind person walking outdoors.
Analyze this image and give ONE concise instruction, max 2 sentences.
Priority: hazards first, then obstacles, then path info.
Use simple words: ahead, left, right, stop, slow down.
Estimate distance: a few steps, nearby, about 2 meters.
If clear, say so. Never say I see or the image shows."""'''

new_prompt = '''PROMPT = """Navigation assistant for blind person. Reply in ONE short sentence only, max 10 words.
Examples: 'Path clear, walk ahead.' or 'Stop, obstacle ahead.' or 'Turn slightly left.'
No explanations. No extra words. Just the instruction."""'''

content = content.replace(old_prompt, new_prompt)
open('/project/blindnav/vision.py', 'w').write(content)
print("Done")
