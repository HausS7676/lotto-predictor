import re

filepath = r"c:\Users\이정호\Desktop\temp\antigravity\lotto-predictor\lotto_predictor_v2.py"
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure `re` is imported at the top
if 'import re' not in content:
    content = 'import re\n' + content

# Split content right after rules_config definition ends
parts = content.split("}\n\n\ngenerate_clicked")
if len(parts) == 1:
    parts = content.split("}\n\ngenerate_clicked")

if len(parts) != 2:
    print("Could not find split point")
    exit(1)

top_part = parts[0] + "}\n\n"
bottom_part = "generate_clicked" + parts[1]

# In bottom_part, we need to extract:
# 1. Recent draws logic block (starts with `if not generate_clicked:`)
# 2. Sidebar setup logic (from `st.sidebar.header("설정")` up to the end of `uploaded_file` processing)
# 3. Generate combos logic (starts with `if generate_clicked:`)
# 4. Final footer (st.markdown("---"))

# This is a bit complex. Let's just use Python's AST or string replacement carefully.
# Actually, it's easier to just find the sections using regex.

# Section: Recent draws logic
recent_draws_match = re.search(r'(if not generate_clicked:.*?)(?=st\.sidebar\.header\("설정"\))', bottom_part, re.DOTALL)
recent_draws_code = recent_draws_match.group(1).strip()

# Section: Sidebar config (excluding upload)
sidebar_config_match = re.search(r'(st\.sidebar\.header\("설정"\).*?)(?=st\.sidebar\.markdown\("---"\)\nst\.sidebar\.markdown\("### 🆘 서버 차단 시 백업 플랜"\))', bottom_part, re.DOTALL)
sidebar_config_code = sidebar_config_match.group(1).strip()

# Section: Upload logic
upload_match = re.search(r'(st\.sidebar\.markdown\("---"\)\nst\.sidebar\.markdown\("### 🆘 서버 차단 시 백업 플랜"\).*?)(?=if generate_clicked:)', bottom_part, re.DOTALL)
upload_code = upload_match.group(1).strip()

# Section: Generation logic
gen_match = re.search(r'(if generate_clicked:.*?)(?=st\.markdown\("---"\)\nst\.markdown\("본 시스템은)', bottom_part, re.DOTALL)
gen_code = gen_match.group(1).strip()

# Section: Footer
footer_match = re.search(r'(st\.markdown\("---"\)\nst\.markdown\("본 시스템은.*?)$', bottom_part, re.DOTALL)
footer_code = footer_match.group(1).strip()

# Now rewrite sidebar_config_code to change multiselect to text_input
new_sidebar_config_code = sidebar_config_code.replace('''st.sidebar.markdown("### 특정 번호 포함/제외")
include_nums = st.sidebar.multiselect("반드시 포함할 번호 (최대 5개)", list(range(1, 46)))
exclude_nums = st.sidebar.multiselect("제외할 번호", list(range(1, 46)))

if len(include_nums) > 5:
    st.sidebar.error("포함할 번호는 5개까지만 선택할 수 있습니다.")
if set(include_nums) & set(exclude_nums):
    st.sidebar.error("포함할 번호와 제외할 번호에 같은 숫자가 있습니다.")''', '''st.sidebar.markdown("### 특정 번호 포함/제외")
include_text = st.sidebar.text_input("반드시 포함할 번호 (콤마나 공백 구분, 최대 5개)", "")
exclude_text = st.sidebar.text_input("제외할 번호 (콤마나 공백 구분)", "")

def parse_numbers(text):
    if not text.strip(): return []
    parts = re.split(r'[,\s]+', text.strip())
    nums = []
    for p in parts:
        if p.isdigit():
            n = int(p)
            if 1 <= n <= 45:
                nums.append(n)
    return list(set(nums))

include_nums = parse_numbers(include_text)
exclude_nums = parse_numbers(exclude_text)

if len(include_nums) > 5:
    st.sidebar.error("포함할 번호는 5개까지만 입력할 수 있습니다.")
if set(include_nums) & set(exclude_nums):
    st.sidebar.error("포함할 번호와 제외할 번호에 중복된 숫자가 있습니다.")''')

# Add the generate button at the end of new_sidebar_config_code
new_sidebar_config_code += '\n\ngenerate_clicked = st.sidebar.button("번호 생성하기", key="generate_button", type="primary", use_container_width=True)'

# Put it all together
new_content = top_part + "\n"
new_content += new_sidebar_config_code + "\n\n"
new_content += upload_code + "\n\n"

# Main area
new_content += "if not generate_clicked:\n"
# indent recent draws code
indented_recent = "\n".join("    " + line for line in recent_draws_code.split("\n")[1:]) # skip the 'if not generate_clicked:' line
new_content += indented_recent + "\n\n"

new_content += "else:\n"
indented_gen = "\n".join("    " + line for line in gen_code.split("\n")[1:]) # skip 'if generate_clicked:'
new_content += indented_gen + "\n\n"

new_content += footer_code + "\n"

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Update 3 complete")
