import feedparser
import anthropic
import httpx
import re
import os

# --- 配置区 ---
RSS_URL = "https://www.reddit.com/r/ClaudeAI/.rss"
MAX_POSTS = 15  # 每次总结多少条帖子，避免超出 Token 限制

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_MAX_CHARS = 4096  # Telegram 单条消息上限

# 初始化 Anthropic 客户端（读取 ANTHROPIC_API_KEY 环境变量）
client = anthropic.Anthropic()


def clean_html(raw_html):
    """清理 Reddit RSS 摘要中的 HTML 标签，只保留纯文本"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext[:300]  # 截取前300字，节省 Token


def fetch_reddit_data(url):
    print("正在同步 Reddit 频道数据...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    feed = feedparser.parse(resp.text)

    posts = []
    for entry in feed.entries[:MAX_POSTS]:
        posts.append({
            "title": entry.title,
            "link": entry.link,
            "summary": clean_html(entry.summary)
        })
    return posts


def generate_report(posts):
    if not posts:
        return "未能抓取到任何内容，请检查网络或 RSS 链接。"

    context = ""
    for i, p in enumerate(posts):
        context += f"编号: {i+1}\n标题: {p['title']}\n摘要: {p['summary']}\n链接: {p['link']}\n\n"

    prompt = f"""
    你是一个专业的信息分析官。请分析以下 Reddit 帖子的内容：

    {context}

    任务要求：
    1. 识别出当前频道最值得关注的 3 个核心话题。
    2. 为每个话题写一段深度总结（包括讨论热点、争议点或技术细节）。
    3. **关键：** 在每个话题末尾，必须列出关联的原始帖子标题和[点击查看]的 Markdown 链接。
    4. 采用清晰的 Markdown 格式，使用二级标题分类。
    5. 如果有特别高赞或有代表性的评论观点，请单独标注。
    """

    print("AI 正在深度解析并生成报告...")
    with client.messages.stream(
        model="claude-haiku-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        report = stream.get_final_message()

    # 提取文本内容
    text = next(
        (block.text for block in report.content if block.type == "text"),
        "（AI 未返回文本内容）"
    )
    return text


def send_telegram(text: str):
    """将报告发送到 Telegram，超过 4096 字符则截断并提示。"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  未配置 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID，跳过 Telegram 发送。")
        return

    if len(text) > TELEGRAM_MAX_CHARS:
        truncated = text[: TELEGRAM_MAX_CHARS - 100]
        text = truncated + "\n\n…（报告过长，已截断，完整内容见 daily_report.md）"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        resp = httpx.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print("✅ 报告已发送至 Telegram")
    except httpx.HTTPStatusError as e:
        print(f"❌ Telegram 发送失败（HTTP {e.response.status_code}）：{e.response.text}")
    except httpx.RequestError as e:
        print(f"❌ Telegram 网络错误：{e}")


if __name__ == "__main__":
    data = fetch_reddit_data(RSS_URL)
    report = generate_report(data)

    print("\n" + "=" * 50)
    print("🚀 深度话题追踪报告")
    print("=" * 50 + "\n")
    print(report)

    # 保存到本地 Markdown 文件
    with open("daily_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        print("\n✅ 报告已保存至 daily_report.md")

    # 发送到 Telegram
    send_telegram(report)
