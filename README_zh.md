# Whisper API WebUI

这是一个简单的 Web 应用，使用 OpenAI Whisper API (或像 Groq 这样的兼容服务) 来进行音频转录。它会自动压缩和分割音频文件，以适应 API 的大小限制，安全易用，并可部署在公网。

## 功能

- 使用 OpenAI Whisper API。
- 自动压缩和分割大于 25MB 的音频文件，以符合 API 的大小限制。
- 在用户界面实时显示转录进度。
- 提供密码保护的面板访问，可部署在公共网络。

## 部署

### Docker 部署

1. **编辑 `docker-compose.yml` 文件，设置所需的环境变量：**
   - **`OPENAI_API_KEY`**: 你的 OpenAI API 密钥。
   - **`API_BASE_URL`**: API 的基础 URL (默认为 `https://api.openai.com`)。你也可以使用像 Groq 这样兼容的服务。
   - **`SECRET_KEY`**: 用于保护应用会话的随机字符串。
   - **`ACCESS_PASSWORD_HASH`**: 用于登录的密码哈希值。

2.  **生成密码及哈希值:**
    使用 `password_gen.py` 生成密码的哈希值:
    ```bash
    python password_gen.py
    ```
    - 复制生成的哈希值，粘贴到 `docker-compose.yml` 中的 `ACCESS_PASSWORD_HASH` 字段。

3.  **启动应用:**
    ```bash
    docker-compose up -d
    ```

4.  **在浏览器中打开应用:**
    ```
    http://localhost:5000
    ```

5.  **使用你设置的密码登录。**

## 注意事项

-   这是一个为音频转录设计的轻量级面板。
-   上传的文件和转录结果不会被存储；处理完成后立即删除。
-   OpenAI API 端点和 API 密钥安全地存储在服务器上，用户不可见不可编辑。
-   Whisper 模型列表会自动从 OpenAI API 获取并过滤，仅显示包含 "whisper" 的模型。

## 截图
![image](https://github.com/user-attachments/assets/3f5fd707-d904-4418-a088-04b46cfe3842)
![image](https://github.com/user-attachments/assets/5379bdb7-9c5c-473f-9455-58558bce8b79)
