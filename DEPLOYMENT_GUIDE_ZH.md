# 把 Ask 从你的电脑搬到网上

## 先认识这三个地方

**这个 HW 4 文件夹**是工作台。`portfolio` 是原网站的一份本地副本，`ask-backend` 是新增的后端。改这里的文件不会自动改变线上网站。

**GitHub**是存放和管理代码的地方。前端继续使用原来的仓库；后端需要一个新的公开仓库。

**Render**负责运行后端。GitHub 存着“工作说明书”，Render 按照说明书让程序持续工作。免费服务空闲时会休眠，第一次访问可能较慢。

## 在本机查看

终端是输入文字指令的窗口。打开 Mac 的“终端”，运行：

```sh
cd "$HOME/Desktop/HW 4/ask-backend"
.venv/bin/python app.py
```

这会启动后端。这个终端需要保持运行；按 Control+C 可以停止。再开一个终端窗口：

```sh
cd "$HOME/Desktop/HW 4/portfolio"
python3 -m http.server 4173 --bind 127.0.0.1
```

浏览器打开 http://127.0.0.1:4173/projects/xiaoliuren/ 。如果代理已经启动了这两个服务，就直接打开网页，无需重复启动。如果提示端口已占用，说明已有程序在这个地址等候请求。

`127.0.0.1` 代表你自己的电脑。`4173` 和 `5050` 是两个不同的门牌号：一个接收页面访问，另一个接收计算请求。

## 第一步：上传后端

1. 登录 GitHub，点击 New repository。
2. 名称填 `ask-backend`，选择 Public，创建仓库。
3. 在空仓库页面选择 uploading an existing file，把本地 `ask-backend` 里的 `app.py`、`requirements.txt`、`render.yaml`、README、说明文档、prompt log 和 `tests` 文件夹上传，提交保存。
4. 不要上传 `.venv`、`__pycache__` 或任何 `.env`。它们不是作业源代码。`.gitignore` 可以上传。
5. 检查仓库首页能直接看到 `app.py`，而不是再套着一个 `ask-backend` 文件夹。

## 第二步：让 Render 运行代码

在 Render 登录后，选择 New → Web Service，连接刚创建的后端仓库。账户注册、条款或 GitHub 授权需要你按界面提示完成。

填写：

| 设置 | 值 | 意思 |
| --- | --- | --- |
| Name | `ask-backend` | 服务的名字，最终网址以 Render 分配的为准 |
| Language / Runtime | Python 3 | 代码使用的语言 |
| Branch | `main` | 使用仓库的主版本 |
| Root Directory | 留空 | app.py 位于仓库最外层 |
| Build Command | `pip install -r requirements.txt` | 安装所需工具 |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 30` | 开始接收请求 |
| Instance Type | Free | 使用免费实例 |
| Health Check Path | `/health` | 检查服务是否正常启动 |

在 Environment 中添加 `PYTHON_VERSION` = `3.12.8`，以及 `ALLOWED_ORIGINS` = `https://toooonyliu.github.io`。它们是环境变量，相当于给运行环境留下的设置便签；这里没有密码，也不需要 API key。

点击部署后观察日志。看到 Live 后，复制 Render 提供的网址。在网址后添加 `/health` 并打开，应看到包含 `"status":"ok"` 的文字。浏览器显示 JSON 而不是漂亮页面是正常的：这是给前端读的回执。

## 第三步：把真实地址告诉前端

打开 `portfolio/projects/xiaoliuren/backend-config.js`：

```js
export const DEPLOYED_BACKEND_URL = '';
```

把空引号替换为 Render 实际分配的 HTTPS 地址，末尾不要加 `/`。不要猜网址，也不要用本机的 `127.0.0.1` 地址。

接着把前端改动提交回原来的 GitHub 仓库，等待 GitHub Pages 更新。改动清单包含 `app.js`、`core.js`、`content.js`、`index.html`，新文件 `backend-api.js`、`backend-config.js`，以及相应 README、prompt log 和测试。

**CORS** 是浏览器检查“这个网页能不能读取那个服务器回答”的规则。我们已在后端允许你的 GitHub Pages 网站。它不是账号登录，也不是后端的密码。

## 第四步：检查作业真的能用

1. 用线上 Ask 页面输入一个新的问题，确认有结果和动画。已有历史问题会直接打开保存结果，因此演示时用新问题。
2. 空着输入框点击开始，应出现友好提示。
3. 用浏览器的开发者工具 → Network 找到 `reading` 请求，确认请求地址是 Render，返回的是 JSON。
4. 检查手机或窄屏，切换中英文。登录和历史沿用原功能，可再确认一次。
5. 把实际 Render 地址补到后端 README。
6. 录制简短视频，展示输入、结果、后台请求以及 GitHub/Render 地址。
7. 将可访问的视频链接、前后端仓库链接、部署链接填入课程表单。视频分享权限要用无痕窗口检查。

目前本地版本不等于已经提交作业；完成部署、视频与表单才是完整交付。
