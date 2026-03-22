import datetime
import os

import feedparser
from google import genai

# --- 配置区 ---
RSS_URL = "https://www.reddit.com/r/ClaudeAI/.rss"
GOOGLE_GEMINI_BASE_URL = "http://localhost:6655/gemini"
GEMINI_API_TOKEN = os.environ["ANTHROPIC_AUTH_TOKEN"]
MAX_POSTS = 15  # 每次总结多少条帖子，避免超出 Token 限制

# 初始化 AI
gemini_client = genai.Client(
    api_key=GEMINI_API_TOKEN, http_options={"base_url": GOOGLE_GEMINI_BASE_URL}
)


def get_reddit_updates(url):
    print(f"正在抓取: {url}...")
    # Reddit 的 RSS 有时需要伪装成浏览器访问，否则会被 429
    feed = feedparser.parse(url)

    entries = []
    for entry in feed.entries[:MAX_POSTS]:
        # 简单清洗 HTML 标签
        summary = entry.summary.split("<")[0] if "<" in entry.summary else entry.summary
        entries.append(
            f"【标题】: {entry.title}\n【链接】: {entry.link}\n【简述】: {summary[:200]}..."
        )

    return "\n\n".join(entries)


def summarize_content(raw_text):
    if not raw_text:
        return "今天该频道没有更新。"

    # prompt = f"""
    # 你是一个专业的资讯分析专家。以下是来自 Reddit 频道的最新动态：
    #
    # {raw_text}
    #
    # 请执行以下任务：
    # 1. 用中文总结今天最值得关注的 3-5 个核心话题。
    # 2. 过滤掉无意义的灌水、广告和情绪化吐槽。
    # 3. 每个话题给出一句话的背景介绍，并说明为什么值得关注。
    # 4. 采用简洁的 Markdown 格式输出。
    # """
    prompt = f"""
    你是一个专业的资讯分析专家。请根据以下 Reddit 内容生成一份中文简报：
    
    {raw_text}

    要求：
    1. 总结出最值得关注的 3-5 个话题。
    2. 过滤掉无意义的灌水、广告和情绪化吐槽。
    3. 每个话题用一小段话描述核心内容。
    3. **非常重要**：在每个话题总结的末尾，必须换行并附上该话题对应的【原文链接】。
    4. 格式示例：
       ### [话题标题]
       这是话题的具体总结内容...
       🔗 原文链接: [这里粘贴对应的 URL]
    """

    print("AI 正在深度思考并总结中...")
    response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text


def main():
    raw_data = get_reddit_updates(RSS_URL)
    summary = summarize_content(raw_data)

    print("\n" + "=" * 30)
    print(f"📅 Reddit 每日摘要 ({datetime.date.today()})")
    print("=" * 30 + "\n")
    print(summary)


if __name__ == "__main__":
    main()
