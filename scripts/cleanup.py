"""
Code cleanup script for Clash Environment Cleaner
用于清理项目中的冗余代码和无用文件
"""
import os
import re
from pathlib import Path


def find_redundant_imports(file_path):
    """查找冗余导入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    imports = []
    used_modules = set()
    
    # 找到所有导入语句
    for line in lines:
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            imports.append(line)
        # 查找使用了哪些模块
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)\.', line)
        if match:
            used_modules.add(match.group(1))
    
    # 检查哪些导入可能未使用
    unused_imports = []
    for imp in imports:
        for module in used_modules:
            if module in imp and 'import' in imp:
                break
        else:
            # 检查是否在代码中使用
            imp_module = imp.split()[-1].split('.')[0] if imp.startswith('import ') else imp.split()[1].split('.')[0]
            if imp_module not in used_modules and not imp.endswith('# Not used in this module'):
                unused_imports.append((imp, imp_module))
    
    return unused_imports


def clean_file(file_path):
    """清理单个文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 移除多余的空行
        if line.strip() == '' and i > 0 and cleaned_lines[-1].strip() == '':
            i += 1
            continue
        
        # 检查是否是注释掉的无用导入
        if '# Not used in this module' in line:
            i += 1
            continue
            
        cleaned_lines.append(line)
        i += 1
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)


def main():
    """主函数"""
    print("开始清理项目中的冗余代码...")
    
    # 遍历src目录下的所有Python文件
    src_dir = Path("src")
    for py_file in src_dir.rglob("*.py"):
        print(f"检查文件: {py_file}")
        
        # 查找冗余导入
        unused_imports = find_redundant_imports(py_file)
        if unused_imports:
            print(f"  发现未使用的导入: {unused_imports}")
        
        # 清理文件
        clean_file(py_file)
        print(f"  已清理: {py_file}")
    
    print("清理完成！")


if __name__ == "__main__":
    main()