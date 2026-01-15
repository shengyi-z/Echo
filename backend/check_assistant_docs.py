"""
检查 Assistant 的文档列表
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://app.backboard.io/api"

def list_assistant_documents(assistant_id: str = None):
    """列出 Assistant 的所有文档"""
    api_key = os.getenv("BACKBOARD_API_KEY")
    
    if not assistant_id:
        assistant_id = os.getenv("BACKBOARD_ASSISTANT_ID")
    
    if not api_key or not assistant_id:
        print("❌ 缺少 API key 或 assistant ID")
        return
    
    headers = {"X-API-Key": api_key}
    
    try:
        print(f"🔍 检查 Assistant: {assistant_id}\n")
        
        # 获取 assistant 信息
        response = requests.get(
            f"{BASE_URL}/assistants/{assistant_id}",
            headers=headers
        )
        response.raise_for_status()
        assistant_data = response.json()
        
        print(f"📋 Assistant 信息:")
        print(f"   名称: {assistant_data.get('name')}")
        print(f"   ID: {assistant_data.get('assistant_id')}")
        print(f"   描述: {assistant_data.get('description', 'N/A')[:100]}...")
        
        # 获取文档列表
        response = requests.get(
            f"{BASE_URL}/assistants/{assistant_id}/documents",
            headers=headers
        )
        response.raise_for_status()
        documents = response.json()
        
        print(f"\n📚 文档列表:")
        if isinstance(documents, list) and len(documents) > 0:
            for i, doc in enumerate(documents, 1):
                print(f"\n   文档 {i}:")
                print(f"   ├─ ID: {doc.get('document_id')}")
                print(f"   ├─ 文件名: {doc.get('filename')}")
                print(f"   ├─ 状态: {doc.get('status')}")
                print(f"   ├─ 创建时间: {doc.get('created_at')}")
                if doc.get('summary'):
                    print(f"   └─ 摘要: {doc.get('summary')[:100]}...")
            
            print(f"\n✅ 总共 {len(documents)} 个文档")
            
            # 检查是否有 indexed 的文档
            indexed_docs = [d for d in documents if d.get('status') == 'indexed']
            if indexed_docs:
                print(f"✅ 有 {len(indexed_docs)} 个文档已索引完成，可以使用")
            else:
                pending_docs = [d for d in documents if d.get('status') in ['pending', 'processing']]
                if pending_docs:
                    print(f"⏳ 有 {len(pending_docs)} 个文档正在处理中...")
        else:
            print("   ⚠️ 没有找到文档")
            print("   提示: 运行 python -m backend.init_echo 创建新 assistant 并自动上传文档")
        
        return documents
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

if __name__ == "__main__":
    list_assistant_documents()
