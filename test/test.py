import pkg_resources

args = []
for dist in pkg_resources.working_set:
    # 过滤掉部分系统包或你不想打包的包
    if dist.project_name.lower() not in ["pip", "setuptools", "wheel"]:
        args.append(f"--include-package={dist.project_name}")

print(" ".join(args))