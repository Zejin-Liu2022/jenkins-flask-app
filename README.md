# Jenkins Flask CI/CD on macOS

本实验使用 Jenkins 在 macOS 上完成 Python Web 项目的完整 CI/CD。

流水线：环境检查 → Git 检出 → 独立环境安装依赖 → Flake8 → Pytest / 覆盖率 → PyInstaller 打包 → 部署并检查 HTTP 响应。

## 页面

- Jenkins：http://localhost:8080/job/jenkins-flask-app/
- Flask：http://localhost:5001/
- 当前运行版本：http://localhost:5001/health

应用首页返回 `Hello, CI/CD with Jenkins!`。构建生成 macOS 可执行文件，部署阶段运行这个构建产物。LaunchAgent 管理后台服务，构建结束后应用继续运行。部署失败时尝试恢复上一版服务。

## 本地开发

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flake8 app.py tests/ scripts/
python -m pytest tests/ --cov=app --cov-branch --cov-report=html
python app.py
```

运行本地源码前先停止已部署的服务，或设置其他端口：`APP_PORT=5002 python app.py`。

## Jenkins 配置

- 使用受支持的 Java 21。
- 插件：Git、Pipeline、JUnit、HTML Publisher、Pipeline Stage View、Timestamper；Email Extension 为可选邮件通知提供支持。
- 新建 Pipeline，使用 Pipeline script from SCM，仓库 `https://github.com/Zejin-Liu2022/jenkins-flask-app.git`，分支 `*/main`，脚本 `Jenkinsfile`。
- Python 路径默认 `/opt/homebrew/bin/python3`，其他机器按实际路径修改。
- 在 Jenkins 节点环境变量配置 `DEMO_DEPLOY_ROOT`，指定本实验的部署目录。
- 首次手动构建后，Poll SCM 每两分钟检查仓库变更并自动构建。
- 在构建页面查看阶段、测试结果、Coverage Report、构建产物。

Jenkins 和演示应用均只监听本机。此实验没有配置 SMTP 邮件通知。

## 自动触发验收

修改此文件的演示标记并提交到 main，等待 SCM 轮询触发构建。构建成功后，`/health` 的 revision 应与该次 Git 提交相同。

演示标记：automatic-trigger-verified
