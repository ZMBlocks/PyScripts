import psutil, os, requests, tqdm, subprocess, traceback, random, time, sys

DiagnosticProgramPath: str = "C:/Program Files/Microsoft Visual Studio 17.0/Team Tools/DiagnosticsHub/Collector/VSDiagnostics.exe"

def quit() -> None:
    os.system("pause")
    sys.exit()

def get_server_list() -> list[psutil.Process]:
    result: list[psutil.Process] = []
    for pid in psutil.pids():
        try: 
            process = psutil.Process(pid)
            if process.name() in ["bedrock_server.exe", "bedrock_server_mod.exe"]:
                result.append(process)
        except psutil.NoSuchProcess: pass
    return result

def downloadProgram() -> None:
    try:
        response: requests.Response = requests.get(
            "https://aka.ms/vs/17/release/RemoteTools.amd64ret.chs.exe",
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            },
            stream = True,
            allow_redirects = True
        )
        if response.status_code != 200:
            print(f"下载失败 HTTP状态码：{response.status_code}")
            quit()
        progress = tqdm.tqdm(desc = f"正在下载诊断程序", total = round(int(response.headers.get("content-length", 0)) / 1024 / 1024, 2), unit = "MB")
        with open("./RemoteTools.amd64ret.chs.exe", "wb") as file:
            for data in response.iter_content(chunk_size = 1024 * 1024):
                file.write(data)
                progress.update(round(len(data) / 1024 / 1024, 2))
        progress.close()
        print("下载完成")
    except requests.exceptions.RequestException as e:
        print(f"下载失败")
        traceback.print_exc()
        quit()

def wait_with_animation(duration: float, title: str, sleep_time: float = 0.2, animation_chars: list[str] = ['-', '\\', '|', '/']) -> None:
    end_time: float = time.time() + duration

    while time.time() < end_time:
        for char in animation_chars:
            sys.stdout.write(f'\r{title} {char}')
            sys.stdout.flush()
            time.sleep(sleep_time)

    print()

def main() -> None:
    if not os.path.exists(DiagnosticProgramPath):
        print("诊断程序未安装")
        if not os.path.exists("./RemoteTools.amd64ret.chs.exe"):
            print("诊断程序安装包未找到 开始下载")
            downloadProgram()
        print("开始安装诊断程序")
        result: subprocess.CompletedProcess[bytes] = subprocess.run(["RemoteTools.amd64ret.chs.exe", "/install", "/quiet", "/norestart", "/log", "install.log"])
        if result.returncode != 0 or not os.path.exists(DiagnosticProgramPath):
            print("安装失败")
            os.system("start install.log")
            quit()
        print("安装完成")
        os.remove("./RemoteTools.amd64ret.chs.exe")
        for file in os.listdir():
            if file.endswith(".log") and file.startswith("install"):
                os.remove(file)
    servers: list[psutil.Process] = get_server_list()
    if len(servers) == 0: return print("没有服务器正在运行")
    for index, server in enumerate(servers):
        print(f"{index + 1}: (PID: {server.pid}) {server.exe()}")
    while True:
        try:
            index = int(input("请输入要监测的服务器编号："))
            if index > len(servers) or index <= 0: raise ValueError
            server: psutil.Process = servers[index - 1]
            break
        except (ValueError, IndexError): pass
    
    id: int = random.randint(1, 255)
    result = subprocess.run(
        [
            DiagnosticProgramPath,
            "start",
            str(id),
            f"/attach:{server.pid}",
            "/loadConfig:AgentConfigs\\CPUUsageBase.json"
        ],
        cwd = os.path.dirname(DiagnosticProgramPath),
        capture_output = True
    )
    if result.returncode != 0:
        print("监视失败")
        quit()
    print(f"监视成功 ID: {id}")
    wait_with_animation(5, "请耐心等待5秒")
    result = subprocess.run(
        [
            DiagnosticProgramPath,
            "stop",
            str(id),
            "/output:output"
        ],
        capture_output = True
    )
    if result.returncode != 0:
        print("停止监视失败")
        quit()
    print("监测完成，请将程序下的output.diagsession文件发送给开发者")
    quit()
    
if __name__ == "__main__":
    main()