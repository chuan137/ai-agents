import feedparser
from google import genai
import re
import os

# --- 配置区 ---
RSS_URL = "https://www.reddit.com/r/ClaudeAI/.rss"
GOOGLE_GEMINI_BASE_URL = "http://localhost:6655/gemini"
GEMINI_API_TOKEN = os.environ["ANTHROPIC_AUTH_TOKEN"]
MAX_POSTS = 15  # 每次总结多少条帖子，避免超出 Token 限制

# 初始化 AI
gemini_client = genai.Client(
    api_key=GEMINI_API_TOKEN, http_options={"base_url": GOOGLE_GEMINI_BASE_URL}
)

def clean_html(raw_html):
    """清理 Reddit RSS 摘要中的 HTML 标签，只保留纯文本"""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext[:300] # 截取前300字，节省 Token

def fetch_reddit_data(url):
    print(f"正在同步 Reddit 频道数据...")
    # 加上 User-Agent 伪装，防止被 Reddit 拒之门外
    feed = feedparser.parse(url, response_headers={'User-Agent': 'Mozilla/5.0'})
    
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

    # 将数据格式化为 AI 易读的字符串
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
    response = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
    return response.text

if __name__ == "__main__":
    # 执行流程
    data = fetch_reddit_data(RSS_URL)
    report = generate_report(data)
    
    print("\n" + "="*50)
    print("🚀 深度话题追踪报告")
    print("="*50 + "\n")
    print(report)
    
    # 可选：保存到本地 Markdown 文件
    with open("daily_report.md", "w", encoding="utf-8") as f:
        f.write(report)
        print("\n✅ 报告已保存至 daily_report.md")
